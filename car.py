import os
import re
import sqlite3
import sys
import time

# --- KODE WARNA TERMINAL (ANSI) ---
HIAJU = "\033[92m"
KUNING = "\033[93m"
CYAN = "\033[96m"
MERAH = "\033[91m"
PUTIH = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"


def bersihkan_angka(teks):
  return re.sub(r"\D", "", teks)


DATABASE_CONFIG = {
    "1": {"label": "DUKCAPIL", "file": "dukcapil.db", "table": "siswa"},
    "2": {"label": "BPJS", "file": "bpjs.db", "table": "bpjs"},
    "3": {"label": "NOMOR / NIKINDO", "file": "nomor.db", "table": "nomor"},
    "4": {
        "label": "SEKOLAH (Pendaftaran & Seleksi)",
        "files": [
            ("pendaftaran.db", "PENDAFTARAN SEKOLAH"),
            ("seleksi.db", "SELEKSI SEKOLAH"),
        ],
        "multi_table": True,
    },
    "5": {"label": "NPWP", "file": "npwp.db", "table": "npwp"},
    "6": {"label": "PLN", "file": "pln.db", "table": "pln"},
    "7": {"label": "BANSOS", "file": "bansos.db", "table": "bansos"},
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


def kumpulkan_data_pencarian(pilihan_db, tipe_pencarian, keyword):
  hasil_koleksi = []

  def scan_db(db_file, table_name, label_db):
    if not os.path.exists(db_file):
      return
    try:
      conn = sqlite3.connect(db_file)
      cur = conn.cursor()
      cur.execute(f"PRAGMA table_info({table_name})")
      cols_info = cur.fetchall()
      if not cols_info:
        conn.close()
        return

      col_names = [c[1] for c in cols_info if c[1].lower() != "id"]

      target_cols = col_names
      if tipe_pencarian == "NIK":
        target_cols = [c for c in col_names if "nik" in c.lower()]
      elif tipe_pencarian == "NOMOR HP":
        target_cols = [
            c
            for c in col_names
            if any(
                x in c.lower() for x in ["phone", "telp", "telepon", "kontak"]
            )
        ]
      elif tipe_pencarian == "NAMA":
        target_cols = [
            c for c in col_names if any(x in c.lower() for x in ["nama", "name"])
        ]
      elif tipe_pencarian == "ALAMAT":
        target_cols = [
            c
            for c in col_names
            if any(
                x in c.lower()
                for x in ["alamat", "address", "kelurahan", "kecamatan", "kab"]
            )
        ]
      elif tipe_pencarian == "SEKOLAH":
        target_cols = [
            c
            for c in col_names
            if any(
                x in c.lower() for x in ["sekolah", "asal", "pilihan", "jalur"]
            )
        ]

      if not target_cols:
        target_cols = col_names

      if tipe_pencarian in ["NIK", "NOMOR HP"]:
        where_clause = " OR ".join(
            [f"CAST(`{c}` AS TEXT) LIKE ?" for c in target_cols]
        )
        param = f"%{keyword}%"
      else:
        where_clause = " OR ".join(
            [f"UPPER(`{c}`) LIKE UPPER(?)" for c in target_cols]
        )
        param = f"%{keyword}%"

      query = f"SELECT * FROM `{table_name}` WHERE {where_clause}"
      cur.execute(query, (param,) * len(target_cols))
      rows = cur.fetchall()
      conn.close()

      for row in rows:
        hasil_koleksi.append(
            {"label": label_db, "table": table_name, "cols": col_names, "data": row}
        )
    except:
      pass

  if pilihan_db == "0":
    single_dbs = [
        ("DUKCAPIL", "dukcapil.db", "siswa"),
        ("BPJS", "bpjs.db", "bpjs"),
        ("NOMOR / NIKINDO", "nomor.db", "nomor"),
        ("NPWP", "npwp.db", "npwp"),
        ("PLN", "pln.db", "pln"),
        ("BANSOS", "bansos.db", "bansos"),
    ]
    for label, db_file, tbl in single_dbs:
      scan_db(db_file, tbl, label)

    for db_file, label_prefix in [
        ("pendaftaran.db", "PENDAFTARAN SEKOLAH"),
        ("seleksi.db", "SELEKSI SEKOLAH"),
    ]:
      for tbl in get_semua_tabel(db_file):
        scan_db(db_file, tbl, label_prefix)

  elif pilihan_db == "4":
    for db_file, label_prefix in [
        ("pendaftaran.db", "PENDAFTARAN SEKOLAH"),
        ("seleksi.db", "SELEKSI SEKOLAH"),
    ]:
      for tbl in get_semua_tabel(db_file):
        scan_db(db_file, tbl, label_prefix)
  else:
    cfg = DATABASE_CONFIG.get(pilihan_db)
    if cfg:
      scan_db(cfg["file"], cfg["table"], cfg["label"])

  return hasil_koleksi


def sensor_teks(teks, tipe="normal"):
  if not teks or teks == "-":
    return "------"
  teks_str = str(teks).strip()

  if tipe == "nik":
    if len(teks_str) >= 12:
      return teks_str[:6] + "xxxxxx"
    return teks_str[:3] + "xxxxxx"
  elif tipe == "nama":
    if len(teks_str) <= 3:
      return teks_str + "***"
    return teks_str[:3] + "******"
  elif tipe == "tgllahir":
    if len(teks_str) >= 8:
      return teks_str[:6] + "xx"
    return teks_str[:4] + "xx"
  else:
    return teks_str[:4] + "****"


def animasi_loading():
  print(f"\n{CYAN}⚡ [SYSTEM] Menghubungkan ke enkripsi server...{RESET}")
  time.sleep(0.3)
  sys.stdout.write(f"{HIAJU}  Decryption Progress : [0%] ")
  sys.stdout.flush()

  bar_steps = [
      ("████░░░░░░", "40%"),
      ("████████░░", "80%"),
      ("██████████", "100% (SECURE)"),
  ]
  for bar, pct in bar_steps:
    time.sleep(0.2)
    sys.stdout.write(f"\r{HIAJU}  Decryption Progress : [{bar}] {pct} {RESET}")
    sys.stdout.flush()
  print("\n")


def proses_pencarian_dummy(pilihan_db, tipe_pencarian, keyword):
  animasi_loading()

  data_ditemukan = kumpulkan_data_pencarian(
      pilihan_db, tipe_pencarian, keyword
  )
  total = len(data_ditemukan)

  if total == 0:
    print(
        f"  {MERAH}⚠️  Tidak ada data ditemukan untuk keyword:"
        f" '{keyword}'{RESET}"
    )
    print(f"{CYAN}─" * 52 + f"{RESET}")
    return

  print(f"{HIAJU}╔" + "═" * 50 + "╗")
  print(f"║{'📊 STATUS: DATA LEAK / TARGET MATCHED':^50}║")
  print("╚" + "═" * 50 + f"╝{RESET}")
  print(f"  🔥 {BOLD}Keyword Target   {RESET} : {KUNING}{keyword.upper()}{RESET}")
  print(f"  📦 {BOLD}Total Data Bocor {RESET} : {HIAJU}{total} Record{RESET}")
  print(
      f"  🛡️  {BOLD}Struktur Kolom   {RESET} :"
      f" {CYAN}NIK | NAMA | KELAMIN | TGL LAHIR{RESET}"
  )
  print(f"{HIAJU}═" * 52 + f"{RESET}")

  print(f"  📋 {PUTIH}Preview 10 Data Teratas (Akurat & Tersensor):{RESET}")
  for i, item in enumerate(data_ditemukan[:10]):
    cols = item["cols"]
    row_data = item["data"]

    p_nik = "3210xxxxxxxx"
    p_nama = "██████████"
    p_kelamin = "L"
    p_tgllahir = "12-05-19xx"

    for idx, col_name in enumerate(cols):
      val = str(row_data[idx + 1]) if idx + 1 < len(row_data) else ""
      c_low = col_name.lower()

      if "nik" in c_low and val:
        p_nik = sensor_teks(val, "nik")
        # Ekstrak tanggal lahir otomatis dari NIK jika format NIK sesuai (min 12 digit)
        b_nik = bersihkan_angka(val)
        if len(b_nik) >= 12:
          tgl_int = int(b_nik[6:8])
          # Jika wanita (NIK ditambah 40 di tanggal)
          if tgl_int > 40:
            tgl_int -= 40
            p_kelamin = "P"
          else:
            p_kelamin = "L"

          dd = f"{tgl_int:02d}"
          mm = b_nik[8:10]
          yy = b_nik[10:12]
          thn = "20" + yy if int(yy) < 30 else "19" + yy
          p_tgllahir = f"{dd}-{mm}-{thn[:2]}xx"

      elif any(x in c_low for x in ["nama", "name"]) and val:
        p_nama = sensor_teks(val, "nama")
      elif any(x in c_low for x in ["kelamin", "jk", "gender", "sex"]) and val:
        p_kelamin = val[:1].upper()
      elif any(
          x in c_low for x in ["tgl", "lahir", "birth", "tanggal", "tg"]
      ) and val:
        p_tgllahir = sensor_teks(val, "tgllahir")

    nomor_urut = f"{i+1:2d}"
    print(
        f"   {KUNING}[{nomor_urut}]{RESET} {item['label']} ➜ NIK:"
        f" {CYAN}{p_nik}{RESET} | Nama: {PUTIH}{p_nama}{RESET} | JK: {CYAN}{p_kelamin}{RESET} | Lahir:"
        f" {HIAJU}{p_tgllahir}{RESET}"
    )

  print(f"{HIAJU}─" * 52 + f"{RESET}")
  opsi_buka = (
      input(
          f"  ⚡ {BOLD}Ingin buka & tampilkan semua detail datanya?{RESET}"
          f" {KUNING}[y/N]{RESET} ➜ "
      )
      .strip()
      .lower()
  )

  if opsi_buka == "y":
    print(
        f"\n{KUNING}🔓 Membuka seluruh {HIAJU}{total}{KUNING} data lengkap...\n"
        f"{RESET}"
    )
    time.sleep(0.3)
    for item in data_ditemukan:
      header_txt = f"{item['label']} [Tabel: {item['table'].upper()}]"
      print(f"{CYAN}╭──────────────────────────────────────────────────╮")
      print(f"│ {header_txt:<48} │")
      print(f"╰──────────────────────────────────────────────────{CYAN}╯{RESET}")
      for idx, val in enumerate(item["data"]):
        if idx == 0:
          continue
        f_name = (
            item["cols"][idx - 1]
            if (idx - 1 < len(item["cols"]))
            else f"kol_{idx}"
        )
        val_str = str(val) if val else "-"
        print(
            f"  {HIAJU}🔹 {f_name:<22} :{RESET}"
            f" {PUTIH}{val_str[:40]}{RESET}"
        )
      print(f"{CYAN}─" * 52 + f"{RESET}")
  else:
    print(
        f"\n{KUNING}✨ Selesai. Tampilan bersih, tanggal lahir otomatis tersensor"
        f" rapi!{RESET}\n"
    )


def main():
  while True:
    print(f"\n{CYAN}╔" + "═" * 50 + "╗")
    print(f"║{BOLD}{HIAJU}✨ CYBER OSINT SEARCH TOOL ✨{RESET}{CYAN}║")
    print("╚" + "═" * 50 + f"╝{RESET}")
    print(f"  {KUNING}[0]{RESET} 🚀 Scan SEMUA Database (Universal)")
    print(f"  {KUNING}[1]{RESET} 🔎 Dukcapil")
    print(f"  {KUNING}[2]{RESET} 📞 BPJS")
    print(f"  {KUNING}[3]{RESET} 📱 Nomor / Nikindo")
    print(f"  {KUNING}[4]{RESET} 🏫 Sekolah (Pendaftaran & Seleksi)")
    print(f"  {KUNING}[5]{RESET} 💳 NPWP")
    print(f"  {KUNING}[6]{RESET} ⚡ PLN")
    print(f"  {KUNING}[7]{RESET} 📦 Bansos")
    print(f"  {KUNING}[q]{RESET} 🚪 Keluar")
    print(f"{CYAN}═" * 52 + f"{RESET}")

    pilihan_db = (
        input(f"  {PUTIH}Pilih Target Database [0-7 / q] ➜ {RESET}")
        .strip()
        .lower()
    )

    if pilihan_db == "q":
      print(f"\n{HIAJU}👋 Keluar program. Sampai jumpa!\n{RESET}")
      break
    elif pilihan_db not in ["0", "1", "2", "3", "4", "5", "6", "7"]:
      print(f"\n{MERAH}❌ Pilihan database tidak valid!{RESET}")
      continue

    if pilihan_db == "0":
      print(f"\n  {CYAN}Pilih Metode Pencarian Universal:{RESET}")
      print(f"  {KUNING}[1]{RESET} Berdasarkan NIK")
      print(f"  {KUNING}[2]{RESET} Berdasarkan Nomor HP / Kontak")
      print(f"  {KUNING}[3]{RESET} Berdasarkan Nama Orang")
      print(f"  {KUNING}[4]{RESET} Berdasarkan Alamat")
      print(f"  {KUNING}[5]{RESET} Berdasarkan Asal Sekolah")
      print(f"  {KUNING}[6]{RESET} Scan Seluruh Keyword (Universal)")

      sub = input(f"  {PUTIH}Pilih Metode [1-6] ➜ {RESET}").strip()
      metode_map = {
          "1": "NIK",
          "2": "NOMOR HP",
          "3": "NAMA",
          "4": "ALAMAT",
          "5": "SEKOLAH",
          "6": "UNIVERSAL",
      }
      tipe_pencarian = metode_map.get(sub, "UNIVERSAL")

    elif pilihan_db == "4":
      print(f"\n  {CYAN}Pilih Metode Pencarian Sekolah:{RESET}")
      print(f"  {KUNING}[1]{RESET} Berdasarkan NIK")
      print(f"  {KUNING}[2]{RESET} Berdasarkan Nama Siswa")
      print(f"  {KUNING}[3]{RESET} Berdasarkan Kontak Orang Tua (No HP)")
      print(f"  {KUNING}[4]{RESET} Berdasarkan Alamat Lengkap")
      print(f"  {KUNING}[5]{RESET} Berdasarkan Asal Sekolah")

      sub = input(f"  {PUTIH}Pilih Metode [1-5] ➜ {RESET}").strip()
      metode_map = {
          "1": "NIK",
          "2": "NAMA",
          "3": "NOMOR HP",
          "4": "ALAMAT",
          "5": "SEKOLAH",
      }
      tipe_pencarian = metode_map.get(sub, "SEKOLAH")
    else:
      cfg = DATABASE_CONFIG[pilihan_db]
      print(f"\n  {CYAN}Pilih Metode untuk {cfg['label']}:{RESET}")
      print(f"  {KUNING}[1]{RESET} Berdasarkan NIK")
      print(f"  {KUNING}[2]{RESET} Berdasarkan Nama")
      print(f"  {KUNING}[3]{RESET} Berdasarkan Nomor HP / Telepon")
      print(f"  {KUNING}[4]{RESET} Berdasarkan Alamat")

      sub = input(f"  {PUTIH}Pilih Metode [1-4] ➜ {RESET}").strip()
      metode_map = {
          "1": "NIK",
          "2": "NAMA",
          "3": "NOMOR HP",
          "4": "ALAMAT",
      }
      tipe_pencarian = metode_map.get(sub, "NAMA")

    if tipe_pencarian in ["NIK", "NOMOR HP"]:
      raw_val = input(f"  {PUTIH}Masukkan {tipe_pencarian} ➜ {RESET}").strip()
      keyword = bersihkan_angka(raw_val)
    else:
      keyword = (
          input(f"  {PUTIH}Masukkan Kata Kunci [{tipe_pencarian}] ➜ {RESET}")
          .strip()
      )

    if not keyword:
      print(f"\n{MERAH}❌ Input tidak boleh kosong.{RESET}")
      continue

    proses_pencarian_dummy(pilihan_db, tipe_pencarian, keyword)


if __name__ == "__main__":
  main()

