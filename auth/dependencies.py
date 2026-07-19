from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth.database import get_db
from app.models.user import User
from app.auth.security import verify_token
from app.auth.database import SessionLocal

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = verify_token(credentials.credentials)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user



async def get_current_user_ws(token: str):

    payload = verify_token(token)

    if payload is None:
        raise Exception("Invalid token")

    db: Session = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.id == int(payload["sub"]))
            .first()
        )

        if user is None:
            raise Exception("User not found")

        return user

    finally:
        db.close()