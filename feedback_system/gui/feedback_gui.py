import sys, os, json, time
from pathlib import Path
from datetime import datetime
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QTextEdit, QPushButton, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon  
from dotenv import load_dotenv 

# ==== 載入環境變數 ====
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
# 讀資源的根目錄（PyInstaller 支援）
PKG_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

# 真正可寫入的目錄（EXE 同層）
if getattr(sys, "frozen", False):
    WRITABLE_DIR = Path(sys.executable).parent
else:
    WRITABLE_DIR = Path(__file__).parent

# 1) 先嘗試讀可寫目錄的 .env（讓使用者可改）
env_candidate = WRITABLE_DIR / ".env"
if env_candidate.exists():
    load_dotenv(env_candidate)
else:
    # 回退到包內預設
    load_dotenv(PKG_DIR / ".env")

API_BASE   = os.environ.get("FEEDBACK_API", "http://127.0.0.1:8000")
QUEUE_PATH = (WRITABLE_DIR / "queue.jsonl").as_posix()
CSV_PATH   = (WRITABLE_DIR / "feedback.csv").as_posix()

# 與後端對接欄位（後端仍使用 "model" 欄位，這裡將類別+品名合併後送出）
FIELDS = [
  "user_id","gender","age","model",
  "mode","intensity","heat","duration_min",
  "relax_score","pain_relief_score","noise_score","heat_fit_score",
  "pain_areas","issues","nps","notes","contact_ok",
]

MODES = ["全身", "頸部", "肩部", "腰部", "伸展"]
CATEGORIES = ["按摩椅", "按摩器", "枕/靠墊", "健身/復健", "其他"]
CHANNELS = ["門市試用", "已購買-家用", "商用場所", "其他"]
PAIN_AREAS = ["shoulder","back","waist","hip"]
ISSUES = ["noise","overheat","jam","too_strong","others"]

class Form(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("產品回饋 GUI（通用版）")
        if os.path.exists(os.path.join(DATA_DIR, "logo.png")):
            self.setWindowIcon(QIcon(os.path.join(DATA_DIR, "logo.png")))

        g = QGridLayout(self)
        r = 0

        # === 基本資訊 ===
        g.addWidget(QLabel("使用者ID"), r, 0); self.user_id = QLineEdit("guest"); g.addWidget(self.user_id, r,1); r+=1
        g.addWidget(QLabel("性別"), r, 0); self.gender = QComboBox(); self.gender.addItems(["男","女","不公開"]); g.addWidget(self.gender, r,1); r+=1
        g.addWidget(QLabel("年齡"), r, 0); self.age = QSpinBox(); self.age.setRange(0,120); g.addWidget(self.age, r,1); r+=1

        # === 產品通用欄位 ===
        g.addWidget(QLabel("產品類別"), r, 0); self.category = QComboBox(); self.category.addItems(CATEGORIES); g.addWidget(self.category, r,1); r+=1
        g.addWidget(QLabel("產品名稱/型號"), r, 0); self.product_name = QLineEdit(); g.addWidget(self.product_name, r,1); r+=1
        g.addWidget(QLabel("使用場景"), r, 0); self.channel = QComboBox(); self.channel.addItems(CHANNELS); g.addWidget(self.channel, r,1); r+=1

        # === 使用情境 ===
        g.addWidget(QLabel("模式"), r, 0); self.mode = QComboBox(); self.mode.addItems(MODES); g.addWidget(self.mode, r,1); r+=1
        g.addWidget(QLabel("強度(1-5)"), r,0); self.intensity = QSpinBox(); self.intensity.setRange(1,5); self.intensity.setValue(3); g.addWidget(self.intensity, r,1); r+=1
        g.addWidget(QLabel("熱敷"), r,0); self.heat = QCheckBox("開啟"); g.addWidget(self.heat, r,1); r+=1
        g.addWidget(QLabel("時長(分鐘)"), r,0); self.duration = QSpinBox(); self.duration.setRange(1, 120); self.duration.setValue(15); g.addWidget(self.duration, r,1); r+=1

        # === 體感 Likert ===
        g.addWidget(QLabel("放鬆分數(1-5)"), r,0); self.relax = QSpinBox(); self.relax.setRange(1,5); self.relax.setValue(4); g.addWidget(self.relax, r,1); r+=1
        g.addWidget(QLabel("酸痛改善(1-5)"), r,0); self.painrelief = QSpinBox(); self.painrelief.setRange(1,5); self.painrelief.setValue(4); g.addWidget(self.painrelief, r,1); r+=1
        g.addWidget(QLabel("噪音感受(1-5)"), r,0); self.noise = QSpinBox(); self.noise.setRange(1,5); self.noise.setValue(3); g.addWidget(self.noise, r,1); r+=1
        g.addWidget(QLabel("熱度恰當(1-5)"), r,0); self.heatfit = QSpinBox(); self.heatfit.setRange(1,5); self.heatfit.setValue(4); g.addWidget(self.heatfit, r,1); r+=1

        # === 痛點/問題 ===
        g.addWidget(QLabel("痛點（文字描述）"), r,0); self.painareas = QTextEdit(); g.addWidget(self.painareas, r,1); r+=1
        g.addWidget(QLabel("問題（文字描述）"), r,0); self.issues = QTextEdit(); g.addWidget(self.issues, r,1); r+=1

        # === NPS/備註 ===
        g.addWidget(QLabel("整體滿意度 NPS(0-10)"), r,0); self.nps = QSpinBox(); self.nps.setRange(0,10); self.nps.setValue(8); g.addWidget(self.nps, r,1); r+=1
        g.addWidget(QLabel("備註"), r,0); self.notes = QTextEdit(); g.addWidget(self.notes, r,1); r+=1
        g.addWidget(QLabel("可聯絡？"), r,0); self.contact = QComboBox(); self.contact.addItems(["否","是"]); g.addWidget(self.contact, r,1); r+=1
        # 連絡方式（僅在「是」時顯示）
        g.addWidget(QLabel("電話"), r,0); self.phone = QLineEdit(); g.addWidget(self.phone, r,1); r+=1
        g.addWidget(QLabel("Gmail"), r,0); self.gmail = QLineEdit(); g.addWidget(self.gmail, r,1); r+=1
        self.phone.setVisible(False); self.gmail.setVisible(False)
        self.contact.currentTextChanged.connect(self._toggle_contact)
        

        # === 按鍵 ===
        self.btn_send = QPushButton("送出到後端")
        self.btn_sync = QPushButton("同步離線佇列")
        g.addWidget(self.btn_send, r,0); g.addWidget(self.btn_sync, r,1); r+=1

        self.btn_send.clicked.connect(self.send_api)
        self.btn_sync.clicked.connect(self.sync_queue)

    def _toggle_contact(self, txt: str):
            show = (txt == "是")
            self.phone.setVisible(show)
            self.gmail.setVisible(show)

    def payload(self):
        model_value = f"{self.category.currentText()}::{self.product_name.text().strip()}"
        contact_yes = (self.contact.currentText() == "是")

        # 基本檢核（選「是」時必填電話/Gmail；可改成更嚴謹的 regex）
        if contact_yes:
            if not self.phone.text().strip() or not self.gmail.text().strip():
                QMessageBox.warning(self, "欄位未填", "選擇『可聯絡：是』時，請填寫電話與 Gmail。")
                raise RuntimeError("contact required")

        return {
        "user_id": self.user_id.text().strip() or "guest",
        "gender": self.gender.currentText(),
        "age": int(self.age.value()),
        "model": model_value,
        "mode": self.mode.currentText(),
        "intensity": int(self.intensity.value()),
        "heat": bool(self.heat.isChecked()),
        "duration_min": int(self.duration.value()),
        "relax_score": int(self.relax.value()),
        "pain_relief_score": int(self.painrelief.value()),
        "noise_score": int(self.noise.value()),
        "heat_fit_score": int(self.heatfit.value()),
        "pain_areas": self.painareas.toPlainText().strip(),
        "issues": self.issues.toPlainText().strip(),
        "nps": int(self.nps.value()),
        "notes": (self.notes.toPlainText().strip() + f"\n[使用場景]{self.channel.currentText()}"),
        "contact_ok": contact_yes,
        "phone": (self.phone.text().strip() if contact_yes else ""),
        "gmail": (self.gmail.text().strip() if contact_yes else ""),
    }


    def append_queue(self, data):
        with open(QUEUE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def send_api(self):
        data = self.payload()
        try:
            r = requests.post(f"{API_BASE}/api/feedback", json=data, timeout=3)
            r.raise_for_status()
            QMessageBox.information(self, "已送出", "後端收到了！")
        except Exception as e:
            self.append_queue(data)
            QMessageBox.warning(self, "改為離線儲存", f"目前無法連線，已加入佇列。`\n{e}")

    def sync_queue(self):
        if not os.path.exists(QUEUE_PATH):
            QMessageBox.information(self, "佇列為空", "沒有待送資料")
            return
        lines = []
        with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        ok, fail = 0, 0
        with open(QUEUE_PATH + ".tmp", 'w', encoding='utf-8') as out:
            for ln in lines:
                try:
                    data = json.loads(ln)
                    r = requests.post(f"{API_BASE}/api/feedback", json=data, timeout=3)
                    r.raise_for_status()
                    ok += 1
                except Exception:
                    out.write(ln + "")
                    fail += 1
                    time.sleep(0.2)
        os.replace(QUEUE_PATH + ".tmp", QUEUE_PATH)
        if fail == 0 and os.path.exists(QUEUE_PATH):
            os.remove(QUEUE_PATH)
        QMessageBox.information(self, "同步完成", f"成功 {ok} 筆，失敗 {fail} 筘")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Form(); w.resize(560, 760); w.show()
    sys.exit(app.exec())