from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from starlette import status
from sessions import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import secrets
import re


router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = secrets.token_hex(20)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pw_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

class CreateUserRequest(BaseModel):
    username : str
    password : str
    
    @field_validator("password")
    def password_validator(cls, value : str) ->  str:
        if not re.fullmatch(r"[a-zA-z0-9!@#$]{8,}", value):
            raise ValueError("Password must be at least 8 characters long and contain only letters, digits, and Special Characters [!@#$]")
        if not re.search(r"[a-z]", value):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r"[A-Z]", value):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r"[0-9]", value):
            raise ValueError('Password must contain at least one numeric character.')
        if not re.search(r"[!@#$]", value):
            raise ValueError('Password must contain at least one special character [!@#$].')
        return value

class Token(BaseModel):
    access_token : str
    token_type : str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(username : str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not pw_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int,expires: timedelta):
    encode_data = {"sub": username, "id" : user_id, "exp": datetime.now()+expires}
    token = jwt.encode(encode_data, SECRET_KEY, algorithm=ALGORITHM)
    return token


db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request : CreateUserRequest):
    create_user_request = Users(
        username = create_user_request.username,
        hashed_password = pw_context.hash(create_user_request.password)
    )
    db.add(create_user_request)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data : Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not Validate the User {form_data.username}")
    token = create_access_token(user.username, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {"access_token" : token, "token_type": "bearer"}

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM])
        username = payload["sub"]
        user_id = payload["id"]
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not Authenticate the user!")
        return {"username" : username, "user_id" : user_id}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not Authenticate the user!")