from abc import ABC, abstractmethod


class VoiceGateway(ABC):
    @abstractmethod
    def normalize(self, text: str) -> str: ...


class WebVoiceGateway(VoiceGateway):
    def normalize(self, text: str) -> str:
        return text.strip()


class XiaozhiVoiceGateway(VoiceGateway):
    """小智仅作语音入口；家庭健康业务仍由独立后端处理。"""

    def normalize(self, text: str) -> str:
        return text.strip().removeprefix("小管家，").removeprefix("小管家,")


class AndroidVoiceGateway(WebVoiceGateway):
    pass


class SmartSpeakerGateway(WebVoiceGateway):
    pass

