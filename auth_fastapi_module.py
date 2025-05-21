print("🔥 auth_fastapi_module is loading...")

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ✅ Safe Firebase Initialization (with error handling & logging)
try:
    if not firebase_admin._apps:
        if not os.path.exists("firebase_key.json"):
            raise FileNotFoundError("❌ firebase_key.json not found. Make sure it's uploaded and the path is correct.")

        print("🚀 Initializing Firebase...")
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully.")
except Exception as e:
    print("❌ Firebase init failed:", e)

# ✅ Initialize Firestore DB client safely
try:
    db = firestore.client()
    users_ref = db.collection("users")
except ValueError as e:
    print("❌ Firestore client could not be initialized. Check Firebase init status.")
    db = None
    users_ref = None

# ✅ FastAPI router setup
router = APIRouter()

# ✅ Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ✅ Pydantic models
class User(BaseModel):
    username: str
    full_name: str = ""
    email: str

class UserCreate(User):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ✅ Password helper functions
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ✅ Authentication helper
def authenticate_user(username: str, password: str):
    if users_ref is None:
        raise HTTPException(status_code=503, detail="Database not initialized.")

    user_doc = users_ref.document(username).get()
    if not user_doc.exists:
        return False
    user_data = user_doc.to_dict()
    if not verify_password(password, user_data['hashed_password']):
        return False
    return user_data

# ✅ Routes
@router.post("/signup", response_model=User)
def signup(user: UserCreate):
    if users_ref is None:
        raise HTTPException(status_code=503, detail="Database not available.")

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

@router.get("/profile")
def read_profile(current_user: dict = Depends(lambda token: get_current_user(token))):
    return current_user

def get_current_user(token: str = Depends(oauth2_scheme)):
    if users_ref is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    user_doc = users_ref.document(token).get()
    if not user_doc.exists:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user_doc.to_dict()

