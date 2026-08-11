from dataclasses import dataclass

from app.services.medical_safety import MedicalSafetyLayer


@dataclass
class SafetyResult:
    possible_emergency: bool
    reason: str | None = None
    status: str = "no_red_flag"
    subject: str = "self"


class SafetyService:
    """独立安全层。规则仅用于保守拦截，正式红旗规则必须由医疗人员审核。"""

    forbidden_advice = ("自行停药", "加倍吃药", "减少药量", "替你诊断", "肯定是癌症")

    def check_input(self, text: str) -> SafetyResult:
        result = MedicalSafetyLayer().assess(text)
        return SafetyResult(result.possible_emergency, result.reason if result.possible_emergency else None, result.status, result.subject)

    def sanitize_output(self, text: str) -> str:
        if any(item in text for item in self.forbidden_advice):
            return "我不能替医生诊断或调整用药。我可以帮你把情况整理清楚，并建议联系专业医疗人员。"
        return text

    @staticmethod
    def emergency_reply() -> str:
        return "这个情况可能需要尽快由专业医疗人员判断。请立即联系家人或医疗机构；如果情况危急，请拨打当地急救电话。"
