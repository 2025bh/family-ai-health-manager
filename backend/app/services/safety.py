from dataclasses import dataclass
import re


@dataclass
class SafetyResult:
    possible_emergency: bool
    reason: str | None = None


class SafetyService:
    """独立安全层。规则仅用于保守拦截，正式红旗规则必须由医疗人员审核。"""

    emergency_phrases = (
        "呼吸困难",
        "喘不上气",
        "胸痛得厉害",
        "突然昏迷",
        "意识不清",
        "口角歪",
        "一边手脚不能动",
        "大量出血",
        "黑便",
        "黑色大便",
        "偏黑",
        "便血",
        "呕血",
        "剧烈腹痛",
        "绞痛",
        "想自杀",
    )
    forbidden_advice = ("自行停药", "加倍吃药", "减少药量", "替你诊断", "肯定是癌症")
    negation_pattern = re.compile(r"(?:没有|并无|无|未见|未出现|不再|不存在|否认)(?:明显|再次|继续|发生|出现|发现|观察到)?[，、；：:\s]*$")

    def check_input(self, text: str) -> SafetyResult:
        hit = next((item for item in self.emergency_phrases if self._has_non_negated_phrase(text, item)), None)
        return SafetyResult(bool(hit), hit)

    @classmethod
    def _has_non_negated_phrase(cls, text: str, phrase: str) -> bool:
        """只拦截实际出现的风险描述，跳过“没有/未出现黑便”等否定表达。"""
        for match in re.finditer(re.escape(phrase), text):
            clause_start = max(text.rfind(mark, 0, match.start()) for mark in "。！？；") + 1
            prefix = text[clause_start:match.start()][-16:]
            if not cls.negation_pattern.search(prefix):
                return True
        return False

    def sanitize_output(self, text: str) -> str:
        if any(item in text for item in self.forbidden_advice):
            return "我不能替医生诊断或调整用药。我可以帮你把情况整理清楚，并建议联系专业医疗人员。"
        return text

    @staticmethod
    def emergency_reply() -> str:
        return "这个情况可能需要尽快由专业医疗人员判断。请立即联系家人或医疗机构；如果情况危急，请拨打当地急救电话。"
