from pydantic import BaseModel, Field, field_validator, EmailStr
from utils.password_validator import validate_password


class SignuprequestDTO(BaseModel):
    username: str = Field(..., min_length=3, description="Username must be at least 3 characters")
    email: EmailStr
    password: str = Field(..., min_length=3, description="Password must be at least 3 characters")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, password: str) -> str:
        return validate_password(password)


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=3, description="Password must be at least 3 characters")
