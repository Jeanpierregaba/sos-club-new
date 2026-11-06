"""Les premières questions du défi du jour (spec 021), à relire par l'équipe nationale avant la prod.

Chargement idempotent, par rang : une question déjà en base n'est ni dupliquée ni modifiée (l'équipe a pu la
corriger ou la désactiver). Appelé par les seeds ; en prod : `uv run python -m app.jeux.banque_initiale`, qui
charge les questions désactivées : rien n'est publié sans validation de l'équipe nationale (docs/RULES.md). Elle
les active une fois relues.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal
from app.jeux.models import DefiQuestion

# (catégorie, question, options, index de la bonne réponse, explication)
QUESTIONS: list[tuple[str, str, list[str], int, str]] = [
    (
        "Maladies & prévention",
        "Quelle est la meilleure façon de se protéger du paludisme la nuit ?",
        ["Dormir sous une moustiquaire imprégnée", "Boire beaucoup d'eau", "Éviter les fruits le soir"],
        0,
        (
            "Le paludisme est transmis par la piqûre d'un moustique qui pique surtout la nuit. La moustiquaire "
            "imprégnée d'insecticide te protège pendant ton sommeil."
        ),
    ),
    (
        "Hygiène",
        "Combien de temps faut-il se laver les mains pour bien les nettoyer ?",
        ["Cinq secondes, à l'eau seulement", "Au moins 20 secondes, avec du savon", "Une seconde, cela suffit"],
        1,
        (
            "Frotter au moins 20 secondes avec du savon, paumes, dos, entre les doigts et sous les ongles, élimine "
            "la plupart des microbes."
        ),
    ),
    (
        "Nutrition",
        "Combien d'eau un adolescent devrait-il boire environ chaque jour ?",
        ["Un demi-litre", "Environ 1,5 à 2 litres", "Cinq litres"],
        1,
        "Environ 1,5 à 2 litres par jour, et davantage quand il fait chaud ou que tu fais du sport.",
    ),
    (
        "Premiers secours",
        "Tu saignes du nez : quel est le bon geste ?",
        ["Pencher la tête en arrière", "Pencher la tête en avant et pincer le nez", "T'allonger sur le dos"],
        1,
        (
            "Tête légèrement en avant, pince le haut des narines une dizaine de minutes. En arrière, le sang coule "
            "dans la gorge."
        ),
    ),
    (
        "Premiers secours",
        "Face à une petite brûlure, que faut-il faire d'abord ?",
        [
            "Mettre du beurre ou de l'huile",
            "La passer sous l'eau tempérée pendant 15 minutes",
            "Percer les cloques",
        ],
        1,
        (
            "C'est la règle des 15 : une eau à 15 °C environ, pendant 15 minutes. Elle refroidit la peau et limite "
            "la brûlure ; le beurre, l'huile ou le dentifrice gardent la chaleur et salissent la plaie."
        ),
    ),
    (
        "Premiers secours",
        "Une personne est inconsciente mais respire. Que fais-tu en attendant les secours ?",
        ["Tu la fais asseoir", "Tu lui donnes à boire", "Tu la mets en position latérale de sécurité"],
        2,
        (
            "Sur le côté, en position latérale de sécurité, ses voies respiratoires restent libres. Ne donne jamais "
            "à boire à une personne inconsciente."
        ),
    ),
    (
        "Santé sexuelle",
        "Lequel de ces gestes ne transmet pas le VIH ?",
        ["Partager une seringue", "Serrer la main ou partager un repas", "Un rapport sexuel sans préservatif"],
        1,
        (
            "Le VIH ne se transmet ni par le contact de la peau, ni par la salive, ni par un repas partagé. Le "
            "rejet des personnes vivant avec le VIH n'a aucune raison d'être."
        ),
    ),
    (
        "Santé sexuelle",
        "Contre quoi le préservatif protège-t-il ?",
        [
            "Seulement contre la grossesse",
            "Contre la grossesse et la plupart des infections sexuellement transmissibles",
            "Contre rien du tout",
        ],
        1,
        (
            "Bien utilisé, le préservatif protège à la fois d'une grossesse non désirée et de la plupart des IST, "
            "dont le VIH."
        ),
    ),
    (
        "Maladies & prévention",
        "Comment attrape-t-on le choléra ?",
        ["En buvant de l'eau ou en mangeant des aliments contaminés", "Par une piqûre de moustique", "En ayant froid"],
        0,
        "Le choléra vient d'une eau ou d'aliments souillés. Boire une eau sûre et se laver les mains protège.",
    ),
    (
        "Hygiène",
        "Pour garder des dents saines, il faut les brosser…",
        ["Une fois par semaine", "Seulement après les bonbons", "Deux fois par jour, pendant deux minutes"],
        2,
        ("Matin et soir, deux minutes, avec un dentifrice au fluor : c'est la meilleure protection contre les caries."),
    ),
    (
        "Bien-être",
        "Combien d'heures de sommeil par nuit conseille-t-on à un adolescent ?",
        ["4 à 5 heures", "8 à 10 heures", "14 heures"],
        1,
        "Entre 8 et 10 heures : le sommeil aide ta mémoire, ta concentration et ta croissance.",
    ),
    (
        "Nutrition",
        "Combien de portions de fruits et légumes est-il conseillé de manger ?",
        ["Au moins cinq portions par jour", "Une portion par semaine", "Seulement le week-end"],
        0,
        (
            "Au moins cinq portions par jour apportent les vitamines, les minéraux et les fibres dont ton corps a "
            "besoin."
        ),
    ),
    (
        "Sport & santé",
        "Combien de temps d'activité physique est recommandé à un adolescent ?",
        ["10 minutes par semaine", "Au moins 60 minutes par jour", "Seulement pendant les vacances"],
        1,
        "Au moins une heure par jour : marche rapide, football, danse… tout mouvement compte.",
    ),
    (
        "Santé mentale",
        "Tu te sens stressé ou triste depuis un moment. Quelle est la meilleure idée ?",
        ["Tout garder pour toi", "T'isoler des autres", "En parler à une personne de confiance"],
        2,
        (
            "Parler à un parent, un enseignant, un ami ou un agent de santé aide à aller mieux. Demander de l'aide "
            "est une force."
        ),
    ),
    (
        "Maladies & prévention",
        "À quoi sert un vaccin ?",
        [
            "À guérir une maladie déjà là",
            "À apprendre au corps à se défendre contre une maladie",
            "À remplacer un repas",
        ],
        1,
        (
            "Le vaccin entraîne ton système immunitaire à reconnaître un microbe, pour te protéger avant que tu "
            "tombes malade."
        ),
    ),
    (
        "Environnement",
        "Brûler les déchets en plastique, c'est…",
        ["Sans danger", "Dangereux : la fumée est toxique", "Bon pour le sol"],
        1,
        (
            "La fumée du plastique brûlé contient des substances toxiques pour les poumons. Mieux vaut trier et "
            "faire ramasser les déchets."
        ),
    ),
    (
        "Environnement",
        "Pourquoi vider les eaux stagnantes autour de la maison ?",
        ["Les moustiques y pondent leurs œufs", "Pour économiser l'eau", "Pour éloigner les fourmis"],
        0,
        (
            "Pots, pneus, boîtes, flaques : une eau qui stagne devient un nid de moustiques. La vider réduit le "
            "risque de paludisme et de dengue."
        ),
    ),
    (
        "Nutrition",
        "Boire beaucoup de sodas augmente surtout le risque de…",
        ["Caries et surpoids", "Mieux dormir", "Grandir plus vite"],
        0,
        "Les sodas contiennent beaucoup de sucre. L'eau reste la meilleure boisson.",
    ),
    (
        "Addictions",
        "Le tabac abîme surtout…",
        ["Les poumons et le cœur", "Seulement les cheveux", "Rien, si l'on commence jeune"],
        0,
        (
            "Le tabac attaque les poumons, le cœur et les vaisseaux. Plus on commence tôt, plus il est difficile "
            "d'arrêter."
        ),
    ),
    (
        "Addictions",
        "Pourquoi l'alcool est-il particulièrement dangereux pour un adolescent ?",
        ["Il fait grandir", "Son cerveau est encore en développement", "Il remplace l'eau"],
        1,
        "Le cerveau se développe jusqu'à environ 25 ans : l'alcool le fragilise et favorise la dépendance.",
    ),
    (
        "Maladies & prévention",
        "Une forte fièvre peut être un signe de paludisme. Que faire ?",
        ["Attendre une semaine", "Aller vite au centre de santé pour un test", "Prendre n'importe quel médicament"],
        1,
        "Seul un test dit s'il s'agit du paludisme. Soigné tôt, il guérit ; attendre peut être grave.",
    ),
    (
        "Premiers secours",
        "Une plaie saigne beaucoup. Quel est le premier geste ?",
        [
            "Appuyer fortement sur la plaie avec un tissu propre",
            "Mettre de la terre dessus",
            "Attendre que cela s'arrête",
        ],
        0,
        "Appuie fort et sans relâcher avec un tissu propre, puis fais appeler les secours.",
    ),
    (
        "Santé sexuelle",
        "Les règles, c'est…",
        ["Une maladie", "Un phénomène naturel du corps", "Un signe de faiblesse"],
        1,
        ("Les règles font partie de la puberté. Elles n'ont rien de honteux et n'empêchent pas d'aller à l'école."),
    ),
    (
        "Valeurs & respect",
        "Dans une relation, le consentement signifie…",
        ["Dire oui librement, et pouvoir changer d'avis", "Céder sous la pression", "Ne rien dire"],
        0,
        "Le consentement est libre, clair et peut être retiré à tout moment. Le silence n'est pas un oui.",
    ),
    (
        "Valeurs & respect",
        "Un camarade se fait harceler. Que peux-tu faire ?",
        ["Rire avec les autres", "En parler à un adulte de confiance", "Partager les vidéos"],
        1,
        "Ne reste pas spectateur : soutiens ton camarade et préviens un adulte de confiance.",
    ),
    (
        "Bien-être",
        "Regarder un écran juste avant de dormir…",
        ["Aide à s'endormir", "Retarde l'endormissement", "N'a aucun effet"],
        1,
        "La lumière des écrans trompe ton horloge interne. Pose le téléphone un peu avant de dormir.",
    ),
    (
        "Hygiène",
        "Pour rendre une eau plus sûre à boire, tu peux…",
        ["La faire bouillir", "Y ajouter du sucre", "La laisser une heure au soleil"],
        0,
        (
            "Faire bouillir l'eau quelques minutes tue la plupart des microbes. Au soleil, il faut au moins 6 heures "
            "dans une bouteille transparente : une heure ne suffit pas. Garde-la ensuite dans un récipient propre."
        ),
    ),
    (
        "Environnement",
        "Planter des arbres autour de l'école aide à…",
        ["Rafraîchir l'air et donner de l'ombre", "Attirer les moustiques", "Rien du tout"],
        0,
        "Les arbres font de l'ombre, rafraîchissent l'air et protègent le sol.",
    ),
    (
        "Maladies & prévention",
        "Une toux qui dure plus de deux semaines doit…",
        ["Être ignorée", "Faire consulter un agent de santé", "Se soigner avec du sucre"],
        1,
        "Une toux qui dure peut être le signe d'une maladie comme la tuberculose, qui se soigne : consulte.",
    ),
    (
        "Nutrition",
        "Prendre un petit-déjeuner aide surtout à…",
        ["Mieux te concentrer en classe", "Dormir en classe", "Sauter le déjeuner"],
        0,
        "Après la nuit, ton corps et ton cerveau ont besoin d'énergie pour bien démarrer la journée.",
    ),
]


async def charger(db: AsyncSession, *, actives: bool = True) -> int:
    """Ajoute les questions absentes (par rang) ; renvoie le nombre de questions ajoutées. `actives=False` : à
    relire avant d'être tirées."""
    presents = set((await db.scalars(select(DefiQuestion.ordre))).all())
    ajoutees = 0
    for ordre, (categorie, question, options, bonne, explication) in enumerate(QUESTIONS, start=1):
        if ordre in presents:
            continue
        db.add(
            DefiQuestion(
                ordre=ordre,
                categorie=categorie,
                question=question,
                options=options,
                bonne_reponse=bonne,
                explication=explication,
                actif=actives,
            )
        )
        ajoutees += 1
    await db.flush()
    return ajoutees


async def _main() -> None:
    # En prod, les questions attendent la relecture de l'équipe nationale avant d'être tirées.
    actives = settings.environnement != "prod"
    async with SessionLocal() as db:
        ajoutees = await charger(db, actives=actives)
        await db.commit()
    etat = "actives" if actives else "désactivées, à relire puis activer"
    print(f"{ajoutees} question(s) ajoutée(s) à la banque des défis ({etat}).")


if __name__ == "__main__":
    asyncio.run(_main())
