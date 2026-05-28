import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt as _bcrypt
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session, User
from app.db.session import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)

SESSION_HOURS = 8


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = body.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    password_ok = user and await asyncio.to_thread(
        _bcrypt.checkpw, body.password.encode(), user.hashed_password.encode()
    )
    if not password_ok:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid email or password."},
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user.last_login_at = now

    expires = now + timedelta(hours=SESSION_HOURS)
    session = Session(id=str(uuid4()), user_id=user.id, expires_at=expires)
    db.add(session)
    await db.commit()

    response.set_cookie(
        key="rl_session",
        value=session.id,
        httponly=True,
        samesite="strict",
        path="/",
        max_age=SESSION_HOURS * 3600,
    )

    return {
        "expires_at": expires.isoformat() + "Z",
        "user": {"id": user.id, "email": user.email},
    }


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    token = (credentials.credentials if credentials else None) or request.cookies.get("rl_session")
    if token:
        result = await db.execute(select(Session).where(Session.id == token))
        session = result.scalar_one_or_none()
        if session:
            await db.delete(session)
            await db.commit()
    response.delete_cookie(key="rl_session", path="/")
