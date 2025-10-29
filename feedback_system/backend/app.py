# app.py 
import sys, os, logging, traceback
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError  # 改抓通用的 DB 例外

from models import Base, Feedback
from schemas import FeedbackIn, FeedbackOut, Insight

# ===== 1) 基底路徑與工作目錄（EXE/原始碼相容）=====
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)  # 避免相對路徑被啟動位置影響

# ===== 2) Logging：寫到檔案 + Console =====
LOG_PATH = BASE_DIR / "backend.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("feedback-backend")

# ===== 3) DB 與 Engine =====
DB_PATH = BASE_DIR / "db.sqlite3"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"  # 用 / 分隔避免 windows 反斜線問題

# timeout=30s + pool_pre_ping，降低鎖表與連線失效
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
    future=True,  # SQLAlchemy 1.4 推薦
)

# 啟用 WAL 與 busy_timeout（SQLite 多流程/執行緒更穩）
with engine.begin() as conn:
    conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
    conn.exec_driver_sql("PRAGMA busy_timeout=30000;")  # 30,000 ms

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# 1) 建表
Base.metadata.create_all(bind=engine)

# 2) 啟動時自動遷移（補上 phone/gmail 欄位，保留既有資料）
def ensure_migration():
    with engine.begin() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(feedback);").fetchall()}
        if "phone" not in cols:
            conn.exec_driver_sql("ALTER TABLE feedback ADD COLUMN phone VARCHAR(32) DEFAULT ''")
        if "gmail" not in cols:
            conn.exec_driver_sql("ALTER TABLE feedback ADD COLUMN gmail VARCHAR(128) DEFAULT ''")

ensure_migration()

# ===== 4) FastAPI App 與路由 =====
app = FastAPI(title="Feedback API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# DI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/health")
async def health():
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return {"ok": True}
    except SQLAlchemyError as e:
        logging.exception("Health check failed:")
        return {"ok": False, "error": type(e).__name__}

# 新增一筆
@app.post("/api/feedback", response_model=FeedbackOut)
async def create_feedback(item: FeedbackIn, db: Session = Depends(get_db)):
    row = Feedback(**item.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackOut(**item.model_dump(), id=row.id, ts=row.ts)

# 列表（含 phone/gmail）
@app.get("/api/feedback", response_model=List[FeedbackOut])
async def list_feedback(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(Feedback).order_by(Feedback.id.desc()).limit(limit).all()
    return [FeedbackOut(
        id=r.id, ts=r.ts,
        user_id=r.user_id, gender=r.gender, age=r.age, model=r.model,
        mode=r.mode, intensity=r.intensity, heat=r.heat, duration_min=r.duration_min,
        relax_score=r.relax_score, pain_relief_score=r.pain_relief_score,
        noise_score=r.noise_score, heat_fit_score=r.heat_fit_score,
        pain_areas=r.pain_areas, issues=r.issues, nps=r.nps,
        notes=r.notes, contact_ok=r.contact_ok,
        phone=r.phone, gmail=r.gmail
    ) for r in rows]

# 最簡洞察
@app.get("/api/insights", response_model=Insight)
async def insights(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT COUNT(*) AS c, AVG(nps) AS avg_nps FROM feedback")).mappings().one()
    count = res["c"] or 0
    avg_nps = float(res["avg_nps"]) if res["avg_nps"] is not None else 0.0
    return Insight(count=count, avg_nps=round(avg_nps, 2), top_issue=None)

# ===== 5) 可執行入口（含錯誤落檔與 h11/asyncio 指定）=====
def main():
    import uvicorn
    try:
        logger.info("Starting Feedback API…")
        logger.info(f"Working dir: {Path.cwd()}")
        logger.info(f"DB path: {DB_PATH}")

        # 啟動前簡單 ping DB（提早暴露錯誤）
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")

        uvicorn.run(
            app,
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8000")),
            log_level=os.environ.get("LOG_LEVEL", "info"),
            reload=False,
            loop="asyncio",
            http="h11",
        )
    except Exception:
        logging.exception("Fatal error on startup:")
        # 再次把 traceback 落檔，避免雙擊看不到
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 60 + "\nTRACEBACK:\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        # 退出非 0：可讓批次檔偵測失敗
        sys.exit(1)

if __name__ == "__main__":
    try:
        import multiprocessing as _mp
        _mp.freeze_support()
    except Exception:
        pass
    main()
