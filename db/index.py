import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
SOURCE = BASE / "source"
DB = BASE / "db"

FILES = {
    "db_dukcapil": "db_dukcapil.json",
    "db_bpjs": "db_bpjs.json",
    "db_nikindo": "db_nikindo.json",
    "db_nomor": "db_nomor.json",
    "db_npwp": "db_npwp.json",
    "db_pln": "db_pln.json",
    "db_slot": "db_slot.json",
    "db_bansos": "Calon Penerima Bansos kecamatan kerek1.json",
    "db_pendaftar": "data-pendaftar_0d5fae71d3a74c67c879e3b4a0577e5bmemek.json",
    "db_seleksi": "data-seleksi_1be9ca842a05cd1ba202c45265b54983.json",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def convert(name, filename):
    source = SOURCE / filename
    output = DB / f"{name}.sqlite"

    if not source.exists():
        print(f"[SKIP] {source.name}")
        return

    print(f"\n[{name}]")
    print(f"Source : {source.name}")

    data = load_json(source)

    conn = sqlite3.connect(output)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS records")

    cur.execute("""
        CREATE TABLE records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL
        )
    """)

    if isinstance(data, list):
        records = data

    elif isinstance(data, dict):
        records = []

        for value in data.values():
            if isinstance(value, list):
                records.extend(value)

    else:
        records = [data]

    count = 0

    for record in records:
        cur.execute(
            "INSERT INTO records (data) VALUES (?)",
            (json.dumps(record, ensure_ascii=False),)
        )

        count += 1

        if count % 10000 == 0:
            print(f"  imported: {count}")

    conn.commit()
    conn.close()

    print(f"✓ Selesai: {count} record")
    print(f"✓ Output: {output.name}")


def main():
    DB.mkdir(exist_ok=True)

    print("=" * 55)
    print("          JSON → SQLITE INDEXER")
    print("=" * 55)

    for name, filename in FILES.items():
        convert(name, filename)

    print("\nSemua selesai.")


if __name__ == "__main__":
    main()
