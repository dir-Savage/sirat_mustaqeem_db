-- Sirate Mustaqeem Database Schema - EXACT MATCH TO APP
-- Generated: 2025-12-26 14:45:42

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
        