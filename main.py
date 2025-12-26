#!/usr/bin/env python3
"""
FIXED QURAN DATABASE CONVERTER for Sirate Mustaqeem App
Matches exact database schema from the Flutter app
"""

import re
import sqlite3
import json
import urllib.request
import requests
from pathlib import Path
from datetime import datetime
import sys
import os

class QuranDatabaseConverter:
    def __init__(self, sql_file_path):
        self.sql_file_path = Path(sql_file_path)
        self.arabic_verses = []
        self.urdu_translations = {}
        self.surah_metadata = []
        self.juz_data = []
        
    def validate_input(self):
        """Check if input files exist"""
        if not self.sql_file_path.exists():
            print(f"❌ Error: SQL file not found: {self.sql_file_path}")
            return False
        
        print(f"✅ Found SQL file: {self.sql_file_path}")
        print(f"   Size: {self.sql_file_path.stat().st_size / 1024:.1f} KB")
        return True
    
    def download_required_data(self):
        """Download missing data files"""
        print("\n📥 Downloading required data files...")
        
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        
        # 1. Urdu Translation (Maududi)
        urdu_url = "https://tanzil.net/trans/ur.maududi"
        urdu_file = "data/urdu_translation.txt"
        
        if not Path(urdu_file).exists():
            print(f"   Downloading Urdu translation...")
            try:
                response = requests.get(urdu_url)
                with open(urdu_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"   ✅ Downloaded: {urdu_file}")
            except Exception as e:
                print(f"   ❌ Failed to download Urdu: {e}")
                print(f"   Using placeholder translations")
        
        # 2. Arabic without diacritics (Uthmani simple)
        arabic_simple_url = "https://tanzil.net/res/text/uthmani-min/quran-uthmani-min.txt"
        arabic_simple_file = "data/arabic_simple.txt"
        
        if not Path(arabic_simple_file).exists():
            print(f"   Downloading Arabic without diacritics...")
            try:
                response = requests.get(arabic_simple_url)
                with open(arabic_simple_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"   ✅ Downloaded: {arabic_simple_file}")
            except:
                print(f"   ⚠️ Could not download Arabic simple text")
        
        return True
    
    def parse_arabic_sql(self):
        """Parse your MySQL SQL file"""
        print("\n🔍 Parsing Arabic Quran SQL file...")
        
        try:
            with open(self.sql_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(self.sql_file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Improved pattern to handle different SQL formats
        patterns = [
            # Pattern 1: (1, 1, 1, 'text'),
            r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']*(?:''[^']*)*)'\s*\)",
            # Pattern 2: INSERT INTO `quran` VALUES (1,1,1,'text')
            r"VALUES\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']*(?:''[^']*)*)'",
            # Pattern 3: Just look for number,number,number,'text' pattern
            r"(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']*(?:''[^']*)*)'"
        ]
        
        matches = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                break
        
        if not matches:
            print("❌ No verses found in SQL file")
            print("💡 Trying alternative parsing...")
            # Try line-by-line parsing
            lines = content.split('\n')
            for line in lines:
                if 'INSERT' in line and 'quran' in line.lower():
                    # Extract values part
                    if 'VALUES' in line:
                        values_part = line.split('VALUES')[1].strip()
                        # Simple extraction
                        match = re.search(r"\(([^)]+)\)", values_part)
                        if match:
                            values = match.group(1).split(',')
                            if len(values) >= 4:
                                idx = values[0].strip()
                                sura = values[1].strip()
                                aya = values[2].strip()
                                text = ','.join(values[3:]).strip().strip("'")
                                matches.append((idx, sura, aya, text))
        
        if not matches:
            print("❌ No verses found using any pattern")
            return False
        
        print(f"✅ Found {len(matches)} Arabic verses")
        
        # Store verses
        self.arabic_verses = []
        for match in matches:
            if len(match) >= 4:
                idx, sura, aya, text = match[:4]
                try:
                    self.arabic_verses.append({
                        'id': int(idx),
                        'surah': int(sura),
                        'ayah': int(aya),
                        'arabic': text.replace("''", "'").strip()
                    })
                except ValueError:
                    continue
        
        # Sort by surah and ayah
        self.arabic_verses.sort(key=lambda x: (x['surah'], x['ayah']))
        
        print(f"✅ Processed {len(self.arabic_verses)} valid verses")
        
        # Verify we have all 6236 verses
        if len(self.arabic_verses) != 6236:
            print(f"⚠️ Warning: Expected 6236 verses, found {len(self.arabic_verses)}")
            print("   This may cause issues with the app")
        
        return True
    
    def parse_urdu_translation(self):
        """Parse Urdu translation file"""
        urdu_file = "data/urdu_translation.txt"
        
        if not Path(urdu_file).exists():
            print("⚠️ Urdu file not found. Using placeholders.")
            return True
        
        print("🔍 Parsing Urdu translation...")
        
        try:
            with open(urdu_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            print("⚠️ Could not read Urdu file")
            return True
        
        self.urdu_translations = {}
        
        for line in lines:
            if '|' in line:
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    try:
                        sura = int(parts[0])
                        aya = int(parts[1])
                        text = parts[2]
                        key = f"{sura}:{aya}"
                        self.urdu_translations[key] = text
                    except:
                        continue
        
        print(f"✅ Loaded {len(self.urdu_translations)} Urdu translations")
        return True
    
    def parse_arabic_simple(self):
        """Parse Arabic without diacritics"""
        simple_file = "data/arabic_simple.txt"
        
        self.arabic_simple = {}
        
        if Path(simple_file).exists():
            print("🔍 Parsing Arabic without diacritics...")
            
            try:
                with open(simple_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except:
                print("⚠️ Could not read Arabic simple file")
                return True
            
            for line in lines:
                if '|' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        try:
                            sura = int(parts[0])
                            aya = int(parts[1])
                            text = parts[2]
                            key = f"{sura}:{aya}"
                            self.arabic_simple[key] = text
                        except:
                            continue
            
            print(f"✅ Loaded {len(self.arabic_simple)} simple Arabic texts")
        else:
            print("⚠️ Arabic simple file not found")
        
        return True
    
    def load_surah_metadata(self):
        """Load complete surah metadata - EXACTLY as app expects"""
        print("\n📚 Loading surah metadata...")
        
        # Complete list of 114 surahs matching the app's Surah model
        self.surah_metadata = [
            # id, name_en, name_ar, ayats, place
            (1, "Al-Fatiha", "الفاتحة", 7, "Meccan"),
            (2, "Al-Baqarah", "البقرة", 286, "Medinan"),
            (3, "Aal-e-Imran", "آل عمران", 200, "Medinan"),
            (4, "An-Nisa", "النساء", 176, "Medinan"),
            (5, "Al-Ma'idah", "المائدة", 120, "Medinan"),
            (6, "Al-An'am", "الأنعام", 165, "Meccan"),
            (7, "Al-A'raf", "الأعراف", 206, "Meccan"),
            (8, "Al-Anfal", "الأنفال", 75, "Medinan"),
            (9, "At-Taubah", "التوبة", 129, "Medinan"),
            (10, "Yunus", "يونس", 109, "Meccan"),
            (11, "Hud", "هود", 123, "Meccan"),
            (12, "Yusuf", "يوسف", 111, "Meccan"),
            (13, "Ar-Ra'd", "الرعد", 43, "Medinan"),
            (14, "Ibrahim", "ابراهيم", 52, "Meccan"),
            (15, "Al-Hijr", "الحجر", 99, "Meccan"),
            (16, "An-Nahl", "النحل", 128, "Meccan"),
            (17, "Al-Isra", "الإسراء", 111, "Meccan"),
            (18, "Al-Kahf", "الكهف", 110, "Meccan"),
            (19, "Maryam", "مريم", 98, "Meccan"),
            (20, "Taha", "طه", 135, "Meccan"),
            (21, "Al-Anbiya", "الأنبياء", 112, "Meccan"),
            (22, "Al-Hajj", "الحج", 78, "Medinan"),
            (23, "Al-Mu'minun", "المؤمنون", 118, "Meccan"),
            (24, "An-Nur", "النور", 64, "Medinan"),
            (25, "Al-Furqan", "الفرقان", 77, "Meccan"),
            (26, "Ash-Shu'ara", "الشعراء", 227, "Meccan"),
            (27, "An-Naml", "النمل", 93, "Meccan"),
            (28, "Al-Qasas", "القصص", 88, "Meccan"),
            (29, "Al-Ankabut", "العنكبوت", 69, "Meccan"),
            (30, "Ar-Rum", "الروم", 60, "Meccan"),
            (31, "Luqman", "لقمان", 34, "Meccan"),
            (32, "As-Sajda", "السجدة", 30, "Meccan"),
            (33, "Al-Ahzab", "الأحزاب", 73, "Medinan"),
            (34, "Saba", "سبإ", 54, "Meccan"),
            (35, "Fatir", "فاطر", 45, "Meccan"),
            (36, "Ya-Sin", "يس", 83, "Meccan"),
            (37, "As-Saffat", "الصافات", 182, "Meccan"),
            (38, "Sad", "ص", 88, "Meccan"),
            (39, "Az-Zumar", "الزمر", 75, "Meccan"),
            (40, "Ghafir", "غافر", 85, "Meccan"),
            (41, "Fussilat", "فصلت", 54, "Meccan"),
            (42, "Ash-Shura", "الشورى", 53, "Meccan"),
            (43, "Az-Zukhruf", "الزخرف", 89, "Meccan"),
            (44, "Ad-Dukhan", "الدخان", 59, "Meccan"),
            (45, "Al-Jathiya", "الجاثية", 37, "Meccan"),
            (46, "Al-Ahqaf", "الأحقاف", 35, "Meccan"),
            (47, "Muhammad", "محمد", 38, "Medinan"),
            (48, "Al-Fath", "الفتح", 29, "Medinan"),
            (49, "Al-Hujurat", "الحجرات", 18, "Medinan"),
            (50, "Qaf", "ق", 45, "Meccan"),
            (51, "Adh-Dhariyat", "الذاريات", 60, "Meccan"),
            (52, "At-Tur", "الطور", 49, "Meccan"),
            (53, "An-Najm", "النجم", 62, "Meccan"),
            (54, "Al-Qamar", "القمر", 55, "Meccan"),
            (55, "Ar-Rahman", "الرحمن", 78, "Medinan"),
            (56, "Al-Waqi'a", "الواقعة", 96, "Meccan"),
            (57, "Al-Hadid", "الحديد", 29, "Medinan"),
            (58, "Al-Mujadila", "المجادلة", 22, "Medinan"),
            (59, "Al-Hashr", "الحشر", 24, "Medinan"),
            (60, "Al-Mumtahina", "الممتحنة", 13, "Medinan"),
            (61, "As-Saff", "الصف", 14, "Medinan"),
            (62, "Al-Jumu'a", "الجمعة", 11, "Medinan"),
            (63, "Al-Munafiqun", "المنافقون", 11, "Medinan"),
            (64, "At-Taghabun", "التغابن", 18, "Medinan"),
            (65, "At-Talaq", "الطلاق", 12, "Medinan"),
            (66, "At-Tahrim", "التحريم", 12, "Medinan"),
            (67, "Al-Mulk", "الملك", 30, "Meccan"),
            (68, "Al-Qalam", "القلم", 52, "Meccan"),
            (69, "Al-Haqqa", "الحاقة", 52, "Meccan"),
            (70, "Al-Ma'arij", "المعارج", 44, "Meccan"),
            (71, "Nuh", "نوح", 28, "Meccan"),
            (72, "Al-Jinn", "الجن", 28, "Meccan"),
            (73, "Al-Muzzammil", "المزمل", 20, "Meccan"),
            (74, "Al-Muddathir", "المدثر", 56, "Meccan"),
            (75, "Al-Qiyama", "القيامة", 40, "Meccan"),
            (76, "Al-Insan", "الانسان", 31, "Medinan"),
            (77, "Al-Mursalat", "المرسلات", 50, "Meccan"),
            (78, "An-Naba", "النبإ", 40, "Meccan"),
            (79, "An-Nazi'at", "النازعات", 46, "Meccan"),
            (80, "Abasa", "عبس", 42, "Meccan"),
            (81, "At-Takwir", "التكوير", 29, "Meccan"),
            (82, "Al-Infitar", "الإنفطار", 19, "Meccan"),
            (83, "Al-Mutaffifin", "المطففين", 36, "Meccan"),
            (84, "Al-Inshiqaq", "الإنشقاق", 25, "Meccan"),
            (85, "Al-Buruj", "البروج", 22, "Meccan"),
            (86, "At-Tariq", "الطارق", 17, "Meccan"),
            (87, "Al-A'la", "الأعلى", 19, "Meccan"),
            (88, "Al-Ghashiya", "الغاشية", 26, "Meccan"),
            (89, "Al-Fajr", "الفجر", 30, "Meccan"),
            (90, "Al-Balad", "البلد", 20, "Meccan"),
            (91, "Ash-Shams", "الشمس", 15, "Meccan"),
            (92, "Al-Lail", "الليل", 21, "Meccan"),
            (93, "Ad-Duha", "الضحى", 11, "Meccan"),
            (94, "Ash-Sharh", "الشرح", 8, "Meccan"),
            (95, "At-Tin", "التين", 8, "Meccan"),
            (96, "Al-Alaq", "العلق", 19, "Meccan"),
            (97, "Al-Qadr", "القدر", 5, "Meccan"),
            (98, "Al-Bayyina", "البينة", 8, "Medinan"),
            (99, "Az-Zalzala", "الزلزلة", 8, "Medinan"),
            (100, "Al-Adiyat", "العاديات", 11, "Meccan"),
            (101, "Al-Qari'a", "القارعة", 11, "Meccan"),
            (102, "At-Takathur", "التكاثر", 8, "Meccan"),
            (103, "Al-Asr", "العصر", 3, "Meccan"),
            (104, "Al-Humaza", "الهمزة", 9, "Meccan"),
            (105, "Al-Fil", "الفيل", 5, "Meccan"),
            (106, "Quraish", "قريش", 4, "Meccan"),
            (107, "Al-Ma'un", "الماعون", 7, "Meccan"),
            (108, "Al-Kawthar", "الكوثر", 3, "Meccan"),
            (109, "Al-Kafirun", "الكافرون", 6, "Meccan"),
            (110, "An-Nasr", "النصر", 3, "Medinan"),
            (111, "Al-Masad", "المسد", 5, "Meccan"),
            (112, "Al-Ikhlas", "الإخلاص", 4, "Meccan"),
            (113, "Al-Falaq", "الفلق", 5, "Meccan"),
            (114, "An-Nas", "الناس", 6, "Meccan")
        ]
        
        print(f"✅ Loaded metadata for {len(self.surah_metadata)} surahs")
        return True
    
    def load_juz_data(self):
        """Load juz metadata - EXACTLY as app expects"""
        print("\n📖 Loading juz data...")
        
        # Juz names matching the app's Juz model
        self.juz_data = [
            # no, name_english, name_arabic
            (1, "Alif Lam Meem", "الم"),
            (2, "Sayaqool", "سيقول"),
            (3, "Tilkal Rusulu", "تلک الرسل"),
            (4, "Lan Tana Loo", "لن تنالوا"),
            (5, "Wal Mohsanatu", "والمحصنات"),
            (6, "La Yuhibbullah", "لا يحب الله"),
            (7, "Wa Iza Samiu", "وإذا سمعوا"),
            (8, "Wa Lau Annana", "ولو أننا"),
            (9, "Qalal Malao", "قال الملأ"),
            (10, "Wa'lamoo", "واعلموا"),
            (11, "Yatazeroon", "يعتذرون"),
            (12, "Wa Mamin Da'abat", "وممن دأبة"),
            (13, "Wa Ma Ubrioo", "وما أبرئ"),
            (14, "Rubama", "ربما"),
            (15, "Subhanallazi", "سبحان الذي"),
            (16, "Qal Alam", "قال ألم"),
            (17, "Aqtarabo", "اقترب"),
            (18, "Qadd Aflaha", "قد أفلح"),
            (19, "Wa Qalallazina", "وقال الذين"),
            (20, "A'man Khalaq", "أمن خلق"),
            (21, "Utlu Ma Oohi", "اتل ما أوحي"),
            (22, "Wa Manyaqnut", "ومن يقنت"),
            (23, "Wa Mali", "وما لي"),
            (24, "Faman Azlam", "فمن أظلم"),
            (25, "Elahe Yuruddo", "إليه يرد"),
            (26, "Ha'a Meem", "حم"),
            (27, "Qala Fama Khatbukum", "قال فما خطبكم"),
            (28, "Qadd Sami Allah", "قد سمع الله"),
            (29, "Tabarakallazi", "تبارك الذي"),
            (30, "Amma", "عم")
        ]
        
        print(f"✅ Loaded {len(self.juz_data)} juz data")
        return True
    
    def get_juz_boundaries(self):
        """Get juz boundaries for determining paraId"""
        # Juz boundaries (surah:verse_start to surah:verse_end)
        boundaries = [
            (1, 1, 2, 141),    # Juz 1
            (2, 142, 2, 252),  # Juz 2
            (2, 253, 3, 92),   # Juz 3
            (3, 93, 4, 23),    # Juz 4
            (4, 24, 4, 147),   # Juz 5
            (4, 148, 5, 81),   # Juz 6
            (5, 82, 6, 110),   # Juz 7
            (6, 111, 7, 87),   # Juz 8
            (7, 88, 8, 40),    # Juz 9
            (8, 41, 9, 92),    # Juz 10
            (9, 93, 11, 5),    # Juz 11
            (11, 6, 12, 52),   # Juz 12
            (12, 53, 14, 52),  # Juz 13
            (15, 1, 16, 128),  # Juz 14
            (17, 1, 18, 74),   # Juz 15
            (18, 75, 20, 135), # Juz 16
            (21, 1, 22, 78),   # Juz 17
            (23, 1, 25, 20),   # Juz 18
            (25, 21, 27, 55),  # Juz 19
            (27, 56, 29, 45),  # Juz 20
            (29, 46, 33, 30),  # Juz 21
            (33, 31, 36, 27),  # Juz 22
            (36, 28, 39, 31),  # Juz 23
            (39, 32, 41, 46),  # Juz 24
            (41, 47, 45, 37),  # Juz 25
            (46, 1, 51, 30),   # Juz 26
            (51, 31, 57, 29),  # Juz 27
            (58, 1, 66, 12),   # Juz 28
            (67, 1, 77, 50),   # Juz 29
            (78, 1, 114, 6)    # Juz 30
        ]
        return boundaries
    
    def get_juz_for_verse(self, surah, ayah):
        """Determine which juz a verse belongs to"""
        boundaries = self.get_juz_boundaries()
        
        for juz_no, (s_start, v_start, s_end, v_end) in enumerate(boundaries, 1):
            if surah == s_start and ayah >= v_start:
                if surah == s_end and ayah <= v_end:
                    return juz_no
                elif surah < s_end:
                    return juz_no
            elif surah > s_start and surah < s_end:
                return juz_no
            elif surah == s_end and ayah <= v_end:
                return juz_no
        
        return 1  # Default to juz 1
    
    def get_sajda_verses(self):
        """Return list of verses with sajdah (prostration)"""
        return [
            (7, 206), (13, 15), (16, 50), (17, 109), (19, 58),
            (22, 18), (22, 77), (25, 60), (27, 26), (32, 15),
            (38, 24), (41, 38), (53, 62), (84, 21), (96, 19)
        ]
    
    def calculate_ruku(self, surah, ayah):
        """Calculate ruku number (simplified algorithm)"""
        # This is a simplified calculation
        # In reality, each surah has specific ruku boundaries
        if surah == 1:
            return 1
        elif surah == 2:
            # Al-Baqarah has 40 rukus
            ruku_boundaries = [1, 26, 44, 60, 75, 92, 106, 124, 142, 158, 
                              177, 189, 204, 219, 235, 249, 260, 274, 286]
            for i, boundary in enumerate(ruku_boundaries):
                if ayah <= boundary:
                    return i + 1
            return 40
        else:
            # Generic calculation for other surahs
            return (ayah - 1) // 10 + 1
    
    def get_manzil(self, para_id):
        """Get manzil number based on para_id"""
        # Manzil divisions (7 manzils)
        if para_id <= 4:
            return 1
        elif para_id <= 8:
            return 2
        elif para_id <= 12:
            return 3
        elif para_id <= 16:
            return 4
        elif para_id <= 20:
            return 5
        elif para_id <= 24:
            return 6
        else:
            return 7
    
    def create_sqlite_database(self):
        """Create the complete SQLite database matching app schema"""
        print("\n" + "=" * 60)
        print("CREATING SQLITE DATABASE FOR SIRATE MUSTAQEEM")
        print("=" * 60)
        
        # Output file - use exact name expected by app
        output_db = "siratemustaqeem-db.db"
        
        # Remove existing file
        if Path(output_db).exists():
            Path(output_db).unlink()
        
        # Connect to SQLite
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        
        # Create all tables EXACTLY as app expects
        print("\n📊 Creating tables...")
        
        # 1. Quran table - MUST MATCH APP SCHEMA
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
        
        # 2. Surah table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS surah (
            id INTEGER PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            ayats INTEGER NOT NULL,
            place TEXT NOT NULL
        )
        ''')
        
        # 3. Juz table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS juz (
            no INTEGER PRIMARY KEY,
            name_english TEXT NOT NULL,
            name_arabic TEXT NOT NULL
        )
        ''')
        
        # 4. Dua table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dua (
            id INTEGER PRIMARY KEY,
            surah TEXT NOT NULL,
            aya_number INTEGER NOT NULL,
            aya TEXT NOT NULL,
            favorite INTEGER DEFAULT 0
        )
        ''')
        
        # 5. Tasbih table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasbih (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            counter INTEGER NOT NULL,
            favorite INTEGER DEFAULT 0
        )
        ''')
        
        # 6. Allah Names table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS allah_names (
            arabic TEXT NOT NULL,
            english TEXT NOT NULL,
            urduMeaning TEXT NOT NULL,
            englishMeaning TEXT NOT NULL,
            englishExplanation TEXT NOT NULL
        )
        ''')
        
        print("✅ Tables created with exact schema")
        
        # Insert Quran data
        print("\n📝 Inserting Quran verses...")
        
        sajda_verses = self.get_sajda_verses()
        total_verses = len(self.arabic_verses)
        inserted = 0
        
        for verse in self.arabic_verses:
            surah = verse['surah']
            ayah = verse['ayah']
            arabic_text = verse['arabic']
            
            # Get Urdu translation
            urdu_key = f"{surah}:{ayah}"
            urdu_text = self.urdu_translations.get(urdu_key, 
                f"سورہ {surah} کی آیت {ayah} کا ترجمہ یہاں درج کیا جائے گا۔")
            
            # Get Arabic without diacritics
            simple_key = f"{surah}:{ayah}"
            without_aerab = self.arabic_simple.get(simple_key, arabic_text)
            
            # Determine juz (paraId)
            para_id = self.get_juz_for_verse(surah, ayah)
            
            # Check if sajda verse
            has_sajda = 1 if (surah, ayah) in sajda_verses else 0
            
            # Calculate ruku
            surah_ruku = self.calculate_ruku(surah, ayah)
            
            # Calculate manzil
            manzil_no = self.get_manzil(para_id)
            
            # Insert into database
            # Note: Using verse['id'] as ayatId to ensure uniqueness
            ayat_id = verse['id'] if verse['id'] > 0 else (surah * 1000 + ayah)
            
            cursor.execute('''
            INSERT INTO quran VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ayat_id,          # ayatId - must be unique
                ayah,             # ayatNumber
                arabic_text,      # arabicText
                urdu_text,        # urduTranslation
                has_sajda,        # ayatSajda
                surah_ruku,       # surahRuku
                surah_ruku,       # paraRuku (simplified)
                para_id,          # paraId
                manzil_no,        # manzilNo
                1,                # ayatVisible
                surah,            # surahId
                without_aerab,    # withoutAerab
                0                 # favourite (British spelling as in app)
            ))
            
            inserted += 1
            if inserted % 500 == 0:
                print(f"  Processed {inserted}/{total_verses} verses...")
        
        print(f"✅ Inserted {inserted} Quran verses")
        
        # Insert surah metadata
        print("\n📝 Inserting surah metadata...")
        cursor.executemany('INSERT INTO surah VALUES (?, ?, ?, ?, ?)', self.surah_metadata)
        print(f"✅ Inserted {len(self.surah_metadata)} surahs")
        
        # Insert juz names
        print("📝 Inserting juz names...")
        juz_names = [(no, eng, ar) for no, eng, ar in self.juz_data]
        cursor.executemany('INSERT INTO juz VALUES (?, ?, ?)', juz_names)
        print(f"✅ Inserted {len(juz_names)} juz")
        
        # Insert sample duas (matching app's Dua model)
        print("📝 Inserting sample duas...")
        sample_duas = [
            (1, "الفاتحة", 1, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", 0),
            (2, "الفاتحة", 2, "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", 0),
            (3, "الفاتحة", 3, "الرَّحْمَٰنِ الرَّحِيمِ", 0),
            (4, "الفاتحة", 4, "مَالِكِ يَوْمِ الدِّينِ", 1),
            (5, "الفاتحة", 5, "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", 1),
            (6, "الفاتحة", 6, "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ", 0),
            (7, "الفاتحة", 7, "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ", 0),
            (8, "البقرة", 255, "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...", 1),  # Ayatul Kursi
        ]
        cursor.executemany('INSERT INTO dua VALUES (?, ?, ?, ?, ?)', sample_duas)
        print(f"✅ Inserted {len(sample_duas)} duas")
        
        # Insert tasbih (matching app's Tasbih model)
        print("📝 Inserting tasbih...")
        tasbihs = [
            (1, "Subhanallah", 33, 1),
            (2, "Alhamdulillah", 33, 1),
            (3, "Allahu Akbar", 34, 1),
            (4, "La ilaha illallah", 100, 0),
            (5, "Astaghfirullah", 100, 0),
            (6, "Custom Tasbih", 50, 0),
            (7, "Morning Remembrance", 100, 1),
        ]
        cursor.executemany('INSERT INTO tasbih VALUES (?, ?, ?, ?)', tasbihs)
        print(f"✅ Inserted {len(tasbihs)} tasbih")
        
        # Insert Allah names (99 names)
        print("📝 Inserting Allah names...")
        allah_names = self.get_allah_names()
        cursor.executemany('INSERT INTO allah_names VALUES (?, ?, ?, ?, ?)', allah_names)
        print(f"✅ Inserted {len(allah_names)} Allah names")
        
        # Create indexes for performance
        print("\n⚡ Creating indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quran_surah ON quran(surahId)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quran_juz ON quran(paraId)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quran_favorite ON quran(favourite)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dua_favorite ON dua(favorite)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasbih_favorite ON tasbih(favorite)')
        print("✅ Indexes created")
        
        # Commit and close
        conn.commit()
        
        # Verify data
        print("\n🔍 Verifying database...")
        tables = ['quran', 'surah', 'juz', 'dua', 'tasbih', 'allah_names']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")
        
        # Get sample data
        cursor.execute("SELECT arabicText, urduTranslation FROM quran WHERE surahId = 1 AND ayatNumber = 1")
        sample = cursor.fetchone()
        
        cursor.execute("SELECT name_en, name_ar FROM surah WHERE id = 1")
        surah_sample = cursor.fetchone()
        
        conn.close()
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ DATABASE CREATION COMPLETE")
        print("=" * 60)
        
        file_size = Path(output_db).stat().st_size / (1024 * 1024)
        print(f"\n📁 Output file: {output_db}")
        print(f"📦 File size: {file_size:.2f} MB")
        print(f"⏰ Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📊 SAMPLE DATA:")
        if sample:
            print(f"   Quran 1:1 - Arabic: {sample[0][:30]}...")
            print(f"   Quran 1:1 - Urdu: {sample[1][:30]}...")
        if surah_sample:
            print(f"   Surah 1: {surah_sample[0]} / {surah_sample[1]}")
        
        return output_db
    
    def get_allah_names(self):
        """Get 99 names of Allah"""
        return [
            ("الرَّحْمَنُ", "Ar-Rahman", "نہایت مہربان", "The Beneficent", "The Most Gracious"),
            ("الرَّحِيمُ", "Ar-Rahim", "نہایت رحم کرنے والا", "The Merciful", "The Most Merciful"),
            ("الْمَلِكُ", "Al-Malik", "بادشاہ", "The King", "The Sovereign Lord"),
            ("الْقُدُّوسُ", "Al-Quddus", "نہایت پاک", "The Holy", "The Most Holy"),
            ("السَّلاَمُ", "As-Salam", "سلامتی دینے والا", "The Source of Peace", "The Source of Peace"),
            ("الْمُؤْمِنُ", "Al-Mu'min", "امن دینے والا", "The Guardian of Faith", "The Inspirer of Faith"),
            ("الْمُهَيْمِنُ", "Al-Muhaymin", "نگہبان", "The Protector", "The Preserver of Safety"),
            ("الْعَزِيزُ", "Al-Aziz", "غالب", "The Mighty", "The Almighty"),
            ("الْجَبَّارُ", "Al-Jabbar", "زبردست", "The Compeller", "The Irresistible"),
            ("الْمُتَكَبِّرُ", "Al-Mutakabbir", "بڑائی والا", "The Majestic", "The Supreme"),
            ("الْخَالِقُ", "Al-Khaliq", "خالق", "The Creator", "The Creator"),
            ("الْبَارِئُ", "Al-Bari", "پیدا کرنے والا", "The Evolver", "The Maker"),
            ("الْمُصَوِّرُ", "Al-Musawwir", "صورت گر", "The Fashioner", "The Shaper"),
            ("الْغَفَّارُ", "Al-Ghaffar", "بہت بخشنے والا", "The Forgiver", "The Repeatedly Forgiving"),
            ("الْقَهَّارُ", "Al-Qahhar", "قہار", "The Subduer", "The All-Compelling Subduer"),
            ("الْوَهَّابُ", "Al-Wahhab", "بہت عطا کرنے والا", "The Bestower", "The Bestower of Gifts"),
            ("الرَّزَّاقُ", "Ar-Razzaq", "رزق دینے والا", "The Provider", "The Provider"),
            ("الْفَتَّاحُ", "Al-Fattah", "کھولنے والا", "The Opener", "The Opener of the Gates of Profits"),
            ("اَلْعَلِيْمُ", "Al-Alim", "جاننے والا", "The Knower", "The All-Knowing"),
            ("الْقَابِضُ", "Al-Qabid", "تنگ کرنے والا", "The Constrictor", "The Withholder"),
            ("الْبَاسِطُ", "Al-Basit", "کشادگی دینے والا", "The Expander", "The Expander"),
            ("الْخَافِضُ", "Al-Khafid", "ذلیل کرنے والا", "The Abaser", "The Reducer"),
            ("الرَّافِعُ", "Ar-Rafi", "بلند کرنے والا", "The Exalter", "The Elevator"),
            ("الْمُعِزُّ", "Al-Mu'izz", "عزت دینے والا", "The Honorer", "The Honorer"),
            ("المُذِلُّ", "Al-Muzill", "ذلت دینے والا", "The Dishonorer", "The Humiliator"),
            ("السَّمِيعُ", "As-Sami", "سننے والا", "The Hearer", "The All-Hearing"),
            ("الْبَصِيرُ", "Al-Basir", "دیکھنے والا", "The Seer", "The All-Seeing"),
            ("الْحَكَمُ", "Al-Hakam", "فیصلہ کرنے والا", "The Judge", "The Judge"),
            ("الْعَدْلُ", "Al-Adl", "انصاف کرنے والا", "The Just", "The Just"),
            ("اللَّطِيفُ", "Al-Latif", "لطیف", "The Kind", "The Subtle One"),
            ("الْخَبِيرُ", "Al-Khabir", "خبر رکھنے والا", "The Aware", "The All-Aware"),
            ("الْحَلِيمُ", "Al-Halim", "حلیم", "The Forbearing", "The Forbearing"),
            ("الْعَظِيمُ", "Al-Azim", "عظیم", "The Great", "The Magnificent"),
            ("الْغَفُورُ", "Al-Ghafur", "بہت بخشنے والا", "The Forgiving", "The Forgiver and Hider of Faults"),
            ("الشَّكُورُ", "Ash-Shakur", "شکر گزار", "The Appreciative", "The Rewarder of Thankfulness"),
            ("الْعَلِيُّ", "Al-Ali", "بلند", "The High", "The Sublime"),
            ("الْكَبِيرُ", "Al-Kabir", "بڑا", "The Great", "The Great"),
            ("الْحَفِيظُ", "Al-Hafiz", "حفاظت کرنے والا", "The Guardian", "The Preserver"),
            ("المُقيِت", "Al-Muqit", "کفالت کرنے والا", "The Sustainer", "The Nourisher"),
            ("الْحَسِيبُ", "Al-Hasib", "حساب لینے والا", "The Reckoner", "The Bringer of Judgment"),
            ("الْجَلِيلُ", "Al-Jalil", "جلیل", "The Majestic", "The Majestic"),
            ("الْكَرِيمُ", "Al-Karim", "کریم", "The Generous", "The Bountiful, The Generous"),
            ("الرَّقِيبُ", "Ar-Raqib", "نگران", "The Watchful", "The Watchful"),
            ("الْمُجِيبُ", "Al-Mujib", "قبول کرنے والا", "The Responsive", "The Responsive, The Answerer"),
            ("الْوَاسِعُ", "Al-Wasi", "وسیع", "The Vast", "The Vast, The All-Embracing"),
            ("الْحَكِيمُ", "Al-Hakim", "حکیم", "The Wise", "The Wise"),
            ("الْوَدُودُ", "Al-Wadud", "محبت کرنے والا", "The Loving", "The Loving"),
            ("الْمَجِيدُ", "Al-Majid", "ماجد", "The Glorious", "The Majestic"),
            ("الْبَاعِثُ", "Al-Ba'ith", "زندہ کرنے والا", "The Resurrector", "The Resurrector"),
            ("الشَّهِيدُ", "Ash-Shahid", "گواہ", "The Witness", "The Witness"),
            ("الْحَقُّ", "Al-Haqq", "حق", "The Truth", "The Truth"),
            ("الْوَكِيلُ", "Al-Wakil", "کارساز", "The Trustee", "The Trustee"),
            ("الْقَوِيُّ", "Al-Qawiyy", "قوی", "The Strong", "The Strong"),
            ("الْمَتِينُ", "Al-Matin", "مضبوط", "The Firm", "The Firm, The Steadfast"),
            ("الْوَلِيُّ", "Al-Waliyy", "ولی", "The Protector", "The Protecting Friend, Patron, and Helper"),
            ("الْحَمِيدُ", "Al-Hamid", "حمید", "The Praiseworthy", "The Praiseworthy"),
            ("الْمُحْصِي", "Al-Muhsi", "شمار کرنے والا", "The Accounter", "The Accounter, The Numberer of All"),
            ("الْمُبْدِئُ", "Al-Mubdi", "پیدا کرنے والا", "The Originator", "The Originator"),
            ("الْمُعِيدُ", "Al-Mu'id", "لوٹانے والا", "The Restorer", "The Restorer, The Reinstater"),
            ("الْمُحْيِي", "Al-Muhyi", "زندہ کرنے والا", "The Giver of Life", "The Giver of Life"),
            ("اَلْمُمِيتُ", "Al-Mumit", "موت دینے والا", "The Taker of Life", "The Taker of Life"),
            ("الْحَيُّ", "Al-Hayy", "زندہ", "The Living", "The Alive"),
            ("الْقَيُّومُ", "Al-Qayyum", "قائم رہنے والا", "The Sustainer", "The Self-Subsisting"),
            ("الْوَاجِدُ", "Al-Wajid", "پانے والا", "The Finder", "The Perceiver"),
            ("الْمَاجِدُ", "Al-Majid", "ماجد", "The Noble", "The Illustrious, The Magnificent"),
            ("الْوَاحِدُ", "Al-Wahid", "اکیل", "The One", "The One, The Unique"),
            ("اَلاَحَدُ", "Al-Ahad", "احد", "The Only One", "The One, The Indivisible"),
            ("الصَّمَدُ", "As-Samad", "بے نیاز", "The Eternal", "The Eternal, The Absolute"),
            ("الْقَادِرُ", "Al-Qadir", "قادر", "The Able", "The Able"),
            ("الْمُقْتَدِرُ", "Al-Muqtadir", "قدرت والا", "The Powerful", "The Powerful"),
            ("الْمُقَدِّمُ", "Al-Muqaddim", "آگے کرنے والا", "The Expediter", "The Expediter"),
            ("الْمُؤَخِّرُ", "Al-Mu'akhkhir", "پیچھے کرنے والا", "The Delayer", "The Delayer"),
            ("الأوَّلُ", "Al-Awwal", "اول", "The First", "The First"),
            ("الآخِرُ", "Al-Akhir", "آخر", "The Last", "The Last"),
            ("الظَّاهِرُ", "Az-Zahir", "ظاہر", "The Manifest", "The Manifest, The Evident"),
            ("الْبَاطِنُ", "Al-Batin", "پوشیدہ", "The Hidden", "The Hidden, The Unmanifest"),
            ("الْوَالِي", "Al-Wali", "والی", "The Governor", "The Governor, The Patron"),
            ("الْمُتَعَالِي", "Al-Muta'ali", "بلند", "The Exalted", "The Exalted, The Most High"),
            ("الْبَرُّ", "Al-Barr", "بھلائی کرنے والا", "The Source of Goodness", "The Good"),
            ("التَّوَّابُ", "At-Tawwab", "توبہ قبول کرنے والا", "The Acceptor of Repentance", "The Acceptor of Repentance"),
            ("الْمُنْتَقِمُ", "Al-Muntaqim", "انتقام لینے والا", "The Avenger", "The Avenger"),
            ("العَفُوُّ", "Al-Afuww", "معاف کرنے والا", "The Pardoner", "The Pardoner"),
            ("الرَّؤُوفُ", "Ar-Ra'uf", "رحم کرنے والا", "The Compassionate", "The Compassionate"),
            ("مَالِكُ الْمُلْكِ", "Malikul-Mulk", "بادشاہی کا مالک", "The Owner of Sovereignty", "The Owner of Sovereignty"),
            ("ذُو الْجَلَالِ وَالْإِكْرَامِ", "Dhu-al-Jalali-wal-Ikram", "جلال اور اکرام والا", "Lord of Majesty and Bounty", "The Lord of Majesty and Generosity"),
            ("الْمُقْسِطُ", "Al-Muqsit", "انصاف کرنے والا", "The Equitable", "The Equitable"),
            ("الْجَامِعُ", "Al-Jami", "جمع کرنے والا", "The Gatherer", "The Gatherer"),
            ("الْغَنِيُّ", "Al-Ghaniyy", "غنی", "The Rich", "The Rich, The Independent"),
            ("الْمُغْنِي", "Al-Mughni", "غنی کرنے والا", "The Enricher", "The Enricher"),
            ("اَلْمَانِعُ", "Al-Mani", "روکنے والا", "The Preventer", "The Preventer"),
            ("الضَّارُّ", "Ad-Darr", "نقصان پہنچانے والا", "The Harmer", "The Distresser"),
            ("النَّافِعُ", "An-Nafi", "نفع پہنچانے والا", "The Benefiter", "The Propitious"),
            ("النُّورُ", "An-Nur", "نور", "The Light", "The Light"),
            ("الْهَادِي", "Al-Hadi", "ہدایت دینے والا", "The Guide", "The Guide"),
            ("الْبَدِيعُ", "Al-Badi", "بے مثال", "The Incomparable", "The Incomparable"),
            ("الْبَاقِي", "Al-Baqi", "ہمیشہ رہنے والا", "The Everlasting", "The Everlasting"),
            ("الْوَارِثُ", "Al-Warith", "وارث", "The Inheritor", "The Inheritor"),
            ("الرَّشِيدُ", "Ar-Rashid", "رہنما", "The Guide", "The Guide to the Right Path"),
            ("الصَّبُورُ", "As-Sabur", "صبر کرنے والا", "The Patient", "The Patient")
        ]
    
    def export_schema(self):
        """Export the exact database schema for documentation"""
        schema_file = "database_schema_exact.sql"
        
        schema = """-- Sirate Mustaqeem Database Schema - EXACT MATCH TO APP
-- Generated: {timestamp}

-- Quran table (EXACT field names from app)
CREATE TABLE quran (
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
    favourite INTEGER DEFAULT 0  -- NOTE: British spelling 'favourite' not 'favorite'
);

-- Surah table (EXACT field names from app)
CREATE TABLE surah (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    ayats INTEGER NOT NULL,
    place TEXT NOT NULL
);

-- Juz table (EXACT field names from app)
CREATE TABLE juz (
    no INTEGER PRIMARY KEY,
    name_english TEXT NOT NULL,
    name_arabic TEXT NOT NULL
);

-- Dua table (EXACT field names from app)
CREATE TABLE dua (
    id INTEGER PRIMARY KEY,
    surah TEXT NOT NULL,
    aya_number INTEGER NOT NULL,
    aya TEXT NOT NULL,
    favorite INTEGER DEFAULT 0
);

-- Tasbih table (EXACT field names from app)
CREATE TABLE tasbih (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    counter INTEGER NOT NULL,
    favorite INTEGER DEFAULT 0
);

-- Allah Names table (EXACT field names from app)
CREATE TABLE allah_names (
    arabic TEXT NOT NULL,
    english TEXT NOT NULL,
    urduMeaning TEXT NOT NULL,
    englishMeaning TEXT NOT NULL,
    englishExplanation TEXT NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_quran_surah ON quran(surahId);
CREATE INDEX idx_quran_juz ON quran(paraId);
CREATE INDEX idx_quran_favorite ON quran(favourite);
CREATE INDEX idx_dua_favorite ON dua(favorite);
CREATE INDEX idx_tasbih_favorite ON tasbih(favorite);
        """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write(schema)
        
        print(f"✅ Exact schema exported to {schema_file}")
        return schema_file
    
    def run(self):
        """Run the complete conversion process"""
        print("=" * 60)
        print("SIRATE MUSTAQEEM DATABASE CONVERTER")
        print("EXACT MATCH TO FLUTTER APP SCHEMA")
        print("=" * 60)
        
        # Step 1: Validate input
        if not self.validate_input():
            return
        
        # Step 2: Download required data
        print("\n📥 Checking for required data files...")
        if not Path("data").exists():
            Path("data").mkdir(exist_ok=True)
        
        # Step 3: Parse Arabic SQL
        if not self.parse_arabic_sql():
            print("❌ Failed to parse Arabic SQL file")
            return
        
        # Step 4: Parse Urdu translation
        self.parse_urdu_translation()
        
        # Step 5: Parse Arabic without diacritics
        self.parse_arabic_simple()
        
        # Step 6: Load metadata
        self.load_surah_metadata()
        self.load_juz_data()
        
        # Step 7: Create SQLite database
        db_file = self.create_sqlite_database()
        
        # Step 8: Export schema
        self.export_schema()
        
        print("\n" + "=" * 60)
        print("🎉 CONVERSION COMPLETE!")
        print("=" * 60)
        
        print(f"\n📱 To use in Flutter app:")
        print(f"1. Copy the database file to your Flutter project:")
        print(f"   cp {db_file} /path/to/your/flutter/project/assets/")
        print(f"\n2. Make sure the file is named exactly: siratemustaqeem-db.db")
        print(f"\n3. Add to pubspec.yaml:")
        print("""
  assets:
    - assets/siratemustaqeem-db.db
        """)
        
        print(f"\n4. The app will automatically:")
        print(f"   - Check if database exists at: databases/siratemustaqeem-db.db")
        print(f"   - Download from URL if not found")
        print(f"   - Initialize all data from the database")
        
        return db_file

def main():
    # Check for SQL file
    import glob
    
    print("🔍 Looking for Quran SQL files...")
    
    # Look for SQL files in common locations
    search_patterns = [
        "*.sql",
        "DB/*.sql",
        "database/*.sql",
        "quran/*.sql",
        "data/*.sql"
    ]
    
    sql_files = []
    for pattern in search_patterns:
        sql_files.extend(glob.glob(pattern))
    
    # Remove duplicates
    sql_files = list(set(sql_files))
    
    if not sql_files:
        print("❌ No SQL files found.")
        print("\n💡 Please:")
        print("   1. Place your Quran SQL file in the current directory")
        print("   2. Or in a DB/ subdirectory")
        print("   3. Common names: quran.sql, quran-simple.sql, quran_uthmani.sql")
        return
    
    print(f"\nFound {len(sql_files)} SQL file(s):")
    for i, file in enumerate(sql_files, 1):
        size = Path(file).stat().st_size / 1024
        print(f"  {i}. {file} ({size:.1f} KB)")
    
    if len(sql_files) == 1:
        sql_file = sql_files[0]
        print(f"\n✅ Using: {sql_file}")
    else:
        choice = input(f"\nSelect file (1-{len(sql_files)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(sql_files):
            sql_file = sql_files[int(choice) - 1]
        else:
            sql_file = sql_files[0]
            print(f"\n⚠️ Using default: {sql_file}")
    
    # Run converter
    print(f"\n🚀 Starting conversion with: {sql_file}")
    converter = QuranDatabaseConverter(sql_file)
    
    try:
        converter.run()
    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        print("💡 Troubleshooting tips:")
        print("   - Make sure the SQL file contains Quran verses")
        print("   - Check file encoding (should be UTF-8)")
        print("   - The file should have INSERT statements for Quran verses")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()