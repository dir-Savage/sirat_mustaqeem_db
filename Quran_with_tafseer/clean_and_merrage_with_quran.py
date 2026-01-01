import sqlite3
import re
import os

old_db_path = 'samples/Quraan_AQ.db'
main_db_path = 'siratemustaqeem_db_20251226_112125.db'

if not os.path.exists(old_db_path):
    print(f"Error: File '{old_db_path}' not found")
    exit()

if not os.path.exists(main_db_path):
    print(f"Error: File '{main_db_path}' not found")
    exit()

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

conn_old = sqlite3.connect(old_db_path)
cur_old = conn_old.cursor()

conn_main = sqlite3.connect(main_db_path)
cur_main = conn_main.cursor()

cur_main.execute('''
CREATE TABLE IF NOT EXISTS tafsir (
    surah_id INTEGER NOT NULL,
    ayah_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (surah_id, ayah_number)
)
''')

cur_old.execute("SELECT SURA_num, AYA_num, Tafsir FROM AQ ORDER BY SURA_num, AYA_num")
rows = cur_old.fetchall()

cleaned_count = 0
for row in rows:
    sura = row[0]
    aya = row[1]
    raw_text = row[2] if row[2] else ""
    cleaned = clean_text(raw_text)
    if cleaned:
        cur_main.execute('''
        INSERT OR REPLACE INTO tafsir (surah_id, ayah_number, text)
        VALUES (?, ?, ?)
        ''', (sura, aya, cleaned))
        cleaned_count += 1

conn_main.commit()

print("Success!")
print(f" - Cleaned and transferred {cleaned_count} ayah tafsir entries")
print(f" - New table: tafsir")
print(f" - Database: {main_db_path}")

conn_old.close()
conn_main.close()