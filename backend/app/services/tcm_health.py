from app.models.entities import MemberHealthSetting


class TcmHealthEngine:
    ENGINE_VERSION = "tcm-skeleton-1.0"

    @staticmethod
    def describe(setting: MemberHealthSetting) -> dict:
        if not setting.tcm_health_enabled:
            return {
                "enabled": False,
                "depth": setting.tcm_depth,
                "status": "not_enabled",
                "message": "中医健康守护尚未开启。",
                "analysis_available": False,
            }
        return {
            "enabled": True,
            "depth": setting.tcm_depth,
            "status": "basic_observation_only",
            "message": "已开启基础观察骨架；完整中医辨证分析尚未实现。不会自动开方、换方、停药或修改剂量。",
            "analysis_available": False,
        }
