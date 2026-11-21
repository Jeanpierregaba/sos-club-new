from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EtatSitePublic(BaseModel):
    """État visible par le client, sans détail sensible."""

    model_config = ConfigDict(extra="forbid")

    maintenance: bool


class EtatMaintenance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    maintenance_active: bool
    active_le: datetime | None


class MiseAJourMaintenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    maintenance_active: bool
