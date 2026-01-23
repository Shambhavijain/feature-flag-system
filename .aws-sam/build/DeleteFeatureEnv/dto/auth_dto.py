from pydantic import BaseModel, Field, field_validator, EmailStr
from utils.password_validator import validate_password


class SignuprequestDTO(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password(password)


class LoginRequestDTO(BaseModel):
    
    email: EmailStr
    password: str

   