import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, Shield, Trophy } from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { dres } from "@/lib/togo-dre";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";

export const Route = createFileRoute("/genie-imhotep/hall-of-fame")({
  head: () => ({
    meta: [
      { title: "Hall of Fame — Génie Imhotep" },
      {
        name: "description",
        content:
          "Le tableau d'honneur du Championnat national Génie Imhotep : les délégations officielles des 7 régions éducatives du Togo, promotion 2026.",
      },
      { property: "og:title", content: "Hall of Fame du Génie Imhotep" },
    ],
  }),
  component: HallOfFame,
});

// Délégations reprises du palmarès du site de référence fourni par le porteur du projet (clubsante.ibdastudio.com).
// Les joueurs sont des élèves mineurs : la page ne montre que leur nombre (docs/RULES.md).
const delegations = [
  { dre: "grand-lome", lycee: "Lycée Adétikopé", titulaires: 6, remplacants: 4 },
  { dre: "maritime", lycee: "Lycée Dalavé", titulaires: 6, remplacants: 6 },
  { dre: "plateaux-est", lycee: "Lycée Wahala", titulaires: 6, remplacants: 7 },
  { dre: "plateaux-ouest", lycee: "Lycée Avétonou", titulaires: 6, remplacants: 6 },
  { dre: "centrale", lycee: "Lycée Tchamba", titulaires: 6, remplacants: 6 },
  { dre: "kara", lycee: "Lycée Scientifique de Kara", titulaires: 6, remplacants: 7 },
  { dre: "savanes", lycee: "Lycée Naki-Est", titulaires: 6, remplacants: 4 },
].map((d) => ({ ...d, region: dres.find((r) => r.id === d.dre)! }));

const ambassadeurs = delegations.reduce((n, d) => n + d.titulaires + d.remplacants, 0);
const titulaires = delegations.reduce((n, d) => n + d.titulaires, 0);

const chiffres = [
  { n: delegations.length, t: "Délégations régionales" },
  { n: ambassadeurs, t: "Ambassadeurs" },
  { n: titulaires, t: "Joueurs titulaires" },
  { n: 2026, t: "Promotion" },
];

function HallOfFame() {
  const [region, setRegion] = useState<string | null>(null);
  const visibles = delegations.filter((d) => !region || d.dre === region);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : la nuit, des rayons dorés qui tournent lentement et les mascottes aux trophées. */}
      <section className="relative isolate overflow-hidden bg-night text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-[70%] -z-10 size-[70rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_210_80/0.10)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite]"
        />
        <div
          aria-hidden
          className="absolute left-1/2 top-[75%] -z-10 size-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sun/30 blur-3xl"
        />
        <div className="mx-auto max-w-7xl px-5 pt-8 md:pt-12">
          <FilAriane rubrique="Génie Imhotep" page="Hall of Fame" clair />
          <div data-reveal className="mx-auto max-w-4xl pt-12 text-center lg:pt-16">
            <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
              <Trophy className="size-4" /> Hall of Fame · Palmarès national
            </p>
            <h1 className="mt-6 text-5xl leading-[0.95] md:text-7xl">
              <span className="block">Génie Imhotep</span>
              <span className="mt-2 block text-3xl text-sun md:text-5xl">
                Premier jeu de culture en santé publique
              </span>
            </h1>
            <p className="mt-6 font-hand text-3xl text-primary md:text-4xl">
              « C’est ici et maintenant »
            </p>
            <p className="mx-auto mt-4 max-w-2xl text-lg font-medium text-white/80">
              Promotion de la culture générale en santé publique auprès des adolescents et des
              jeunes.
            </p>
          </div>
          <img
            src={mascottesTrophees}
            alt="Les mascottes du Club Santé brandissent leurs trophées"
            width={1122}
            height={1402}
            data-reveal="zoom"
            className="mx-auto mt-8 w-64 drop-shadow-2xl md:w-80"
          />
        </div>
        <dl className="relative border-t border-white/10 bg-white/5 backdrop-blur">
          <div className="mx-auto grid max-w-7xl grid-cols-2 divide-white/10 px-5 md:grid-cols-4 md:divide-x">
            {chiffres.map((c) => (
              <div key={c.t} className="flex flex-col-reverse py-6 text-center md:py-8">
                <dt className="mt-2 text-sm font-bold text-white/70">{c.t}</dt>
                <dd className="font-display text-4xl leading-none text-sun md:text-5xl">{c.n}</dd>
              </div>
            ))}
          </div>
        </dl>
      </section>

      {/* Tableau d'honneur : une carte par délégation, aux couleurs de sa région. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <EnTete
          sur={`Délégations officielles · ${ambassadeurs} ambassadeurs`}
          bleu="Le tableau"
          vert="d’honneur"
        >
          Les délégations officielles de chaque région éducative : joueurs titulaires d’élite et
          remplaçants ou supporters dévoués.
        </EnTete>

        <div data-reveal className="mt-8 flex flex-wrap gap-2">
          {[null, ...delegations.map((d) => d.dre)].map((id) => {
            const d = delegations.find((x) => x.dre === id);
            const on = region === id;
            return (
              <button
                key={id ?? "toutes"}
                type="button"
                aria-pressed={on}
                onClick={() => setRegion(id)}
                className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                  on
                    ? "bg-night text-white shadow-card"
                    : "bg-white ring-1 ring-border hover:ring-night/30"
                }`}
              >
                {d && (
                  <span
                    className="size-2.5 rounded-full"
                    style={{ backgroundColor: d.region.couleur }}
                  />
                )}
                {d ? d.region.nom : "Toutes les régions"}
                <span className={on ? "text-white/60" : "text-muted-foreground"}>
                  {d ? d.titulaires + d.remplacants : ambassadeurs}
                </span>
              </button>
            );
          })}
        </div>

        <ul className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {visibles.map((d, i) => (
            <li
              key={d.dre}
              data-reveal
              style={retard(i % 3)}
              className="card-fx relative isolate overflow-hidden rounded-[2rem] bg-white p-7 shadow-card"
            >
              <span
                aria-hidden
                className="absolute inset-x-0 top-0 h-2"
                style={{ backgroundColor: d.region.couleur }}
              />
              <Trophy
                aria-hidden
                className="absolute -bottom-6 -right-6 -z-10 size-40 -rotate-12 text-sun/15"
              />
              <p className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                <span
                  className="size-2.5 rounded-full"
                  style={{ backgroundColor: d.region.couleur }}
                />
                DRE {d.region.nom} · Promotion 2026
              </p>
              <h3 className="mt-3 text-3xl leading-tight text-logo-blue">{d.lycee}</h3>
              <p className="mt-1 text-sm font-semibold text-muted-foreground">
                Délégation officielle de la région {d.region.nom}
              </p>

              <p className="mt-6 text-xs font-extrabold uppercase tracking-wider">
                Joueurs titulaires · {d.titulaires}
              </p>
              <ul className="mt-2 flex flex-wrap gap-2" aria-hidden>
                {Array.from({ length: d.titulaires }, (_, k) => (
                  <li
                    key={k}
                    className="inline-flex size-10 items-center justify-center rounded-xl font-display text-lg text-white shadow-sm"
                    style={{ backgroundColor: d.region.couleur }}
                  >
                    {k + 1}
                  </li>
                ))}
              </ul>
              <p className="mt-5 text-xs font-extrabold uppercase tracking-wider">
                Remplaçants & supporters · {d.remplacants}
              </p>
              <ul className="mt-2 flex flex-wrap gap-2" aria-hidden>
                {Array.from({ length: d.remplacants }, (_, k) => (
                  <li
                    key={k}
                    className="inline-flex size-9 items-center justify-center rounded-xl border-2 text-xs font-extrabold"
                    style={{ borderColor: d.region.couleur, color: d.region.couleur }}
                  >
                    R{k + 1}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>

        <p
          data-reveal
          className="mt-8 flex items-start gap-3 rounded-2xl bg-mist-soft p-5 text-sm font-semibold text-muted-foreground ring-1 ring-border"
        >
          <Shield aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-blue" />
          Pour protéger les élèves, les noms des joueurs ne sont pas publiés ici. Les délégations
          sont présentées par établissement.
        </p>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal="zoom"
          className="flex flex-col items-start justify-between gap-6 rounded-[2rem] bg-sun p-8 md:flex-row md:items-center md:p-12"
        >
          <div>
            <h2 className="text-3xl text-ink md:text-4xl">
              Et si ton lycée entrait au <span className="text-logo-blue">Hall of Fame</span> ?
            </h2>
            <p className="mt-2 max-w-2xl font-semibold text-ink/75">
              Les inscriptions au Championnat national passent par ton chef d’établissement ou les
              encadreurs de ton Club Santé.
            </p>
          </div>
          <a
            href="/genie-imhotep/inscription"
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            S’inscrire au championnat <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
