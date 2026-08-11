from enum import StrEnum


class Intent(StrEnum):
    DAILY_HEALTH_LOG = "DAILY_HEALTH_LOG"
    START_DOCTOR_MODE = "START_DOCTOR_MODE"
    CONTINUE_DOCTOR_MODE = "CONTINUE_DOCTOR_MODE"
    POST_VISIT = "POST_VISIT"
    RECORD_MEASUREMENT = "RECORD_MEASUREMENT"
    CALL_CONTACT = "CALL_CONTACT"
    VIEW_HEALTH_HISTORY = "VIEW_HEALTH_HISTORY"
    GENERAL_CHAT = "GENERAL_CHAT"
    UNKNOWN = "UNKNOWN"


class IntentRouter:
    """Mock 规则路由；真实模型也必须输出同一组稳定意图。"""

    def route(self, text: str) -> Intent:
        compact = text.replace(" ", "")
        if any(x in compact for x in ("看完医生", "医院回来了", "医生今天说")):
            return Intent.POST_VISIT
        if any(x in compact for x in ("去医院", "看医生", "看大夫", "帮我整理一下")):
            return Intent.START_DOCTOR_MODE
        if any(x in compact for x in ("打电话", "联系家人", "给儿子打", "给女儿打")):
            return Intent.CALL_CONTACT
        if any(x in compact for x in ("血糖", "血压", "体温", "体重")) and any(ch.isdigit() for ch in compact):
            return Intent.RECORD_MEASUREMENT
        if any(x in compact for x in ("最近记录", "以前发生", "健康历史", "时间线")):
            return Intent.VIEW_HEALTH_HISTORY
        if any(x in compact for x in ("头晕", "睡", "吃了", "走了", "心情", "大便", "疼", "不舒服", "不得劲")):
            return Intent.DAILY_HEALTH_LOG
        if any(x in compact for x in ("你好", "谢谢", "陪我聊")):
            return Intent.GENERAL_CHAT
        return Intent.UNKNOWN
