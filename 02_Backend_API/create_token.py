import jwt
import datetime

# كلمة السر بتاعتك اللي موجودة في ملف .env
SECRET_KEY = "super_secret_key_change_me"

payload = {
    "role": "ai_engine",
    # التوكن ده هيفضل شغال لمدة 10 سنين
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3650)
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print("Your JWT Token is:\n\n", token)