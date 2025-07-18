from sqlalchemy.orm import Mapped, mapped_column

from project.keygen.db.model_base import Base

class Key(Base):
    __tablename__ = 'keys'
    
    username: Mapped[str]
    key: Mapped[str] = mapped_column(primary_key=True)
    rpm_limit: Mapped[int] = mapped_column(nullable=True)
    max_budget: Mapped[float] = mapped_column(nullable=True)
    budget_duration: Mapped[str] = mapped_column(nullable=True)
    expiration_date: Mapped[str] = mapped_column(nullable=True)
    blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] 
    updated_at: Mapped[str]

