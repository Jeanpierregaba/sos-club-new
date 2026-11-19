import type { StatistiquesCertification } from "@/lib/api/client";

const nombre = (n: number) => n.toLocaleString("fr-FR");
const pourcent = (x: number | null) => (x === null ? "—" : `${Math.round(x * 100)} %`);
const semaine = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });

function Tuile({ libelle, valeur }: { libelle: string; valeur: number }) {
  return (
    <div className="rounded-3xl bg-white p-4 shadow-sm ring-1 ring-border">
      <p className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
        {libelle}
      </p>
      <p className="mt-1 text-3xl font-extrabold text-logo-blue">{nombre(valeur)}</p>
    </div>
  );
}

function Section({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <section className="rounded-3xl bg-white p-4 shadow-sm ring-1 ring-border md:p-5">
      <h2 className="mb-3 text-lg font-extrabold">{titre}</h2>
      {children}
    </section>
  );
}

// Les chiffres du suivi des certifications (spec 043) : totaux, entonnoir des 20 places, DRE et semaines.
export function SuiviCertification({ stats }: { stats: StatistiquesCertification }) {
  const { totaux, entonnoir, par_dre, par_semaine } = stats;
  const plusTentes = Math.max(1, ...entonnoir.map((e) => e.tentes));
  const sansDre = totaux.candidats - par_dre.reduce((s, d) => s + d.candidats, 0);
  const plusSemaine = Math.max(1, ...par_semaine.map((s) => Math.max(s.candidats, s.certifies)));

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Tuile libelle="Candidats" valeur={totaux.candidats} />
        <Tuile libelle="Actifs sur 30 jours" valeur={totaux.actifs_30_jours} />
        <Tuile libelle="Badges délivrés" valeur={totaux.badges.reduce((s, b) => s + b.nombre, 0)} />
        <Tuile libelle="Certifiés" valeur={totaux.certifies} />
      </div>
      <ul className="flex flex-wrap gap-2" aria-label="Badges délivrés par badge">
        {totaux.badges.map((b) => (
          <li
            key={b.rang}
            className="rounded-full bg-mist-soft px-3 py-1.5 text-xs font-bold text-night"
          >
            {b.nom} : {nombre(b.nombre)}
          </li>
        ))}
      </ul>

      <Section titre="Entonnoir des 20 quiz">
        <ol className="grid gap-2" aria-label="Candidats par place">
          {entonnoir.map((e) => (
            <li
              key={e.place}
              className="grid gap-1 text-sm sm:grid-cols-[6rem_1fr_14rem] sm:items-center"
            >
              <span className="font-bold">Place {e.place}</span>
              {e.quiz_publie ? (
                <span
                  className="relative h-5 overflow-hidden rounded-full bg-mist-soft"
                  aria-hidden="true"
                >
                  <span
                    className="absolute inset-y-0 left-0 rounded-full bg-logo-blue/30"
                    style={{ width: `${(e.tentes / plusTentes) * 100}%` }}
                  />
                  <span
                    className="absolute inset-y-0 left-0 rounded-full bg-logo-blue"
                    style={{ width: `${(e.reussis / plusTentes) * 100}%` }}
                  />
                </span>
              ) : (
                <span className="text-xs font-semibold text-muted-foreground">
                  Pas de quiz publié
                </span>
              )}
              <span className="text-xs font-semibold text-muted-foreground">
                {nombre(e.tentes)} tentés · {nombre(e.reussis)} réussis ·{" "}
                {pourcent(e.taux_reussite)}
                {e.tentatives_avant_reussite !== null &&
                  ` · ${e.tentatives_avant_reussite.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} essais`}
              </span>
            </li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-muted-foreground">
          Barre claire : candidats qui ont tenté la place ; barre foncée : ceux qui l'ont réussie.
          Le taux compte les tentatives réussies sur les tentatives terminées ; les essais, le
          nombre moyen de tentatives jusqu'à la réussite.
        </p>
      </Section>

      <div className="grid gap-5 lg:grid-cols-2">
        <Section titre="Par DRE">
          {par_dre.length === 0 ? (
            <p className="text-sm font-semibold text-muted-foreground">Aucun candidat.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="py-2 pr-3">DRE</th>
                    <th className="py-2 pr-3 text-right">Candidats</th>
                    <th className="py-2 pr-3 text-right">Badges</th>
                    <th className="py-2 text-right">Certifiés</th>
                  </tr>
                </thead>
                <tbody>
                  {par_dre.map((d) => (
                    <tr key={d.code} className="border-t">
                      <td className="py-2 pr-3 font-bold">{d.dre}</td>
                      <td className="py-2 pr-3 text-right">{nombre(d.candidats)}</td>
                      <td className="py-2 pr-3 text-right">{nombre(d.badges)}</td>
                      <td className="py-2 text-right">{nombre(d.certifies)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {sansDre > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Et {nombre(sansDre)} candidat{sansDre > 1 ? "s" : ""} sans établissement rattaché.
                </p>
              )}
            </div>
          )}
        </Section>

        <Section titre="12 dernières semaines">
          <ol className="grid gap-1.5" aria-label="Nouveaux candidats et certifiés par semaine">
            {par_semaine.map((s) => (
              <li
                key={s.debut}
                className="grid grid-cols-[4.5rem_1fr_6.5rem] items-center gap-2 text-xs"
              >
                <span className="font-semibold text-muted-foreground">{semaine(s.debut)}</span>
                <span className="grid gap-0.5" aria-hidden="true">
                  <span
                    className="h-2 rounded-full bg-logo-blue"
                    style={{ width: `${(s.candidats / plusSemaine) * 100}%` }}
                  />
                  <span
                    className="h-2 rounded-full bg-leaf"
                    style={{ width: `${(s.certifies / plusSemaine) * 100}%` }}
                  />
                </span>
                <span className="text-right font-semibold">
                  {s.candidats} · {s.certifies}
                </span>
              </li>
            ))}
          </ol>
          <p className="mt-3 text-xs text-muted-foreground">
            En bleu, les nouveaux candidats ; en vert, les nouveaux certifiés (semaine du lundi).
          </p>
        </Section>
      </div>
    </div>
  );
}
