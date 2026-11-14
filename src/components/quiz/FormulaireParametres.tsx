import { useRouter } from "@tanstack/react-router";
import { Save } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  changerParametresQuiz,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type AdminMoi,
  type HistoriqueParametres,
  type ParametresEntree,
  type Parcours,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

type Cle = Exclude<keyof ParametresEntree, "arret_premiere_erreur">;

const CHAMPS: { cle: Cle; libelle: string; secondes?: boolean }[] = [
  { cle: "nb_questions", libelle: "Questions par partie" },
  { cle: "temps_ms", libelle: "Temps affiché par question (secondes)", secondes: true },
  { cle: "tolerance_ms", libelle: "Tolérance réseau (secondes)", secondes: true },
  { cle: "seuil", libelle: "Bonnes réponses pour réussir" },
  { cle: "tentatives_par_jour", libelle: "Parties par quiz et par jour (vide : sans limite)" },
];

// Les paramètres versionnés d'un parcours (spec 027 pour les jeux, spec 029 pour la certification).
export function FormulaireParametres({
  historique,
  parcours,
  admin,
}: {
  historique: HistoriqueParametres;
  parcours: Parcours;
  admin: AdminMoi;
}) {
  const { en_cours, versions } = historique;
  const router = useRouter();
  // Les règles de toutes les parties : réservé à qui publie (l'API exige aussi la double authentification).
  const modifiable = peut(admin, "quiz", "approuver");
  const [valeurs, setValeurs] = useState<Record<Cle, string>>({
    nb_questions: String(en_cours.nb_questions),
    temps_ms: String(en_cours.temps_ms / 1000),
    tolerance_ms: String(en_cours.tolerance_ms / 1000),
    seuil: String(en_cours.seuil),
    tentatives_par_jour:
      en_cours.tentatives_par_jour === null ? "" : String(en_cours.tentatives_par_jour),
  });
  // Spec 034 : la certification s'arrête à la première erreur ou au premier temps dépassé.
  const [arret, setArret] = useState(en_cours.arret_premiere_erreur);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  async function enregistrer() {
    setErreur(null);
    setInfo(null);
    setEnCours(true);
    const nombre = (cle: Cle, secondes = false) =>
      Math.round(Number(valeurs[cle].replace(",", ".")) * (secondes ? 1000 : 1));
    try {
      const v = await changerParametresQuiz(
        {
          nb_questions: nombre("nb_questions"),
          temps_ms: nombre("temps_ms", true),
          tolerance_ms: nombre("tolerance_ms", true),
          seuil: nombre("seuil"),
          tentatives_par_jour: valeurs.tentatives_par_jour.trim()
            ? nombre("tentatives_par_jour")
            : null,
          arret_premiere_erreur: arret,
        },
        parcours,
      );
      setInfo(`Version ${v.version} en vigueur pour les prochaines parties.`);
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form
        className="grid gap-4 rounded-3xl bg-white p-5 shadow-card sm:p-7"
        onSubmit={(e) => {
          e.preventDefault();
          void enregistrer();
        }}
      >
        <h2 className="font-display text-xl text-ink">Version {en_cours.version} en vigueur</h2>
        <p className="text-sm text-muted-foreground">
          Un changement crée une nouvelle version : une partie commencée garde ses règles.
        </p>
        {CHAMPS.map((c) => (
          <Champ key={c.cle} libelle={c.libelle}>
            <input
              className={CHAMP_ADMIN}
              inputMode="decimal"
              value={valeurs[c.cle]}
              disabled={!modifiable}
              onChange={(e) => setValeurs((v) => ({ ...v, [c.cle]: e.target.value }))}
            />
          </Champ>
        ))}
        {parcours === "certification" && (
          <label className="flex items-center gap-2 text-sm font-semibold text-ink">
            <input
              type="checkbox"
              checked={arret}
              disabled={!modifiable}
              onChange={(e) => setArret(e.target.checked)}
            />
            Arrêter la partie à la première erreur ou au premier temps dépassé (seuil = nombre de
            questions)
          </label>
        )}
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        {info && (
          <p role="status" className="text-sm font-semibold text-primary">
            {info}
          </p>
        )}
        {modifiable && (
          <Button type="submit" className="w-fit rounded-full font-bold" disabled={enCours}>
            <Save className="size-4" /> Enregistrer une nouvelle version
          </Button>
        )}
      </form>

      <section className="rounded-3xl bg-white p-5 shadow-card sm:p-7">
        <h2 className="font-display text-xl text-ink">Historique</h2>
        <ul className="mt-3 grid gap-2 text-sm">
          {versions.map((v) => (
            <li key={v.version} className="rounded-2xl bg-mist/60 p-3">
              <strong>Version {v.version}</strong> · {dateCourte(v.cree_le)} — {v.nb_questions}{" "}
              questions, {v.temps_ms / 1000} s + {v.tolerance_ms / 1000} s, réussite à {v.seuil},{" "}
              {v.tentatives_par_jour === null
                ? "sans limite de parties"
                : `${v.tentatives_par_jour} parties par jour`}
              {v.arret_premiere_erreur && ", arrêt à la première erreur"}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
