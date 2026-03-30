import logging
import sys
from logging.handlers import RotatingFileHandler # İŞTE YENİ SİLAHIMIZ

# 1. Logger'ımızı oluşturuyoruz
logger = logging.getLogger("olykube_api")
logger.setLevel(logging.INFO)

# 2. Format Belirleme (Kara Kutunun Düzeni)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 3. Terminale Yazdıran Handler (Geliştirme yaparken anlık görmek için)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# 4. DOSYAYA YAZDIRAN HANDLER (Kalıcı Hafıza)
# maxBytes=5000000 (5 MB limit), backupCount=3 (En fazla 3 eski dosya tutar)
file_handler = RotatingFileHandler(
    "olykube.log", 
    maxBytes=5000000, 
    backupCount=3, 
    encoding="utf-8" # Türkçe karakter sorunu yaşamamak için
)
file_handler.setFormatter(formatter)

# 5. Handler'ları Sisteme Ekleme
if not logger.handlers:
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler) # Yeni dosya yazıcımızı da ekledik!