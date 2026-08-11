from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import FamilyMember, MemberHealthSetting


class HealthSettingService:
    CONSENT_VERSION = "tcm-consent-v1"

    def get_or_create(self, db: Session, member_id: int) -> MemberHealthSetting:
        if not db.get(FamilyMember, member_id):
            raise LookupError("家庭成员不存在")
        row = db.scalar(select(MemberHealthSetting).where(MemberHealthSetting.member_id == member_id))
        if row:
            return row
        row = MemberHealthSetting(member_id=member_id, western_prevention_enabled=True, tcm_health_enabled=False, tcm_depth="basic")
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update(self, db: Session, member_id: int, data: dict) -> MemberHealthSetting:
        row = self.get_or_create(db, member_id)
        if data.get("western_prevention_enabled") is not None:
            row.western_prevention_enabled = bool(data["western_prevention_enabled"])
        if data.get("tcm_health_enabled") is True:
            if not data.get("tcm_consent_confirmed"):
                raise PermissionError("首次开启中医健康守护前，需要确认知情说明")
            row.tcm_health_enabled = True
            row.tcm_enabled_at = datetime.now().replace(microsecond=0)
            row.tcm_consent_version = data.get("tcm_consent_version") or self.CONSENT_VERSION
        elif data.get("tcm_health_enabled") is False:
            row.tcm_health_enabled = False
        if data.get("tcm_depth"):
            row.tcm_depth = data["tcm_depth"]
        db.commit()
        db.refresh(row)
        return row
