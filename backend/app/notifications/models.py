"""Centre de notifications sur le site (spec 023) : aucun e-mail ni SMS aux élèves (PRD, hors périmètre).

Une notification ne s'adresse qu'à un compte, et ne contient jamais un contenu non approuvé d'un autre que lui.
"""

from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Notification(Base):
    __tablename__ = "notification"
    __table_args__ = (Index("ix_notification_utilisateur_id_lue_le", "utilisateur_id", "lue_le", "cree_le"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    # Par exemple `article_approuve` : le site choisit son icône.
    type: Mapped[str] = mapped_column(String(40))
    titre: Mapped[str] = mapped_column(String(200))
    message: Mapped[str | None] = mapped_column(String(1000))
    # Chemin du site, par exemple `/mes-articles/<id>`.
    lien: Mapped[str | None] = mapped_column(String(300))
    lue_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
