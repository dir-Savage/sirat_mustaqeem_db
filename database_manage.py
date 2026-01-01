import sqlite3
import json
import os
from glob import glob

# Paths for JSON data
AYAHS_PATH = "ayahs_positions/ayahs/"
PAGES_PATH = "ayahs_positions/pages/"

# New database path
DB_PATH = "new.db"

# Remove existing database if any
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Connect to new SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.executescript("""
CREATE TABLE surah (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    ayats INTEGER NOT NULL,
    place TEXT NOT NULL
);

CREATE TABLE juz (
    no INTEGER PRIMARY KEY,
    name_english TEXT NOT NULL,
    name_arabic TEXT NOT NULL
);

CREATE TABLE quran (
    ayat_id INTEGER PRIMARY KEY,
    ayat_number INTEGER NOT NULL,
    arabic_text TEXT NOT NULL,
    urdu_translation TEXT NOT NULL,
    ayat_sajda INTEGER DEFAULT 0,
    surah_ruku INTEGER DEFAULT 0,
    para_ruku INTEGER DEFAULT 0,
    para_id INTEGER NOT NULL,
    manzil_no INTEGER DEFAULT 0,
    ayat_visible INTEGER DEFAULT 1,
    sura_id INTEGER NOT NULL,
    without_aerab TEXT NOT NULL,
    favourite INTEGER DEFAULT 0
);

CREATE INDEX idx_quran_surah ON quran(sura_id);
CREATE INDEX idx_quran_juz ON quran(para_id);
CREATE INDEX idx_quran_favourite ON quran(favourite);

CREATE TABLE dua (
    id INTEGER PRIMARY KEY,
    surah TEXT NOT NULL,
    aya_number INTEGER NOT NULL,
    aya TEXT NOT NULL,
    favourite INTEGER DEFAULT 0
);

CREATE TABLE tasbih (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    counter INTEGER NOT NULL,
    favourite INTEGER DEFAULT 0
);

CREATE TABLE allah_names (
    arabic TEXT NOT NULL,
    english TEXT NOT NULL,
    urdu_meaning TEXT NOT NULL,
    english_meaning TEXT NOT NULL,
    english_explanation TEXT NOT NULL
);

CREATE TABLE tafsir (
    sura_id INTEGER NOT NULL,
    aya_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (sura_id, aya_number)
);

CREATE TABLE ayahs (
    aya_id INTEGER PRIMARY KEY,
    sura_id INTEGER NOT NULL,
    type INTEGER DEFAULT 0,
    text TEXT NOT NULL,
    external_id INTEGER
);

CREATE TABLE ayah_pages (
    page_id INTEGER PRIMARY KEY,
    sura_id INTEGER NOT NULL,
    aya_id INTEGER NOT NULL,
    segs TEXT NOT NULL
);
""")

conn.commit()

# Function to load JSON files from a folder
def load_json_files(path):
    data = []
    for file in glob(os.path.join(path, "*.json")):
        with open(file, "r", encoding="utf-8") as f:
            try:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    data.extend(file_data)
                else:
                    print(f"Warning: {file} does not contain a list")
            except json.JSONDecodeError as e:
                print(f"Error decoding {file}: {e}")
    return data

# Load ayahs JSON
ayahs_data = load_json_files(AYAHS_PATH)
print(f"Loaded {len(ayahs_data)} ayahs")

# Insert ayahs into database with safety checks
inserted = 0
skipped = 0
for entry in ayahs_data:
    if "aya_id" not in entry or "sura_id" not in entry:
        skipped += 1
        continue
    if "text" not in entry:
        skipped += 1
        print(f"Skipping aya_id {entry.get('aya_id')} in sura {entry.get('sura_id')} due to missing text")
        continue

    aya_type = entry.get("type", 0)
    cursor.execute("""
        INSERT OR REPLACE INTO ayahs (aya_id, sura_id, type, text, external_id)
        VALUES (?, ?, ?, ?, ?)
    """, (entry["aya_id"], entry["sura_id"], aya_type, entry["text"], entry.get("id")))
    inserted += 1

conn.commit()
print(f"Inserted {inserted} ayahs, skipped {skipped}")

# Load pages JSON
pages_data = load_json_files(PAGES_PATH)
print(f"Loaded {len(pages_data)} pages")

# Insert pages into database
for idx, entry in enumerate(pages_data, start=1):
    segs_json = json.dumps(entry.get("segs", []), ensure_ascii=False)
    cursor.execute("""
        INSERT OR REPLACE INTO ayah_pages (page_id, sura_id, aya_id, segs)
        VALUES (?, ?, ?, ?)
    """, (idx, entry["sura_id"], entry["aya_id"], segs_json))

conn.commit()
print("Ayah pages inserted successfully.")

# Close the connection
conn.close()
print(f"Database created at {DB_PATH}")
