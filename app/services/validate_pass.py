import re
from fastapi import HTTPException

def validate_password(password: str):
    """
    Перевіряє, чи пароль відповідає вимогам безпеки:
    - Мінімум 8 символів
    - Хоча б одна велика літера
    - Хоча б одна цифра
    - Хоча б один спеціальний символ (!@#$%^&*()_+ і т.д.)
    """
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character.")
    return password
