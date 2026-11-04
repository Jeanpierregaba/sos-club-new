import { School } from "lucide-react";

import { ChoixEtablissement } from "@/components/ChoixEtablissement";
import { CHAMP, LISTE } from "@/components/inscription/styles";
import { Input } from "@/components/ui/input";
import type { DrePublique } from "@/lib/api/client";
import type { SaisieEtablissement } from "@/lib/saisie-etablissement";

export function ChampEtablissement({
  dre,
  saisie,
  onSaisie,
  erreur,
}: {
  dre: DrePublique[];
  saisie: SaisieEtablissement;
  onSaisie: (saisie: SaisieEtablissement) => void;
  erreur: string | null;
}) {
  const changer = (champs: Partial<SaisieEtablissement>) => onSaisie({ ...saisie, ...champs });
  const inspections = dre.find((d) => d.code === saisie.dre)?.iesg ?? [];

  return (
    <fieldset className="space-y-3">
      <legend className="mb-2 flex items-center gap-2 text-lg font-bold text-logo-blue">
        <School aria-hidden className="size-5" /> Ton établissement
      </legend>
      {saisie.proposer ? (
        <div className="space-y-4 rounded-2xl bg-mist-soft p-4">
          <p className="text-sm font-medium text-ink/80">
            L'équipe nationale vérifiera ton établissement avant de l'ajouter à la liste. Tu peux
            utiliser la plateforme dès maintenant.
          </p>
          <label className="block space-y-2">
            <span className="text-sm font-semibold">Direction régionale (DRE)</span>
            <select
              value={saisie.dre}
              onChange={(e) => changer({ dre: e.target.value, iesg: "" })}
              aria-invalid={Boolean(erreur) && !saisie.dre}
              className={LISTE}
            >
              <option value="">Choisis ta DRE</option>
              {dre.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.nom}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold">Inspection (IESG)</span>
            <select
              value={saisie.iesg}
              onChange={(e) => changer({ iesg: e.target.value })}
              disabled={!saisie.dre}
              aria-invalid={Boolean(erreur) && !saisie.iesg}
              className={LISTE}
            >
              <option value="">Choisis ton inspection</option>
              {inspections.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.nom}
                  {i.zone ? ` — ${i.zone}` : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold">Nom de l'établissement</span>
            <Input
              value={saisie.nom}
              onChange={(e) => changer({ nom: e.target.value })}
              aria-invalid={Boolean(erreur) && saisie.nom.trim().length < 2}
              maxLength={150}
              className={CHAMP}
            />
          </label>
          <button
            type="button"
            onClick={() => changer({ proposer: false })}
            className="text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            Revenir à la recherche
          </button>
        </div>
      ) : (
        <>
          <ChoixEtablissement
            valeur={saisie.choix}
            onChoix={(choix) => changer({ choix })}
            invalide={Boolean(erreur)}
          />
          {!saisie.choix && dre.length > 0 && (
            <button
              type="button"
              onClick={() => changer({ proposer: true })}
              className="text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              Je ne trouve pas mon établissement
            </button>
          )}
        </>
      )}
      {erreur && (
        <p role="alert" className="text-sm font-medium text-destructive">
          {erreur}
        </p>
      )}
    </fieldset>
  );
}
