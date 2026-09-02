from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedIdentity(BaseModel):
    uid: str
    display_name: str | None
    email: str
    photo_url: str | None


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    uid: str
    display_name: str | None = Field(default=None, alias="displayName")
    email: str
    photo_url: str | None = Field(default=None, alias="photoURL")
    locale: str
    status: str
    created_at: datetime = Field(alias="createdAt")
    last_login: datetime = Field(alias="lastLogin")
