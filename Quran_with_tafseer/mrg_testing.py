import sqlite3

# Path to your main database (the one you just merged tafsir into)
db_path = 'siratemustaqeem_db_20251226_112125.db'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Test 1: Check if the tafsir table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tafsir';")
table_exists = cur.fetchone()
if table_exists:
    print("✓ Table 'tafsir' exists")
else:
    print("✗ Table 'tafsir' does NOT exist")
    conn.close()
    exit()

# Test 2: Count how many tafsir entries we have
cur.execute("SELECT COUNT(*) FROM tafsir")
count = cur.fetchone()[0]
print(f"✓ Total tafsir entries: {count}")

# Test 3: Show sample from Surah Al-Baqarah (Surah ID = 2)
print("\n--- Sample from Surah Al-Baqarah (Surah 2) ---")
cur.execute("""
SELECT ayah_number, substr(text, 1, 300) || '...' AS preview 
FROM tafsir 
WHERE surah_id = 2 
ORDER BY ayah_number 
LIMIT 5
""")
samples = cur.fetchall()
for aya_num, preview in samples:
    print(f"Ayah {aya_num}: {preview}")

# Test 4: Test a specific famous ayah - Ayat Al-Kursi (2:255)
print("\n--- Test Ayat Al-Kursi (2:255) ---")
cur.execute("""
SELECT text 
FROM tafsir 
WHERE surah_id = 2 AND ayah_number = 255
""")
kursi = cur.fetchone()
if kursi:
    print("✓ Found Ayat Al-Kursi tafsir")
    print(kursi[0][:500] + "..." if len(kursi[0]) > 500 else kursi[0])
else:
    print("✗ Ayat Al-Kursi tafsir NOT found")

# Test 5: Test the ayah you sent earlier (Al-Baqarah 271)
print("\n--- Test Al-Baqarah Ayah 271 (the one you shared) ---")
cur.execute("""
SELECT substr(text, 1, 600) || '...' AS preview 
FROM tafsir 
WHERE surah_id = 2 AND ayah_number = 271
""")
ayah_271 = cur.fetchone()
if ayah_271:
    print("✓ Found Ayah 271")
    print(ayah_271[0])
else:
    print("✗ Ayah 271 NOT found")

conn.close()
print("\nTest completed!")