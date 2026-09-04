import re
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator

_CONTROL_CHARS = re.compile(r"[\r\n\x00]")


class ServiceType(StrEnum):
    DOG_WALKING = "dog_walking"
    CAT_HOME_VISIT = "cat_home_visit"
    VACATION_PET_SITTING = "vacation_pet_sitting"
    FEEDING_VISIT = "feeding_visit"
    DAYTIME_OCCASIONAL_CARE = "daytime_occasional_care"


SERVICE_LABELS: dict[ServiceType, str] = {
    ServiceType.DOG_WALKING: "Promenade de chiens",
    ServiceType.CAT_HOME_VISIT: "Visite à domicile pour chats",
    ServiceType.VACATION_PET_SITTING: "Garde pendant les vacances",
    ServiceType.FEEDING_VISIT: "Passage nourriture / eau",
    ServiceType.DAYTIME_OCCASIONAL_CARE: "Garde ponctuelle en journée",
}


class ContactFields(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=30)
    service: ServiceType
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def strip_required(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if _CONTROL_CHARS.search(value):
                raise ValueError("caractères de contrôle non autorisés")
        return value

    @field_validator("message", mode="before")
    @classmethod
    def strip_optional(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value
