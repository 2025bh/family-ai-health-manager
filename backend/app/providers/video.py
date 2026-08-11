from abc import ABC, abstractmethod


class VideoCallProvider(ABC):
    @abstractmethod
    def create_call(self, contact_id: int) -> str: ...


class WebRTCVideoCallProvider(VideoCallProvider):
    def create_call(self, contact_id: int) -> str:
        raise NotImplementedError("V0.2 再实现家庭视频；V0.1 不自动操作微信")

