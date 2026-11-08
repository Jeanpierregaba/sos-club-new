import { createIsomorphicFn } from "@tanstack/react-start";
import { getRequestHeader } from "@tanstack/react-start/server";

import type { components } from "./schema.gen";

type Schemas = components["schemas"];
export type Moi = Schemas["Moi"];
export type EtapeCode = Schemas["EtapeCode"];
export type AdminMoi = Schemas["AdminMoi"];
export type Catalogue = Schemas["Catalogue"];
export type Droit = Schemas["Droit"];
export type TableauDeBord = Schemas["TableauDeBord"];
export type CollaborateurResume = Schemas["CollaborateurResume"];
export type CollaborateurDetail = Schemas["CollaborateurDetail"];
export type InvitationEntree = Schemas["InvitationEntree"];
export type InvitationCree = Schemas["InvitationCree"];
export type DroitsEntree = Schemas["DroitsEntree"];
export type ActivationInfo = Schemas["ActivationInfo"];
export type Enrolement = Schemas["Enrolement"];
export type PageInscrits = Schemas["PageInscrits"];
export type InscritDetail = Schemas["InscritDetail"];
export type EvenementJournal = Schemas["EvenementJournal"];
export type PageJournal = Schemas["PageJournal"];
export type ExportEntree = Schemas["ExportEntree"];
export type ExportResume = Schemas["ExportResume"];
export type ExportCree = Schemas["ExportCree"];
export type Apercu = Schemas["Apercu"];
export type DrePublique = Schemas["DrePublique"];
export type DreAnnuaire = Schemas["DreAnnuaire"];
export type EtablissementTrouve = Schemas["EtablissementTrouve"];
export type TypeEtablissement = Schemas["TypeEtablissement"];
export type StatutEtablissement = Schemas["StatutEtablissement"];
export type AxePublic = Schemas["AxePublic"];
export type DreAdmin = Schemas["DreAdmin"];
export type IesgAdmin = Schemas["IesgAdmin"];
export type EtablissementAdmin = Schemas["EtablissementAdmin"];
export type PageEtablissements = Schemas["PageEtablissements"];
export type AxeAdmin = Schemas["AxeAdmin"];
export type DreCreation = Schemas["DreCreation"];
export type DreModification = Schemas["DreModification"];
export type IesgCreation = Schemas["IesgCreation"];
export type IesgModification = Schemas["IesgModification"];
export type EtablissementCreation = Schemas["EtablissementCreation"];
export type EtablissementModification = Schemas["EtablissementModification"];
export type AxeCreation = Schemas["AxeCreation"];
export type AxeModification = Schemas["AxeModification"];
export type Remplacement = Schemas["Remplacement"];
export type EtatInscription = Schemas["EtatInscription"];
export type InscriptionEntree = Schemas["InscriptionEntree"];
export type Classe = Schemas["Classe"];
export type EspaceEleve = Schemas["EspaceEleve"];
export type ProfilModification = Schemas["ProfilModification"];
export type ResumePoints = Schemas["ResumePoints"];
export type ProfilEleveAdmin = Schemas["ProfilEleveAdmin"];
export type SemestreAdmin = Schemas["SemestreAdmin"];
export type SemestreCreation = Schemas["SemestreCreation"];
export type SemestreModification = Schemas["SemestreModification"];
export type LigneBaremeAdmin = Schemas["LigneBaremeAdmin"];
export type LigneBaremeModification = Schemas["LigneBaremeModification"];
export type InscriptionEncadreur = Schemas["InscriptionEncadreur"];
export type EspaceEncadreur = Schemas["EspaceEncadreur"];
export type ProfilEncadreurModification = Schemas["ProfilEncadreurModification"];
export type Fonction = Schemas["Fonction"];
export type EtatVerification = Schemas["EtatVerification"];
export type DemandeEncadreur = Schemas["DemandeEncadreur"];
export type FileEncadreurs = Schemas["FileEncadreurs"];
export type ProfilEncadreurAdmin = Schemas["ProfilEncadreurAdmin"];
export type ClubPublic = Schemas["ClubPublic"];
export type ClubFiche = Schemas["ClubFiche"];
export type ClubResume = Schemas["ClubResume"];
export type MonClub = Schemas["MonClub"];
export type DemandeClub = Schemas["DemandeClub"];
export type DemandeClubEntree = Schemas["DemandeClubEntree"];
export type EncadreurAssocie = Schemas["EncadreurAssocie"];
export type FileClubs = Schemas["FileClubs"];
export type FilePassations = Schemas["FilePassations"];
export type Passation = Schemas["Passation"];
export type PassationApercu = Schemas["PassationApercu"];
export type PassationEntree = Schemas["PassationEntree"];
export type EtatClub = Schemas["EtatClub"];
export type ClubInscrit = Schemas["ClubInscrit"];
export type EtablissementRattache = Schemas["EtablissementRattache"];
export type AdhesionResume = Schemas["AdhesionResume"];
export type DemandeAdhesion = Schemas["DemandeAdhesion"];
export type MembreClub = Schemas["MembreClub"];
export type EncadreurDuClub = Schemas["EncadreurDuClub"];
export type MembresDuClub = Schemas["MembresDuClub"];
export type RattachementResume = Schemas["RattachementResume"];
export type DemandeRattachement = Schemas["DemandeRattachement"];
export type MesClubs = Schemas["MesClubs"];
export type PassationAConfirmer = Schemas["PassationAConfirmer"];
export type AffiliationAValider = Schemas["AffiliationAValider"];
export type RattachementAValider = Schemas["RattachementAValider"];
export type FileAffiliations = Schemas["FileAffiliations"];
export type FileRattachements = Schemas["FileRattachements"];
export type ResultatLot = Schemas["ResultatLot"];
export type ElementLot = Schemas["ElementLot"];
export type QuestionnaireQuelAxe = Schemas["QuestionnaireQuelAxe"];
export type QuestionQuelAxe = Schemas["QuestionQuelAxe"];
export type ResultatQuelAxe = Schemas["ResultatQuelAxe"];
export type CodeAxe = ResultatQuelAxe["principal"];
export type DefiDuJour = Schemas["DefiDuJour"];
export type CorrectionDefi = Schemas["CorrectionDefi"];
export type ClubPodium = Schemas["ClubPodium"];
export type ChampsArticle = Schemas["ChampsArticle"];
export type ArticleEcriture = Schemas["ArticleEcriture"];
export type ArticleAuteur = Schemas["ArticleAuteur"];
export type ResumeArticleAuteur = Schemas["ResumeArticleAuteur"];
export type MesArticles = Schemas["MesArticles"];
export type EtatContenu = Schemas["EtatContenu"];
export type TypeDecision = Schemas["TypeDecision"];
export type ArticlePublic = Schemas["ArticlePublic"];
export type ResumeArticle = Schemas["ResumeArticle"];
export type ArticlesPublics = Schemas["ArticlesPublics"];
export type Signature = Schemas["Signature"];
export type FileModeration = Schemas["FileModeration"];
export type ElementFile = Schemas["ElementFile"];
export type ApercuModeration = Schemas["ApercuModeration"];
export type NotificationSortie = Schemas["NotificationSortie"];
export type Notifications = Schemas["Notifications"];
export type PhotoAuteur = Schemas["PhotoAuteur"];
export type PhotoPublique = Schemas["PhotoPublique"];
export type PhotoModeration = Schemas["PhotoModeration"];
export type CommentaireAuteur = Schemas["CommentaireAuteur"];
export type MesCommentaires = Schemas["MesCommentaires"];
export type CommentairePublic = Schemas["CommentairePublic"];
export type CommentairesPublics = Schemas["CommentairesPublics"];

export const MESSAGE_SAISIE = "Vérifie le formulaire : un champ est vide, trop long ou mal rempli.";

export const MESSAGE_INDISPONIBLE =
  "Connexion impossible pour le moment. Réessaie dans quelques instants.";

export class ErreurApi extends Error {
  constructor(
    readonly statut: number,
    message: string,
  ) {
    super(message);
    this.name = "ErreurApi";
  }
}

// Dans le navigateur, /api passe par le domaine du site (ADR-0006). Pendant le rendu serveur, le site
// appelle l'API directement et lui transmet le cookie reçu du navigateur.
const envoyer = createIsomorphicFn()
  .server((chemin: string, init: RequestInit) => {
    const base = process.env["API_URL_INTERNE"] || "http://127.0.0.1:8000";
    const cookie = getRequestHeader("cookie");
    return fetch(`${base}${chemin}`, {
      ...init,
      headers: { ...init.headers, ...(cookie ? { cookie } : {}) },
      signal: AbortSignal.timeout(5000),
    });
  })
  .client((chemin: string, init: RequestInit) =>
    fetch(chemin, { ...init, signal: AbortSignal.timeout(15000) }),
  );

async function requeteApi<T>(chemin: string, init: RequestInit = {}): Promise<T> {
  let reponse: Response;
  try {
    reponse = await envoyer(chemin, init);
  } catch {
    throw new ErreurApi(0, MESSAGE_INDISPONIBLE);
  }
  if (reponse.status === 204) return undefined as T;

  const corps: unknown = await reponse.json().catch(() => null);
  if (!reponse.ok) {
    const detail = (corps as { detail?: unknown } | null)?.detail;
    // Un refus de validation (422) détaille les champs dans une liste, sans les valeurs saisies.
    const message =
      typeof detail === "string"
        ? detail
        : reponse.status === 422
          ? MESSAGE_SAISIE
          : MESSAGE_INDISPONIBLE;
    throw new ErreurApi(reponse.status, message);
  }
  return corps as T;
}

// Renvoie null pour un visiteur. Une API en panne reste une erreur : ce n'est pas la même chose.
export async function chargerMoi(): Promise<Moi | null> {
  try {
    return await requeteApi<Moi>("/api/comptes/moi");
  } catch (erreur) {
    if (erreur instanceof ErreurApi && erreur.statut === 401) return null;
    throw erreur;
  }
}

function envoyerJson<T>(chemin: string, corps?: unknown, method = "POST"): Promise<T> {
  return requeteApi<T>(chemin, {
    method,
    headers: { "Content-Type": "application/json" },
    body: corps === undefined ? null : JSON.stringify(corps),
  });
}

// Les paramètres vides sont omis : l'API garde alors sa valeur par défaut.
function avecParametres(
  chemin: string,
  parametres: Record<string, string | number | null | undefined>,
) {
  const recherche = new URLSearchParams();
  for (const [cle, valeur] of Object.entries(parametres)) {
    if (valeur !== undefined && valeur !== null && valeur !== "")
      recherche.set(cle, String(valeur));
  }
  const texte = recherche.toString();
  return texte ? `${chemin}?${texte}` : chemin;
}

// Si la double authentification est active, la réponse est une étape « code » et aucune session n'est ouverte.
export function connecter(identifiant: string, motDePasse: string): Promise<Moi | EtapeCode> {
  return envoyerJson<Moi | EtapeCode>("/api/comptes/connexion", {
    identifiant,
    mot_de_passe: motDePasse,
  });
}

export function connecterAvecCode(jeton: string, code: string): Promise<Moi> {
  return envoyerJson<Moi>("/api/comptes/connexion/code", { jeton, code });
}

export function deconnecter(): Promise<void> {
  return requeteApi<void>("/api/comptes/deconnexion", { method: "POST" });
}

// Espace administrateur (spec 015) -----------------------------------------------------------------------

export const chargerAdminMoi = () => requeteApi<AdminMoi>("/api/admin/moi");
export const chargerCatalogue = () => requeteApi<Catalogue>("/api/admin/catalogue");
export const chargerTableauDeBord = () => requeteApi<TableauDeBord>("/api/admin/tableau-de-bord");

export const commencerEnrolement = () =>
  envoyerJson<Enrolement>("/api/admin/double-auth/enrolement");
export const confirmerEnrolement = (code: string) =>
  envoyerJson<{ codes: string[] }>("/api/admin/double-auth/confirmer", { code });
export const regenererCodesSecours = (code: string) =>
  envoyerJson<{ codes: string[] }>("/api/admin/double-auth/codes-secours", { code });

export const listerCollaborateurs = (filtres: Record<string, string | undefined> = {}) =>
  requeteApi<CollaborateurResume[]>(avecParametres("/api/admin/collaborateurs", filtres));
export const chargerCollaborateur = (id: string) =>
  requeteApi<CollaborateurDetail>(`/api/admin/collaborateurs/${id}`);
export const inviterCollaborateur = (entree: InvitationEntree) =>
  envoyerJson<InvitationCree>("/api/admin/collaborateurs", entree);
export const renvoyerInvitation = (id: string) =>
  envoyerJson<InvitationCree>(`/api/admin/collaborateurs/${id}/invitation`);
export const modifierDroits = (id: string, entree: DroitsEntree) =>
  envoyerJson<CollaborateurDetail>(`/api/admin/collaborateurs/${id}/permissions`, entree, "PUT");
export const changerStatutCollaborateur = (
  id: string,
  action: "suspendre" | "reactiver" | "revoquer",
  motif: string,
) => envoyerJson<CollaborateurDetail>(`/api/admin/collaborateurs/${id}/${action}`, { motif });
export const reinitialiserDoubleAuth = (id: string, motif: string) =>
  envoyerJson<CollaborateurDetail>(`/api/admin/collaborateurs/${id}/double-auth/reinitialiser`, {
    motif,
  });
export const annulerInvitation = (id: string, motif: string) =>
  envoyerJson<CollaborateurDetail>(`/api/admin/collaborateurs/${id}/invitation/annuler`, { motif });
export const marquerRevu = (id: string) =>
  envoyerJson<CollaborateurDetail>(`/api/admin/collaborateurs/${id}/revue`);

// Le jeton voyage dans le corps de la requête : dans l'adresse, il finirait dans les journaux d'accès.
export const voirInvitation = (jeton: string) =>
  envoyerJson<ActivationInfo>("/api/activation/info", { jeton });
export const activerInvitation = (jeton: string, identifiant: string, motDePasse: string) =>
  envoyerJson<Moi>("/api/activation", { jeton, identifiant, mot_de_passe: motDePasse });

export const listerInscrits = (filtres: Record<string, string | number | undefined>) =>
  requeteApi<PageInscrits>(avecParametres("/api/admin/inscrits", filtres));
export const chargerInscrit = (id: string) =>
  requeteApi<InscritDetail>(`/api/admin/inscrits/${id}`);
export const changerStatutInscrit = (
  id: string,
  action: "suspendre" | "reactiver",
  motif: string,
) => envoyerJson<InscritDetail>(`/api/admin/inscrits/${id}/${action}`, { motif });

export const apercuExport = (entree: ExportEntree) =>
  envoyerJson<Apercu>("/api/admin/exports/apercu", entree);
export const creerExport = (entree: ExportEntree) =>
  envoyerJson<ExportCree>("/api/admin/exports", entree);
export const historiqueExports = () => requeteApi<ExportResume[]>("/api/admin/exports");

export const imposerPseudonyme = (id: string, pseudonyme: string, motif: string) =>
  envoyerJson<InscritDetail>(`/api/admin/inscrits/${id}/pseudonyme`, { pseudonyme, motif });
export const reinitialiserMotDePasse = (id: string, motif: string) =>
  envoyerJson<{ mot_de_passe: string }>(`/api/admin/inscrits/${id}/mot-de-passe`, { motif });

export const chargerJournal = (filtres: Record<string, string | number | undefined>) =>
  requeteApi<PageJournal>(avecParametres("/api/admin/journal", filtres));

// Référentiel (spec 016) ----------------------------------------------------------------------------------

export const chargerDre = () => requeteApi<DrePublique[]>("/api/referentiel/dre");
export const chargerAnnuaire = () => requeteApi<DreAnnuaire[]>("/api/referentiel/annuaire");
export const chercherEtablissements = (filtres: {
  recherche?: string;
  iesg?: string;
  dre?: string;
}) => requeteApi<EtablissementTrouve[]>(avecParametres("/api/referentiel/etablissements", filtres));
export const chargerAxes = () => requeteApi<AxePublic[]>("/api/referentiel/axes");

const REFERENTIEL = "/api/admin/referentiel";
export const adminListerDre = () => requeteApi<DreAdmin[]>(`${REFERENTIEL}/dre`);
export const adminCreerDre = (entree: DreCreation) =>
  envoyerJson<DreAdmin>(`${REFERENTIEL}/dre`, entree);
export const adminModifierDre = (code: string, entree: DreModification) =>
  envoyerJson<DreAdmin>(`${REFERENTIEL}/dre/${code}`, entree, "PATCH");
export const adminCreerIesg = (entree: IesgCreation) =>
  envoyerJson<IesgAdmin>(`${REFERENTIEL}/iesg`, entree);
export const adminModifierIesg = (id: string, entree: IesgModification) =>
  envoyerJson<IesgAdmin>(`${REFERENTIEL}/iesg/${id}`, entree, "PATCH");
export const adminListerEtablissements = (filtres: Record<string, string | number | undefined>) =>
  requeteApi<PageEtablissements>(avecParametres(`${REFERENTIEL}/etablissements`, filtres));
export const adminCreerEtablissement = (entree: EtablissementCreation) =>
  envoyerJson<EtablissementAdmin>(`${REFERENTIEL}/etablissements`, entree);
export const adminModifierEtablissement = (id: string, entree: EtablissementModification) =>
  envoyerJson<EtablissementAdmin>(`${REFERENTIEL}/etablissements/${id}`, entree, "PATCH");
export const adminRemplacerEtablissement = (id: string, entree: Remplacement) =>
  envoyerJson<EtablissementAdmin>(`${REFERENTIEL}/etablissements/${id}/remplacer`, entree);
export const adminListerAxes = () => requeteApi<AxeAdmin[]>(`${REFERENTIEL}/axes`);
export const adminCreerAxe = (entree: AxeCreation) =>
  envoyerJson<AxeAdmin>(`${REFERENTIEL}/axes`, entree);
export const adminModifierAxe = (code: string, entree: AxeModification) =>
  envoyerJson<AxeAdmin>(`${REFERENTIEL}/axes/${code}`, entree, "PATCH");

// Compte élève et points (spec 017) ----------------------------------------------------------------------

export const chargerEtatInscription = () => requeteApi<EtatInscription>("/api/eleves/inscription");
export const inscrireEleve = (entree: InscriptionEntree) =>
  envoyerJson<Moi>("/api/eleves/inscription", entree);
export const chargerEspaceEleve = () => requeteApi<EspaceEleve>("/api/eleves/moi");
export const modifierProfilEleve = (entree: ProfilModification) =>
  envoyerJson<EspaceEleve>("/api/eleves/moi", entree, "PATCH");
export const changerMotDePasse = (actuel: string, nouveau: string) =>
  envoyerJson<void>("/api/comptes/mot-de-passe", { actuel, nouveau });

const POINTS = "/api/admin/points";
export const adminListerSemestres = () => requeteApi<SemestreAdmin[]>(`${POINTS}/semestres`);
export const adminCreerSemestre = (entree: SemestreCreation) =>
  envoyerJson<SemestreAdmin>(`${POINTS}/semestres`, entree);
export const adminModifierSemestre = (id: string, entree: SemestreModification) =>
  envoyerJson<SemestreAdmin>(`${POINTS}/semestres/${id}`, entree, "PATCH");
export const adminListerBareme = () => requeteApi<LigneBaremeAdmin[]>(`${POINTS}/bareme`);
export const adminModifierBareme = (code: string, entree: LigneBaremeModification) =>
  envoyerJson<LigneBaremeAdmin>(`${POINTS}/bareme/${code}`, entree, "PATCH");

// Compte encadreur (spec 018) ----------------------------------------------------------------------------

export const inscrireEncadreur = (entree: InscriptionEncadreur) =>
  envoyerJson<Moi>("/api/encadreurs/inscription", entree);
export const chargerEspaceEncadreur = () => requeteApi<EspaceEncadreur>("/api/encadreurs/moi");
export const modifierProfilEncadreur = (entree: ProfilEncadreurModification) =>
  envoyerJson<EspaceEncadreur>("/api/encadreurs/moi", entree, "PATCH");
export const renvoyerDemandeEncadreur = () =>
  envoyerJson<EspaceEncadreur>("/api/encadreurs/moi/renvoyer");

const ENCADREURS = "/api/admin/encadreurs";
export const adminFileEncadreurs = (etat: EtatVerification) =>
  requeteApi<FileEncadreurs>(avecParametres(ENCADREURS, { etat }));
export const adminActiverEncadreur = (id: string, version: number) =>
  envoyerJson<DemandeEncadreur>(`${ENCADREURS}/${id}/activer`, { version });
export const adminRefuserEncadreur = (id: string, version: number, motif: string) =>
  envoyerJson<DemandeEncadreur>(`${ENCADREURS}/${id}/refuser`, { version, motif });

// Clubs et présidence (spec 019) --------------------------------------------------------------------------

export const demanderClub = (entree: DemandeClubEntree) =>
  envoyerJson<ClubResume>("/api/clubs/demande", entree);
export const renvoyerDemandeClub = () => envoyerJson<ClubResume>("/api/clubs/demande/renvoyer");
export const chargerMonClub = () => requeteApi<MonClub>("/api/clubs/moi");
export const proposerPassation = (pseudonyme: string, version: number) =>
  envoyerJson<PassationApercu>("/api/clubs/moi/passation", { pseudonyme, version });
export const annulerPassation = () =>
  envoyerJson<PassationApercu>("/api/clubs/moi/passation/annuler");

export const chargerClubsPublics = () => requeteApi<ClubPublic[]>("/api/clubs");
export const chargerFicheClub = (id: string) => requeteApi<ClubFiche>(`/api/clubs/${id}`);
export const chargerClubParEtablissement = (etablissementId: string) =>
  requeteApi<ClubPublic | undefined>(
    avecParametres("/api/clubs/par-etablissement", { etablissement_id: etablissementId }),
  );

const CLUBS_ADMIN = "/api/admin/clubs";
export const adminFileClubs = (etat: "en_attente" | "refuse") =>
  requeteApi<FileClubs>(avecParametres(CLUBS_ADMIN, { etat }));
export const adminActiverClub = (id: string, version: number) =>
  envoyerJson<DemandeClub>(`${CLUBS_ADMIN}/${id}/activer`, { version });
export const adminRefuserClub = (id: string, version: number, motif: string) =>
  envoyerJson<DemandeClub>(`${CLUBS_ADMIN}/${id}/refuser`, { version, motif });
export const adminFilePassations = () => requeteApi<FilePassations>(`${CLUBS_ADMIN}/passations`);
export const adminValiderPassation = (id: string, version: number) =>
  envoyerJson<Passation>(`${CLUBS_ADMIN}/passations/${id}/valider`, { version });
export const adminRefuserPassation = (id: string, version: number, motif: string) =>
  envoyerJson<Passation>(`${CLUBS_ADMIN}/passations/${id}/refuser`, { version, motif });

// Affiliations et rattachements (spec 020) ------------------------------------------------------------------

const club = (id: string) => `/api/clubs/${id}`;

export const demanderAdhesion = (clubId: string) =>
  envoyerJson<AdhesionResume>(`${club(clubId)}/adhesions`);
export const quitterClub = (clubId: string) =>
  envoyerJson<AdhesionResume>(`${club(clubId)}/adhesions/moi`, undefined, "DELETE");
export const chargerDemandesAdhesion = (clubId: string) =>
  requeteApi<DemandeAdhesion[]>(`${club(clubId)}/adhesions/demandes`);
export const confirmerAdhesion = (clubId: string, id: string, version: number) =>
  envoyerJson<AdhesionResume>(`${club(clubId)}/adhesions/${id}/confirmer`, { version });
export const refuserAdhesion = (clubId: string, id: string, version: number, motif: string) =>
  envoyerJson<AdhesionResume>(`${club(clubId)}/adhesions/${id}/refuser`, { version, motif });
export const retirerMembre = (clubId: string, id: string, version: number, motif?: string) =>
  envoyerJson<AdhesionResume>(`${club(clubId)}/adhesions/${id}/retirer`, {
    version,
    motif: motif || null,
  });
export const chargerMembres = (clubId: string) =>
  requeteApi<MembresDuClub>(`${club(clubId)}/membres`);

export const demanderRattachement = (clubId: string) =>
  envoyerJson<RattachementResume>(`${club(clubId)}/rattachements`);
export const quitterClubEncadre = (clubId: string) =>
  envoyerJson<RattachementResume>(`${club(clubId)}/rattachements/moi`, undefined, "DELETE");
export const chargerDemandesRattachement = (clubId: string) =>
  requeteApi<DemandeRattachement[]>(`${club(clubId)}/rattachements/demandes`);
export const confirmerRattachement = (clubId: string, id: string, version: number) =>
  envoyerJson<RattachementResume>(`${club(clubId)}/rattachements/${id}/confirmer`, { version });
export const refuserRattachement = (clubId: string, id: string, version: number, motif: string) =>
  envoyerJson<RattachementResume>(`${club(clubId)}/rattachements/${id}/refuser`, {
    version,
    motif,
  });
export const retirerEncadreur = (clubId: string, id: string, version: number, motif?: string) =>
  envoyerJson<RattachementResume>(`${club(clubId)}/rattachements/${id}/retirer`, {
    version,
    motif: motif || null,
  });
export const chargerMesClubs = () => requeteApi<MesClubs>("/api/encadreurs/moi/clubs");
export const confirmerPassationEncadreur = (clubId: string, version: number) =>
  envoyerJson<PassationAConfirmer>(`${club(clubId)}/passation/confirmer`, { version });
export const refuserPassationEncadreur = (clubId: string, version: number, motif: string) =>
  envoyerJson<PassationAConfirmer>(`${club(clubId)}/passation/refuser`, { version, motif });

export const adminFileAffiliations = () =>
  requeteApi<FileAffiliations>(`${CLUBS_ADMIN}/affiliations`);
export const adminDeciderAffiliations = (
  decision: "valider" | "refuser",
  elements: ElementLot[],
  motif?: string,
) =>
  envoyerJson<ResultatLot>(
    `${CLUBS_ADMIN}/affiliations/${decision}`,
    decision === "refuser" ? { elements, motif } : { elements },
  );
export const adminFileRattachements = () =>
  requeteApi<FileRattachements>(`${CLUBS_ADMIN}/rattachements`);
export const adminDeciderRattachements = (
  decision: "valider" | "refuser",
  elements: ElementLot[],
  motif?: string,
) =>
  envoyerJson<ResultatLot>(
    `${CLUBS_ADMIN}/rattachements/${decision}`,
    decision === "refuser" ? { elements, motif } : { elements },
  );

// Jeux de l'accueil (spec 021). « Quel axe » est réservé aux élèves actifs : l'API répond 401 ou 403 sinon.
export const chargerQuelAxe = () => requeteApi<QuestionnaireQuelAxe>("/api/jeux/quel-axe");
export const calculerQuelAxe = (reponses: string[]) =>
  envoyerJson<ResultatQuelAxe>("/api/jeux/quel-axe/resultat", { reponses });
export const chargerDefiDuJour = () => requeteApi<DefiDuJour>("/api/jeux/defi-du-jour");
export const corrigerDefi = (id: string, choix: number) =>
  envoyerJson<CorrectionDefi>(`/api/jeux/defis/${id}/reponse`, { choix });
export const chargerPodiumClubs = () => requeteApi<ClubPodium[]>("/api/clubs/podium");

// Articles (spec 023) : rédaction par l'auteur, lecture publique, modération.
const MES_ARTICLES = "/api/mes-articles";
export const chargerMesArticles = () => requeteApi<MesArticles>(MES_ARTICLES);
export const chargerMonArticle = (id: string) => requeteApi<ArticleAuteur>(`${MES_ARTICLES}/${id}`);
export const creerArticle = (entree: ArticleEcriture) =>
  envoyerJson<ArticleAuteur>(MES_ARTICLES, entree);
export const modifierArticle = (id: string, entree: ArticleEcriture) =>
  envoyerJson<ArticleAuteur>(`${MES_ARTICLES}/${id}`, entree, "PATCH");
export const soumettreArticle = (id: string, version: number) =>
  envoyerJson<ArticleAuteur>(`${MES_ARTICLES}/${id}/soumettre`, { version });
export const retirerArticle = (id: string, version: number) =>
  envoyerJson<ArticleAuteur>(`${MES_ARTICLES}/${id}/retirer`, { version });
export const supprimerArticle = (id: string) =>
  envoyerJson<void>(`${MES_ARTICLES}/${id}`, undefined, "DELETE");

export const chargerArticles = (filtres: { page?: number; axe?: string } = {}) =>
  requeteApi<ArticlesPublics>(avecParametres("/api/articles", filtres));
export const chargerArticle = (adresse: string) =>
  requeteApi<ArticlePublic>(`/api/articles/${encodeURIComponent(adresse)}`);

// Commentaires (spec 025) : en attente jusqu'à leur approbation, puis lisibles sous l'article.
const commentairesDe = (adresse: string) => `/api/articles/${encodeURIComponent(adresse)}/commentaires`;
export const chargerCommentaires = (adresse: string, page = 1) =>
  requeteApi<CommentairesPublics>(avecParametres(commentairesDe(adresse), { page }));
export const commenterArticle = (adresse: string, texte: string) =>
  envoyerJson<CommentaireAuteur>(commentairesDe(adresse), { texte });
export const chargerMesCommentaires = (article?: string) =>
  requeteApi<MesCommentaires>(avecParametres("/api/mes-commentaires", { article }));
export const retirerCommentaire = (id: string) =>
  envoyerJson<void>(`/api/mes-commentaires/${id}`, undefined, "DELETE");

const MODERATION = "/api/admin/moderation";
export const chargerFileModeration = (filtres: Record<string, string | undefined> = {}) =>
  requeteApi<FileModeration>(avecParametres(MODERATION, filtres));
export const chargerApercuModeration = (id: string) =>
  requeteApi<ApercuModeration>(`${MODERATION}/${id}`);
export const deciderModeration = (
  id: string,
  decision: "approuver" | "corriger" | "refuser" | "depublier",
  version: number,
  motif?: string,
) =>
  envoyerJson<ApercuModeration>(
    `${MODERATION}/${id}/${decision}`,
    decision === "approuver" ? { version } : { version, motif },
  );

// Centre de notifications (spec 023).
export const chargerNotifications = () => requeteApi<Notifications>("/api/notifications");
export const compterNotifications = () =>
  requeteApi<{ non_lues: number }>("/api/notifications/compte");
export const marquerNotificationLue = (id: string) =>
  envoyerJson<void>(`/api/notifications/${id}/lue`);
export const marquerToutesLues = () => envoyerJson<void>("/api/notifications/lues");

// Photos des articles (spec 024). L'envoi passe par XMLHttpRequest pour suivre la progression sur un réseau lent.
export type TaillePhoto = "grande" | "vignette";
export const urlPhotoAuteur = (articleId: string, photoId: string, taille: TaillePhoto) =>
  `${MES_ARTICLES}/${articleId}/photos/${photoId}/${taille}`;
export const urlPhotoPublique = (adresse: string, photoId: string, taille: TaillePhoto) =>
  `/api/articles/${encodeURIComponent(adresse)}/photos/${photoId}/${taille}`;
export const urlPhotoModeration = (contenuId: string, photoId: string, taille: TaillePhoto) =>
  `${MODERATION}/${contenuId}/photos/${photoId}/${taille}`;

export function envoyerPhoto(
  articleId: string,
  entree: { fichier: File; version: number; legende: string; couverture: boolean },
  progression: (fraction: number) => void,
): Promise<ArticleAuteur> {
  const donnees = new FormData();
  donnees.append("fichier", entree.fichier);
  donnees.append("version", String(entree.version));
  donnees.append("attestation", "true");
  if (entree.legende.trim()) donnees.append("legende", entree.legende.trim());
  donnees.append("couverture", entree.couverture ? "true" : "false");
  return new Promise((resoudre, rejeter) => {
    const requete = new XMLHttpRequest();
    requete.open("POST", `${MES_ARTICLES}/${articleId}/photos`);
    requete.timeout = 120_000;
    requete.upload.onprogress = (e) => e.lengthComputable && progression(e.loaded / e.total);
    requete.onload = () => {
      let corps: unknown = null;
      try {
        corps = JSON.parse(requete.responseText);
      } catch {
        corps = null;
      }
      if (requete.status >= 200 && requete.status < 300) return resoudre(corps as ArticleAuteur);
      // Au-delà de 20 Mo, le proxy répond lui-même, sans message de l'API.
      if (requete.status === 413)
        return rejeter(
          new ErreurApi(413, "Cette photo est trop lourde : choisis une photo de 8 Mo au plus."),
        );
      const detail = (corps as { detail?: unknown } | null)?.detail;
      rejeter(new ErreurApi(requete.status, typeof detail === "string" ? detail : MESSAGE_SAISIE));
    };
    requete.onerror = requete.ontimeout = () => rejeter(new ErreurApi(0, MESSAGE_INDISPONIBLE));
    requete.send(donnees);
  });
}
export const modifierPhoto = (
  articleId: string,
  photoId: string,
  entree: { version: number; legende?: string | null; couverture?: boolean; ordre?: number },
) => envoyerJson<ArticleAuteur>(`${MES_ARTICLES}/${articleId}/photos/${photoId}`, entree, "PATCH");
export const retirerPhoto = (articleId: string, photoId: string, version: number) =>
  envoyerJson<ArticleAuteur>(
    `${MES_ARTICLES}/${articleId}/photos/${photoId}?version=${version}`,
    undefined,
    "DELETE",
  );
