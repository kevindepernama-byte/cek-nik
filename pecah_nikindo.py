import sqlite3, os

source_db = "db/nikindo.db"
table_name = "nikindo"
max_rows_per_file = 500000

if not os.path.exists(source_db):
    print(f"File {source_db} tidak ditemukan!")
    exit()

print(f"Membaca {source_db}...")
conn = sqlite3.connect(source_db)
cursor = conn.cursor()

cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
create_table_sql = cursor.fetchone()
if not create_table_sql:
    print(f"Tabel '{table_name}' tidak ditemukan!")
    conn.close()
    exit()

create_table_sql = create_table_sql[0]

cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
total_rows = cursor.fetchone()[0]
print(f"Total data: {total_rows} baris.")

offset = 0
part = 1

while offset < total_rows:
    # Langsung disimpan di dalam folder db/
    target_db = f"db/nikindo{part}.db"
    print(f"Membuat {target_db}...")
    
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()
    target_cursor.execute(create_table_sql)

    cursor.execute(f"SELECT * FROM {table_name} LIMIT {max_rows_per_file} OFFSET {offset}")
    rows = cursor.fetchall()

    if rows:
        placeholders = ",".join(["?"] * len(rows[0]))
        target_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
        target_conn.commit()

    target_conn.close()
    offset += max_rows_per_file
    part += 1

conn.close()
print("\nSelesai! File nikindo berhasil dipecah langsung di folder db/")
