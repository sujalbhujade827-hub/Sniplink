import random
import string
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# 1. DATABASE SETUP
engine = create_engine("sqlite:///./database.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. DATABASE TABLES
class URLItem(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True)
    original_url = Column(String)
    short_code = Column(String, unique=True)

Base.metadata.create_all(bind=engine)

# 3. FASTAPI SETUP
app = FastAPI()

# Allow our HTML frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

# 4. API ROUTES
@app.post("/shorten")
def make_short_link(request: URLRequest, db: Session = Depends(get_db)):
    # Generate random 6-letter string
    letters = string.ascii_letters + string.digits
    random_code = "".join(random.choice(letters) for i in range(6))

    # Save to database
    new_link = URLItem(original_url=request.url, short_code=random_code)
    db.add(new_link)
    db.commit()

    return {"short_code": random_code}

@app.get("/{short_code}")
def redirect_to_website(short_code: str, db: Session = Depends(get_db)):
    # Look up the code
    link_record = db.query(URLItem).filter(URLItem.short_code == short_code).first()

    if not link_record:
        raise HTTPException(status_code=404, detail="Link not found")

    # Redirect
    return RedirectResponse(url=link_record.original_url)