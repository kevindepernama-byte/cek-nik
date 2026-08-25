from flask import Flask, render_template, request, redirect, url_for
import os
import re
import glob
import sqlite3
import zipfile
import base64
app = Flask(__name__)


ZIP_FILE = base64.b64decode("ZGJfYW1hbi56aXA=").decode()
PASSWORD = base64.b64decode("UGFzc3dvcmRSYWhhc2lhS2FtdTEyMw==").decode()
DB_DIR = base64.b64decode("ZGI=").decode()
def siapkan_database_aman():
    if not os.path.exists(DB_DIR) or not os.path.exists(os.path.join(DB_DIR, "dukcapil.db")):
        if os.path.exists(ZIP_FILE):
            os.makedirs(DB_DIR, exist_ok=True)
            try:
                with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
                    zf.extractall(path=".", pwd=PASSWORD.encode('utf-8'))
            except Exception as e:
                print(f"[-] Gagal ekstrak database: {e}")

siapkan_database_aman()

# Rate Limiting IP (Max 5x)
IP_LIMITS = {}
MAX_LIMIT = 100

def cek_dan_update_limit(ip_address):
    if ip_address not in IP_LIMITS:
        IP_LIMITS[ip_address] = {"count": 0}
    if IP_LIMITS[ip_address]["count"] >= MAX_LIMIT:
        return False
    IP_LIMITS[ip_address]["count"] += 1
    return True

def get_sisa_limit(ip_address):
    if ip_address not in IP_LIMITS:
        return MAX_LIMIT
    return max(0, MAX_LIMIT - IP_LIMITS[ip_address]["count"])

def bersihkan_angka(teks):
    return re.sub(r'\D', '', teks)

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

def cari_di_tabel(db_file, table_name, label_db, keyword, tipe_pencarian, target_id):
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

        # ATURAN EKSEKUSI QUERY (100% sama atau mirip)
        # Jika Target Khusus Sekolah (target_id == '4') atau NIK/Nomor HP, gunakan EXACT MATCH (=) agar tidak meleset
        if target_id == '4' or tipe_pencarian in ["NIK", "NOMOR HP"]:
            where_clause = " OR ".join([f"CAST(`{c}` AS TEXT) = ?" for c in target_cols])
            param = keyword
        else:
            # Untuk selain sekolah (Nama/Alamat), gunakan EXACT MATCH juga (100% sama)
            where_clause = " OR ".join([f"UPPER(`{c}`) = UPPER(?)" for c in target_cols])
            param = keyword

        query = f"SELECT * FROM `{table_name}` WHERE {where_clause}"
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

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/dashboard")
def dashboard():
    user_ip = request.remote_addr
    sisa_limit = get_sisa_limit(user_ip)
    return render_template("dashboard.html", sisa_limit=sisa_limit)

@app.route("/cari/<target_id>", methods=["GET", "POST"])
def cari(target_id):
    user_ip = request.remote_addr
    sisa_limit = get_sisa_limit(user_ip)
    
    db_labels = {
        "0": "Scan SEMUA Database & File Pecahan",
        "1": "Dukcapil",
        "2": "BPJS",
        "3": "Nomor / Nikindo",
        "4": "Sekolah (Pendaftaran & Seleksi)",
        "5": "NPWP",
        "6": "PLN",
        "7": "Bansos"
    }
    
    nama_db = db_labels.get(target_id, "Database")
    hasil = None
    error_msg = None
    keyword = ""
    selected_metode = "1"

    if request.method == "POST":
        if sisa_limit <= 0:
            error_msg = "⚠️ Batas limit pencarian Anda sudah habis (Maksimal 5x percobaan)."
        else:
            keyword = request.form.get("keyword", "").strip()
            selected_metode = request.form.get("metode", "1")

            # VALIDASI KETAT INPUT
            # VALIDASI KETAT INPUT
            if target_id == '4':
                if selected_metode == '1': # Khusus NIK di menu Sekolah
                    keyword = bersihkan_angka(keyword)
                    if len(keyword) != 16:
                        error_msg = "⚠️ NIK wajib berupa angka dan harus pas 16 digit!"
                elif selected_metode == '3': # Khusus Kontak/No HP di menu Sekolah
                    keyword = bersihkan_angka(keyword)
                else: # Untuk Nama, Alamat, Asal Sekolah (Huruf)
                    keyword = keyword.upper()
            else:
                if selected_metode in ['1', '3']: # Jika NIK atau Nomor HP umum
                    keyword = bersihkan_angka(keyword)
                    if selected_metode == '1' and len(keyword) != 16:
                        error_msg = "⚠️ NIK wajib berupa angka dan harus pas 16 digit!"
                elif selected_metode in ['2', '4']: 
                    keyword = keyword.upper()

            if not error_msg and not keyword:
                error_msg = "⚠️ Kata kunci tidak boleh kosong."
            
            if not error_msg:
                if not cek_dan_update_limit(user_ip):
                    error_msg = "⚠️ Batas limit pencarian Anda sudah habis."
                    sisa_limit = get_sisa_limit(user_ip)
                    return render_template("cari.html", target_id=target_id, nama_db=nama_db, hasil=None, error=error_msg, sisa_limit=sisa_limit, keyword=keyword, selected_metode=selected_metode)

                sisa_limit = get_sisa_limit(user_ip)

                if target_id == "4":
                    metode_map = {"1": "NIK", "2": "NAMA", "3": "NOMOR HP", "4": "ALAMAT", "5": "SEKOLAH"}
                elif target_id == "0":
                    metode_map = {"1": "NIK", "2": "NOMOR HP", "3": "NAMA", "4": "ALAMAT", "5": "SEKOLAH", "6": "UNIVERSAL"}
                else:
                    metode_map = {"1": "NIK", "2": "NAMA", "3": "NOMOR HP", "4": "ALAMAT"}

                tipe_pencarian = metode_map.get(selected_metode, "NIK")

                temp_hasil = []
                if target_id == "0":
                    for db_file, label in [
                        ("db/dukcapil.db", "DUKCAPIL"), ("db/bpjs.db", "BPJS"),
                        ("db/npwp.db", "NPWP"), ("db/pln.db", "PLN"), ("db/bansos.db", "BANSOS")
                    ]:
                        for tbl in get_semua_tabel(db_file):
                            temp_hasil.extend(cari_di_tabel(db_file, tbl, label, keyword, tipe_pencarian, target_id))
                    for db_file in glob.glob("db/nikindo*.db") + glob.glob("db/nomor*.db") + ["db/nomor.db", "db/nikindo.db"]:
                        for tbl in get_semua_tabel(db_file):
                            temp_hasil.extend(cari_di_tabel(db_file, tbl, "NOMOR / NIKINDO", keyword, tipe_pencarian, target_id))
                    for db_file, label in [("db/pendaftaran.db", "PENDAFTARAN SEKOLAH"), ("db/seleksi.db", "SELEKSI SEKOLAH")]:
                        for tbl in get_semua_tabel(db_file):
                            temp_hasil.extend(cari_di_tabel(db_file, tbl, label, keyword, tipe_pencarian, target_id))
                elif target_id == "1":
                    for tbl in get_semua_tabel("db/dukcapil.db"):
                        temp_hasil.extend(cari_di_tabel("db/dukcapil.db", tbl, "DUKCAPIL", keyword, tipe_pencarian, target_id))
                elif target_id == "2":
                    for tbl in get_semua_tabel("db/bpjs.db"):
                        temp_hasil.extend(cari_di_tabel("db/bpjs.db", tbl, "BPJS", keyword, tipe_pencarian, target_id))
                elif target_id == "3":
                    for db_file in glob.glob("db/nikindo*.db") + glob.glob("db/nomor*.db") + ["db/nomor.db", "db/nikindo.db"]:
                        for tbl in get_semua_tabel(db_file):
                            temp_hasil.extend(cari_di_tabel(db_file, tbl, "NOMOR / NIKINDO", keyword, tipe_pencarian, target_id))
                elif target_id == "4":
                    for db_file, label in [("db/pendaftaran.db", "PENDAFTARAN SEKOLAH"), ("db/seleksi.db", "SELEKSI SEKOLAH")]:
                        for tbl in get_semua_tabel(db_file):
                            temp_hasil.extend(cari_di_tabel(db_file, tbl, label, keyword, tipe_pencarian, target_id))
                elif target_id == "5":
                    for tbl in get_semua_tabel("db/npwp.db"):
                        temp_hasil.extend(cari_di_tabel("db/npwp.db", tbl, "NPWP", keyword, tipe_pencarian, target_id))
                elif target_id == "6":
                    for tbl in get_semua_tabel("db/pln.db"):
                        temp_hasil.extend(cari_di_tabel("db/pln.db", tbl, "PLN", keyword, tipe_pencarian, target_id))
                elif target_id == "7":
                    for tbl in get_semua_tabel("db/bansos.db"):
                        temp_hasil.extend(cari_di_tabel("db/bansos.db", tbl, "BANSOS", keyword, tipe_pencarian, target_id))

                # HILANGKAN DUPLIKAT & BATASI HANYA 1 DATA SAJA
                unique_hasil = []
                seen = set()
                for item in temp_hasil:
                    # Buat string identifier unik dari isinya
                    item_str = str(sorted(item['data'].items()))
                    if item_str not in seen:
                        seen.add(item_str)
                        unique_hasil.append(item)

                # Batasi mutlak hanya 1 data saja yang ditampilkan
                hasil = unique_hasil[:1]

    return render_template("cari.html", target_id=target_id, nama_db=nama_db, hasil=hasil, error=error_msg, 
                           sisa_limit=sisa_limit, keyword=keyword, selected_metode=selected_metode)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

