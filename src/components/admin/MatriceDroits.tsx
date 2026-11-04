import { ShieldCheck } from "lucide-react";

import { cleDroit } from "@/lib/admin";
import type { Catalogue, Droit } from "@/lib/api/client";

// La grille des droits : modules en lignes, actions en colonnes. Les droits sensibles portent un bouclier :
// ils exigent la double authentification. Les modules « à venir » se préparent déjà.
export function MatriceDroits({
  catalogue,
  valeur,
  onChange,
  lectureSeule = false,
}: {
  catalogue: Catalogue;
  valeur: Set<string>;
  onChange?: (valeur: Set<string>) => void;
  lectureSeule?: boolean;
}) {
  const actions = Object.keys(catalogue.actions) as Droit["action"][];
  const sensibles = new Set(catalogue.sensibles.map(cleDroit));

  const basculer = (cle: string) => {
    const suivant = new Set(valeur);
    if (suivant.has(cle)) suivant.delete(cle);
    else suivant.add(cle);
    onChange?.(suivant);
  };

  return (
    <div className="overflow-x-auto rounded-2xl ring-1 ring-border">
      <table className="w-full min-w-[44rem] text-sm">
        <caption className="sr-only">Droits par module et par action</caption>
        <thead className="bg-mist-soft text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
          <tr>
            <th scope="col" className="px-3 py-2.5 text-left">
              Module
            </th>
            {actions.map((a) => (
              <th key={a} scope="col" className="px-1 py-2.5 text-center">
                {catalogue.actions[a]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {catalogue.modules.map((m) => (
            <tr key={m.id} className="border-t">
              <th scope="row" className="px-3 py-2 text-left font-bold">
                {m.libelle}
                {!m.disponible && (
                  <span className="ml-2 rounded-full bg-mist px-1.5 py-0.5 text-[10px] font-extrabold uppercase text-ink/60">
                    À venir
                  </span>
                )}
              </th>
              {actions.map((a) => {
                const cle = `${m.id}:${a}`;
                if (!m.actions.includes(a)) {
                  return (
                    <td key={a} className="text-center text-ink/20" aria-hidden>
                      ·
                    </td>
                  );
                }
                const sensible = sensibles.has(cle);
                return (
                  <td key={a} className="px-1 py-1.5 text-center">
                    <label className="relative inline-flex size-9 cursor-pointer items-center justify-center rounded-lg hover:bg-mist-soft">
                      <input
                        type="checkbox"
                        checked={valeur.has(cle)}
                        disabled={lectureSeule}
                        onChange={() => basculer(cle)}
                        aria-label={`${m.libelle} : ${catalogue.actions[a]}${sensible ? " (sensible)" : ""}`}
                        className="size-4 accent-[var(--primary)]"
                      />
                      {sensible && (
                        <ShieldCheck
                          aria-hidden
                          className="absolute right-0.5 top-0.5 size-3 text-logo-red"
                        />
                      )}
                    </label>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="flex items-center gap-1.5 border-t bg-mist-soft px-3 py-2 text-xs font-semibold text-ink/70">
        <ShieldCheck aria-hidden className="size-3.5 text-logo-red" /> Droit sensible : la double
        authentification est obligatoire.
      </p>
    </div>
  );
}
