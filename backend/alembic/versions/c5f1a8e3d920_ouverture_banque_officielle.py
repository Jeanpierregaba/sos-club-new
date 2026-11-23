"""ouverture : banque officielle et remise à zéro (spec 049)

Avant l'ouverture au public :

1. les quiz Jeux et de certification publiés sont dépubliés ; les 80 quiz Jeux et les 20 quiz de certification de
   la banque officielle (`alembic/donnees/banque_officielle.json`) sont publiés ;
2. les parties Jeux passent à 10 questions, réussies à 8 (les quiz ont 10 questions) ;
3. les parties en cours sur les anciens quiz sont closes sans réussite ;
4. chaque gain des Jeux et de la certification (élèves, encadreurs, et donc la part des clubs) est annulé au
   registre, avec un motif : rien n'est effacé (ADR-0004) ;
5. les étoiles, places réussies et badges passent dans leurs tables d'archive ; les certificats valides sont
   révoqués, et tous sont archivés pour ne plus bloquer un nouveau certificat.

Le schéma (tables d'archive, `certificat.archive_le`) s'applique partout ; les données seulement sur une base qui a
la banque d'AIMES-AFRIQUE (préprod, prod, base de développement), pas sur celle des tests.

Le retour arrière enlève le schéma tant qu'aucune archive n'existe ; une remise à zéro faite ne se défait pas.

Revision ID: c5f1a8e3d920
Revises: 9aa1a0ded79b
Create Date: 2026-11-23

"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c5f1a8e3d920"
down_revision: str | Sequence[str] | None = "9aa1a0ded79b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FICHIER = Path(__file__).resolve().parents[1] / "donnees" / "banque_officielle.json"
VALIDATEUR = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
QUALITE = "Document officiel « Banque de 1 000 questions – Quiz santé des Clubs Santé »"
DESCRIPTION = "Banque officielle des Clubs Santé (spec 049)"
MOTIF_QUIZ = "Remplacé par la banque officielle de 1 000 questions (spec 049)."
MOTIF = "Remise à zéro avant l'ouverture au public (spec 049)."
NB_QUESTIONS_JEUX, SEUIL_JEUX = 10, 8
# Les gains annulés : ceux des parcours Jeux et certification, et la certification des encadreurs.
ACTIONS_ENCADREUR = ("encadreur.certification", "encadreur.certification_eleve", "encadreur.quiz")

quiz = sa.table(
    "quiz",
    sa.column("id", sa.Uuid()),
    sa.column("titre", sa.String()),
    sa.column("description", sa.String()),
    sa.column("axe_code", sa.String()),
    sa.column("etat", sa.String()),
    sa.column("parcours", sa.String()),
    sa.column("place", sa.Integer()),
    sa.column("niveau", sa.String()),
    sa.column("numero", sa.Integer()),
    sa.column("contenu_de_test", sa.Boolean()),
    sa.column("validateur_nom", sa.String()),
    sa.column("validateur_qualite", sa.String()),
    sa.column("publie_le", sa.DateTime(timezone=True)),
)
question = sa.table(
    "question_quiz",
    sa.column("id", sa.Uuid()),
    sa.column("quiz_id", sa.Uuid()),
    sa.column("enonce", sa.String()),
    sa.column("choix", postgresql.JSONB()),
    sa.column("bonne_reponse", sa.Integer()),
    sa.column("explication", sa.String()),
    sa.column("ordre", sa.Integer()),
)


def _schema() -> None:
    op.create_table(
        "etoile_obtenue_archive",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("niveau", sa.String(length=20), nullable=False),
        sa.Column("mouvement_id", sa.Uuid(), nullable=True),
        sa.Column("obtenue_le", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archive_le", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["mouvement_id"],
            ["mouvement_points.id"],
            name=op.f("fk_etoile_obtenue_archive_mouvement_id_mouvement_points"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_etoile_obtenue_archive_utilisateur_id_utilisateur"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_etoile_obtenue_archive")),
    )
    op.create_index(
        op.f("ix_etoile_obtenue_archive_utilisateur_id"), "etoile_obtenue_archive", ["utilisateur_id"], unique=False
    )
    op.create_table(
        "place_reussie_archive",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("place", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Uuid(), nullable=False),
        sa.Column("tentative_id", sa.Uuid(), nullable=False),
        sa.Column("reussie_le", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archive_le", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["quiz_id"], ["quiz.id"], name=op.f("fk_place_reussie_archive_quiz_id_quiz"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tentative_id"],
            ["tentative_quiz.id"],
            name=op.f("fk_place_reussie_archive_tentative_id_tentative_quiz"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_place_reussie_archive_utilisateur_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_place_reussie_archive")),
    )
    op.create_index(
        op.f("ix_place_reussie_archive_utilisateur_id"), "place_reussie_archive", ["utilisateur_id"], unique=False
    )
    op.create_table(
        "badge_obtenu_archive",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("rang", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=40), nullable=False),
        sa.Column("palier", sa.Integer(), nullable=False),
        sa.Column("regles_version", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Uuid(), nullable=True),
        sa.Column("mouvement_id", sa.Uuid(), nullable=True),
        sa.Column("obtenu_le", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archive_le", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["club_id"], ["club.id"], name=op.f("fk_badge_obtenu_archive_club_id_club"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["mouvement_id"],
            ["mouvement_points.id"],
            name=op.f("fk_badge_obtenu_archive_mouvement_id_mouvement_points"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_badge_obtenu_archive_utilisateur_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_badge_obtenu_archive")),
    )
    op.create_index(
        op.f("ix_badge_obtenu_archive_utilisateur_id"), "badge_obtenu_archive", ["utilisateur_id"], unique=False
    )
    op.add_column("certificat", sa.Column("archive_le", sa.DateTime(timezone=True), nullable=True))
    op.drop_index("uq_certificat_origine", table_name="certificat")
    op.create_index(
        "uq_certificat_origine",
        "certificat",
        ["utilisateur_id"],
        unique=True,
        postgresql_where=sa.text("remplace_id IS NULL AND archive_le IS NULL"),
    )


def _a_la_banque(connexion: sa.Connection) -> bool:
    return bool(
        connexion.execute(
            # Les 100 défis Jeux d'AIMES-AFRIQUE (spec 034) : chargés seulement là où la banque l'est.
            sa.text(
                "SELECT 1 FROM quiz WHERE validateur_nom = :validateur AND parcours = 'jeux' AND numero IS NOT NULL "
                "LIMIT 1"
            ),
            {"validateur": VALIDATEUR},
        ).first()
    )


def _remplacer_les_quiz(connexion: sa.Connection, maintenant: datetime) -> bool:
    """Vrai si la banque officielle vient d'être chargée ; faux si elle l'était déjà (des parties y ont été jouées)."""
    deja = connexion.execute(
        sa.text("SELECT 1 FROM quiz WHERE description LIKE :d LIMIT 1"), {"d": f"{DESCRIPTION}%"}
    ).first()
    if deja:
        return False
    connexion.execute(
        sa.text(
            "UPDATE quiz SET etat = 'depublie', motif = :motif, version = version + 1, modifie_le = :maintenant "
            "WHERE etat = 'publie' AND parcours IN ('jeux', 'certification')"
        ),
        {"motif": MOTIF_QUIZ, "maintenant": maintenant},
    )
    donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
    for parcours, entrees in (("jeux", donnees["jeux"]), ("certification", donnees["certification"])):
        for entree in entrees:
            quiz_id = uuid7()
            connexion.execute(
                quiz.insert().values(
                    id=quiz_id,
                    titre=entree["titre"],
                    description=entree["description"],
                    axe_code=entree["axe"],
                    etat="publie",
                    parcours=parcours,
                    place=entree.get("place"),
                    niveau=entree.get("niveau"),
                    numero=entree.get("numero"),
                    contenu_de_test=False,
                    validateur_nom=VALIDATEUR,
                    validateur_qualite=QUALITE,
                    publie_le=maintenant,
                )
            )
            connexion.execute(
                question.insert(),
                [
                    {
                        "id": uuid7(),
                        "quiz_id": quiz_id,
                        "enonce": q["enonce"],
                        "choix": q["choix"],
                        "bonne_reponse": q["bonne"],
                        "explication": None,
                        "ordre": rang,
                    }
                    for rang, q in enumerate(entree["questions"], start=1)
                ],
            )

    return True


def _parametres_jeux(connexion: sa.Connection) -> None:
    """Une nouvelle version des paramètres Jeux à 10 questions et 8 bonnes réponses, le reste gardé."""
    en_cours = (
        connexion.execute(
            sa.text("SELECT * FROM parametres_quiz WHERE parcours = 'jeux' ORDER BY version DESC LIMIT 1")
        )
        .mappings()
        .first()
    )
    if en_cours and (en_cours["nb_questions"], en_cours["seuil"]) == (NB_QUESTIONS_JEUX, SEUIL_JEUX):
        return
    valeurs = (
        {k: en_cours[k] for k in ("temps_ms", "tolerance_ms", "tentatives_par_jour", "arret_premiere_erreur")}
        | {"version": en_cours["version"] + 1}
        if en_cours
        else {
            "temps_ms": 15000,
            "tolerance_ms": 2000,
            "tentatives_par_jour": 10,
            "arret_premiere_erreur": False,
            "version": 1,
        }
    )
    connexion.execute(
        sa.text(
            "INSERT INTO parametres_quiz (id, parcours, version, nb_questions, temps_ms, tolerance_ms, seuil, "
            "tentatives_par_jour, arret_premiere_erreur) VALUES (uuidv7(), 'jeux', :version, :nb, :temps_ms, "
            ":tolerance_ms, :seuil, :tentatives_par_jour, :arret_premiere_erreur)"
        ),
        valeurs | {"nb": NB_QUESTIONS_JEUX, "seuil": SEUIL_JEUX},
    )


def _deja_remise_a_zero(connexion: sa.Connection) -> bool:
    return bool(
        connexion.execute(
            sa.text("SELECT 1 FROM mouvement_points WHERE motif = :motif LIMIT 1"), {"motif": MOTIF}
        ).first()
    )


def _remettre_a_zero(connexion: sa.Connection, maintenant: datetime) -> None:
    # L'API encore en service pendant le déploiement attend la fin de la migration : aucun gain, aucune place ni aucun
    # badge ne s'écrit entre l'annulation et l'archivage.
    connexion.execute(
        sa.text(
            "LOCK TABLE mouvement_points, tentative_quiz, place_reussie, badge_obtenu, etoile_obtenue, certificat "
            "IN SHARE ROW EXCLUSIVE MODE"
        )
    )
    # Les parties en cours sur les anciens quiz : closes sans réussite, elles ne rapportent plus rien.
    connexion.execute(
        sa.text(
            "UPDATE tentative_quiz SET etat = 'terminee', reussie = false, terminee_le = :maintenant "
            "WHERE etat = 'en_cours'"
        ),
        {"maintenant": maintenant},
    )
    # Les gains, annulés comme le fait `registre.annuler_ligne` (spec 036) : ligne négative, part du club négative,
    # dans l'année et le semestre du gain. Chaque période revient à zéro, aucune ne devient négative.
    connexion.execute(
        sa.text(
            """
            INSERT INTO mouvement_points (id, utilisateur_id, action, montant, annee_id, semestre_id, cle, annule_id,
                                          motif, club_id, demi_points_club)
            SELECT uuidv7(), m.utilisateur_id, m.action, -m.montant, m.annee_id,
                   m.semestre_id,
                   'annulation:' || m.id, m.id, :motif, m.club_id, -m.demi_points_club
            FROM mouvement_points m
            JOIN bareme b ON b.code = m.action
            WHERE m.annule_id IS NULL AND m.montant > 0
              AND (b.parcours IN ('jeux', 'certification') OR m.action = ANY(:encadreur))
              AND NOT EXISTS (SELECT 1 FROM mouvement_points a WHERE a.annule_id = m.id)
            """
        ),
        {"motif": MOTIF, "encadreur": list(ACTIONS_ENCADREUR)},
    )
    parametres = {"maintenant": maintenant}
    connexion.execute(
        sa.text(
            "INSERT INTO etoile_obtenue_archive (id, utilisateur_id, niveau, mouvement_id, obtenue_le, archive_le) "
            "SELECT id, utilisateur_id, niveau, mouvement_id, obtenue_le, :maintenant FROM etoile_obtenue"
        ),
        parametres,
    )
    connexion.execute(sa.text("DELETE FROM etoile_obtenue"))
    connexion.execute(
        sa.text(
            "INSERT INTO place_reussie_archive (id, utilisateur_id, place, quiz_id, tentative_id, reussie_le, "
            "archive_le) SELECT uuidv7(), utilisateur_id, place, quiz_id, tentative_id, reussie_le, :maintenant "
            "FROM place_reussie"
        ),
        parametres,
    )
    connexion.execute(sa.text("DELETE FROM place_reussie"))
    connexion.execute(
        sa.text(
            "INSERT INTO badge_obtenu_archive (id, utilisateur_id, rang, nom, palier, regles_version, club_id, "
            "mouvement_id, obtenu_le, archive_le) SELECT uuidv7(), utilisateur_id, rang, nom, palier, "
            "regles_version, club_id, mouvement_id, obtenu_le, :maintenant FROM badge_obtenu"
        ),
        parametres,
    )
    connexion.execute(sa.text("DELETE FROM badge_obtenu"))
    connexion.execute(
        sa.text(
            "UPDATE certificat SET etat = 'revoque', motif = :motif, decide_le = :maintenant WHERE etat = 'valide'"
        ),
        {"motif": MOTIF, "maintenant": maintenant},
    )
    connexion.execute(sa.text("UPDATE certificat SET archive_le = :maintenant WHERE archive_le IS NULL"), parametres)


def upgrade() -> None:
    _schema()
    connexion = op.get_bind()
    if not _a_la_banque(connexion):
        print("Spec 049 : base sans les 100 défis d'AIMES-AFRIQUE, ni quiz ni remise à zéro.")
        return
    maintenant = datetime.now(UTC)
    chargee = _remplacer_les_quiz(connexion, maintenant)
    _parametres_jeux(connexion)
    # La remise à zéro ne se fait qu'une fois, avec le chargement : jamais sur des gains de la nouvelle banque.
    if not chargee or _deja_remise_a_zero(connexion):
        print("Spec 049 : la remise à zéro est déjà faite ; elle n'est pas refaite.")
        return
    _remettre_a_zero(connexion, maintenant)
    print("Spec 049 : banque officielle chargée, Jeux et certification remis à zéro.")


def downgrade() -> None:
    connexion = op.get_bind()
    archives = connexion.execute(
        sa.text(
            "SELECT (SELECT count(*) FROM etoile_obtenue_archive) + (SELECT count(*) FROM place_reussie_archive) "
            "+ (SELECT count(*) FROM badge_obtenu_archive) + (SELECT count(*) FROM certificat WHERE archive_le IS NOT NULL)"
        )
    ).scalar_one()
    if archives or _deja_remise_a_zero(connexion):
        raise RuntimeError("La remise à zéro de l'ouverture (spec 049) a été faite : elle ne se défait pas.")
    # Les quiz de la banque officielle jamais joués sont retirés (ils seront rechargés) ; les autres restent,
    # dépubliés, avec leurs parties. Les anciens quiz ne sont pas republiés.
    jamais_joues = "description LIKE :d AND NOT EXISTS (SELECT 1 FROM tentative_quiz t WHERE t.quiz_id = quiz.id)"
    d = {"d": f"{DESCRIPTION}%"}
    connexion.execute(
        sa.text(f"DELETE FROM question_quiz WHERE quiz_id IN (SELECT id FROM quiz WHERE {jamais_joues})"), d
    )
    connexion.execute(sa.text(f"DELETE FROM quiz WHERE {jamais_joues}"), d)
    connexion.execute(
        sa.text(
            "UPDATE quiz SET etat = 'depublie', version = version + 1 WHERE description LIKE :d AND etat = 'publie'"
        ),
        d,
    )
    op.drop_index("uq_certificat_origine", table_name="certificat")
    op.create_index(
        "uq_certificat_origine",
        "certificat",
        ["utilisateur_id"],
        unique=True,
        postgresql_where=sa.text("remplace_id IS NULL"),
    )
    op.drop_column("certificat", "archive_le")
    op.drop_index(op.f("ix_badge_obtenu_archive_utilisateur_id"), table_name="badge_obtenu_archive")
    op.drop_table("badge_obtenu_archive")
    op.drop_index(op.f("ix_place_reussie_archive_utilisateur_id"), table_name="place_reussie_archive")
    op.drop_table("place_reussie_archive")
    op.drop_index(op.f("ix_etoile_obtenue_archive_utilisateur_id"), table_name="etoile_obtenue_archive")
    op.drop_table("etoile_obtenue_archive")
