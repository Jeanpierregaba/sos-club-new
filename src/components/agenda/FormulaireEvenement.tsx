import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErreurApi } from "@/lib/api/client";
import type { AxePublic } from "@/lib/api/client";
import { TYPES_EVENEMENT, versSaisie } from "@/lib/agenda";

export type ChampsSaisis = {
  titre: string;
  type: string;
  axe_code: string | null;
  objectif: string | null;
  description: string;
  lieu: string | null;
  en_ligne: boolean;
  lien: string | null;
  public_vise: string | null;
  debut: string;
  fin: string;
  places: number | null;
};

const VIDE: ChampsSaisis = {
  titre: "",
  type: "sensibilisation",
  axe_code: null,
  objectif: null,
  description: "",
  lieu: null,
  en_ligne: false,
  lien: null,
  public_vise: null,
  debut: "",
  fin: "",
  places: null,
};

const champCls =
  "mt-1 block h-12 w-full rounded-xl border bg-white px-4 font-medium outline-none transition focus:border-logo-blue";

function depuisDonnees(donnees: Record<string, unknown> | null | undefined): ChampsSaisis {
  if (!donnees) return VIDE;
  const texte = (cle: string) =>
    typeof donnees[cle] === "string" ? (donnees[cle] as string) : null;
  return {
    ...VIDE,
    titre: texte("titre") ?? "",
    type: texte("type") ?? VIDE.type,
    axe_code: texte("axe_code"),
    objectif: texte("objectif"),
    description: texte("description") ?? "",
    lieu: texte("lieu"),
    en_ligne: donnees["en_ligne"] === true,
    lien: texte("lien"),
    public_vise: texte("public_vise"),
    debut: versSaisie(texte("debut")),
    fin: versSaisie(texte("fin")),
    places: typeof donnees["places"] === "number" ? (donnees["places"] as number) : null,
  };
}

// Le formulaire d'un événement, en une page. Les heures sont celles de Lomé ; l'API vérifie tout (dates, lieu ou
// lien, axe) et nomme le champ fautif.
export function FormulaireEvenement({
  initial,
  axes,
  axeObligatoire = true,
  bouton,
  onEnvoi,
}: {
  initial?: Record<string, unknown> | null;
  axes: AxePublic[];
  axeObligatoire?: boolean;
  bouton: string;
  onEnvoi: (champs: ChampsSaisis) => Promise<unknown>;
}) {
  const [champs, setChamps] = useState<ChampsSaisis>(() => depuisDonnees(initial));
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const changer = <K extends keyof ChampsSaisis>(cle: K, valeur: ChampsSaisis[K]) =>
    setChamps((avant) => ({ ...avant, [cle]: valeur }));
  const facultatif = (valeur: string) => (valeur.trim() ? valeur : null);

  async function envoyer(e: FormEvent) {
    e.preventDefault();
    setEnCours(true);
    setErreur(null);
    try {
      await onEnvoi(champs);
    } catch (err) {
      setErreur(err instanceof ErreurApi ? err.message : "L'événement n'a pas pu être enregistré.");
    } finally {
      setEnCours(false);
    }
  }

  return (
    <form
      onSubmit={(e) => void envoyer(e)}
      className="space-y-5 rounded-[1.75rem] bg-white p-5 shadow-card md:p-8"
    >
      <label className="block text-sm font-bold">
        Titre
        <input
          required
          minLength={3}
          maxLength={150}
          value={champs.titre}
          onChange={(e) => changer("titre", e.target.value)}
          className={champCls}
        />
      </label>
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="block text-sm font-bold">
          Type d'activité
          <select
            value={champs.type}
            onChange={(e) => changer("type", e.target.value)}
            className={champCls}
          >
            {Object.entries(TYPES_EVENEMENT).map(([code, libelle]) => (
              <option key={code} value={code}>
                {libelle}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-bold">
          Axe
          <select
            required={axeObligatoire}
            value={champs.axe_code ?? ""}
            onChange={(e) => changer("axe_code", e.target.value || null)}
            className={champCls}
          >
            <option value="">{axeObligatoire ? "Choisis un axe" : "Aucun axe"}</option>
            {axes.map((a) => (
              <option key={a.code} value={a.code}>
                {a.libelle}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="block text-sm font-bold">
          Début (heure de Lomé)
          <input
            required
            type="datetime-local"
            value={champs.debut}
            onChange={(e) => changer("debut", e.target.value)}
            className={champCls}
          />
        </label>
        <label className="block text-sm font-bold">
          Fin (heure de Lomé)
          <input
            required
            type="datetime-local"
            value={champs.fin}
            onChange={(e) => changer("fin", e.target.value)}
            className={champCls}
          />
        </label>
      </div>
      <fieldset className="space-y-3">
        <legend className="text-sm font-bold">Où ?</legend>
        <label className="flex items-center gap-2 text-sm font-semibold">
          <input
            type="checkbox"
            checked={champs.en_ligne}
            onChange={(e) => changer("en_ligne", e.target.checked)}
            className="size-5"
          />
          En ligne
        </label>
        {champs.en_ligne ? (
          <label className="block text-sm font-bold">
            Lien (https://…)
            <input
              required
              type="url"
              pattern="https://.*"
              value={champs.lien ?? ""}
              onChange={(e) => changer("lien", facultatif(e.target.value))}
              className={champCls}
            />
          </label>
        ) : (
          <label className="block text-sm font-bold">
            Lieu
            <input
              required
              maxLength={200}
              value={champs.lieu ?? ""}
              onChange={(e) => changer("lieu", facultatif(e.target.value))}
              className={champCls}
            />
          </label>
        )}
      </fieldset>
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="block text-sm font-bold">
          Public visé <span className="font-medium text-muted-foreground">(facultatif)</span>
          <input
            maxLength={200}
            value={champs.public_vise ?? ""}
            onChange={(e) => changer("public_vise", facultatif(e.target.value))}
            className={champCls}
          />
        </label>
        <label className="block text-sm font-bold">
          Nombre de places <span className="font-medium text-muted-foreground">(facultatif)</span>
          <input
            type="number"
            min={1}
            max={10000}
            value={champs.places ?? ""}
            onChange={(e) => changer("places", e.target.value ? Number(e.target.value) : null)}
            className={champCls}
          />
        </label>
      </div>
      <label className="block text-sm font-bold">
        Objectif <span className="font-medium text-muted-foreground">(facultatif)</span>
        <textarea
          maxLength={1000}
          rows={2}
          value={champs.objectif ?? ""}
          onChange={(e) => changer("objectif", facultatif(e.target.value))}
          className="mt-1 block w-full rounded-xl border bg-white px-4 py-3 font-medium outline-none focus:border-logo-blue"
        />
      </label>
      <label className="block text-sm font-bold">
        Programme
        <textarea
          required
          minLength={10}
          maxLength={5000}
          rows={5}
          value={champs.description}
          onChange={(e) => changer("description", e.target.value)}
          className="mt-1 block w-full rounded-xl border bg-white px-4 py-3 font-medium outline-none focus:border-logo-blue"
        />
      </label>
      {erreur && (
        <p
          role="alert"
          className="rounded-xl bg-logo-red/10 px-4 py-3 text-sm font-semibold text-ink"
        >
          {erreur}
        </p>
      )}
      <Button
        type="submit"
        disabled={enCours}
        className="h-12 w-full rounded-full text-base font-bold sm:w-auto sm:px-8"
      >
        {enCours ? "Enregistrement…" : bouton}
      </Button>
    </form>
  );
}
