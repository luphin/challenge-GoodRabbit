from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Estados permitidos
EmployeeStatus = Literal["active", "inactive"]


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    phone_number: str = Field(min_length=6)
    email: EmailStr


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    phone_number: str | None = Field(default=None, min_length=6)
    email: EmailStr | None = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    last_name: str
    phone_number: str
    email: str
    status: str


class EmployeeDeactivation(BaseModel):
    id: int
    status: str
    regla_removida: bool
    mensaje: str
