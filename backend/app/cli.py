import argparse
import asyncio
import getpass

from argon2 import PasswordHasher
from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import Base, User


async def create_owner(email: str, password: str) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        existing = await session.scalar(select(User).where(User.is_owner.is_(True)))
        if existing:
            raise SystemExit("Owner 已存在；系统不允许创建第二个账户。")
        session.add(User(email=email.lower(), password_hash=PasswordHasher().hash(password)))
        await session.commit()
    print(f"Owner {email.lower()} 已创建。")


def main() -> None:
    parser = argparse.ArgumentParser(prog="varbaia")
    subcommands = parser.add_subparsers(dest="command", required=True)
    owner = subcommands.add_parser("create-owner")
    owner.add_argument("--email", required=True)
    arguments = parser.parse_args()
    if arguments.command == "create-owner":
        password = getpass.getpass("Owner password: ")
        if len(password) < 12:
            raise SystemExit("密码至少 12 个字符。")
        asyncio.run(create_owner(arguments.email, password))


if __name__ == "__main__":
    main()
