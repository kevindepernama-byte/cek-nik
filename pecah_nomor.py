import sqlite3, os

source_db = "db/nomor.db"
table_name = "nomor"
max_rows_per_file = 500000

if not os.path.exists(source_db):
    print(f"File {source_db} tidak ditemukan!")
    exit()

print(f"Membaca {source_db}...")

try:
    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    result = cursor.fetchone()

    if not result:
        print(f"Tabel '{table_name}' tidak ditemukan!")
        conn.close()
        exit()

    create_table_sql = result[0]

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        print(f"Total data: {total_rows} baris.")
    except sqlite3.DatabaseError as e:
        print(f"COUNT gagal karena database corrupt: {e}")
        print("Tetap mencoba membaca data...")

    offset = 0
    part = 1

    while True:
        target_db = f"db/nomor{part}.db"
        print(f"\nMembuat {target_db}...")

        target_conn = sqlite3.connect(target_db)
        target_cursor = target_conn.cursor()
        target_cursor.execute(create_table_sql)

        copied = 0
        skipped = 0

        try:
            cursor.execute(
                f"SELECT * FROM {table_name} "
                f"LIMIT {max_rows_per_file} OFFSET {offset}"
            )

            while copied < max_rows_per_file:
                try:
                    row = cursor.fetchone()
                except sqlite3.DatabaseError as e:
                    print(f"  Baris corrupt dilewati: {e}")
                    skipped += 1
                    continue

                if row is None:
                    break

                try:
                    placeholders = ",".join(["?"] * len(row))
                    target_cursor.execute(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        row
                    )
                    copied += 1
                except sqlite3.DatabaseError as e:
                    print(f"  Data corrupt dilewati: {e}")
                    skipped += 1

        except sqlite3.DatabaseError as e:
            print(f"  Bagian corrupt dilewati: {e}")

        target_conn.commit()
        target_conn.close()

        print(f"  Berhasil: {copied} baris")
        print(f"  Dilewati: {skipped} baris")

        if copied == 0:
            print("\nTidak ada data lagi. Selesai.")
            break

        offset += max_rows_per_file
        part += 1

    conn.close()

except Exception as e:
    print(f"\nError: {e}")

print("\nSelesai! Data yang bisa dibaca sudah dipecah ke folder db/")
