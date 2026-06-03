from pydantic import BaseModel, EmailStr
from typing import Optional, List

class StartCallResponse(BaseModel):
    session_id: str

class AudioChunk(BaseModel):
    session_id: str
    # For local testing we accept `text` (transcript) instead of binary audio
    text: Optional[str] = None
    audio_base64: Optional[str] = None

class EndCallRequest(BaseModel):
    session_id: str

class AuthSignup(BaseModel):
    email: EmailStr
    display_name: str
    password: str

class AuthLogin(BaseModel):
    email: EmailStr
    password: str
