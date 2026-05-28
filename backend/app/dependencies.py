from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session, User
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # Prefer HttpOnly cookie; fall back to Bearer header for API clients.
    token = request.cookies.get("rl_session") or (credentials.credentials if credentials else None)
    if not token:
        raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Authentication required."})

    result = await db.execute(select(Session).where(Session.id == token))
    session = result.scalar_one_or_none()

    if not session or session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session expired or invalid."})

    user = await db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "User not found."})

    return user
