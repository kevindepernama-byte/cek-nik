import json

# Cek struktur db_nikindo.json
with open("source/db_nikindo.json", "r") as f:
  data = json.load(f)
  print("Contoh data nikindo.json:", data[0] if isinstance(data, list) else list(data.keys()))

# Cek struktur db_nomor.json
with open("source/db_nomor.json", "r") as f:
  data = json.load(f)
  print("Contoh data nomor.json:", data[0] if isinstance(data, list) else list(data.keys()))

