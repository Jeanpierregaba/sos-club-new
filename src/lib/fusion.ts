import type { FicheDoublon, OrdreEnseignement } from "@/lib/api/client";

export const ETATS_CLUB: Record<string, string> = {
  en_constitution: "en constitution",
  actif: "actif",
  en_regularisation: "en régularisation",
  suspendu: "suspendu",
};

// L'ordre d'enseignement de la liste nationale (spec 035).
export const ORDRES: Record<OrdreEnseignement, string> = {
  public: "Public",
  prive_laic: "Privé laïc",
  prive_catholique: "Privé catholique",
  prive_protestant: "Privé protestant",
  prive_islamique: "Privé islamique",
  communautaire: "Communautaire",
};

export const pluriel = (n: number, mot: string) => `${n} ${mot}${n > 1 ? "s" : ""}`;

// Le gardé par défaut (spec 042) : un établissement actif, puis celui dont le club a dépassé « en constitution »,
// puis celui qui a le plus d'inscrits, puis le plus ancien (l'identifiant UUIDv7 suit l'ordre de création).
export function prefereGarder(a: FicheDoublon, b: FicheDoublon): boolean {
  const cles = (f: FicheDoublon) => [
    f.statut === "actif" ? 1 : 0,
    f.club && f.club.etat !== "en_constitution" ? 1 : 0,
    f.nb_eleves + f.nb_encadreurs,
  ];
  const [ca, cb] = [cles(a), cles(b)];
  for (let i = 0; i < ca.length; i++) if (ca[i] !== cb[i]) return ca[i]! > cb[i]!;
  return a.id < b.id;
}
