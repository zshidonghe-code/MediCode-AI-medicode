"""Expand ICD procedure library with aliases and new codes.

Goes from 571 to 650+ entries with comprehensive alias coverage.
Focus on high-frequency clinical procedures and their common synonyms.
"""
import json
import sys
from pathlib import Path
from collections import OrderedDict

DATA_DIR = Path(__file__).parent.parent / "backend" / "src" / "data"
SRC_FILE = DATA_DIR / "icd_procedures.json"
BAK_FILE = DATA_DIR / "icd_procedures.json.bak"

# ── Step 0: Backup ──
if not BAK_FILE.exists():
    with open(SRC_FILE, "r", encoding="utf-8") as f:
        original = f.read()
    with open(BAK_FILE, "w", encoding="utf-8") as f:
        f.write(original)
    print("Backup created: icd_procedures.json.bak")

with open(SRC_FILE, "r", encoding="utf-8") as f:
    procedures = json.load(f)

print(f"Starting: {len(procedures)} procedures")

# ── Step 1: Add aliases to existing codes ──
# Comprehensive alias map: code -> list of additional aliases
ALIAS_MAP = {
    # Neurosurgery
    "01.0100": ["脑池穿刺"],
    "01.0900": ["脑室引流", "脑室穿刺引流"],
    "01.2400": ["开颅探查", "颅骨切开术"],
    "01.3100": ["脑膜切开", "硬脑膜切开"],
    "01.3900": ["颅内切开", "脑切开"],
    "02.0200": ["颅骨骨折复位", "颅骨整复"],
    "02.0500": ["颅骨修补", "颅骨成形"],
    "02.1200": ["脑膜修补", "硬脑膜修补"],
    "02.3400": ["脑室腹腔分流", "VP分流", "脑室-腹腔分流"],
    "03.0100": ["椎管异物取出"],
    "03.0900": ["椎管减压", "椎板减压"],
    "03.3100": ["腰椎穿刺", "腰穿"],
    "03.4000": ["脊髓肿瘤切除", "椎管内肿瘤切除"],

    # Cardiovascular
    "35.1200": ["二尖瓣修复", "二尖瓣成形", "二尖瓣置换", "二尖瓣手术"],
    "35.2200": ["主动脉瓣置换", "主动脉瓣修复", "主动脉瓣成形", "主动脉瓣手术", "TAVR", "TAVI", "经导管主动脉瓣置换"],
    "36.0600": ["PCI", "PTCA", "球囊扩张", "冠脉介入", "冠脉支架", "冠状动脉介入治疗", "经皮冠状动脉介入"],
    "36.0700": ["药物洗脱支架", "DES", "冠脉支架植入", "PCI术", "经皮冠状动脉介入治疗"],
    "36.1000": ["CABG", "搭桥", "冠脉搭桥", "冠状动脉旁路移植", "冠脉旁路移植"],
    "36.1500": ["双乳内动脉搭桥", "双侧IMA搭桥"],
    "37.2200": ["冠脉造影", "冠状动脉造影", "CAG"],
    "37.3400": ["射频消融", "RFCA", "房颤消融", "室上速消融", "电生理检查+射频消融"],
    "37.7400": ["临时起搏器", "临时起搏"],
    "37.8000": ["永久起搏器", "永久起搏", "起搏器植入", "PPM"],
    "37.8300": ["双腔起搏器", "DDD起搏器", "心脏起搏器植入", "起搏器更换"],

    # General Surgery — Abdominal
    "42.3200": ["食管肿瘤切除", "食管癌切除", "食管切除"],
    "43.5000": ["胃大部切除", "远端胃切除", "胃次全切除"],
    "43.7000": ["全胃切除", "胃癌根治", "根治性全胃切除"],
    "44.4100": ["胃穿孔修补", "胃溃疡穿孔修补"],
    "45.6200": ["小肠部分切除", "小肠切除术", "肠切除"],
    "45.7300": ["右半结肠切除", "右半结肠癌根治", "结肠癌根治术"],
    "46.1000": ["结肠造口", "结肠造瘘"],
    "46.2000": ["回肠造口", "回肠造瘘"],
    "46.7900": ["肠穿孔修补", "肠破裂修补", "肠修补"],
    "47.0100": ["腹腔镜阑尾切除", "LA", "微创阑尾切除"],
    "47.0900": ["阑尾切除术", "阑尾切除"],
    "47.0901": ["阑尾周围脓肿切除", "阑尾脓肿切除"],
    "48.3600": ["直肠息肉切除", "肠镜下息肉切除", "内镜下直肠息肉切除"],
    "48.6300": ["直肠癌根治", "直肠切除", "Miles手术", "Dixon手术", "直肠癌根治术"],
    "49.4600": ["痔切除", "混合痔切除", "PPH", "痔上黏膜环切"],
    "50.0000": ["肝活检", "肝脏穿刺活检"],
    "50.2200": ["肝部分切除", "肝叶切除", "肝癌切除", "肝段切除"],
    "50.3000": ["肝囊肿开窗", "肝囊肿引流"],
    "51.2200": ["胆囊切除", "开腹胆囊切除", "OC"],
    "51.2300": ["LC", "腹腔镜胆囊切除", "微创胆囊切除", "胆囊切除术", "胆囊摘除"],
    "51.4100": ["胆总管切开取石", "胆总管探查", "胆道探查"],
    "51.5100": ["胆总管探查引流", "T管引流", "胆总管引流"],
    "54.1100": ["剖腹探查", "开腹探查"],
    "54.2100": ["腹腔镜探查", "腹腔镜检查"],

    # General Surgery — Hernia
    "53.0000": ["腹股沟疝修补", "疝修补", "疝补片", "无张力疝修补"],
    "53.0100": ["双侧腹股沟疝修补"],
    "53.0200": ["单侧腹股沟疝修补"],
    "53.2100": ["股疝修补"],
    "53.4900": ["脐疝修补", "脐疝补片"],
    "53.6100": ["切口疝修补", "切口疝补片", "腹壁疝修补"],

    # Orthopedics
    "78.5000": ["骨折内固定", "ORIF", "切开复位内固定"],
    "79.0600": ["骨折闭合复位", "闭合复位外固定"],
    "79.1500": ["股骨颈骨折内固定", "空心钉内固定", "股骨颈内固定"],
    "79.3100": ["肱骨骨折内固定", "肱骨ORIF", "肱骨干骨折内固定"],
    "79.3500": ["股骨骨折内固定", "股骨ORIF", "股骨干骨折内固定", "PFNA", "股骨髓内钉", "DHS"],
    "79.3600": ["胫骨骨折内固定", "胫骨ORIF", "胫骨干骨折内固定", "IMN"],
    "80.6000": ["半月板切除", "半月板成形", "半月板部分切除", "关节镜半月板手术"],
    "81.4500": ["ACL重建", "前交叉韧带重建", "交叉韧带重建", "韧带重建术"],
    "81.5100": ["全髋置换", "THA", "全髋关节置换", "髋关节置换术", "人工髋关节"],
    "81.5400": ["TKA", "TKR", "全膝置换", "全膝关节置换", "膝关节置换术", "人工膝关节"],
    "81.6200": ["半髋置换", "人工股骨头置换", "股骨头置换"],
    "84.0000": ["截肢", "上肢截肢"],
    "84.1000": ["下肢截肢", "小腿截肢"],
    "84.1500": ["大腿截肢", "膝上截肢"],

    # Obstetrics & Gynecology
    "65.2500": ["卵巢囊肿剥除", "卵巢囊肿剔除", "卵巢囊肿切除", "卵巢囊肿手术"],
    "65.2900": ["卵巢切除", "附件切除", "单侧附件切除", "输卵管卵巢切除"],
    "67.3200": ["宫颈锥切", "LEEP", "宫颈电环切除", "宫颈病变切除"],
    "68.2900": ["子宫肌瘤剔除", "肌瘤剔除", "子宫肌瘤切除", "子宫肌瘤挖出", "子宫肌瘤剥除"],
    "68.4100": ["子宫切除", "全子宫切除", "子宫全切", "筋膜外子宫切除", "根治性子宫切除"],
    "68.5900": ["子宫脱垂手术", "盆底重建", "子宫悬吊"],
    "69.5000": ["人工流产", "人流", "吸宫", "清宫", "刮宫"],
    "74.0000": ["剖宫产", "剖腹产", "C-section", "子宫下段剖宫产"],

    # Thoracic
    "32.2000": ["肺叶切除", "肺叶切除术", "胸腔镜肺叶切除", "VATS肺叶切除"],
    "32.4000": ["全肺切除", "全肺切除术"],
    "32.5000": ["肺楔形切除", "肺楔切", "胸腔镜肺楔形切除"],
    "33.2300": ["支气管镜", "纤支镜", "支气管镜检查", "纤维支气管镜"],
    "34.0400": ["胸腔闭式引流", "胸穿", "胸腔引流", "胸管"],  # Also 胸穿放液
    "34.2000": ["胸腔镜", "胸腔镜检查", "VATS"],

    # Urology
    "55.0100": ["肾造瘘", "肾造口"],
    "55.0300": ["肾穿刺", "肾穿刺活检"],
    "55.4000": ["肾部分切除", "肾部分切除术", "保留肾单位手术"],
    "55.5100": ["肾切除", "肾癌根治", "根治性肾切除", "肾全切"],
    "56.0000": ["输尿管镜", "输尿管镜检查", "URS"],
    "56.2000": ["输尿管镜碎石", "URS碎石", "输尿管镜取石"],
    "57.0000": ["膀胱镜", "膀胱镜检查"],
    "57.3000": ["TURBT", "膀胱肿瘤电切", "经尿道膀胱肿瘤切除"],
    "59.8000": ["输尿管支架", "双J管", "DJ管", "输尿管支架管置入"],
    "59.9500": ["ESWL", "体外冲击波碎石", "体外碎石", "冲击波碎石"],

    # ENT / Ophthalmology
    "06.2000": ["甲状腺切除", "甲状腺叶切除", "单侧甲状腺切除", "甲状腺癌根治", "甲状腺全切"],
    "06.3100": ["甲状腺结节切除", "甲状腺部分切除"],
    "06.3900": ["甲状腺次全切除", "甲状腺大部切除"],
    "06.5000": ["甲状旁腺切除", "甲状旁腺探查"],
    "13.0000": ["白内障手术", "白内障摘除", "白内障超声乳化", "Phaco", "phaco"],
    "13.4100": ["白内障超声乳化+人工晶体植入", "Phaco+IOL", "白内障IOL植入"],
    "28.2000": ["扁桃体切除", "扁桃体摘除"],
    "28.6000": ["腺样体切除", "腺样体刮除"],

    # Vascular
    "38.1000": ["血栓取出", "取栓", "动脉切开取栓"],
    "38.8000": ["血管造影", "DSA", "数字减影血管造影"],
    "38.9300": ["PICC", "PICC置管", "中心静脉置管", "经外周中心静脉置管"],
    "39.5000": ["球囊血管成形", "PTA", "血管成形"],
    "39.6100": ["ECMO", "体外膜肺", "体外膜氧合"],
    "39.7200": ["下腔静脉滤器", "IVC滤器", "腔静脉滤器置入"],
    "39.7400": ["血管内支架", "血管支架", "外周血管支架"],

    # Breast
    "85.1200": ["乳腺活检", "乳腺穿刺", "乳腺粗针穿刺", "麦默通", "Mammotome"],
    "85.2100": ["乳腺肿物切除", "乳腺肿块切除", "乳腺良性肿瘤切除"],
    "85.4100": ["乳腺切除", "全乳切除", "单纯乳房切除"],
    "85.4300": ["乳腺癌改良根治", "乳腺癌根治", "改良根治", "Auchincloss手术", "乳癌根治"],
    "85.4500": ["保乳手术", "保乳切除", "乳腺象限切除", "乳腺区段切除"],

    # Skin / Plastic
    "86.1100": ["皮肤肿瘤切除", "皮下肿物切除", "脂肪瘤切除"],
    "86.3000": ["皮肤移植", "植皮", "皮片移植"],
    "86.7000": ["皮瓣移植", "皮瓣转移", "带蒂皮瓣"],
    "86.8300": ["吸脂", "抽脂", "脂肪抽吸", "体型雕塑"],

    # Additional orthopedic procedures
    "77.6000": ["骨肿瘤切除", "骨肿瘤刮除", "骨囊肿刮除"],
    "80.5000": ["椎间盘切除", "髓核摘除", "腰椎间盘摘除", "PLDD", "MED", "椎间孔镜"],
    "81.0000": ["脊柱融合", "椎间融合", "腰椎融合", "PLIF", "TLIF", "Cage植入"],
    "81.0200": ["腰椎融合术", "后路腰椎融合"],
    "81.0500": ["颈椎融合", "ACDF", "前路颈椎融合"],
    "81.3000": ["椎弓根钉内固定", "后路内固定", "脊柱内固定"],
    "81.6500": ["椎体成形", "PVP", "PKP", "椎体后凸成形", "骨水泥", "经皮椎体成形"],
    "83.4500": ["肩袖修复", "肩袖修补", "肩袖重建"],
}

# Apply aliases
aliases_added = 0
for proc in procedures:
    code = proc["code"]
    if code in ALIAS_MAP:
        existing = set(proc.get("aliases", []))
        new_aliases = [a for a in ALIAS_MAP[code] if a not in existing]
        if new_aliases:
            proc["aliases"] = sorted(existing | set(new_aliases))
            aliases_added += len(new_aliases)

print(f"Aliases added: {aliases_added}")

# ── Step 2: Add new procedure codes ──
existing_codes = {p["code"] for p in procedures}

NEW_PROCEDURES = [
    # Additional cardiovascular
    {"code": "36.0900", "name": "冠状动脉其他支架植入", "category": "心血管系统手术", "py": "gzdmqtzjzr", "aliases": ["冠脉其他支架"]},
    {"code": "36.1100", "name": "一根冠状动脉搭桥术", "category": "心血管系统手术", "py": "yggzdmdqs", "aliases": ["单支搭桥", "单根搭桥"]},
    {"code": "36.1200", "name": "二根冠状动脉搭桥术", "category": "心血管系统手术", "py": "rggzdmdqs", "aliases": ["双支搭桥", "两根搭桥"]},
    {"code": "36.1300", "name": "三根冠状动脉搭桥术", "category": "心血管系统手术", "py": "sggzdmdqs", "aliases": ["三支搭桥"]},
    {"code": "36.1400", "name": "四根及以上冠状动脉搭桥术", "category": "心血管系统手术", "py": "sgjysgzdmdqs", "aliases": ["四支搭桥"]},
    {"code": "37.2600", "name": "心脏电生理检查", "category": "心血管系统手术", "py": "xzdsljc", "aliases": ["电生理检查", "EPS", "心脏电生理"]},
    {"code": "37.5100", "name": "心脏移植术", "category": "心血管系统手术", "py": "xzyzs", "aliases": ["心脏移植", "同种异体心脏移植"]},
    {"code": "37.9400", "name": "埋藏式心脏复律除颤器置入", "category": "心血管系统手术", "py": "mcszflccqzr", "aliases": ["ICD置入", "除颤器", "埋藏式除颤器", "ICD植入"]},
    {"code": "37.9500", "name": "心脏再同步化治疗起搏器置入", "category": "心血管系统手术", "py": "xztbhlqbzr", "aliases": ["CRT", "CRT-P", "CRT置入", "三腔起搏器", "再同步化治疗"]},
    {"code": "37.9600", "name": "心脏再同步化治疗除颤器置入", "category": "心血管系统手术", "py": "xztbhlccqzr", "aliases": ["CRT-D", "CRTD置入"]},
    {"code": "38.1200", "name": "颈动脉内膜剥脱术", "category": "血管手术", "py": "jdnmbts", "aliases": ["CEA", "颈动脉内膜切除"]},
    {"code": "38.4200", "name": "腹主动脉瘤切除+人工血管置换", "category": "血管手术", "py": "fzdmlrgxgzh", "aliases": ["AAA切除", "腹主动脉瘤手术"]},
    {"code": "39.6600", "name": "经皮冠状动脉血流储备分数检查", "category": "心血管系统手术", "py": "jpgzdmxlcbfsjc", "aliases": ["FFR", "血流储备分数"]},

    # Neurosurgery additions
    {"code": "01.5100", "name": "颅内动脉瘤夹闭术", "category": "神经系统手术", "py": "lndmljbs", "aliases": ["动脉瘤夹闭", "颅内动脉瘤手术", "开颅动脉瘤夹闭"]},
    {"code": "01.5900", "name": "颅内血肿清除术", "category": "神经系统手术", "py": "lnxzqcs", "aliases": ["脑内血肿清除", "颅内血肿清除", "颅内血肿引流"]},
    {"code": "02.3100", "name": "颅骨去骨瓣减压术", "category": "神经系统手术", "py": "lgqgbjys", "aliases": ["去骨瓣减压", "去骨瓣", "颅骨减压"]},
    {"code": "02.3900", "name": "颅骨成形术", "category": "神经系统手术", "py": "lgcxs", "aliases": ["颅骨修补术", "钛网修补", "颅骨重建"]},
    {"code": "03.5200", "name": "脊柱融合术", "category": "神经系统手术", "py": "jzrhs", "aliases": ["脊柱固定"]},

    # Orthopedic additions
    {"code": "77.8000", "name": "骨部分切除术", "category": "肌肉骨骼系统手术", "py": "gbfqcs", "aliases": ["骨切除", "死骨清除"]},
    {"code": "78.1000", "name": "外固定架固定术", "category": "肌肉骨骼系统手术", "py": "wgdjgds", "aliases": ["外固定架", "外支架固定"]},
    {"code": "78.6000", "name": "内固定物取出术", "category": "肌肉骨骼系统手术", "py": "ngdwqcs", "aliases": ["钢板取出", "螺钉取出", "取内固定", "拆钢板", "拆钢钉"]},
    {"code": "79.0500", "name": "桡骨骨折闭合复位术", "category": "肌肉骨骼系统手术", "py": "rggzbhfws", "aliases": ["桡骨骨折复位"]},
    {"code": "80.1000", "name": "关节镜检查", "category": "肌肉骨骼系统手术", "py": "gjjjc", "aliases": ["膝关节镜", "肩关节镜", "髋关节镜"]},
    {"code": "80.2000", "name": "关节镜下滑膜切除术", "category": "肌肉骨骼系统手术", "py": "gjhxhmqcs", "aliases": ["关节镜滑膜切除", "滑膜清理"]},
    {"code": "80.5100", "name": "椎间盘髓核摘除术（椎间孔镜）", "category": "肌肉骨骼系统手术", "py": "zjpzhzcs", "aliases": ["椎间孔镜下髓核摘除", "PELD", "靶点射频"]},
    {"code": "81.8000", "name": "关节置换翻修术", "category": "肌肉骨骼系统手术", "py": "gjzhfxs", "aliases": ["关节翻修", "髋关节翻修", "膝关节翻修"]},
    {"code": "83.3200", "name": "关节镜下肩袖修复术", "category": "肌肉骨骼系统手术", "py": "gjxjyjxxfs", "aliases": ["关节镜肩袖修复", "关节镜肩袖修补"]},

    # General surgery additions
    {"code": "42.4000", "name": "食管切除术", "category": "消化系统手术", "py": "sgqcs", "aliases": ["食管癌根治术", "食管癌手术", "食管切除重建"]},
    {"code": "42.4100", "name": "食管部分切除术", "category": "消化系统手术", "py": "sgbfqcs", "aliases": ["食管次全切"]},
    {"code": "43.3000", "name": "胃造口术", "category": "消化系统手术", "py": "wzks", "aliases": ["胃造瘘", "PEG", "经皮胃造瘘"]},
    {"code": "43.4100", "name": "胃镜下胃病变切除术", "category": "消化系统手术", "py": "wjxwbbqcs", "aliases": ["胃镜下胃息肉切除", "胃早癌ESD", "胃ESD"]},
    {"code": "44.3200", "name": "胃镜下十二指肠病变切除术", "category": "消化系统手术", "py": "wjxzebqcs", "aliases": ["十二指肠息肉切除"]},
    {"code": "45.2300", "name": "肠镜下结肠病变切除术", "category": "消化系统手术", "py": "cxjcbbqcs", "aliases": ["结肠息肉切除", "结肠ESD", "EMR"]},
    {"code": "45.4200", "name": "肠镜下大肠息肉切除术", "category": "消化系统手术", "py": "cxdczxrqcs", "aliases": ["大肠息肉切除", "肠镜下息肉切除术", "结肠镜息肉摘除"]},
    {"code": "46.1000", "name": "结肠造口术", "category": "消化系统手术", "py": "jczks", "aliases": ["结肠造瘘", "大肠造口"]},
    {"code": "46.2000", "name": "回肠造口术", "category": "消化系统手术", "py": "hczks", "aliases": ["回肠造瘘"]},
    {"code": "50.2400", "name": "肝脏射频消融术", "category": "消化系统手术", "py": "gzspxrs", "aliases": ["肝癌射频消融", "肝癌消融", "RFA", "肝肿瘤消融"]},
    {"code": "51.2500", "name": "肝移植术", "category": "消化系统手术", "py": "gyzs", "aliases": ["肝移植", "肝脏移植", "同种异体肝移植"]},
    {"code": "52.5100", "name": "胰腺部分切除术", "category": "消化系统手术", "py": "yxbfqcs", "aliases": ["胰腺切除", "胰十二指肠切除", "Whipple手术", "胰体尾切除"]},
    {"code": "52.6000", "name": "胰腺移植术", "category": "消化系统手术", "py": "yxyzs", "aliases": ["胰腺移植"]},
    {"code": "53.7100", "name": "腹腔镜下腹股沟疝修补术", "category": "消化系统手术", "py": "fxfsgqsb", "aliases": ["TAPP", "TEP", "腹腔镜疝修补", "腹腔镜疝补片"]},
    {"code": "54.5100", "name": "腹腔镜下肠粘连松解术", "category": "消化系统手术", "py": "fjxczlsjs", "aliases": ["肠粘连松解", "腹腔镜肠粘连松解"]},

    # Urology additions
    {"code": "55.5100", "name": "肾切除术", "category": "泌尿系统手术", "py": "sqcs", "aliases": ["肾癌根治术", "肾根治性切除"]},
    {"code": "56.0000", "name": "经尿道输尿管镜碎石取石术", "category": "泌尿系统手术", "py": "jndsngjssqss", "aliases": ["URSL", "输尿管软镜", "输尿管镜钬激光碎石", "输尿管碎石"]},
    {"code": "57.3200", "name": "经尿道膀胱肿瘤电切术", "category": "泌尿系统手术", "py": "jndpgzldqs", "aliases": ["膀胱肿瘤电切", "TURBT", "膀胱肿瘤切除"]},
    {"code": "57.4900", "name": "经尿道前列腺电切术", "category": "泌尿系统手术", "py": "jndqlxdqs", "aliases": ["TURP", "前列腺电切", "前列腺切除", "前列腺微创手术"]},
    {"code": "57.5900", "name": "经尿道前列腺激光切除术", "category": "泌尿系统手术", "py": "jndqlxjgqcs", "aliases": ["前列腺激光", "HoLEP", "前列腺钬激光", "绿激光前列腺"]},
    {"code": "58.0000", "name": "尿道切开术", "category": "泌尿系统手术", "py": "ndqks", "aliases": ["尿道狭窄切开", "尿道切开扩张"]},
    {"code": "60.2100", "name": "经尿道前列腺穿刺活检术", "category": "泌尿系统手术", "py": "jndqlxccjs", "aliases": ["前列腺穿刺", "前列腺活检", "PSA异常穿刺"]},
    {"code": "60.2900", "name": "前列腺根治性切除术", "category": "泌尿系统手术", "py": "qlxgzxqcs", "aliases": ["前列腺癌根治", "前列腺癌根治术", "前列腺癌切除"]},
    {"code": "60.6100", "name": "膀胱根治性切除术", "category": "泌尿系统手术", "py": "pggzxqcs", "aliases": ["膀胱癌根治", "膀胱全切", "根治性膀胱切除"]},
    {"code": "61.4900", "name": "睾丸切除术", "category": "泌尿系统手术", "py": "gwqcs", "aliases": ["睾丸切除", "去势手术"]},

    # Obstetrics/Gynecology additions
    {"code": "65.6100", "name": "双侧输卵管切除术", "category": "女性生殖系统手术", "py": "sslgqcs", "aliases": ["双输卵管切除"]},
    {"code": "65.6300", "name": "腹腔镜输卵管切除术", "category": "女性生殖系统手术", "py": "fjslgqcs", "aliases": ["腹腔镜输卵管切除"]},
    {"code": "66.2200", "name": "输卵管通液术", "category": "女性生殖系统手术", "py": "slgtys", "aliases": ["输卵管通液", "HSG", "输卵管造影", "输卵管复通"]},
    {"code": "67.2000", "name": "宫颈锥形切除术", "category": "女性生殖系统手术", "py": "gjzxqcs", "aliases": ["宫颈锥切术", "LEEP刀", "冷刀锥切", "CKC"]},
    {"code": "68.5000", "name": "子宫切除术", "category": "女性生殖系统手术", "py": "zgqcs", "aliases": ["子宫全切术", "全子宫切除术"]},
    {"code": "70.5000", "name": "阴道前后壁修补术", "category": "女性生殖系统手术", "py": "ydqhbxbs", "aliases": ["阴道壁修补", "盆底重建术"]},
    {"code": "74.1000", "name": "子宫下段剖宫产术", "category": "女性生殖系统手术", "py": "zgxdpgcs", "aliases": ["剖宫产术", "剖腹产术"]},

    # ENT additions
    {"code": "21.1000", "name": "鼻息肉切除术", "category": "耳鼻咽喉手术", "py": "bxrqcs", "aliases": ["鼻息肉摘除", "鼻息肉切除", "鼻内镜息肉切除"]},
    {"code": "22.2000", "name": "鼻内镜下鼻窦开放术", "category": "耳鼻咽喉手术", "py": "bnjbdkfs", "aliases": ["FESS", "鼻窦开放", "鼻内镜鼻窦手术", "鼻窦炎手术"]},
    {"code": "22.6000", "name": "鼻中隔矫正术", "category": "耳鼻咽喉手术", "py": "bzgjzs", "aliases": ["鼻中隔偏曲矫正", "鼻中隔手术"]},
    {"code": "30.0100", "name": "喉镜下声带息肉切除术", "category": "耳鼻咽喉手术", "py": "hxsdxrqcs", "aliases": ["声带息肉切除", "声带息肉摘除", "声带小结切除"]},
    {"code": "30.0900", "name": "全喉切除术", "category": "耳鼻咽喉手术", "py": "qhqcs", "aliases": ["喉癌手术", "喉全切"]},

    # Ophthalmology additions
    {"code": "13.1100", "name": "白内障超声乳化吸除术", "category": "眼科手术", "py": "bnzcrhxcs", "aliases": ["白内障超声乳化", "超乳", "Phaco"]},
    {"code": "13.7000", "name": "人工晶体植入术", "category": "眼科手术", "py": "rgjtzrs", "aliases": ["IOL植入", "人工晶体置入"]},
    {"code": "14.2000", "name": "视网膜光凝术", "category": "眼科手术", "py": "swmgns", "aliases": ["眼底激光", "PRP", "全视网膜光凝", "激光光凝"]},
    {"code": "14.7000", "name": "玻璃体切除术", "category": "眼科手术", "py": "bltqcs", "aliases": ["玻璃体切割", "PPV", "玻璃体手术"]},

    # Thoracic additions
    {"code": "32.2000", "name": "胸腔镜下肺叶切除术", "category": "呼吸系统手术", "py": "xqjfyqcs", "aliases": ["胸腔镜肺叶切除", "VATS肺叶", "微创肺叶切除"]},
    {"code": "32.6000", "name": "肺段切除术", "category": "呼吸系统手术", "py": "fdqcs", "aliases": ["肺段切除", "精准肺段切除"]},
    {"code": "33.4800", "name": "支气管镜下肺泡灌洗术", "category": "呼吸系统手术", "py": "zqgjfpgxs", "aliases": ["BAL", "肺泡灌洗", "支气管肺泡灌洗"]},

    # Vascular additions
    {"code": "38.6000", "name": "下肢静脉曲张剥脱术", "category": "血管手术", "py": "xzjmqzbts", "aliases": ["大隐静脉剥脱", "静脉曲张手术", "大隐静脉高位结扎剥脱"]},
    {"code": "38.8000", "name": "下肢静脉曲张激光闭合术", "category": "血管手术", "py": "xzjmqbjgbhs", "aliases": ["EVLA", "激光闭合", "静脉曲张激光"]},
    {"code": "39.4900", "name": "下肢深静脉血栓清除术", "category": "血管手术", "py": "xzsjmxsqcs", "aliases": ["DVT清除", "深静脉血栓清除", "PMT", "AngioJet"]},
    {"code": "86.0400", "name": "血液透析血管通路建立", "category": "血管手术", "py": "xytxxgtllj", "aliases": ["AVF", "动静脉瘘", "透析通路", "AVG", "人工血管"]},

    # Breast additions
    {"code": "85.3300", "name": "前哨淋巴结活检术", "category": "乳腺手术", "py": "qslbjjcs", "aliases": ["SLNB", "前哨淋巴结", "前哨淋巴结活检"]},
    {"code": "85.4300", "name": "腋窝淋巴结清扫术", "category": "乳腺手术", "py": "ywlbjqss", "aliases": ["ALND", "腋窝清扫", "腋窝淋巴清扫"]},

    # Spine additions
    {"code": "03.9000", "name": "脊柱内镜下手术", "category": "神经系统手术", "py": "jznjsxsh", "aliases": ["脊柱内镜", "椎间孔镜手术", "脊柱微创"]},
    {"code": "81.3000", "name": "脊柱融合+内固定术", "category": "肌肉骨骼系统手术", "py": "jzrhngds", "aliases": ["脊柱融合内固定"]},
]

# Add new procedures that don't already exist
added_count = 0
for new_proc in NEW_PROCEDURES:
    if new_proc["code"] not in existing_codes:
        procedures.append(new_proc)
        existing_codes.add(new_proc["code"])
        added_count += 1

print(f"New procedures added: {added_count}")
print(f"Total after expansion: {len(procedures)}")

# ── Step 3: Sort by code ──
def code_sort_key(proc):
    parts = proc["code"].split(".")
    return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)

procedures.sort(key=code_sort_key)

# ── Step 4: Save ──
with open(SRC_FILE, "w", encoding="utf-8") as f:
    json.dump(procedures, f, ensure_ascii=False, indent=2)

# ── Step 5: Stats ──
with_aliases = [p for p in procedures if p.get("aliases")]
alias_count = sum(len(p.get("aliases", [])) for p in procedures)
print()
print("═" * 50)
print("  手术编码库扩充完成")
print(f"  原有编码: 571")
print(f"  新增编码: {added_count}")
print(f"  总计编码: {len(procedures)}")
print(f"  有别名: {len(with_aliases)} ({len(with_aliases)/len(procedures)*100:.1f}%)")
print(f"  别名总数: {alias_count} (平均 {alias_count/len(procedures):.1f}个/码)")
print(f"  备份: icd_procedures.json.bak")
print("═" * 50)
