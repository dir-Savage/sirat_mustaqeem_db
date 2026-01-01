import sqlite3
import json
import os

BASE_DB = "ayahs_positions/currentdb.db"
NEW_DB = "ayahs_positions/newwww_db.db"

# الملفات الجديدة
AYAHS_PATH = "ayahs_positions/ayahs"
PAGES_PATH = "ayahs_positions/pages"

# إنشاء نسخة جديدة من القاعدة
if os.path.exists(NEW_DB):
    os.remove(NEW_DB)
conn_new = sqlite3.connect(NEW_DB)
conn_old = sqlite3.connect(BASE_DB)

# نسخ قاعدة البيانات القديمة بالكامل
with conn_new:
    for line in conn_old.iterdump():
        conn_new.execute(line)

conn_old.close()

# إنشاء جداول للآيات الجديدة لو مش موجودة
with conn_new:
    conn_new.execute("""
        CREATE TABLE IF NOT EXISTS ayahs (
            aya_id INTEGER PRIMARY KEY,
            sura_id INTEGER NOT NULL,
            type INTEGER DEFAULT 0,
            text TEXT NOT NULL,
            external_id INTEGER
        )
    """)
    conn_new.execute("""
        CREATE TABLE IF NOT EXISTS ayah_pages (
            page_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sura_id INTEGER NOT NULL,
            aya_id INTEGER NOT NULL,
            segs TEXT NOT NULL
        )
    """)

# إدراج بيانات الآيات الجديدة
for filename in os.listdir(AYAHS_PATH):
    if filename.endswith(".json"):
        with open(os.path.join(AYAHS_PATH, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
        with conn_new:
            for entry in data:
                aya_id = entry.get("aya_id")
                sura_id = entry.get("sura_id")
                type_val = entry.get("type", 0)   # default 0
                text = entry.get("text", "")
                external_id = entry.get("id", None)
                if aya_id and sura_id and text:
                    conn_new.execute("""
                        INSERT OR REPLACE INTO ayahs (aya_id, sura_id, type, text, external_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (aya_id, sura_id, type_val, text, external_id))

# إدراج بيانات الصفحات
for filename in os.listdir(PAGES_PATH):
    if filename.endswith(".json"):
        with open(os.path.join(PAGES_PATH, filename), "r", encoding="utf-8") as f:
            pages = json.load(f)
        with conn_new:
            for page in pages:
                aya_id = page.get("aya_id")
                sura_id = page.get("sura_id")
                segs = json.dumps(page.get("segs", []), ensure_ascii=False)
                if aya_id and sura_id:
                    conn_new.execute("""
                        INSERT INTO ayah_pages (sura_id, aya_id, segs)
                        VALUES (?, ?, ?)
                    """, (sura_id, aya_id, segs))

conn_new.close()
print("New database created successfully:", NEW_DB)
