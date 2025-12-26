#!/usr/bin/env python3
"""
Convert MySQL Quran SQL to Sirate Mustaqeem SQLite Database
"""

import re
import sqlite3
from pathlib import Path

def parse_mysql_sql_file(sql_file_path):
    """Parse your MySQL SQL file and extract all verses"""
    print(f"📖 Parsing: {sql_file_path}")
    
    verses = []
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all INSERT statements
    # Pattern for: INSERT INTO `quran_text` (`index`, `sura`, `aya`, `text`) VALUES (...);
    insert_pattern = r"INSERT INTO `quran_text`\s*\([^)]+\)\s*VALUES\s*(.*?);"
    
    # Find all INSERT blocks
    insert_matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not insert_matches:
        print("⚠️  No INSERT statements found. Trying alternative parsing...")
        # Try to parse line by line
        lines = content.split('\n')
        for line in lines:
            if 'INSERT INTO' in line.upper() and 'VALUES' in line.upper():
                # Extract values part
                values_part = line.split('VALUES')[1].strip()
                # Remove parentheses and split
                values_part = values_part.strip('();')
                # This is a simple parser - might need adjustment
                print(f"Found line: {line[:100]}...")
    
    # Let's try a simpler approach - parse the entire file
    print("🔍 Parsing all data lines...")
    
    # Look for pattern: (1, 1, 1, 'بِسْمِ اللَّهِ...'),
    value_pattern = r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']*(?:''[^']*)*)'\s*\)"
    
    matches = re.findall(value_pattern, content)
    
    print(f"✅ Found {len(matches)} verse entries")
    
    for match in matches[:5]:  # Show first 5
        idx, sura, aya, text = match
        print(f"  Verse {idx}: Sura {sura}:{aya} - {text[:50]}...")
    
    return matches

def get_urdu_translation_for_verse(sura, aya):
    """Get Urdu translation - placeholder for now"""
    # You'll need to download Urdu translation file
    # For testing, return placeholder
    return f"Urdu translation for Sura {sura}, Aya {aya}"

def create_siratemustaqeem_db(quran_verses, output_db='siratemustaqeem-db.db'):
    """Create the complete SQLite database"""
    print(f"\n🗄️ Creating SQLite database: {output_db}")
    
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    # 1. Create the Quran table (exact schema from app)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quran (
        ayatId INTEGER PRIMARY KEY,
        ayatNumber INTEGER NOT NULL,
        arabicText TEXT NOT NULL,
        urduTranslation TEXT NOT NULL,
        ayatSajda INTEGER DEFAULT 0,
        surahRuku INTEGER DEFAULT 0,
        paraRuku INTEGER DEFAULT 0,
        paraId INTEGER NOT NULL,
        manzilNo INTEGER DEFAULT 0,
        ayatVisible INTEGER DEFAULT 1,
        surahId INTEGER NOT NULL,
        withoutAerab TEXT NOT NULL,
        favourite INTEGER DEFAULT 0
    )
    ''')
    
    # 2. Create other required tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS surah (
        id INTEGER PRIMARY KEY,
        name_en TEXT NOT NULL,
        name_ar TEXT NOT NULL,
        ayats INTEGER NOT NULL,
        place TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS juz (
        no INTEGER PRIMARY KEY,
        name_english TEXT NOT NULL,
        name_arabic TEXT NOT NULL
    )
    ''')
    
    # 3. Insert Quran data
    print("📝 Inserting Quran verses...")
    
    # Juz boundaries (simplified - 30 juz)
    juz_boundaries = [
        (1, 1, 1, 2, 141), (2, 2, 142, 2, 252), (3, 2, 253, 3, 92),
        (4, 3, 93, 4, 23), (5, 4, 24, 4, 147), (6, 4, 148, 5, 81),
        (7, 5, 82, 6, 110), (8, 6, 111, 7, 87), (9, 7, 88, 8, 40),
        (10, 8, 41, 9, 92), (11, 9, 93, 11, 5), (12, 11, 6, 12, 52),
        (13, 12, 53, 14, 52), (14, 15, 1, 16, 128), (15, 17, 1, 18, 74),
        (16, 18, 75, 20, 135), (17, 21, 1, 22, 78), (18, 23, 1, 25, 20),
        (19, 25, 21, 27, 55), (20, 27, 56, 29, 45), (21, 29, 46, 33, 30),
        (22, 33, 31, 36, 27), (23, 36, 28, 39, 31), (24, 39, 32, 41, 46),
        (25, 41, 47, 45, 37), (26, 46, 1, 51, 30), (27, 51, 31, 57, 29),
        (28, 58, 1, 66, 12), (29, 67, 1, 77, 50), (30, 78, 1, 114, 6)
    ]
    
    # Sajda verses
    sajda_verses = [
        (7, 206), (13, 15), (16, 50), (17, 109), (19, 58),
        (22, 18), (22, 77), (25, 60), (27, 26), (32, 15),
        (38, 24), (41, 38), (53, 62), (84, 21), (96, 19)
    ]
    
    inserted_count = 0
    batch_size = 500
    
    for i, verse_data in enumerate(quran_verses):
        idx, sura, aya, arabic_text = verse_data
        sura = int(sura)
        aya = int(aya)
        
        # Clean Arabic text (handle escaped quotes)
        arabic_text = arabic_text.replace("''", "'")
        
        # Determine juz
        juz = 1
        for j, s_start, v_start, s_end, v_end in juz_boundaries:
            if sura == s_start and aya >= v_start:
                juz = j
                break
            elif sura > s_start and sura < s_end:
                juz = j
                break
            elif sura == s_end and aya <= v_end:
                juz = j
                break
        
        # Check if sajda verse
        has_sajda = 1 if (sura, aya) in sajda_verses else 0
        
        # Urdu translation (placeholder - you need actual data)
        urdu_trans = get_urdu_translation_for_verse(sura, aya)
        
        # Without aerab (same as with for now)
        without_aerab = arabic_text  # You should get proper text without diacritics
        
        # Calculate ruku (simplified)
        surah_ruku = (aya - 1) // 10 + 1
        
        # Insert into database
        cursor.execute('''
        INSERT INTO quran (ayatId, ayatNumber, arabicText, urduTranslation, 
                          ayatSajda, surahRuku, paraRuku, paraId, manzilNo, 
                          ayatVisible, surahId, withoutAerab, favourite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(idx) + 1000,  # ayatId (offset to avoid conflicts)
            aya,              # ayatNumber
            arabic_text,      # arabicText
            urdu_trans,       # urduTranslation
            has_sajda,        # ayatSajda
            surah_ruku,       # surahRuku
            surah_ruku,       # paraRuku (same as surahRuku for now)
            juz,              # paraId
            (juz - 1) // 4 + 1,  # manzilNo (1-7)
            1,                # ayatVisible
            sura,             # surahId
            without_aerab,    # withoutAerab
            0                 # favourite
        ))
        
        inserted_count += 1
        
        # Show progress
        if inserted_count % batch_size == 0:
            print(f"  Processed {inserted_count} verses...")
    
    print(f"✅ Inserted {inserted_count} Quran verses")
    
    # 4. Insert surah metadata (you need to complete this)
    print("📝 Adding surah metadata...")
    # Sample - you need all 114 surahs
    surahs = [
        (1, "Al-Fatiha", "الفاتحة", 7, "Meccan"),
        (2, "Al-Baqarah", "البقرة", 286, "Medinan"),
        (114, "An-Nas", "الناس", 6, "Meccan")
    ]
    
    cursor.executemany('INSERT INTO surah VALUES (?, ?, ?, ?, ?)', surahs)
    
    # 5. Insert juz names
    print("📝 Adding juz names...")
    juz_names = [(i, f"Juz {i}", f"جزء {i}") for i in range(1, 31)]
    cursor.executemany('INSERT INTO juz VALUES (?, ?, ?)', juz_names)
    
    # 6. Create other tables (empty for now)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dua (
        id INTEGER PRIMARY KEY,
        surah TEXT NOT NULL,
        aya_number INTEGER NOT NULL,
        aya TEXT NOT NULL,
        favorite INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasbih (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        counter INTEGER NOT NULL,
        favorite INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS allah_names (
        arabic TEXT NOT NULL,
        english TEXT NOT NULL,
        urduMeaning TEXT NOT NULL,
        englishMeaning TEXT NOT NULL,
        englishExplanation TEXT NOT NULL
    )
    ''')
    
    # Add some sample tasbih
    cursor.executemany('''
    INSERT INTO tasbih VALUES (?, ?, ?, ?)
    ''', [
        (1, "Subhanallah", 33, 1),
        (2, "Alhamdulillah", 33, 1),
        (3, "Allahu Akbar", 34, 1)
    ])
    
    # Add sample Allah names
    cursor.executemany('''
    INSERT INTO allah_names VALUES (?, ?, ?, ?, ?)
    ''', [
        ("الرَّحْمَنُ", "Ar-Rahman", "نہایت مہربان", 
         "The Beneficent", "The Most Gracious"),
        ("الرَّحِيمُ", "Ar-Rahim", "نہایت رحم کرنے والا",
         "The Merciful", "The Most Merciful")
    ])
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM quran")
    quran_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM quran WHERE surahId = 1 LIMIT 1")
    sample = cursor.fetchone()
    
    print(f"\n✅ Database created successfully!")
    print(f"📊 Stats:")
    print(f"   Quran verses: {quran_count}")
    print(f"   Surahs: {len(surahs)}")
    print(f"   Juz: 30")
    
    print(f"\n📄 Sample verse (Surah 1:1):")
    print(f"   Arabic: {sample[2][:50]}...")
    print(f"   Urdu: {sample[3][:50]}...")
    print(f"   Juz: {sample[7]}")
    
    conn.close()
    
    # Get file size
    file_size = Path(output_db).stat().st_size / (1024 * 1024)
    print(f"\n📁 File: {output_db}")
    print(f"📦 Size: {file_size:.2f} MB")
    
    return output_db

def main():
    print("=" * 60)
    print("MYSQL TO SQLITE QURAN CONVERTER")
    print("=" * 60)
    
    # Path to your SQL file
    sql_file = "DB/quran-simple.sql"
    
    if not Path(sql_file).exists():
        print(f"❌ File not found: {sql_file}")
        print("\n💡 Please place your SQL file in the DB/ folder")
        print("   Or update the path in the script")
        return
    
    # Parse the SQL file
    verses = parse_mysql_sql_file(sql_file)
    
    if not verses:
        print("❌ No verses could be parsed")
        return
    
    # Create the database
    db_path = create_siratemustaqeem_db(verses)
    
    print(f"\n🎉 Conversion complete!")
    print(f"\n📱 To use in Flutter:")
    print(f"1. Copy to assets: cp {db_path} your_flutter_project/assets/")
    print(f"2. Add to pubspec.yaml:")
    print("""
  assets:
    - assets/siratemustaqeem-db.db
    """)
    print(f"3. Test with the app!")

if __name__ == "__main__":
    main()