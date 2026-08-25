from flask import Flask, render_template, request
import os
import re
import glob
import sqlite3
import zipfile

app = Flask(__name__)

# --- KEAMANAN: AUTO-EXTRACT DATABASE DARI ZIP ---
ZIP_FILE = "db_aman.zip"
PASSWORD = "PasswordRahasiaKamu123"  # Sesuaikan password zip Anda
DB_DIR = "db"

def siapkan_database_aman():
    if not os.path.exists(DB_DIR) or not os.path.exists(os.path.join(DB_DIR, "dukcapil.db")):
        if os.path.exists(ZIP_FILE):
            print("[*] Mengekstrak database aman untuk web...")
            os.makedirs(DB_DIR, exist_ok=True)
            try:
                with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
                    zf.extractall(path=".", pwd=PASSWORD.encode('utf-8'))
                print("[+] Database berhasil dibuka.")
            except Exception as e:
                print(f"[-] Gagal ekstrak database: {e}")

siapkan_database_aman()

def bersihkan_angka(teks):
    return re.sub(r'\D', '', teks)

DATABASE_CONFIG = {
    "1": {
        "label": "DUKCAPIL",
        "files": ["db/dukcapil.db"],
        "table": "siswa",
    },
    "2": {
        "label": "BPJS",
        "files": ["db/bpjs.db"],
        "table": "bpjs",
    },
    "3": {
        "label": "NOMOR / NIKINDO",
        "files": glob.glob("db/nikindo*.db") + glob.glob("db/nomor*.db") + ["db/nomor.db", "db/nikindo.db"],
        "table": "nomor",
    },
    "4": {
        "label": "SEKOLAH (Pendaftaran & Seleksi)",
        "multi_files": [
            ("db/pendaftaran.db", "PENDAFTARAN SEKOLAH"),
            ("db/seleksi.db", "SELEKSI SEKOLAH"),
        ],
        "multi_table": True,
    },
    "5": {
        "label": "NPWP",
        "files": ["db/npwp.db"],
        "table": "npwp",
    },
    "6": {
        "label": "PLN",
        "files": ["db/pln.db"],
        "table": "pln",
    },
    "7": {
        "label": "BANSOS",
        "files": ["db/bansos.db"],
        "table": "bansos",
    },
}

def get_semua_tabel(db_file):
    if not os.path.exists(db_file):
        return []
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall() if row[0] != "sqlite_sequence"]
        conn.close()
        return tables
    except:
        return []

def cari_di_tabel(db_file, table_name, label_db, keyword, tipe_pencarian):
    if not os.path.exists(db_file):
        return []

    hasil_list = []
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()

        cur.execute(f"PRAGMA table_info(`{table_name}`)")
        cols_info = cur.fetchall()
        if not cols_info:
            conn.close()
            return []

        col_names = [c[1] for c in cols_info if c[1].lower() != "id"]
        target_cols = []
        
        if tipe_pencarian == "NIK":
            target_cols = [c for c in col_names if "nik" in c.lower()]
        elif tipe_pencarian == "NOMOR HP":
            target_cols = [c for c in col_names if any(x in c.lower() for x in ["phone", "telp", "telepon", "kontak", "nomor"])]
        elif tipe_pencarian == "NAMA":
            target_cols = [c for c in col_names if any(x in c.lower() for x in ["nama", "name"])]
        elif tipe_pencarian == "ALAMAT":
            target_cols = [c for c in col_names if any(x in c.lower() for x in ["alamat", "address", "kelurahan", "kecamatan", "kab"])]
        elif tipe_pencarian == "SEKOLAH":
            target_cols = [c for c in col_names if any(x in c.lower() for x in ["sekolah", "asal", "pilihan", "jalur"])]
        elif tipe_pencarian == "UNIVERSAL":
            target_cols = col_names

        if not target_cols:
            target_cols = col_names

        if tipe_pencarian in ["NIK", "NOMOR HP"]:
            where_clause = " OR ".join([f"CAST(`{c}` AS TEXT) LIKE ?" for c in target_cols])
            param = f"%{keyword}%"
        else:
            where_clause = " OR ".join([f"UPPER(`{c}`) LIKE UPPER(?)" for c in target_cols])
            param = f"%{keyword}%"

        query = f"SELECT * FROM `{table_name}` WHERE {where_clause} LIMIT 50"
        cur.execute(query, (param,) * len(target_cols))
        rows = cur.fetchall()
        conn.close()

        file_display = os.path.basename(db_file)
        for data in rows:
            row_data = {}
            for idx, val in enumerate(data):
                if cols_info[idx][1].lower() == "id":
                    continue
                field_name = col_names[idx - 1] if (idx - 1 < len(col_names)) else f"kolom_{idx}"
                row_data[field_name] = val if val is not None and val != '' else '-'
            
            hasil_list.append({
                "source": f"{label_db} [{file_display}]",
                "data": row_data
            })
    except Exception as e:
        pass

    return hasil_list

def cari_di_database_fleksibel(db_files, label_db, keyword, tipe_pencarian):
    semua_hasil = []
    unique_files = sorted(list(set(db_files)))
    for db_file in unique_files:
        if not os.path.exists(db_file):
            continue
        tabel_list = get_semua_tabel(db_file)
        if not tabel_list:
            tabel_list = ["nomor", "siswa", "bpjs", "npwp", "pln", "bansos"]
        for tbl in tabel_list:
            semua_hasil.extend(cari_di_tabel(db_file, tbl, label_db, keyword, tipe_pencarian))
    return semua_hasil

@app.route("/", methods=["GET", "POST"])
def index():
    hasil = None
    total_ditemukan = 0
    pilihan_db = "0"
    tipe_pencarian = "UNIVERSAL"
    keyword = ""

    if request.method == "POST":
        pilihan_db = request.form.get("pilihan_db", "0")
        sub_metode = request.form.get("metode", "6")
        raw_keyword = request.form.get("keyword", "").strip()

        # Petakan metode berdasarkan pilihan database
        if pilihan_db == "0":
            metode_map = {"1": "NIK", "2": "NOMOR HP", "3": "NAMA", "4": "ALAMAT", "5": "SEKOLAH", "6": "UNIVERSAL"}
            tipe_pencarian = metode_map.get(sub_metode, "UNIVERSAL")
        elif pilihan_db == "4":
            metode_map = {"1": "NIK", "2": "NAMA", "3": "NOMOR HP", "4": "ALAMAT", "5": "SEKOLAH"}
            tipe_pencarian = metode_map.get(sub_metode, "SEKOLAH")
        else:
            metode_map = {"1": "NIK", "2": "NAMA", "3": "NOMOR HP", "4": "ALAMAT"}
            tipe_pencarian = metode_map.get(sub_metode, "NAMA")

        if tipe_pencarian in ["NIK", "NOMOR HP"]:
            keyword = bersihkan_angka(raw_keyword)
        else:
            keyword = raw_keyword

        if keyword:
            hasil = []
            if pilihan_db == "0":
                hasil.extend(cari_di_database_fleksibel(["db/dukcapil.db"], "DUKCAPIL", keyword, tipe_pencarian))
                hasil.extend(cari_di_database_fleksibel(["db/bpjs.db"], "BPJS", keyword, tipe_pencarian))
                hasil.extend(cari_di_database_fleksibel(glob.glob("db/nikindo*.db") + glob.glob("db/nomor*.db") + ["db/nomor.db", "db/nikindo.db"], "NOMOR / NIKINDO", keyword, tipe_pencarian))
                hasil.extend(cari_di_database_fleksibel(["db/npwp.db"], "NPWP", keyword, tipe_pencarian))
                hasil.extend(cari_di_database_fleksibel(["db/pln.db"], "PLN", keyword, tipe_pencarian))
                hasil.extend(cari_di_database_fleksibel(["db/bansos.db"], "BANSOS", keyword, tipe_pencarian))
                for db_file, label_prefix in [("db/pendaftaran.db", "PENDAFTARAN SEKOLAH"), ("db/seleksi.db", "SELEKSI SEKOLAH")]:
                    for tbl in get_semua_tabel(db_file):
                        hasil.extend(cari_di_tabel(db_file, tbl, label_prefix, keyword, tipe_pencarian))
            elif pilihan_db == "4":
                for db_file, label_prefix in [("db/pendaftaran.db", "PENDAFTARAN SEKOLAH"), ("db/seleksi.db", "SELEKSI SEKOLAH")]:
                    for tbl in get_semua_tabel(db_file):
                        hasil.extend(cari_di_tabel(db_file, tbl, label_prefix, keyword, tipe_pencarian))
            else:
                cfg = DATABASE_CONFIG.get(pilihan_db)
                if cfg:
                    label = cfg["label"]
                    if "files" in cfg:
                        hasil.extend(cari_di_database_fleksibel(cfg["files"], label, keyword, tipe_pencarian))
                    else:
                        hasil.extend(cari_di_tabel(cfg["file"], cfg["table"], label, keyword, tipe_pencarian))
            
            total_ditemukan = len(hasil)

    return render_template("index.html", hasil=hasil, total=total_ditemukan, pilihan_db=pilihan_db, keyword=keyword)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

