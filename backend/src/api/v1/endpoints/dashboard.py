"""仪表盘数据接口 — 从数据库查询真实运营数据"""

from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from src.api.v1.endpoints.auth import get_current_user
from src.models.database import async_session
from src.models.patient import MedicalRecord
from src.models.icd import CodingResult
from src.models.qc import QCResult
from src.config.settings import get_settings

router = APIRouter()

settings = get_settings()


def _days_ago(days: int) -> date:
    return (datetime.now() - timedelta(days=days)).date()


@router.get("/overview")
async def get_overview(user: dict = Depends(get_current_user)):
    """全院DRG运营概览"""
    async with async_session() as db:
        # Total cases
        total_cases_r = await db.execute(select(func.count()).select_from(MedicalRecord))
        total_cases = total_cases_r.scalar() or 0

        # Average stay days
        avg_stay_r = await db.execute(
            select(func.avg(
                func.julianday(MedicalRecord.discharge_date) - func.julianday(MedicalRecord.admission_date)
            )).where(MedicalRecord.discharge_date.isnot(None), MedicalRecord.admission_date.isnot(None))
        )
        avg_stay_days = round(avg_stay_r.scalar() or 0.0, 1)

        # AI coding rate
        ai_count_r = await db.execute(
            select(func.count()).select_from(CodingResult).where(CodingResult.coder_type == "ai")
        )
        ai_coding_rate = round((ai_count_r.scalar() or 0) / max(total_cases, 1), 2)

        # QC pass rate (records with 0 QC issues)
        records_with_issues_r = await db.execute(
            select(func.count(func.distinct(QCResult.record_id)))
        )
        records_with_issues = records_with_issues_r.scalar() or 0
        qc_pass_rate = round(1 - records_with_issues / max(total_cases, 1), 2)

        # Extract DRG weights from coding results JSON and compute CMI / total RW
        # Use SQLite JSON functions to extract $.drg_weight from codes JSON
        drg_stats_r = await db.execute(
            select(
                func.count(),
                func.sum(func.json_extract(CodingResult.codes, '$.drg_weight')),
            ).where(CodingResult.codes.isnot(None))
        )
        drg_count, total_weight = drg_stats_r.one()
        cmi = round(total_weight / max(drg_count, 1), 2) if total_weight else 0.0
        total_weight = round(total_weight or 0.0, 2)

        # Cost/time consumption indices (benchmark vs. expected)
        cost_idx_r = await db.execute(
            select(func.avg(func.json_extract(CodingResult.codes, '$.drg_weight') * settings.drg_base_rate))
            .where(CodingResult.codes.isnot(None))
        )
        avg_cost = round(cost_idx_r.scalar() or 0.0, 0)

        # Time consumption index: actual avg days / expected avg days (from DRG weight * 3.5)
        time_idx_r = await db.execute(
            select(
                func.avg(
                    (func.julianday(MedicalRecord.discharge_date) - func.julianday(MedicalRecord.admission_date))
                    / func.nullif(func.json_extract(CodingResult.codes, '$.drg_weight') * 3.5, 0)
                )
            ).select_from(MedicalRecord).join(CodingResult, CodingResult.record_id == MedicalRecord.id)
            .where(
                MedicalRecord.discharge_date.isnot(None),
                MedicalRecord.admission_date.isnot(None),
                CodingResult.codes.isnot(None),
            )
        )
        time_consumption_index = round(time_idx_r.scalar() or 1.0, 2)

        # Low risk mortality (simulated — we don't track mortality in demo data)
        low_risk_mortality_rate = 0.0

    return {
        "total_cases": total_cases,
        "total_weight": total_weight,
        "cmi": cmi,
        "avg_cost": avg_cost,
        "avg_stay_days": avg_stay_days,
        "cost_consumption_index": round(avg_cost / max(settings.drg_base_rate, 1.0) / max(cmi, 0.1), 2),
        "time_consumption_index": time_consumption_index,
        "low_risk_mortality_rate": low_risk_mortality_rate,
        "ai_coding_rate": ai_coding_rate,
        "qc_pass_rate": qc_pass_rate,
    }


@router.get("/department-ranking")
async def get_department_ranking(limit: int = 10,
                                 user: dict = Depends(get_current_user)):
    """科室排名 — 按CMI降序"""
    async with async_session() as db:
        # Join MedicalRecord → CodingResult to get DRG weight per record, then group by department
        dept_r = await db.execute(
            select(
                MedicalRecord.department,
                func.count().label("cases"),
                func.avg(func.json_extract(CodingResult.codes, '$.drg_weight')).label("avg_weight"),
                func.avg(
                    func.julianday(MedicalRecord.discharge_date) - func.julianday(MedicalRecord.admission_date)
                ).label("avg_stay"),
            )
            .join(CodingResult, CodingResult.record_id == MedicalRecord.id)
            .where(
                MedicalRecord.discharge_date.isnot(None),
                MedicalRecord.admission_date.isnot(None),
                CodingResult.codes.isnot(None),
            )
            .group_by(MedicalRecord.department)
            .order_by(func.avg(func.json_extract(CodingResult.codes, '$.drg_weight')).desc())
        )

        rankings = []
        for i, (dept, cases, avg_weight, avg_stay) in enumerate(dept_r.all()):
            if dept is None:
                continue
            rankings.append({
                "rank": i + 1,
                "dept": dept,
                "cases": cases,
                "cmi": round(avg_weight or 0.0, 2),
                "cost_index": round((avg_weight or 1.0) * settings.drg_base_rate / 18560, 2),
                "avg_days": round(avg_stay or 0.0, 1),
            })

        # Apply limit and optional metric sort
        rankings = rankings[:limit]
    return {"rankings": rankings}


@router.get("/qc-trend")
async def get_qc_trend(days: int = 90, user: dict = Depends(get_current_user)):
    """质控评分趋势 — 按周聚合QC结果，3周移动平均平滑"""
    async with async_session() as db:
        cutoff = _days_ago(min(days, 180))

        # Two queries: one for total records per day, one for records with issues per day
        # This avoids the LEFT JOIN row-duplication problem
        daily_total_r = await db.execute(
            select(
                func.date(MedicalRecord.admission_date).label("dt"),
                func.count(MedicalRecord.id).label("total_checks"),
            )
            .where(MedicalRecord.admission_date >= cutoff)
            .group_by(func.date(MedicalRecord.admission_date))
            .order_by("dt")
        )
        daily_totals = {row[0]: row[1] for row in daily_total_r.all()}

        daily_issues_r = await db.execute(
            select(
                func.date(MedicalRecord.admission_date).label("dt"),
                func.count(func.distinct(MedicalRecord.id)).label("records_with_issues"),
            )
            .select_from(MedicalRecord)
            .join(QCResult, QCResult.record_id == MedicalRecord.id)
            .where(MedicalRecord.admission_date >= cutoff)
            .group_by(func.date(MedicalRecord.admission_date))
            .order_by("dt")
        )
        daily_issues = {row[0]: row[1] for row in daily_issues_r.all()}

        # Aggregate into weekly buckets
        weeks: dict[str, list] = {}
        for dt_str in sorted(set(daily_totals.keys()) | set(daily_issues.keys())):
            total = daily_totals.get(dt_str, 0)
            issues = daily_issues.get(dt_str, 0)
            d = datetime.strptime(dt_str, "%Y-%m-%d").date()
            week_start = (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")
            if week_start not in weeks:
                weeks[week_start] = {"total": 0, "issues": 0}
            weeks[week_start]["total"] += total
            weeks[week_start]["issues"] += issues

        # Build weekly trend
        raw_trend = []
        for wk in sorted(weeks.keys()):
            w = weeks[wk]
            defect_rate = round(w["issues"] / max(w["total"], 1), 3)
            score = round(100.0 - defect_rate * 100, 1)
            raw_trend.append({
                "date": wk,
                "avg_score": score,
                "total_checks": w["total"],
                "defect_rate": defect_rate,
            })

        # 3-week moving average for smoothness (if >= 3 weeks of data)
        trend = raw_trend
        if len(raw_trend) >= 3:
            trend = []
            for i in range(len(raw_trend)):
                window = raw_trend[max(0, i - 2):i + 1]
                w_size = len(window)
                trend.append({
                    "date": raw_trend[i]["date"],
                    "avg_score": round(sum(w["avg_score"] for w in window) / w_size, 1),
                    "total_checks": sum(w["total_checks"] for w in window),
                    "defect_rate": round(sum(w["defect_rate"] for w in window) / w_size, 2),
                })

        # Daily CMI for the trend chart
        daily_cmi_r = await db.execute(
            select(
                func.date(MedicalRecord.admission_date).label("dt"),
                func.avg(func.json_extract(CodingResult.codes, '$.drg_weight')).label("avg_cmi"),
            )
            .join(CodingResult, CodingResult.record_id == MedicalRecord.id)
            .where(MedicalRecord.admission_date >= cutoff, CodingResult.codes.isnot(None))
            .group_by(func.date(MedicalRecord.admission_date))
            .order_by("dt")
        )
        daily_cmi = {row[0]: row[1] for row in daily_cmi_r.all()}

        # Attach cmi to each trend week
        for t in trend:
            wk_d = datetime.strptime(t["date"], "%Y-%m-%d").date()
            week_cmis = [round(cmi, 2) for dt_str, cmi in daily_cmi.items()
                         if (datetime.strptime(dt_str, "%Y-%m-%d").date() - timedelta(days=datetime.strptime(dt_str, "%Y-%m-%d").date().weekday())).strftime("%Y-%m-%d") == t["date"]]
            t["cmi"] = round(sum(week_cmis) / len(week_cmis), 2) if week_cmis else None

    return {"trend": trend}


@router.get("/coding-accuracy")
async def get_coding_accuracy(days: int = 90, user: dict = Depends(get_current_user)):
    """编码准确率趋势 — 按日期聚合AI/人工编码置信度"""
    async with async_session() as db:
        cutoff = _days_ago(min(days, 180))

        # Daily AI accuracy from confidence_scores JSON
        daily_r = await db.execute(
            select(
                func.date(MedicalRecord.admission_date).label("dt"),
                func.avg(
                    func.json_extract(CodingResult.confidence_scores, '$.total')
                ).label("ai_acc"),
                func.count(CodingResult.id).label("cnt"),
            )
            .select_from(MedicalRecord)
            .join(CodingResult, CodingResult.record_id == MedicalRecord.id)
            .where(
                MedicalRecord.admission_date >= cutoff,
                CodingResult.coder_type == "ai",
                CodingResult.confidence_scores.isnot(None),
            )
            .group_by(func.date(MedicalRecord.admission_date))
            .order_by("dt")
        )

        trend = []
        for dt, ai_acc, cnt in daily_r.all():
            trend.append({
                "date": str(dt),
                "ai_accuracy": round(ai_acc or 0.0, 3),
            })

        # Overall accuracy
        overall_r = await db.execute(
            select(func.avg(func.json_extract(CodingResult.confidence_scores, '$.total')))
            .where(CodingResult.coder_type == "ai", CodingResult.confidence_scores.isnot(None))
        )
        overall_accuracy = round(overall_r.scalar() or 0.0, 3)

    return {
        "accuracy_trend": trend,
        "overall_accuracy": overall_accuracy,
    }


@router.get("/high-frequency-issues")
async def get_high_frequency_issues(days: int = 90, limit: int = 10,
                                     user: dict = Depends(get_current_user)):
    """高频质控缺陷 — 按QC问题描述聚合"""
    async with async_session() as db:
        cutoff = _days_ago(min(days, 180))

        issues_r = await db.execute(
            select(
                QCResult.line_snippet,
                func.count().label("cnt"),
            )
            .join(MedicalRecord, MedicalRecord.id == QCResult.record_id)
            .where(MedicalRecord.admission_date >= cutoff)
            .group_by(QCResult.line_snippet)
            .order_by(func.count().desc())
            .limit(limit)
        )

        total_qc_r = await db.execute(
            select(func.count(QCResult.id))
            .join(MedicalRecord, MedicalRecord.id == QCResult.record_id)
            .where(MedicalRecord.admission_date >= cutoff)
        )
        total_qc = max(total_qc_r.scalar() or 1, 1)

        issues = []
        for snippet, cnt in issues_r.all():
            issues.append({
                "issue": snippet or "未知问题",
                "count": cnt,
                "rate": f"{round(cnt / total_qc * 100, 1)}%",
            })

    return {"issues": issues}


@router.get("/revenue-analysis")
async def get_revenue_analysis(days: int = 90, user: dict = Depends(get_current_user)):
    """DRG收入分析 — 从DRG权重×费率计算预期vs实际收入"""
    async with async_session() as db:
        cutoff = _days_ago(min(days, 180))

        # Monthly revenue: group by month, sum(weight * rate)
        monthly_r = await db.execute(
            select(
                func.strftime("%Y-%m", MedicalRecord.admission_date).label("month"),
                func.sum(func.json_extract(CodingResult.codes, '$.drg_weight') * settings.drg_base_rate).label("expected"),
                func.count(MedicalRecord.id).label("cnt"),
            )
            .join(CodingResult, CodingResult.record_id == MedicalRecord.id)
            .where(
                MedicalRecord.admission_date >= cutoff,
                CodingResult.codes.isnot(None),
            )
            .group_by(func.strftime("%Y-%m", MedicalRecord.admission_date))
            .order_by("month")
        )

        months_data = monthly_r.all()
        expected_total = sum(row[1] or 0 for row in months_data)

        trend = []
        for month_str, exp, cnt in months_data:
            trend.append({
                "month": month_str,
                "expected": round(exp or 0, 0),
                "cases": cnt,
            })

    return {
        "expected_total": int(expected_total),
        "trend": trend,
    }


