from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut
from app.utils.security import get_password_hash, verify_password, create_access_token

class AuthService:
    @staticmethod
    def register_user(db: Session, request: UserRegister) -> Token:
        email_clean = request.email.strip().lower()
        existing = db.query(User).filter(User.email == email_clean).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )

        hashed_pw = get_password_hash(request.password)
        user = User(
            name=request.name.strip(),
            email=email_clean,
            password_hash=hashed_pw
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

    @staticmethod
    def authenticate_user(db: Session, request: UserLogin) -> Token:
        email_clean = request.email.strip().lower()
        user = db.query(User).filter(User.email == email_clean).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))
