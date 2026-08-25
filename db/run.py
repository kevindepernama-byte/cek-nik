import json
from pathlib import Path

BASE = Path(__file__).parent
FILES = sorted(BASE.glob("*.json"))


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return None


def get_records(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        records = []

        # Contoh: {"Eligible": [...]}
        for value in data.values():
            if isinstance(value, list):
                records.extend(value)

        return records

    return []


def value_matches(value, keyword):
    if value is None:
        return False

    if isinstance(value, (dict, list)):
        return False

    return str(value).strip().lower() == keyword.strip().lower()


def search_record(record, keyword):
    if isinstance(record, dict):

        for key, value in record.items():

            # Dukcapil-style:
            # {"_source": {...}}
            if isinstance(value, dict):
                if search_record(value, keyword):
                    return True

            elif isinstance(value, list):
                for item in value:
                    if search_record(item, keyword):
                        return True

            elif value_matches(value, keyword):
                return True

    elif isinstance(record, list):

        for item in record:
            if search_record(item, keyword):
                return True

    else:
        return value_matches(record, keyword)

    return False


def search_database(path, keyword):
    data = load_json(path)

    if data is None:
        return []

    records = get_records(data)
    hasil = []

    for record in records:
        if search_record(record, keyword):
            hasil.append(record)

    return hasil


def print_value(value, indent=4):
    prefix = " " * indent

    if isinstance(value, dict):
        for key, val in value.items():
            if isinstance(val, (dict, list)):
                print(f"{prefix}{key}:")
                print_value(val, indent + 4)
            else:
                print(f"{prefix}{key}: {val}")

    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                print_value(item, indent + 4)
            else:
                print(f"{prefix}- {item}")

    else:
        print(f"{prefix}{value}")


def tampilkan(nama, hasil):
    print("\n" + "=" * 65)
    print(f"[ {nama} ]")
    print("=" * 65)

    if not hasil:
        print("✗ Tidak ditemukan")
        return 0

    print(f"✓ Ditemukan {len(hasil)} record")

    for nomor, record in enumerate(hasil, 1):
        print(f"\n--- Record {nomor} ---")

        if isinstance(record, dict):
            print_value(record)
        else:
            print(f"    {record}")

    return len(hasil)


def tampilkan_menu():
    print("\n" + "=" * 65)
    print("                         CEK DATA")
    print("=" * 65)

    print("1. Cek SEMUA database")

    for nomor, file in enumerate(FILES, 2):
        print(f"{nomor}. {file.name}")

    print("0. Keluar")
    print("=" * 65)


def main():

    if not FILES:
        print("Tidak ada file JSON di:")
        print(BASE)
        return

    print(f"\n✓ Ditemukan {len(FILES)} file JSON")

    while True:

        tampilkan_menu()

        pilihan = input("Pilih metode: ").strip()

        if pilihan == "0":
            print("Keluar.")
            break

        if not pilihan.isdigit():
            print("✗ Pilihan tidak valid.")
            continue

        pilihan = int(pilihan)

        # ==========================
        # SEMUA DATABASE
        # ==========================

        if pilihan == 1:

            keyword = input(
                "\nMasukkan identifier: "
            ).strip()

            if not keyword:
                print("✗ Identifier kosong.")
                continue

            print("\n")
            print("#" * 65)
            print("                    HASIL SEMUA DATABASE")
            print("#" * 65)

            total = 0

            for file in FILES:

                print(f"\nMemeriksa {file.name}...")

                hasil = search_database(
                    file,
                    keyword
                )

                total += tampilkan(
                    file.name,
                    hasil
                )

            print("\n" + "#" * 65)
            print(f"TOTAL RECORD DITEMUKAN: {total}")
            print("#" * 65)

        # ==========================
        # DATABASE TERTENTU
        # ==========================

        elif 2 <= pilihan <= len(FILES) + 1:

            file = FILES[pilihan - 2]

            print(f"\nDatabase:")
            print(file.name)

            keyword = input(
                "Masukkan identifier: "
            ).strip()

            if not keyword:
                print("✗ Identifier kosong.")
                continue

            hasil = search_database(
                file,
                keyword
            )

            tampilkan(
                file.name,
                hasil
            )

        else:
            print("✗ Pilihan tidak tersedia.")


if __name__ == "__main__":
    main()
