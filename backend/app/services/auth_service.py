from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserRegister, TokenResponse, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(
            full_name=data.full_name,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            role=data.role,
            phone=data.phone,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id), "role": user.role})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )
