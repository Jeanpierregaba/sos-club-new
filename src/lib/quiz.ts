// Catalogue des 100 quiz de gamification, repris du parcours officiel publié par la coordination nationale.
// Chaque quiz compte 10 questions tirées du référentiel des 922 QCM. Le nombre qui suit chaque titre est la
// cotation du parcours officiel : il ne sert plus qu'à classer le niveau. Tout quiz réussi rapporte le même
// barème (spec 022, `src/lib/bareme.ts`).
// Les questions elles-mêmes restent côté API : le serveur seul arbitre les quiz (ADR-0004).

export type Niveau = "Débutant" | "Intermédiaire" | "Avancé" | "Championnat";

export const niveauDe = (cotation: number): Niveau =>
  cotation <= 50
    ? "Débutant"
    : cotation <= 65
      ? "Intermédiaire"
      : cotation <= 75
        ? "Avancé"
        : "Championnat";

export type Pole = {
  id: string;
  nom: string;
  sur: string;
  d: string;
  themes: string[];
  couleur: string;
  quiz: [titre: string, cotation: number][];
};

export const poles: Pole[] = [
  {
    id: "aimes-afrique",
    nom: "AIMES-AFRIQUE & SOS Docteur TV",
    sur: "Histoire & média santé",
    d: "La genèse humanitaire et la 1re chaîne 100 % santé d’Afrique.",
    themes: ["ONG AIMES-AFRIQUE", "Dr Michel Kodom", "SOS Docteur TV", "Missions foraines"],
    couleur: "var(--logo-blue)",
    quiz: [
      ["Histoire & fondation d’AIMES-AFRIQUE", 50],
      ["Dr Michel Kodom : parcours & valeurs", 50],
      ["SOS Docteur TV : 1re télévision 100 % santé", 50],
      ["Missions médico-chirurgicales foraines gratuites", 60],
      ["Cliniques mobiles & blocs opératoires ruraux", 60],
      ["Mutuelle de santé des artisans & économie sociale", 60],
      ["Les 10 villages pilotes et cantons d’intervention", 65],
      ["Rayonnement panafricain & partenariats internationaux", 70],
    ],
  },
  {
    id: "genie-imhotep",
    nom: "Championnat national Génie Imhotep",
    sur: "Compétition & citoyenneté",
    d: "Épreuves au buzzer, questions de rapidité, culture médicale et esprit d’équipe : les règles du jeu, les valeurs civiques et l’excellence scolaire.",
    themes: [
      "Buzzer & rapidité",
      "Clubs Santé scolaires",
      "Fair-play & civisme",
      "Podium national",
    ],
    couleur: "var(--sky)",
    quiz: [
      ["Origine & charte des Clubs Santé scolaires", 50],
      ["Le championnat télévisé Génie Imhotep", 60],
      ["Rôle du capitaine de club & sentinelles de santé", 60],
      ["Les épreuves au buzzer & vitesse de réaction", 65],
      ["Fair-play, éthique & esprit d’équipe", 50],
      ["Boîtes à idées & initiatives écologiques scolaires", 60],
      ["Le journal mural & sensibilisation par les pairs", 65],
      ["Le grand podium national & titre d’ambassadeur or", 80],
    ],
  },
  {
    id: "hygiene",
    nom: "Santé, hygiène & nutrition locale",
    sur: "Gestes du quotidien & hygiène",
    d: "20 quiz pour ancrer les réflexes de prévention : hygiène bucco-dentaire, eau potable, nutrition locale équilibrée et sommeil réparateur.",
    themes: [
      "Lavage des mains",
      "Eau potable & SRO",
      "Nutrition togolaise",
      "Hygiène bucco-dentaire",
    ],
    couleur: "var(--primary)",
    quiz: [
      ["Les 7 étapes du lavage des mains à l’eau et au savon", 50],
      ["Eau potable, désinfection & conservation saine", 60],
      ["Diarrhées aiguës & solution de réhydratation orale (SRO)", 50],
      ["Hygiène bucco-dentaire : dents saines & brossage", 50],
      ["Protection contre les caries & visites dentaires", 60],
      ["Nutrition équilibrée : les 3 familles d’aliments", 50],
      ["Trésors nutritifs locaux : moringa, niébé & fonio", 60],
      ["Carence en fer & prévention de l’anémie nutritionnelle", 65],
      ["Risques des boissons gazeuses, sucres rapides & sodas", 60],
      ["Hygiène corporelle & prévention de la gale scolaire", 50],
      ["Sommeil réparateur, rythme circadien & écrans", 50],
      ["Posture scolaire, port du sac à dos & santé du dos", 60],
      ["Santé visuelle : fatigue oculaire & éclairage scolaire", 60],
      ["Intoxications alimentaires & conservation des plats", 65],
      ["Vente d’aliments en milieu scolaire & salubrité", 60],
      ["Bienfaits de l’activité physique & marche active", 50],
      ["Hydratation corporelle & besoins quotidiens en eau", 50],
      ["Prévention du choléra & épidémies hydriques", 70],
      ["Santé mentale : gestion du stress & examens", 65],
      ["Hygiène vestimentaire & séchage efficace au soleil", 50],
    ],
  },
  {
    id: "evss",
    nom: "Santé sexuelle & reproductive (EVSS)",
    sur: "Droits, genre & bien-être",
    d: "30 quiz sans tabou pour comprendre son corps, prévenir les grossesses précoces en milieu scolaire, dire NON aux violences et développer l’estime de soi.",
    themes: ["Puberté", "Hygiène menstruelle", "Prévention IST/VIH", "Consentement & droits"],
    couleur: "var(--rose)",
    quiz: [
      ["La puberté chez la fille : transformations & rythmes", 50],
      ["La puberté chez le garçon : voix & spermatogenèse", 50],
      ["Anatomie de l’appareil reproducteur féminin", 60],
      ["Anatomie de l’appareil reproducteur masculin", 60],
      ["Le cycle menstruel & le calcul de l’ovulation", 65],
      ["Gestion de l’hygiène menstruelle en milieu scolaire", 50],
      ["Démystification des tabous autour des menstruations", 50],
      ["Fécondation, nidation & développement de la grossesse", 60],
      ["Prévention des grossesses précoces en milieu scolaire", 65],
      ["Conséquences scolaires & sanitaires des grossesses précoces", 65],
      ["Le consentement éclairé & le respect de son corps", 50],
      ["Assertivité : compétences psychosociales pour dire NON", 60],
      ["Violences basées sur le genre (VBG) en milieu scolaire", 65],
      ["Cadre juridique : le Code de l’enfant togolais", 70],
      ["VIH/sida : modes de transmission & précautions", 60],
      ["Le test de diagnostic rapide (TDR) & dépistage anonyme", 50],
      ["Traitement post-exposition (TPE) dans les 72 heures", 65],
      ["Vérités & mythes sur la transmission du VIH", 50],
      ["Les infections sexuellement transmissibles (IST) bactériennes", 60],
      ["Les IST virales : hépatite B, herpès & papillomavirus", 65],
      ["Le préservatif masculin et féminin : mode d’emploi", 60],
      ["Non-discrimination des personnes vivant avec le VIH", 50],
      ["Communication parents-enfants sur la santé sexuelle", 50],
      ["Mutilations génitales féminines : dangers & lois", 70],
      ["Mariages d’enfants & mariages forcés : conséquences", 65],
      ["Estime de soi & préservation de son avenir", 50],
      ["Harcèlement en milieu scolaire & cyberharcèlement", 60],
      ["Numéros verts & centres d’écoute au Togo", 50],
      ["Égalité filles-garçons & coopération scolaire", 50],
      ["Construire son projet de vie professionnel & personnel", 60],
    ],
  },
  {
    id: "journees-mondiales",
    nom: "Journées mondiales & environnement",
    sur: "Maladies & calendrier de santé",
    d: "20 quiz consacrés aux dates phares de la santé mondiale, à la drépanocytose, au paludisme, au don de sang bénévole et à l’éco-jogging scolaire.",
    themes: [
      "Calendrier OMS & ONU",
      "Lutte antipaludique",
      "Drépanocytose & HTA",
      "1 élève, 1 arbre",
    ],
    couleur: "var(--tangerine)",
    quiz: [
      ["Le calendrier OMS des Journées mondiales de la santé", 50],
      ["24 mars : Journée mondiale de lutte contre la tuberculose", 60],
      ["7 avril : Journée mondiale de la santé & rôle de l’OMS", 50],
      ["25 avril : Journée mondiale du paludisme", 50],
      ["Moustique anophèle, gîtes larvaires & moustiquaires imprégnées", 60],
      ["31 mai : Journée mondiale sans tabac & sevrage", 60],
      ["14 juin : Journée mondiale du donneur de sang bénévole", 50],
      ["Groupes sanguins, rhésus & don de sang", 65],
      ["19 juin : Journée mondiale de la drépanocytose", 65],
      ["Drépanocytose : électrophorèse de l’hémoglobine (AA, AS, SS)", 70],
      ["28 juillet : Journée mondiale contre les hépatites virales", 65],
      ["Octobre rose : prévention & dépistage du cancer du sein", 65],
      ["Novembre bleu : dépistage précoce du cancer de la prostate", 65],
      ["14 novembre : Journée mondiale du diabète", 65],
      ["1er décembre : Journée mondiale de lutte contre le sida", 50],
      ["Hypertension artérielle : dépistage & mesure de la tension", 65],
      ["Maladies tropicales négligées (MTN) au Togo", 70],
      ["Santé environnementale : projet « 1 élève, 1 arbre »", 50],
      ["Éco-jogging & lutte contre la pollution plastique", 50],
      ["Changement climatique & santé des populations", 65],
    ],
  },
  {
    id: "secourisme",
    nom: "Secourisme & santé publique pratique",
    sur: "Réflexes d’urgence & vaccination",
    d: "14 quiz pratiques sur les gestes vitaux face aux malaises, blessures et accidents, et sur le calendrier vaccinal togolais.",
    themes: [
      "Position latérale de sécurité",
      "Étouffement & brûlures",
      "Appel au 118",
      "Calendrier vaccinal",
    ],
    couleur: "var(--logo-red)",
    quiz: [
      ["La règle d’or du secourisme : protéger, alerter, secourir", 50],
      ["L’appel des sapeurs-pompiers : le numéro d’urgence 118", 50],
      ["La position latérale de sécurité (PLS) pas à pas", 65],
      ["Étouffement & manœuvre de Heimlich chez l’adulte", 65],
      ["Hémorragies externes & compression directe efficace", 65],
      ["Brûlures thermiques & règle des 15 (eau fraîche)", 50],
      ["Malaise & perte de connaissance : réflexes immédiats", 60],
      ["Traumatismes : entorses, fractures & pas d’automédication", 60],
      ["Morsures de serpents : gestes qui sauvent & interdictions", 70],
      ["Prévention des noyades & sécurité aux points d’eau", 50],
      ["Calendrier vaccinal du PEV au Togo & vaccins vitaux", 65],
      ["La trousse d’urgence du Club Santé dans l’établissement", 50],
      ["Pyramide sanitaire togolaise : USP, CHP, CHR, CHU", 75],
      ["Grand défi ultime des 100 quiz : champion Génie Imhotep", 100],
    ],
  },
];
