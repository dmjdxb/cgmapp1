from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

router = APIRouter()

# Firebase initialization
if not firebase_admin._apps:
    cred_json = os.environ.get("FIREBASE_CREDENTIALS")
    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    else:
        cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
users_ref = db.collection("users")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Models
class User(BaseModel):
    username: str
    full_name: str = ""
    email: str

class UserCreate(User):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helpers
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user_doc = users_ref.document(username).get()
    if not user_doc.exists:
        return False
    user_data = user_doc.to_dict()
    if not verify_password(password, user_data['hashed_password']):
        return False
    return user_data

# Routes
@router.post("/signup", response_model=User)
def signup(user: UserCreate):
    if users_ref.document(user.username).get().exists:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_ref.document(user.username).set({
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
    })
    return User(username=user.username, full_name=user.full_name, email=user.email)

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"access_token": user['username'], "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    user_doc = users_ref.document(token).get()
    if not user_doc.exists:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user_doc.to_dict()

@router.get("/profile")
def read_profile(current_user: dict = Depends(get_current_user)):
    return current_user
