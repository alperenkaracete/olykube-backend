from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Şifre hash'le
hashed = pwd_context.hash("123456")
print("Hash:", hashed)

# Doğrula
print("Doğru mu:", pwd_context.verify("123456", hashed))
print("Yanlış mı:", pwd_context.verify("yanlissifre", hashed))

SECRET_KEY = "gizli-anahtar"
ALGORITHM = "HS256"

# Token oluştur
data = {"sub": "kullanici@mail.com"}
token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
print("Token:", token)

# Token çöz
decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
print("Decoded:", decoded)