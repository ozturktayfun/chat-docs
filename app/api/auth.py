from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.schemas import Token, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Create a new user account and return the persisted record."""
    service = AuthService(db)
    user = service.register_user(user_in)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate the user and issue a JWT access token."""
    service = AuthService(db)
    user = service.authenticate(credentials.email, credentials.password)
    token = service.create_token(user)
    return Token(access_token=token)
