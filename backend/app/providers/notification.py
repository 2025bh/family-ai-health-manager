from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    @abstractmethod
    def notify(self, recipients: list[dict], message: str) -> dict: ...


class MockNotificationProvider(NotificationProvider):
    def notify(self, recipients: list[dict], message: str) -> dict:
        return {
            "provider": "mock",
            "sent": len(recipients),
            "recipients": [item["name"] for item in recipients],
            "message": "模拟家属通知成功，未发送到真实手机或飞书。",
        }


class AndroidNotificationProvider(NotificationProvider):
    def notify(self, recipients: list[dict], message: str) -> dict:
        raise NotImplementedError("接入 Android 推送服务后启用")

