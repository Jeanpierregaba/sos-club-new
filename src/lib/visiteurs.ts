import type { Region } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

// Le libellé est lu à l'affichage, dans la langue de la page (spec 052).
const region = (valeur: Region, libelle: () => string) => ({
  valeur,
  get libelle() {
    return libelle();
  },
});

// Les régions proposées au visiteur (spec 030).
export const REGIONS: { valeur: Region; readonly libelle: string }[] = [
  region("maritime", m.region_maritime),
  region("plateaux", m.region_plateaux),
  region("centrale", m.region_centrale),
  region("kara", m.region_kara),
  region("savanes", m.region_savanes),
  region("hors_togo", m.region_hors_togo),
];

export const libelleRegion = (region: Region | null) =>
  REGIONS.find((r) => r.valeur === region)?.libelle ?? "Non précisée";
