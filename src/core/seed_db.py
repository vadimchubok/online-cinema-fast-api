import asyncio
from sqlalchemy import select
from src.core.database import async_session_maker
from src.auth.models import UserGroup, UserGroupEnum
from src.movies.models import Certification


async def seed_data():
    async with async_session_maker() as session:
        for group in UserGroupEnum:
            stmt = select(UserGroup).where(UserGroup.name == group.value)
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                session.add(UserGroup(name=group.value))

        certifications = ["G", "PG", "PG-13", "R", "NC-17"]
        for cert_name in certifications:
            stmt = select(Certification).where(Certification.name == cert_name)
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                session.add(Certification(name=cert_name))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_data())
