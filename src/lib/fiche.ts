import { z } from "zod";

import type { FicheEntree, FicheSortie, Reseau, Sexe } from "@/lib/api/client";
import { normaliserTelephone, telephoneValide } from "@/lib/telephone";

// La fiche d'adhésion de l'élève (spec 030) : mêmes règles que l'API, pour prévenir avant l'envoi.

export const AGE_MIN = 8;
export const AGE_MAX = 30;
export const AXES_MAX = 3;

export const SEXES: { valeur: Sexe; libelle: string }[] = [
  { valeur: "feminin", libelle: "Féminin" },
  { valeur: "masculin", libelle: "Masculin" },
];

export const RESEAUX: { valeur: Reseau; libelle: string }[] = [
  { valeur: "facebook", libelle: "Facebook" },
  { valeur: "tiktok", libelle: "TikTok" },
  { valeur: "instagram", libelle: "Instagram" },
  { valeur: "autre", libelle: "Autre" },
];

const texte = (max: number) => z.string().trim().max(max, `${max} caractères au plus.`);
const requis = (max: number, message: string) => texte(max).min(1, message);
const telephone = z
  .string()
  .trim()
  .max(30, "Ce numéro est trop long.")
  .refine(telephoneValide, "De 8 à 15 chiffres, avec « + » au début si besoin.");
const telephoneRequis = telephone.refine(
  (v) => normaliserTelephone(v) !== "",
  "Indique un numéro de téléphone.",
);
const annee = z
  .string()
  .trim()
  .refine((v) => {
    const m = /^(\d{4})-(\d{4})$/.exec(v);
    return m !== null && Number(m[2]) === Number(m[1]) + 1;
  }, "Sous la forme 2025-2026.");

export function age(naissance: Date, jour: Date) {
  const avant =
    jour.getMonth() < naissance.getMonth() ||
    (jour.getMonth() === naissance.getMonth() && jour.getDate() < naissance.getDate());
  return jour.getFullYear() - naissance.getFullYear() - (avant ? 1 : 0);
}

const parent = z.object({ nom: texte(150), profession: texte(100), telephone });

export const schemaFiche = z
  .object({
    numeroAdhesion: texte(30),
    prefecture: texte(100),
    commune: texte(100),
    canton: texte(100),
    sexe: z.string().min(1, "Choisis une réponse."),
    dateNaissance: z
      .string()
      .min(1, "Indique ta date de naissance.")
      .refine((v) => {
        const date = new Date(`${v}T00:00:00`);
        if (Number.isNaN(date.getTime())) return false;
        const a = age(date, new Date());
        return date <= new Date() && a >= AGE_MIN && a <= AGE_MAX;
      }, `Vérifie la date : un élève a entre ${AGE_MIN} et ${AGE_MAX} ans.`),
    lieuNaissance: requis(100, "Indique ton lieu de naissance."),
    telephone,
    pere: parent,
    mere: parent,
    responsableNom: requis(150, "Indique le nom de ton parent ou tuteur."),
    responsableTelephone: telephoneRequis,
    axes: z
      .array(z.string())
      .min(1, "Choisis au moins un axe.")
      .max(AXES_MAX, `${AXES_MAX} axes au plus.`),
    parcours: z
      .array(
        z.object({
          annee,
          etablissement: requis(150, "Indique l'établissement."),
          iesg: texte(150),
        }),
      )
      .max(2),
    reseaux: z.array(z.string()),
    reseauAutre: texte(60),
    engagement: z.boolean().refine((v) => v, "Coche cette case pour t'engager."),
  })
  .superRefine((v, ctx) => {
    if (v.reseaux.includes("autre") && !v.reseauAutre)
      ctx.addIssue({ code: "custom", path: ["reseauAutre"], message: "Précise le réseau." });
  });

export type ValeursFiche = z.infer<typeof schemaFiche>;

const PARENT_VIDE = { nom: "", profession: "", telephone: "" };

export const FICHE_VIDE: ValeursFiche = {
  numeroAdhesion: "",
  prefecture: "",
  commune: "",
  canton: "",
  sexe: "",
  dateNaissance: "",
  lieuNaissance: "",
  telephone: "",
  pere: PARENT_VIDE,
  mere: PARENT_VIDE,
  responsableNom: "",
  responsableTelephone: "",
  axes: [],
  parcours: [],
  reseaux: [],
  reseauAutre: "",
  engagement: false,
};

const ouNul = (v: string) => v.trim() || null;

function parentVersApi(p: ValeursFiche["pere"]) {
  return p.nom || p.profession || p.telephone
    ? { nom: ouNul(p.nom), profession: ouNul(p.profession), telephone: ouNul(p.telephone) }
    : null;
}

export function ficheVersApi(v: ValeursFiche): FicheEntree {
  const autre = v.reseaux.includes("autre");
  return {
    numero_adhesion: ouNul(v.numeroAdhesion),
    prefecture: ouNul(v.prefecture),
    commune: ouNul(v.commune),
    canton: ouNul(v.canton),
    sexe: v.sexe as Sexe,
    date_naissance: v.dateNaissance,
    lieu_naissance: v.lieuNaissance,
    telephone: ouNul(v.telephone),
    pere: parentVersApi(v.pere),
    mere: parentVersApi(v.mere),
    responsable: { nom: v.responsableNom, telephone: v.responsableTelephone },
    axes: v.axes,
    parcours: v.parcours.map((p) => ({
      annee: p.annee,
      etablissement: p.etablissement,
      iesg: ouNul(p.iesg),
    })),
    reseaux: v.reseaux as Reseau[],
    reseau_autre: autre ? ouNul(v.reseauAutre) : null,
    engagement: true,
  };
}

const parentDepuisApi = (p: FicheSortie["pere"]) => ({
  nom: p?.nom ?? "",
  profession: p?.profession ?? "",
  telephone: p?.telephone ?? "",
});

export function ficheDepuisApi(f: FicheSortie): ValeursFiche {
  return {
    numeroAdhesion: f.numero_adhesion ?? "",
    prefecture: f.prefecture ?? "",
    commune: f.commune ?? "",
    canton: f.canton ?? "",
    sexe: f.sexe ?? "",
    dateNaissance: f.date_naissance ?? "",
    lieuNaissance: f.lieu_naissance ?? "",
    telephone: f.telephone ?? "",
    pere: parentDepuisApi(f.pere),
    mere: parentDepuisApi(f.mere),
    responsableNom: f.responsable?.nom ?? "",
    responsableTelephone: f.responsable?.telephone ?? "",
    axes: f.axes,
    parcours: f.parcours.map((p) => ({
      annee: p.annee,
      etablissement: p.etablissement,
      iesg: p.iesg ?? "",
    })),
    reseaux: f.reseaux,
    reseauAutre: f.reseau_autre ?? "",
    engagement: f.engagement_le !== null,
  };
}

// Les champs de chaque étape du formulaire : « Suivant » ne valide que ceux de l'étape affichée.
export const CHAMPS_ETAPES = {
  lieu: ["numeroAdhesion", "prefecture", "commune", "canton"],
  toi: ["sexe", "dateNaissance", "lieuNaissance", "telephone"],
  famille: ["pere", "mere", "responsableNom", "responsableTelephone"],
  club: ["axes", "parcours", "reseaux", "reseauAutre", "engagement"],
} as const satisfies Record<string, readonly (keyof ValeursFiche)[]>;
