// Un bloc de la page « Activité » (spec 051) : chiffres comparés à la période précédente, courbes, tableaux et
// heatmaps. La forme est la même pour les 8 blocs : l'API décide du contenu, ce composant l'affiche.
import { Download, Info } from "lucide-react";

import { ecart, formater } from "@/lib/activite-admin";
import type { BlocActivite as Bloc } from "@/lib/api/client";

type Chiffre = Bloc["chiffres"][number];

const JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
const JOUR_COURT = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

// Vide : aucun chiffre ni sur la période ni sur la précédente, et aucune mesure dans les tableaux (le numéro d'une
// place de la certification n'est pas une mesure).
function estVide(bloc: Bloc): boolean {
  return (
    bloc.chiffres.every((c) => !c.valeur && !c.precedent) &&
    bloc.tableaux.every((t) =>
      t.lignes.every((l) =>
        t.colonnes.every((c) => c.unite === "texte" || c.cle === "place" || !l[c.cle]),
      ),
    ) &&
    bloc.series.every((s) => s.points.every((p) => !p.valeur)) &&
    bloc.grilles.every((g) => g.valeurs.every((ligne) => ligne.every((v) => !v)))
  );
}

function CarteChiffre({ chiffre }: { chiffre: Chiffre }) {
  const difference = ecart(chiffre);
  return (
    <div className="rounded-2xl bg-mist-soft p-4">
      <p className="text-sm font-semibold text-muted-foreground">{chiffre.libelle}</p>
      <p className="mt-1 font-display text-3xl text-logo-blue">
        {formater(chiffre.valeur, chiffre.unite)}
      </p>
      {difference && (
        <p
          className={`mt-1 text-xs font-bold ${
            difference.sens === "hausse"
              ? "text-primary"
              : difference.sens === "baisse"
                ? "text-logo-red"
                : "text-muted-foreground"
          }`}
        >
          {difference.texte}{" "}
          <span className="font-medium text-muted-foreground">vs période précédente</span>
        </p>
      )}
    </div>
  );
}

function Courbe({ serie }: { serie: Bloc["series"][number] }) {
  const max = Math.max(1, ...serie.points.map((p) => p.valeur));
  return (
    <figure className="rounded-2xl bg-mist-soft p-4">
      <figcaption className="text-sm font-bold text-ink">{serie.libelle}</figcaption>
      <div
        className="mt-3 flex h-28 items-end gap-px"
        role="img"
        aria-label={`${serie.libelle} par jour : ${formater(serie.points.reduce((t, p) => t + p.valeur, 0))} au total, ${formater(max)} au plus haut`}
      >
        {serie.points.map((p) => (
          <div
            key={p.jour}
            title={`${JOUR_COURT.format(new Date(p.jour))} : ${formater(p.valeur)}`}
            className="min-w-0 flex-1 rounded-t bg-primary/70 hover:bg-primary"
            style={{ height: `${(p.valeur / max) * 100}%` }}
          />
        ))}
      </div>
      {serie.points.length > 0 && (
        <div className="mt-1 flex justify-between text-xs text-muted-foreground">
          <span>{JOUR_COURT.format(new Date(serie.points[0]!.jour))}</span>
          <span>max {formater(max)}</span>
          <span>{JOUR_COURT.format(new Date(serie.points.at(-1)!.jour))}</span>
        </div>
      )}
    </figure>
  );
}

function TableauActivite({ tableau }: { tableau: Bloc["tableaux"][number] }) {
  return (
    <div className="overflow-hidden rounded-2xl ring-1 ring-border">
      <h4 className="bg-mist-soft px-4 py-2 text-sm font-bold text-ink">{tableau.titre}</h4>
      {tableau.lignes.length === 0 ? (
        <p className="px-4 py-3 text-sm text-muted-foreground">Rien sur cette période.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                {tableau.colonnes.map((c) => (
                  <th
                    key={c.cle}
                    scope="col"
                    className={`px-4 py-2 ${c.unite === "texte" ? "" : "text-right"}`}
                  >
                    {c.libelle}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableau.lignes.map((ligne, i) => (
                <tr key={i} className="border-t border-border">
                  {tableau.colonnes.map((c) => (
                    <td
                      key={c.cle}
                      className={`px-4 py-2 ${c.unite === "texte" ? "break-words font-medium" : "text-right tabular-nums"}`}
                    >
                      {formater(ligne[c.cle], c.unite)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Heatmap({ grille }: { grille: Bloc["grilles"][number] }) {
  const max = Math.max(1, ...grille.valeurs.flat());
  const jourMax = grille.valeurs.findIndex((ligne) => ligne.includes(max));
  const heureMax = jourMax >= 0 ? (grille.valeurs[jourMax] ?? []).indexOf(max) : -1;
  return (
    <figure className="rounded-2xl bg-mist-soft p-4">
      <figcaption className="text-sm font-bold text-ink">{grille.titre}</figcaption>
      <p className="sr-only">
        {jourMax >= 0
          ? `Moment le plus chargé : ${JOURS[jourMax]} à ${heureMax} h, ${formater(max)}.`
          : "Aucune activité sur la période."}
      </p>
      <div className="mt-3 overflow-x-auto">
        <div
          aria-hidden
          className="grid min-w-[520px] grid-cols-[2.5rem_repeat(24,minmax(0,1fr))] gap-0.5 text-[10px]"
        >
          <span />
          {Array.from({ length: 24 }, (_, h) => (
            <span key={h} className="text-center text-muted-foreground">
              {h % 3 === 0 ? `${h}h` : ""}
            </span>
          ))}
          {grille.valeurs.map((ligne, j) => (
            <div key={j} className="contents">
              <span className="font-semibold text-muted-foreground">{JOURS[j]}</span>
              {ligne.map((v, h) => (
                <span
                  key={h}
                  title={`${JOURS[j]} ${h}h : ${formater(v)}`}
                  className="aspect-square rounded-sm bg-primary"
                  style={{ opacity: v ? 0.15 + 0.85 * (v / max) : 0.05 }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </figure>
  );
}

export function BlocActivite({
  titre,
  bloc,
  urlExport,
}: {
  titre: string;
  bloc: Bloc;
  urlExport: string;
}) {
  const vide = estVide(bloc);
  return (
    <section
      aria-labelledby={`bloc-${bloc.bloc}`}
      className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border sm:p-7"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id={`bloc-${bloc.bloc}`} className="text-xl text-logo-blue">
          {titre}
        </h2>
        <a
          href={urlExport}
          download
          className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-bold text-logo-blue ring-1 ring-border hover:bg-mist-soft"
        >
          <Download aria-hidden className="size-4" /> CSV
        </a>
      </div>
      {vide ? (
        <p className="mt-4 rounded-2xl bg-mist-soft p-4 text-sm font-semibold text-muted-foreground">
          Pas encore de données sur cette période.
        </p>
      ) : (
        <div className="mt-5 space-y-5">
          {bloc.chiffres.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {bloc.chiffres.map((c) => (
                <CarteChiffre key={c.cle} chiffre={c} />
              ))}
            </div>
          )}
          {bloc.series.length > 0 && (
            <div className="grid gap-3 lg:grid-cols-2">
              {bloc.series.map((s) => (
                <Courbe key={s.cle} serie={s} />
              ))}
            </div>
          )}
          {bloc.grilles.map((g) => (
            <Heatmap key={g.cle} grille={g} />
          ))}
          {bloc.tableaux.length > 0 && (
            <div className="grid gap-4 xl:grid-cols-2">
              {bloc.tableaux.map((t) => (
                <TableauActivite key={t.cle} tableau={t} />
              ))}
            </div>
          )}
        </div>
      )}
      {bloc.notes.map((note) => (
        <p key={note} className="mt-4 flex gap-2 text-xs font-medium text-muted-foreground">
          <Info aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          {note}
        </p>
      ))}
    </section>
  );
}
