"""ChromaDB'nin varsayılan embedding modelini (all-MiniLM-L6-v2) build sırasında indirir.

Chroma'nın kendi indiricisi kopan bağlantıda ~80 MB'a sıfırdan başlar. Bu script
HTTP Range ile kaldığı yerden devam eder, SHA-256'yı doğrular; arşivi açma işini
yine Chroma'ya bırakır (arşiv geçerliyse Chroma indirmeyi atlar, sadece açar).
"""
import hashlib
import os
import time
import urllib.error
import urllib.request

from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

MAX_ATTEMPTS = 50
model = ONNXMiniLM_L6_V2
archive = os.path.join(model.DOWNLOAD_PATH, model.ARCHIVE_FILENAME)
os.makedirs(model.DOWNLOAD_PATH, exist_ok=True)


def sha256_ok(path: str) -> bool:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest() == model._MODEL_SHA256


for attempt in range(1, MAX_ATTEMPTS + 1):
    have = os.path.getsize(archive) if os.path.exists(archive) else 0
    request = urllib.request.Request(model.MODEL_DOWNLOAD_URL, headers={"Range": f"bytes={have}-"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            # 206: kaldığı yerden devam; 200: sunucu Range'i yok saydı, baştan yaz
            mode = "ab" if response.status == 206 else "wb"
            with open(archive, mode) as f:
                while chunk := response.read(1 << 16):
                    f.write(chunk)
    except urllib.error.HTTPError as e:
        if e.code != 416:  # 416: dosya zaten tamamen inmiş
            print(f"Deneme {attempt}: HTTP {e.code}, {have} bayt inmişti; tekrar deneniyor")
            time.sleep(5)
            continue
    except Exception as e:  # bağlantı kopması, DNS, SSL, timeout
        print(f"Deneme {attempt}: {e!r}, {have} bayt inmişti; kaldığı yerden devam ediliyor")
        time.sleep(5)
        continue

    if sha256_ok(archive):
        break
    print(f"Deneme {attempt}: SHA-256 uyuşmadı, arşiv baştan indirilecek")
    os.remove(archive)
else:
    raise SystemExit(f"Model {MAX_ATTEMPTS} denemede indirilemedi")

# Arşivi açar ve modeli bir kez çalıştırarak kurulumu doğrular
model()(["warmup"])
# Chroma yalnızca açılmış dosyalara bakar; arşivi image'da tutmak ~80 MB israf
os.remove(archive)
print("Embedding modeli hazır:", model.DOWNLOAD_PATH)
