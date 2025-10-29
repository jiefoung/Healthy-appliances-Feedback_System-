from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Boolean

class Base(DeclarativeBase):
    pass

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user_id: Mapped[str] = mapped_column(String(64))
    gender: Mapped[str] = mapped_column(String(8))   # 男/女/不公開
    age: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(64))   # 產品類別::產品名稱/型號

    mode: Mapped[str] = mapped_column(String(32))    # 全身/頸部/肩部/腰部/伸展
    intensity: Mapped[int] = mapped_column(Integer)
    heat: Mapped[bool] = mapped_column(Boolean)
    duration_min: Mapped[int] = mapped_column(Integer)

    relax_score: Mapped[int] = mapped_column(Integer)           # 放鬆評分
    pain_relief_score: Mapped[int] = mapped_column(Integer)     # 痠痛改善評分
    noise_score: Mapped[int] = mapped_column(Integer)           # 噪音感受評分
    heat_fit_score: Mapped[int] = mapped_column(Integer)        # 熱度感受評分

    pain_areas: Mapped[str] = mapped_column(String(256))   # 痠痛的地方(痛點)
    issues: Mapped[str] = mapped_column(String(512))       # 問題
    nps: Mapped[int] = mapped_column(Integer)              # 整體滿意度

    notes: Mapped[str] = mapped_column(String(1024))
    contact_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str] = mapped_column(String(32), default="")
    gmail: Mapped[str] = mapped_column(String(128), default="")