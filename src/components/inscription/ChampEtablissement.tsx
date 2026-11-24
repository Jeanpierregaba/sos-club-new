import { School } from "lucide-react";

import { ChoixEtablissement } from "@/components/ChoixEtablissement";
import { CHAMP, LISTE } from "@/components/inscription/styles";
import { Input } from "@/components/ui/input";
import type { DrePublique } from "@/lib/api/client";
import type { SaisieEtablissement } from "@/lib/saisie-etablissement";
import { traduireValidation } from "@/lib/erreurs";
import { m } from "@/paraglide/messages.js";

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
        <School aria-hidden className="size-5" /> {m.etab_ton()}
      </legend>
      {saisie.proposer ? (
        <div className="space-y-4 rounded-2xl bg-mist-soft p-4">
          <p className="text-sm font-medium text-ink/80">{m.etab_verifiera()}</p>
          <label className="block space-y-2">
            <span className="text-sm font-semibold">{m.etab_dre()}</span>
            <select
              value={saisie.dre}
              onChange={(e) => changer({ dre: e.target.value, iesg: "" })}
              aria-invalid={Boolean(erreur) && !saisie.dre}
              className={LISTE}
            >
              <option value="">{m.etab_choisis_dre()}</option>
              {dre.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.nom}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold">{m.etab_iesg()}</span>
            <select
              value={saisie.iesg}
              onChange={(e) => changer({ iesg: e.target.value })}
              disabled={!saisie.dre}
              aria-invalid={Boolean(erreur) && !saisie.iesg}
              className={LISTE}
            >
              <option value="">{m.etab_choisis_iesg()}</option>
              {inspections.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.nom}
                  {i.zone ? ` — ${i.zone}` : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold">{m.etab_nom()}</span>
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
            {m.etab_revenir()}
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
              {m.etab_pas_trouve()}
            </button>
          )}
        </>
      )}
      {erreur && (
        <p role="alert" className="text-sm font-medium text-destructive">
          {traduireValidation(erreur)}
        </p>
      )}
    </fieldset>
  );
}
