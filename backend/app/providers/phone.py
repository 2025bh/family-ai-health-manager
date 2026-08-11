from abc import ABC, abstractmethod


class PhoneProvider(ABC):
    @abstractmethod
    def call(self, name: str, phone: str) -> str: ...


class MockPhoneProvider(PhoneProvider):
    def call(self, name: str, phone: str) -> str:
        masked = f"{phone[:3]}****{phone[-4:]}" if len(phone) >= 7 else "已隐藏"
        return f"模拟拨号成功：{name}（{masked}）"


class AndroidCompanionPhoneProvider(PhoneProvider):
    """预留给 Android Companion 的指令通道。"""

    def call(self, name: str, phone: str) -> str:
        return f"拨号指令已发送到 FamilyCare Companion：{name}"

