// Les erreurs de l'API dans la langue de la page (spec 052). L'API répond toujours en français : sur une page en
// anglais ou en allemand, le site traduit les messages qu'il connaît (formulaires publics : connexion, inscription,
// codes et liens), puis, à défaut, les limites (429) et les pannes (5xx, réseau coupé) par leur statut. Un autre
// message reste tel quel, en français, plutôt que rien.
import { LANGUE_DE_BASE, langueCourante } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

const CONNUS: Record<string, () => string> = {
  "Vérifie le formulaire : un champ est vide, trop long ou mal rempli.": m.erreur_saisie,
  "Connexion impossible pour le moment. Réessaie dans quelques instants.": m.erreur_indisponible,
  "Identifiant ou mot de passe incorrect": m.erreur_identifiants,
  "Trop d'essais. Réessaie dans 15 minutes.": m.erreur_trop_essais,
  "Ce compte est suspendu. Contacte un encadreur ou l'équipe nationale.": m.erreur_suspendu,
  "Ce délai est dépassé. Reconnecte-toi.": m.erreur_delai_depasse,
  "Code incorrect.": m.erreur_code_incorrect,
  "Ce lien a expiré ou a déjà servi. Demande un nouveau lien.": m.erreur_lien_expire,
  "Cette action ne peut venir que du site.": m.erreur_origine,
  "Connecte-toi pour continuer.": m.erreur_connecte_toi,
  "Cet établissement n'existe pas ou n'est plus actif : choisis-en un autre.":
    m.erreur_etablissement_inconnu,
  "Cette inspection n'existe pas ou n'est plus active.": m.erreur_inspection_inconnue,
  "Tu es déjà connecté : déconnecte-toi pour créer un compte.": m.erreur_deja_connecte,
  "Trop de tentatives depuis ce réseau. Réessaie dans un moment.": m.erreur_tentatives_reseau,
  "Les inscriptions ne sont pas encore ouvertes.": m.erreur_inscriptions_fermees,
  "Trop d'inscriptions depuis ce réseau. Réessaie dans une heure.": m.erreur_inscriptions_reseau,
  "L'envoi des e-mails est indisponible pour le moment : réessaie un peu plus tard.":
    m.erreur_emails_indisponibles,
  "Ce code est incorrect ou expiré. Vérifie-le, ou demande un nouveau code.": m.erreur_code_expire,
  "Trop de vérifications depuis ce réseau. Réessaie dans 15 minutes.":
    m.erreur_verifications_reseau,
  "Ton pseudonyme doit être différent de ton identifiant : l'identifiant reste secret.":
    m.erreur_pseudo_identifiant,
  "Ton pseudonyme ne doit pas contenir ton prénom et ton nom : ils restent privés.":
    m.erreur_pseudo_nom,
  "Ce pseudonyme est déjà pris.": m.erreur_pseudo_pris,
  "Cet identifiant est déjà pris.": m.erreur_identifiant_pris,
  "Cet identifiant ou cet e-mail est déjà pris.": m.erreur_identifiant_email_pris,
  "Cet identifiant ou cet email est déjà pris.": m.erreur_identifiant_email_pris_2,
  "Cet email est déjà pris.": m.erreur_email_pris,
  "Cet e-mail est déjà utilisé par un autre compte.": m.erreur_email_utilise,
  "Un de ces éléments est déjà pris.": m.erreur_element_pris,
  "Un des axes choisis n'existe pas ou n'est plus proposé : choisis-en un autre.":
    m.erreur_axe_inconnu,
  "Précise ta fonction.": m.erreur_fonction,
  "Tape au moins 2 lettres ou choisis une inspection.": m.erreur_recherche_courte,
  "Le site est en maintenance. Réessaie plus tard.": m.erreur_maintenance,
  "Trop de parties sans compte depuis ce réseau : crée ton compte.": m.erreur_parties_reseau,
  "Les quiz sont réservés aux comptes inscrits.": m.erreur_quiz_inscrits,
  "Ce lien d'invitation n'est plus valide. Demande une nouvelle invitation.":
    m.erreur_invitation_invalide,
  // Une réponse de succès, affichée telle quelle par le formulaire du mot de passe oublié.
  "Si cette adresse correspond à un compte, un lien vient d'y être envoyé.": m.mdp_lien_envoye,
};

/** Un message connu de l'API (erreur ou confirmation) dans la langue de la page, sinon tel quel. */
export const traduireMessageApi = (message: string): string =>
  langueCourante() === LANGUE_DE_BASE ? message : (CONNUS[message]?.() ?? message);

/** Le message d'une erreur de l'API (en français) dans la langue de la page ; `statut` 0 : réseau coupé. */
export function traduireErreur(message: string, statut: number): string {
  if (langueCourante() === LANGUE_DE_BASE) return message;
  const connu = CONNUS[message];
  if (connu) return connu();
  if (statut === 429) return m.erreur_trop_generique();
  if (statut === 0 || statut >= 500) return m.erreur_indisponible();
  return message;
}

// Les messages de validation du site (schémas zod des formulaires publics), écrits en français et traduits à
// l'affichage par `FormMessage` : les schémas, partagés avec les espaces connectés, restent tels quels.
const VALIDATION: Record<string, () => string> = {
  "Ce numéro est trop long.": m.val_numero_long,
  "De 8 à 15 chiffres, avec « + » au début si besoin.": m.val_telephone_format,
  "Indique un numéro de téléphone.": m.val_telephone_requis,
  "Sous la forme 2025-2026.": m.val_annee,
  "Indique ta commune.": m.val_commune,
  "Choisis une réponse.": m.val_choisis_reponse,
  "Indique ta date de naissance.": m.val_naissance,
  "Indique ton lieu de naissance.": m.val_lieu_naissance,
  "Indique le nom de ton parent ou tuteur.": m.val_responsable,
  "Choisis au moins un axe.": m.val_axe_min,
  "Indique l'établissement.": m.val_etablissement,
  "Coche cette case pour t'engager.": m.val_engagement,
  "Précise le réseau.": m.val_reseau,
  "Indique ton prénom.": m.val_prenom,
  "Ce prénom est trop long.": m.val_prenom_long,
  "Indique ton nom.": m.val_nom,
  "Ce nom est trop long.": m.val_nom_long,
  "De 3 à 30 lettres sans accent, chiffres, « . », « - » ou « _ ».": m.val_identifiant_format,
  "Au moins 8 caractères.": m.val_mdp_min,
  "Ce mot de passe est trop long.": m.val_mdp_long,
  "Cet email est trop long.": m.val_email_long,
  "Cet email n'est pas valide.": m.val_email_invalide,
  "Choisis ta classe.": m.val_classe,
  "Tu dois accepter la charte.": m.val_charte,
  "L'accord de ton parent ou tuteur est nécessaire.": m.val_accord_parent,
  "Indique ton email : il sert à te prévenir de la vérification.": m.val_email_encadreur,
  "Indique ton téléphone ou ton WhatsApp.": m.val_telephone_whatsapp,
  "Cette discipline est trop longue.": m.val_discipline_long,
  "Ce nom de commune est trop long.": m.val_commune_long,
  "Choisis ta fonction.": m.val_fonction,
  "Cette précision est trop longue.": m.val_precision_long,
  "Ton accord est nécessaire pour vérifier ton compte.": m.val_accord_verification,
  "Précise ta fonction.": m.erreur_fonction,
  "Indique tes prénoms.": m.val_prenoms,
  "C'est trop long.": m.val_trop_long,
  "Indique ta ville.": m.val_ville,
  "Indique ton adresse e-mail : ton code y sera envoyé.": m.val_email_visiteur,
  "Cette adresse est trop longue.": m.val_adresse_longue,
  "Cette adresse n'est pas valide.": m.val_adresse_invalide,
  "Cette confirmation est nécessaire.": m.val_confirmation,
  "Ton pseudonyme ne contient que des lettres, des chiffres, des espaces, « - » et « . ».":
    m.val_pseudo_caracteres,
  "Ton pseudonyme contient au moins une lettre.": m.val_pseudo_lettre,
  "Ton pseudonyme ne peut pas contenir de numéro de téléphone.": m.val_pseudo_telephone,
  "Choisis ton établissement dans la liste.": m.etab_choisis_liste,
  "Indique ta DRE, ton inspection et le nom de ton établissement.": m.etab_indique_tout,
};

// Les messages qui portent un nombre.
const VALIDATION_AVEC_NOMBRES: [RegExp, (n: string[]) => string][] = [
  [/^(\d+) caractères au plus\.$/, ([max]) => m.val_max_caracteres({ max: max ?? "" })],
  [
    /^Ton pseudonyme fait de (\d+) à (\d+) caractères\.$/,
    ([min, max]) => m.val_pseudo_longueur({ min: min ?? "", max: max ?? "" }),
  ],
  [/^(\d+) axes au plus\.$/, ([max]) => m.val_max_axes({ max: max ?? "" })],
  [
    /^Vérifie la date : un élève a entre (\d+) et (\d+) ans\.$/,
    ([min, max]) => m.val_age({ min: min ?? "", max: max ?? "" }),
  ],
];

/** Un message de validation du site dans la langue de la page ; un message inconnu reste tel quel. */
export function traduireValidation(message: string): string {
  if (langueCourante() === LANGUE_DE_BASE) return message;
  const connu = VALIDATION[message] ?? CONNUS[message];
  if (connu) return connu();
  for (const [motif, traduire] of VALIDATION_AVEC_NOMBRES) {
    const trouve = motif.exec(message);
    if (trouve) return traduire(trouve.slice(1));
  }
  return message;
}
