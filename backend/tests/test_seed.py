from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.seed import seed_demo
from app.db.session import Base
from app.models.entities import FamilyMember, HealthProfile


def test_fresh_database_seed_creates_four_demo_members():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        seed_demo(session)
        assert session.scalar(select(func.count()).select_from(FamilyMember)) == 4
        profile = session.scalar(select(HealthProfile).where(HealthProfile.member_id == 4))
        assert "高血压" in profile.known_conditions
