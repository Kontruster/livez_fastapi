from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # TODO: Проверить токен, достать user_id из БД
    # Для примера возвращаем заглушку:
    return {"id": 1, "username": "test_user"}