"""État global du site (spec 047) : le mode maintenance est stocké en base pour survivre aux redémarrages."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EtatSite(Base):
    """Une seule ligne : l'état de maintenance de la plateforme."""

    __tablename__ = "etat_site"
    __table_args__ = (CheckConstraint("id = 1", name="ligne_unique"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text("1"))
    maintenance_active: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    active_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_par_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
