from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Dict
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")  # <-- path to your Firebase service account key
firebase_admin.initialize_app(cred)
db = firestore.client()
users_ref = db.collection("users")

# Create the FastAPI app
app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme definition
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Define the user model
class User(BaseModel):
    username: str
    full_name: str = ""
    email: str

# Define the user creation model
class UserCreate(User):
    password: str

# Define the token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Helper function to hash passwords
def get_password_hash(password):
    return pwd_context.hash(password)  # Hashes the password for secure storage

# Helper function to verify passwords
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Sign-up route to register new users
@app.post("/signup", response_model=User)
def signup(user: UserCreate):
    user_doc = users_ref.document(user.username).get()
    if user_doc.exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    users_ref.document(user.username).set({
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
    })
    return User(username=user.username, full_name=user.full_name, email=user.email)

# Login route to generate token
def authenticate_user(username: str, password: str):
    user_doc = users_ref.document(username).get()
    if not user_doc.exists:
        return False
    user_data = user_doc.to_dict()
    if not verify_password(password, user_data['hashed_password']):
        return False
    return user_data

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"access_token": user['username'], "token_type": "bearer"}  # Token can be improved later

# Dependency to protect routes
def get_current_user(token: str = Depends(oauth2_scheme)):
    user_doc = users_ref.document(token).get()
    if not user_doc.exists:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user_doc.to_dict()

# Protected route example
@app.get("/profile")
def read_profile(current_user: dict = Depends(get_current_user)):
    return current_user
