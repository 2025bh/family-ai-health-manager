from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re


@dataclass
class SafetyAssessment:
    possible_emergency: bool
    status: str
    subject: str
    temporal_status: str
    assertion: str
    reason: str | None = None
    risk_level: str = "green"
    escalation_action: str = "continue_monitoring"
    rule_ids: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class MedicalSafetyLayer:
    """在所有健康分析前运行的确定性语义安全层。

    这里只判断是否存在“当前、本人、肯定表达”的保守红旗信号，不做疾病诊断。
    规则来源为产品安全基线，仍等待医疗专业人员逐条审核。
    """

    RULE_SET_VERSION = "safety-baseline-1.0"
    RED_FLAG_RULES = {
        "MSL-BREATHING-001": ("呼吸困难", "喘不上气"),
        "MSL-CHEST-001": ("胸痛得厉害", "剧烈胸痛"),
        "MSL-NEURO-001": ("突然昏迷", "意识不清", "口角歪", "一边手脚不能动"),
        "MSL-BLEEDING-001": ("大量出血", "黑便", "黑色大便", "便血", "呕血"),
        "MSL-ABDOMEN-001": ("剧烈腹痛", "绞痛"),
        "MSL-SELF-HARM-001": ("想自杀", "不想活了"),
    }
    NEGATION = re.compile(r"(?:没有|并无|无|未见|未出现|不再|不存在|否认|没得)(?:明显|再次|继续|发生|出现|发现|观察到|检查出)?[，、；：:\s]*$")
    HISTORICAL = re.compile(r"(?:去年|前年|以前|之前|曾经|既往|前些天|前两天|上次|过去有过)")
    CURRENT = re.compile(r"(?:今天|刚刚|现在|目前|今早|今晚|突然|正在|这会儿|刚才)")
    OTHER_SUBJECT = re.compile(r"(?:我爸爸|我爸|我妈妈|我妈|我爷爷|我奶奶|我姐姐|我妹妹|我哥哥|我弟弟|家里有人|朋友|同事|患者)")
    HYPOTHETICAL = re.compile(r"(?:如果|假如|万一|要是|以后出现|会不会)")
    QUESTION = re.compile(r"(?:是不是|严重吗|怎么办|是什么原因|为什么|需要.*吗|\?|？)")
    RECOVERED = re.compile(r"(?:现在|目前|已经).{0,8}(?:好了|恢复了|没有了|消失了|不再)|(?:症状|它).{0,5}(?:好了|消失了)")

    def assess(self, text: str) -> SafetyAssessment:
        normalized = self._normalize(text)
        hits = self._find_hits(normalized)
        if not hits:
            if self.RECOVERED.search(normalized):
                return SafetyAssessment(False, "recovered", "self", "current", "recovered", risk_level="green")
            if re.search(r"(?:没有|未出现|无).{0,5}(?:腹泻|拉肚子)", normalized) and re.search(r"(?:但是|但|下午|晚上).{0,8}(?:腹泻|拉了|拉肚子)", normalized):
                return SafetyAssessment(False, "conflicting_current_statements", "self", "current", "uncertain", risk_level="insufficient_data", uncertainty=["同一描述中同时出现否定和后续发生记录，需要确认实际时间线"])
            vague = any(term in normalized for term in ("不太舒服", "不得劲", "之前有过", "好像不对")) or bool(self.OTHER_SUBJECT.search(normalized))
            return SafetyAssessment(
                False,
                "insufficient_context" if vague else "no_red_flag",
                "unclear" if "家里有人" in normalized else "self",
                "unclear" if vague else "current",
                "uncertain" if vague else "none",
                risk_level="insufficient_data" if vague else "green",
                uncertainty=["缺少具体症状、对象或时间信息"] if vague else [],
            )

        classifications: list[tuple[str, str, str, str]] = []
        for rule_id, phrase, start in hits:
            clause = self._clause_for(normalized, start)
            prefix = clause[: max(0, clause.find(phrase))][-20:]
            subject = "other" if self.OTHER_SUBJECT.search(clause) else "self"
            if self.NEGATION.search(prefix):
                assertion = "negated"
            elif self.RECOVERED.search(clause):
                assertion = "recovered"
            elif self.HYPOTHETICAL.search(clause):
                assertion = "hypothetical"
            elif self.QUESTION.search(clause) and not self.CURRENT.search(clause):
                assertion = "question"
            else:
                assertion = "affirmed"
            temporal = "current" if self.CURRENT.search(clause) else "historical" if self.HISTORICAL.search(clause) else "unclear"
            classifications.append((rule_id, phrase, subject, f"{assertion}:{temporal}"))

        current = [x for x in classifications if x[2] == "self" and x[3].startswith("affirmed:") and not x[3].endswith(":historical")]
        if current:
            rule_ids = list(dict.fromkeys(x[0] for x in current))
            phrases = list(dict.fromkeys(x[1] for x in current))
            return SafetyAssessment(
                True,
                "current_red_flag",
                "self",
                "current" if any(x[3].endswith(":current") for x in current) else "unclear",
                "affirmed",
                reason="、".join(phrases),
                risk_level="red",
                escalation_action="urgent_escalation" if "MSL-SELF-HARM-001" in rule_ids else "seek_timely_medical_evaluation",
                rule_ids=rule_ids,
                uncertainty=[] if any(x[3].endswith(":current") for x in current) else ["未明确症状发生时间，按当前风险保守提醒"],
            )

        priority = ("other", "hypothetical", "question", "recovered", "negated", "historical")
        states = []
        for _, _, subject, combined in classifications:
            assertion, temporal = combined.split(":", 1)
            states.append("other" if subject == "other" else assertion if assertion != "affirmed" else temporal)
        status = next((item for item in priority if item in states), "insufficient_context")
        subject = "other" if status == "other" else "self"
        temporal = "historical" if "historical" in states else "current" if status in ("negated", "recovered") else "unclear"
        assertion = status if status in ("hypothetical", "question", "recovered", "negated") else "uncertain"
        return SafetyAssessment(
            False,
            status,
            subject,
            temporal,
            assertion,
            reason=classifications[0][1],
            risk_level="insufficient_data" if status in ("other", "insufficient_context") else "green",
            uncertainty=["该描述不是当前本人的肯定症状，未按当前风险记录"] if status != "negated" else [],
        )

    def _find_hits(self, text: str) -> list[tuple[str, str, int]]:
        hits: list[tuple[str, str, int]] = []
        for rule_id, phrases in self.RED_FLAG_RULES.items():
            for phrase in phrases:
                hits.extend((rule_id, phrase, match.start()) for match in re.finditer(re.escape(phrase), text))
        return sorted(hits, key=lambda item: item[2])

    @staticmethod
    def _clause_for(text: str, position: int) -> str:
        left = max((text.rfind(mark, 0, position) for mark in "。！？；;"), default=-1) + 1
        right_candidates = [text.find(mark, position) for mark in "。！？；;" if text.find(mark, position) >= 0]
        right = min(right_candidates) if right_candidates else len(text)
        clause = text[left:right]
        # 转折后的肯定描述应独立于前面的否定描述。
        for marker in ("但是", "但", "不过", "可是"):
            marker_pos = clause.rfind(marker, 0, max(0, position - left + 1))
            if marker_pos >= 0:
                clause = clause[marker_pos + len(marker):]
        return clause

    @staticmethod
    def _normalize(text: str) -> str:
        return text.strip().replace("黒便", "黑便").replace("便皿", "便血").replace("黑色便", "黑便")
