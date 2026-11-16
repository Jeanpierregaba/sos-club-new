"""Cartes numériques de l'élève et de l'encadreur (spec 040, R15).

La table ne garde que ce qui ne se recalcule pas : le numéro, le code du QR, le type, la date de délivrance et la
suspension par l'équipe. La validité, le club et le rôle se calculent à chaque lecture (`service.etat_de`), depuis le
compte, l'affiliation ou le rattachement : aucune autre partie du code n'a à tenir la carte à jour.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Sequence, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TypeCarte(StrEnum):
    membre = "membre"
    encadreur = "encadreur"


PREFIXES = {TypeCarte.membre: "CS-M", TypeCarte.encadreur: "CS-E"}
# Une seule séquence pour les deux types : un numéro n'est jamais attribué deux fois.
SEQUENCE_NUMERO = Sequence("carte_numero_seq")
# Le code du QR : 32 caractères URL-sûrs (192 bits), la forme de `secrets.token_urlsafe(24)`.
FORMAT_CODE = r"^[A-Za-z0-9_-]{32}$"


class Carte(Base):
    __tablename__ = "carte"
    __table_args__ = (
        CheckConstraint("(suspendue_le IS NULL) = (motif_suspension IS NULL)", name="motif_si_suspendue"),
        CheckConstraint(f"code ~ '{FORMAT_CODE}'", name="code_format"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    # SET NULL : la carte, et donc son numéro, survit à une suppression du compte ; il n'est jamais réattribué.
    utilisateur_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"), unique=True)
    type: Mapped[TypeCarte] = mapped_column(
        Enum(TypeCarte, name="type_carte", native_enum=False, create_constraint=True, length=10,
             values_callable=lambda enum: [membre.value for membre in enum])
    )  # fmt: skip
    numero: Mapped[str] = mapped_column(String(14), unique=True)
    # En clair : il doit être réimprimé à chaque téléchargement. Il ne donne accès qu'au statut, au numéro et au club,
    # et n'apparaît ni au journal ni dans les exports.
    code: Mapped[str] = mapped_column(String(32), unique=True)
    delivree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    suspendue_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspendue_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_suspension: Mapped[str | None] = mapped_column(Text)
