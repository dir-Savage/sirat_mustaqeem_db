import sqlite3
import os

db_path = 'new.db'

if not os.path.exists(db_path):
    print(f"خطأ: الملف '{db_path}' مش موجود. تأكد من الاسم والمسار.")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== SCHEMA لقاعدة البيانات ===\n")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = cursor.fetchall()

if not tables:
    print("مش لاقي جداول في الـ DB!")
else:
    for table in tables:
        table_name = table[0]
        print(f"-- جدول: {table_name}")
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        create_sql = f"CREATE TABLE {table_name} (\n"
        column_defs = []
        for col in columns:
            cid, name, col_type, notnull, dflt_value, pk = col
            col_def = f"    {name} {col_type}"
            if pk:
                col_def += " PRIMARY KEY"
            if notnull:
                col_def += " NOT NULL"
            if dflt_value is not None:
                col_def += f" DEFAULT {dflt_value}"
            column_defs.append(col_def)
        
        create_sql += ",\n".join(column_defs)
        create_sql += "\n);"
        
        print(create_sql + "\n")

    print("-- الـ Indexes (إن وجدت)")
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL;")
    indexes = cursor.fetchall()
    if indexes:
        for idx in indexes:
            print(f"-- Index: {idx[0]} على جدول {idx[1]}")
            print(idx[2] + ";\n")
    else:
        print("مش لاقي Indexes.\n")

conn.close()
print("تم استخراج الـ schema بنجاح!")