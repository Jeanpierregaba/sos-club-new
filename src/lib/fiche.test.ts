import { describe, expect, it } from "vitest";

import {
  age,
  FICHE_VIDE,
  ficheDepuisApi,
  ficheVersApi,
  schemaFiche,
  type ValeursFiche,
} from "./fiche";

const ilYa = (ans: number) => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - ans);
  d.setDate(1);
  return d.toISOString().slice(0, 10);
};

const valide: ValeursFiche = {
  ...FICHE_VIDE,
  sexe: "feminin",
  dateNaissance: ilYa(16),
  lieuNaissance: "Lomé",
  responsableNom: "Koffi Mensah",
  responsableTelephone: "90 11 22 33",
  axes: ["genie-imhotep"],
  engagement: true,
};

const erreurs = (v: ValeursFiche) => {
  const r = schemaFiche.safeParse(v);
  return r.success ? [] : [...new Set(r.error.issues.map((i) => i.path.join(".")))];
};

describe("fiche d'adhésion", () => {
  it("accepte une fiche complète", () => {
    expect(erreurs(valide)).toEqual([]);
  });

  it("exige le sexe, la naissance, le responsable, un axe et l'engagement", () => {
    expect(erreurs(FICHE_VIDE).sort()).toEqual(
      [
        "axes",
        "dateNaissance",
        "engagement",
        "lieuNaissance",
        "responsableNom",
        "responsableTelephone",
        "sexe",
      ].sort(),
    );
  });

  it.each([7, 31])("refuse un élève de %i ans", (ans) => {
    expect(erreurs({ ...valide, dateNaissance: ilYa(ans) })).toEqual(["dateNaissance"]);
  });

  it("limite les axes à trois", () => {
    expect(erreurs({ ...valide, axes: ["a", "b", "c", "d"] })).toEqual(["axes"]);
  });

  it("demande de préciser l'autre réseau", () => {
    expect(erreurs({ ...valide, reseaux: ["autre"] })).toEqual(["reseauAutre"]);
    expect(erreurs({ ...valide, reseaux: ["autre"], reseauAutre: "Snapchat" })).toEqual([]);
  });

  it("vérifie l'année scolaire du parcours", () => {
    const parcours = [{ annee: "2025-2027", etablissement: "CEG Bè", iesg: "" }];
    expect(erreurs({ ...valide, parcours })).toEqual(["parcours.0.annee"]);
  });

  it("calcule l'âge au jour près", () => {
    expect(age(new Date(2010, 5, 15), new Date(2026, 5, 14))).toBe(15);
    expect(age(new Date(2010, 5, 15), new Date(2026, 5, 15))).toBe(16);
  });

  it("envoie des nuls pour les champs vides et omet un parent non renseigné", () => {
    const corps = ficheVersApi({
      ...valide,
      pere: { nom: "Koffi", profession: "", telephone: "" },
      reseaux: ["facebook"],
      reseauAutre: "reste d'une saisie",
    });

    expect(corps.pere).toEqual({ nom: "Koffi", profession: null, telephone: null });
    expect(corps.mere).toBeNull();
    expect(corps.numero_adhesion).toBeNull();
    expect(corps.reseau_autre).toBeNull();
    expect(corps.responsable).toEqual({ nom: "Koffi Mensah", telephone: "90 11 22 33" });
  });

  it("relit une fiche de l'API", () => {
    const relue = ficheDepuisApi({
      annee_scolaire: "2026-2027",
      numero_adhesion: null,
      prefecture: "Golfe",
      commune: null,
      canton: null,
      sexe: "masculin",
      date_naissance: "2010-03-14",
      lieu_naissance: "Kpalimé",
      telephone: null,
      pere: null,
      mere: { nom: "Ama", profession: null, telephone: "90000000" },
      responsable: { nom: "Ama", telephone: "90000000" },
      axes: ["genie-imhotep"],
      parcours: [],
      reseaux: [],
      reseau_autre: null,
      engagement_le: "2026-11-09T10:00:00Z",
      complete_le: "2026-11-09T10:00:00Z",
      cree_le: "2026-11-09T10:00:00Z",
      version: 1,
    });

    expect(relue.mere).toEqual({ nom: "Ama", profession: "", telephone: "90000000" });
    expect(relue.pere).toEqual({ nom: "", profession: "", telephone: "" });
    expect(relue.engagement).toBe(true);
    expect(erreurs(relue)).toEqual([]);
  });
});
