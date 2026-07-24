from src.services.icd_coder.coder import ICDCandidate, icd_coder
from src.services.icd_coder.scoring import primary_score
from src.services.llm_engine import llm_engine
from src.services.nlp_engine.engine import nlp_parser
from src.services.qc_engine.engine import qc_engine
from src.services.review_agent.contracts import ReviewDocument
from src.services.review_agent.evidence import extract_laterality_evidence, find_laterality_conflicts


def _combine_documents(documents: list[ReviewDocument]) -> str:
    return "\n\n".join(f"【{document.title}】\n{document.content}" for document in documents)


def _item(candidate: ICDCandidate, is_primary: bool = False) -> dict:
    return {
        "code": candidate.code,
        "name": candidate.name,
        "category": candidate.category,
        "confidence": round(candidate.score, 2),
        "is_primary": is_primary,
    }


class ReviewTools:
    async def extract(self, documents: list[ReviewDocument]) -> dict:
        record = nlp_parser.parse("discharge", _combine_documents(documents))
        return {
            "diagnoses": [entity.text for entity in record.diagnoses],
            "surgeries": [entity.text for entity in record.surgeries],
            "summary": record.summary,
            "document_count": len(documents),
        }

    async def code(self, extracted: dict, preferred_mode: str) -> dict:
        mode = "rule_based"
        use_llm = False
        if preferred_mode == "auto":
            try:
                mode = await llm_engine.prewarm()
                use_llm = mode == "ollama"
            except Exception:
                mode = "rule_based"

        diagnoses: dict[str, ICDCandidate] = {}
        procedures: dict[str, ICDCandidate] = {}
        for text in extracted.get("diagnoses", []):
            for candidate in await icd_coder.recommend(text, use_llm=use_llm):
                if candidate.code not in diagnoses or candidate.score > diagnoses[candidate.code].score:
                    diagnoses[candidate.code] = candidate
        for text in extracted.get("surgeries", []):
            for candidate in await icd_coder.recommend(text, use_llm=use_llm):
                if candidate.code not in procedures or candidate.score > procedures[candidate.code].score:
                    procedures[candidate.code] = candidate

        ranked_diagnoses = sorted(
            diagnoses.values(), key=lambda candidate: primary_score(candidate.code, candidate.score), reverse=True
        )
        primary = _item(ranked_diagnoses[0], is_primary=True) if ranked_diagnoses else None
        secondaries = [_item(candidate) for candidate in ranked_diagnoses[1:10]]
        procedure_items = [_item(candidate) for candidate in procedures.values()]
        confidence = primary["confidence"] if primary else 0.0
        return {
            "primary_diagnosis": primary,
            "secondary_diagnoses": secondaries,
            "procedures": procedure_items,
            "total_confidence": confidence,
            "mode": mode,
        }

    async def quality_check(self, documents: list[ReviewDocument], coding: dict, mode: str) -> dict:
        result = await qc_engine.check(
            record_type="discharge",
            content=_combine_documents(documents),
            coding_result=coding,
            patient_info=None,
            use_llm=mode == "ollama",
        )
        return {
            "total_issues": result.total,
            "critical_count": result.critical_count,
            "major_count": result.major_count,
            "minor_count": result.minor_count,
            "info_count": result.info_count,
            "qc_score": result.score,
            "issues": [
                {
                    "rule_id": issue.rule_id,
                    "rule_name": issue.rule_name,
                    "rule_type": issue.rule_type.value if hasattr(issue.rule_type, "value") else issue.rule_type,
                    "severity": issue.severity.value if hasattr(issue.severity, "value") else issue.severity,
                    "description": issue.description,
                    "line_snippet": issue.line_snippet,
                    "suggestion": issue.suggestion,
                }
                for issue in result.issues
            ],
        }

    def evidence(self, documents: list[ReviewDocument]) -> dict:
        evidence = extract_laterality_evidence(documents)
        return {"items": evidence, "conflicts": find_laterality_conflicts(evidence)}
