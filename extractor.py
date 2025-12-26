# simple_converter.py
import sqlite3
import re

# Read your SQL file
with open('DB/quran-simple.sql', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all INSERT values using regex
pattern = r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']*(?:''[^']*)*)'\s*\)"
matches = re.findall(pattern, content)

print(f"Found {len(matches)} verses")

# Create SQLite DB
conn = sqlite3.connect('quran-converted.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE quran (
    ayatId INTEGER PRIMARY KEY,
    ayatNumber INTEGER,
    arabicText TEXT,
    urduTranslation TEXT,
    surahId INTEGER,
    paraId INTEGER DEFAULT 1,
    favourite INTEGER DEFAULT 0
)
''')

# Insert first 100 verses for testing
for idx, sura, aya, text in matches[:100]:
    cursor.execute('''
    INSERT INTO quran (ayatId, ayatNumber, arabicText, urduTranslation, surahId, paraId, favourite)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (int(idx), int(aya), text.replace("''", "'"), 
          f"Urdu for {sura}:{aya}", int(sura), 1, 0))

conn.commit()
conn.close()

print("✅ Test database created: quran-converted.db")