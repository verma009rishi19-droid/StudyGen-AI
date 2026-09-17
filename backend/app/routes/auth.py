from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut
from app.services.auth_service import AuthService
from app.utils.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(request: UserRegister, db: Session = Depends(get_db)):
    return AuthService.register_user(db, request)

@router.post("/login", response_model=Token)
def login(request: UserLogin, db: Session = Depends(get_db)):
    return AuthService.authenticate_user(db, request)

@router.post("/guest", response_model=Token)
def guest_login(db: Session = Depends(get_db)):
    return AuthService.get_or_create_guest_user(db)

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
