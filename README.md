# Healthy appliances_Feedback_System 

一款可簡單快速上手的健康家電使用者回饋系統：前端 **PySide6 GUI**、後端 **FastAPI + SQLite**。支援離線佇列、`.env` 設定（避免硬編 URL），目前在測試開發階段使用 SQLite 做資料庫管理，未來可改用 PostgreSQL。

---

## 功能

* 表單蒐集體感（模式、強度、熱敷、時長、滿意度分數等資料）。
* 送出到後端 API；離線時寫入 `queue.jsonl`，恢復連線可一鍵同步。
* 後端提供 `/api/feedback`（新增/查詢）、`/api/health`、`/api/insights`。
* `.env` 設定 `FEEDBACK_API`，支援跨環境部署。

---

## 結構

```
feedback_system/
  backend/
  gui/
  README.md
```

---

## 快速開始

```bash
# 後端
cd feedback_system/backend
python -m venv .venv && . .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py  # 啟動後端：http://127.0.0.1:8000

# 前端
cd ../gui
python -m venv .venv && . .venv/Scripts/activate
pip install -r requirements.txt
# 設定 API 位址
echo FEEDBACK_API=http://127.0.0.1:8000 > .env
python feedback_gui.py
```

---

## 設定

### gui/.env

```
FEEDBACK_API=http://127.0.0.1:8000
```

### gui/.gitignore

```
.env
__pycache__/
*.pyc
queue.jsonl
db.sqlite3
*.sqlite3
```

---

## 區網 / 雲端連線

* **區網：** 後端以 `--host 0.0.0.0` 啟動，前端 `.env` 指向 `http://<後端IP>:8000`。
* **雲端：** 可改用 **Nginx/Traefik + HTTPS**，設定 CORS 白名單、JWT/Token 驗證。

---

## API 範例

```bash
# 健康檢查
curl http://127.0.0.1:8000/api/health

# 新增回饋
curl -X POST http://127.0.0.1:8000/api/feedback \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id":"guest","gender":"不公開","age":25,
    "model":"按摩椅::T-800","mode":"全身","intensity":3,
    "heat":true,"duration_min":20,
    "relax_score":4,"pain_relief_score":4,"noise_score":3,"heat_fit_score":4,
    "pain_areas":"肩頸緊繃","issues":"右側滾輪略有噪音",
    "nps":8,"notes":"[使用場景]門市試用","contact_ok":false
  }'
```

---

## 常見問題

* **GUI 送不出去？** 檢查 `.env` 的 `FEEDBACK_API` 是否正確、後端是否啟動。
* **跨機連線失敗？** 確認防火牆已開放 TCP 8000，Wi‑Fi AP 未啟用 Client Isolation。
* **離線資料在哪？** `gui/queue.jsonl`；按「同步離線佇列」會嘗試重送。

---

## 安全

* 測試階段使用 SQLite；正式建議切換至 PostgreSQL，並導入 **TLS、JWT、RBAC 權限管理**。
* `.env` 與暫存檔均已加入 `.gitignore`，防止敏感資訊外洩。

---

## 授權

使用 **MIT** 授權條款。
