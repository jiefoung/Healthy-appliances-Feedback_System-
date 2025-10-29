from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FeedbackIn(BaseModel):
    user_id: str = "guest"
    gender: str = "不公開"   # 男/女/不公開
    age: int = 0
    model: str = ""

    mode: str  # 全身/頸部/肩部/腰部/伸展
    intensity: int = Field(ge=1, le=5)
    heat: bool = False
    duration_min: int = Field(ge=1, le=120)

    relax_score: int = Field(ge=1, le=5)
    pain_relief_score: int = Field(ge=1, le=5)
    noise_score: int = Field(ge=1, le=5)
    heat_fit_score: int = Field(ge=1, le=5)

    pain_areas: str = ""     # 自由文字
    issues: str = ""         # 自由文字
    nps: int = Field(ge=0, le=10)

    notes: str = ""
    contact_ok: bool = False
    phone: str = ""
    gmail: str = ""

class FeedbackOut(FeedbackIn):
    id: int
    ts: datetime

class Insight(BaseModel):
    count: int
    avg_nps: float
    top_issue: Optional[str] = None