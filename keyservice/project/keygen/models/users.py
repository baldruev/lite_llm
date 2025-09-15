from sqlalchemy.orm import Mapped, mapped_column

from project.keygen.db.model_base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
