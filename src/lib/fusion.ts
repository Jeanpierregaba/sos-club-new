import type { FicheDoublon } from "@/lib/api/client";

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
