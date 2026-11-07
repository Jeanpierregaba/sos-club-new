from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationSortie(BaseModel):
    id: UUID
    type: str
    titre: str
    message: str | None
    lien: str | None
    lue: bool
    cree_le: datetime


class Notifications(BaseModel):
    notifications: list[NotificationSortie]
    non_lues: int


class CompteNotifications(BaseModel):
    non_lues: int
