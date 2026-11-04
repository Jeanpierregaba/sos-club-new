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
