import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, MapPin, Search, X } from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion } from "@/components/SiteMotion";
import { dres, grandLome, type Dre } from "@/lib/togo-dre";
import { etablissements, type TypeEtablissement } from "@/lib/etablissements";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";

export const Route = createFileRoute("/carte-des-clubs")({
  head: () => ({
    meta: [
      { title: "Carte des clubs — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Carte des Clubs Santé SOS Docteur TV au Togo : les 7 Directions Régionales de l'Éducation, leurs 19 IESG et les 844 collèges et lycées du réseau.",
      },
      { property: "og:title", content: "La carte des Clubs Santé du Togo" },
    ],
  }),
  component: CarteDesClubs,
});

const types: Record<TypeEtablissement, { t: string; c: string }> = {
  lycee: { t: "Lycée", c: "text-sky" },
  college: { t: "Collège", c: "text-primary" },
  complexe: { t: "Complexe", c: "text-tangerine" },
  autre: { t: "Établissement", c: "text-muted-foreground" },
};

const totalClubs = dres.reduce((n, r) => n + r.clubs, 0);
const totalIesg = dres.reduce((n, r) => n + r.iesg.length, 0);
const chiffres = [
  { n: dres.length, t: "Directions régionales" },
  { n: totalIesg, t: "Inspections (IESG)" },
  { n: totalClubs, t: "Collèges & lycées" },
];

// Comparaison sans accents ni majuscules, pour que « agoe » trouve « Agoè ».
const normaliser = (s: string) =>
  s
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

const index = dres.flatMap((d) =>
  d.iesg.flatMap((i) =>
    (etablissements[i.nom] ?? []).map((e) => ({
      ...e,
      iesg: i.nom,
      dre: d,
      cle: normaliser(e.nom),
    })),
  ),
);

const APERCU = 30;

function CarteDesClubs() {
  const [dre, setDre] = useState<Dre>(grandLome);
  const [iesg, setIesg] = useState(grandLome.iesg[0]?.nom ?? "");
  const [type, setType] = useState<TypeEtablissement | null>(null);
  const [toutVoir, setToutVoir] = useState(false);
  const [recherche, setRecherche] = useState("");

  const choisir = (d: Dre, i = d.iesg[0]?.nom ?? "") => {
    setDre(d);
    setIesg(i);
    setType(null);
    setToutVoir(false);
    setRecherche("");
  };

  // Amène sous les yeux la colonne où s'affichent la région choisie ou les résultats d'une recherche lancée dans la bannière.
  const montrerExplorateur = () =>
    document.getElementById("explorateur")?.scrollIntoView({ behavior: "smooth" });

  const liste = etablissements[iesg] ?? [];
  const filtres = (Object.keys(types) as TypeEtablissement[])
    .map((t) => ({ t, n: liste.filter((e) => e.type === t).length }))
    .filter((f) => f.n > 0);
  const affiches = liste.filter((e) => !type || e.type === type);
  const visibles = toutVoir ? affiches : affiches.slice(0, APERCU);

  const q = normaliser(recherche.trim());
  const resultats = useMemo(
    () => (q.length < 2 ? [] : index.filter((e) => e.cle.includes(q))),
    [q],
  );

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : titre, recherche et chiffres à gauche ; les mascottes à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue to-night text-white">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_55%)]" />
          <div className="absolute -right-40 top-1/2 size-[46rem] -translate-y-1/2 rounded-full border-[3rem] border-white/5" />
          <div className="absolute -right-8 top-1/2 size-[30rem] -translate-y-1/2 rounded-full border-2 border-dashed border-white/15" />
          <div className="absolute -bottom-24 left-1/4 size-80 rounded-full bg-primary/25 blur-3xl" />
        </div>

        <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 pb-16 pt-8 md:pt-12 lg:grid-cols-[1.2fr_1fr] lg:pb-20">
          <div>
            <FilAriane rubrique="Vie du club" page="Carte des clubs" clair />
            <div data-reveal="left" className="pt-10 lg:pt-14">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-bold backdrop-blur-sm">
                <MapPin className="size-4 text-sun" /> Réseau national · Togo
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">La carte</span>
                <span className="block text-sun">des clubs santé</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/80">
                Les clubs santé de chaque Direction Régionale de l’Éducation et de chaque Inspection
                (IESG). Choisis ta région sur la carte, ou cherche directement ton établissement.
              </p>

              {/* Entrée amène les résultats, affichés dans l'explorateur, sous les yeux. */}
              <form
                role="search"
                onSubmit={(e) => {
                  e.preventDefault();
                  montrerExplorateur();
                }}
                className="relative mt-8 max-w-xl"
              >
                <Search
                  aria-hidden
                  className="pointer-events-none absolute left-5 top-1/2 size-5 -translate-y-1/2 text-muted-foreground"
                />
                <input
                  type="text"
                  enterKeyHint="search"
                  value={recherche}
                  onChange={(e) => setRecherche(e.target.value)}
                  placeholder="Cherche ton collège ou lycée…"
                  aria-label="Rechercher un établissement"
                  className="h-14 w-full rounded-full border-2 border-transparent bg-white pl-14 pr-14 text-base font-semibold text-ink shadow-card outline-none transition placeholder:font-medium placeholder:text-muted-foreground focus:border-sun"
                />
                {recherche && (
                  <button
                    type="button"
                    onClick={() => setRecherche("")}
                    aria-label="Effacer la recherche"
                    className="absolute right-3 top-1/2 inline-flex size-9 -translate-y-1/2 items-center justify-center rounded-full text-muted-foreground transition hover:bg-mist hover:text-ink"
                  >
                    <X className="size-4" />
                  </button>
                )}
              </form>

              <dl className="mt-8 grid max-w-xl grid-cols-3 gap-2 sm:gap-3">
                {chiffres.map((c) => (
                  <div
                    key={c.t}
                    className="flex flex-col-reverse rounded-2xl border border-white/15 bg-white/10 p-3 backdrop-blur-sm sm:p-4"
                  >
                    <dt className="mt-1.5 text-xs font-bold leading-tight text-white/75 sm:text-sm">
                      {c.t}
                    </dt>
                    <dd className="font-display text-3xl leading-none text-sun md:text-4xl">
                      {c.n}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>

          {/* Les sept mascottes, posées sur le bas de la bannière. */}
          <img
            data-reveal="right"
            src={mascottesEquipe}
            alt="Les sept mascottes des Clubs Santé, en polo du club : trophée, trousse de secours, plante, mégaphone, micro"
            width={1122}
            height={1402}
            className="mx-auto -mb-16 w-full max-w-xs self-end drop-shadow-[0_24px_40px_oklch(0_0_0/0.35)] sm:max-w-sm lg:-mb-24 lg:max-w-md"
          />
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-8 px-5 pb-20 pt-12 lg:grid-cols-[19rem_1fr]">
        {/* Carte et liste des régions : la liste sert aussi au clavier et aux lecteurs d'écran. */}
        <aside
          data-reveal="left"
          className="grid grid-cols-[6.5rem_1fr] items-center gap-5 self-start rounded-[2rem] border bg-white p-5 sm:grid-cols-[8rem_1fr] lg:sticky lg:top-24 lg:grid-cols-1"
        >
          <svg
            viewBox="0 0 250 640"
            aria-hidden
            className="mx-auto w-full overflow-visible lg:max-w-44"
          >
            {[...dres.filter((r) => r.id !== dre.id), dre].map((r) => (
              <path
                key={r.id}
                d={r.d}
                fill={r.couleur}
                onClick={() => choisir(r)}
                strokeLinejoin="round"
                className={`cursor-pointer transition-[opacity,stroke-width] duration-200 ${
                  r.id === dre.id
                    ? "stroke-ink stroke-[2.5]"
                    : "stroke-white stroke-[1.5] opacity-35 hover:opacity-70"
                }`}
              />
            ))}
          </svg>
          <ul className="grid gap-0.5">
            {dres.map((r) => {
              const on = r.id === dre.id;
              return (
                <li key={r.id}>
                  <button
                    type="button"
                    aria-pressed={on}
                    onClick={() => choisir(r)}
                    className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition ${
                      on
                        ? "bg-mist font-extrabold text-logo-blue"
                        : "font-semibold hover:bg-mist-soft"
                    }`}
                  >
                    <span
                      className="size-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: r.couleur }}
                    />
                    <span className="flex-1">{r.nom}</span>
                    <span className="tabular-nums text-muted-foreground">{r.clubs}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <div id="explorateur" data-reveal="right" className="min-w-0 scroll-mt-24">
          {q.length >= 2 ? (
            <div className="rounded-[2rem] border bg-white p-6 md:p-8">
              <p aria-live="polite" className="font-bold">
                {resultats.length === 0
                  ? `Aucun établissement ne correspond à « ${recherche.trim()} ».`
                  : `${resultats.length} établissement${resultats.length > 1 ? "s" : ""} pour « ${recherche.trim()} »`}
              </p>
              {resultats.length > 0 && (
                <ul className="mt-5 divide-y border-y">
                  {resultats.slice(0, 50).map((e, k) => (
                    <li key={`${e.iesg}-${e.nom}-${k}`}>
                      <button
                        type="button"
                        onClick={() => choisir(e.dre, e.iesg)}
                        className="group flex w-full items-center gap-4 py-3.5 text-left"
                      >
                        <MapPin
                          aria-hidden
                          className="size-4 shrink-0"
                          style={{ color: e.dre.couleur }}
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block font-bold group-hover:text-logo-blue">
                            {e.nom}
                          </span>
                          <span className="block text-sm text-muted-foreground">
                            {e.iesg} · DRE {e.dre.nom}
                          </span>
                        </span>
                        <span className={`text-xs font-extrabold uppercase ${types[e.type].c}`}>
                          {types[e.type].t}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {resultats.length > 50 && (
                <p className="mt-4 text-sm font-semibold text-muted-foreground">
                  Précise ta recherche pour voir les {resultats.length - 50} autres.
                </p>
              )}
            </div>
          ) : (
            <div
              key={dre.id}
              className="rounded-[2rem] border bg-white p-6 animate-in fade-in duration-300 md:p-10"
            >
              <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-3">
                <div>
                  <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
                    <span
                      className="size-2.5 rounded-full"
                      style={{ backgroundColor: dre.couleur }}
                    />
                    Direction régionale de l’éducation
                  </p>
                  <h2 className="mt-2 text-4xl md:text-5xl">
                    <span className="text-logo-blue">DRE</span>{" "}
                    <span className="text-primary">{dre.nom}</span>
                  </h2>
                </div>
                <p className="text-sm font-semibold text-muted-foreground">
                  <strong className="text-ink">{dre.clubs}</strong> établissements ·{" "}
                  <strong className="text-ink">{dre.iesg.length}</strong> IESG ·{" "}
                  <strong className="text-ink">
                    {Math.round((dre.clubs / totalClubs) * 100)} %
                  </strong>{" "}
                  du réseau
                </p>
              </div>

              <div
                role="group"
                aria-label="Inspections de la région"
                className="mt-8 flex flex-wrap gap-2"
              >
                {dre.iesg.map((i) => {
                  const on = i.nom === iesg;
                  return (
                    <button
                      key={i.nom}
                      type="button"
                      aria-pressed={on}
                      onClick={() => choisir(dre, i.nom)}
                      className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                        on
                          ? "bg-logo-blue text-white"
                          : "bg-mist-soft text-ink ring-1 ring-border hover:ring-logo-blue/40"
                      }`}
                    >
                      {i.nom}{" "}
                      <span className={on ? "text-white/70" : "text-muted-foreground"}>
                        {i.clubs}
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-3 text-sm font-bold">
                {[{ t: null, n: liste.length }, ...filtres].map((f) => {
                  const on = type === f.t;
                  return (
                    <button
                      key={f.t ?? "tous"}
                      type="button"
                      aria-pressed={on}
                      onClick={() => {
                        setType(f.t);
                        setToutVoir(false);
                      }}
                      className={`border-b-2 pb-1 transition ${
                        on
                          ? "border-logo-blue text-logo-blue"
                          : "border-transparent text-muted-foreground hover:text-ink"
                      }`}
                    >
                      {f.t ? `${types[f.t].t}s` : "Tous"}{" "}
                      <span className="font-semibold">({f.n})</span>
                    </button>
                  );
                })}
              </div>

              <ol className="mt-4 grid border-t sm:grid-cols-2 sm:gap-x-8 xl:grid-cols-3">
                {visibles.map((e, k) => (
                  <li
                    key={`${e.nom}-${k}`}
                    className="flex items-baseline gap-3 border-b border-border/60 py-3"
                  >
                    <span className="w-6 shrink-0 text-right text-xs font-bold tabular-nums text-muted-foreground">
                      {k + 1}
                    </span>
                    <span className="min-w-0 flex-1 font-semibold leading-snug">{e.nom}</span>
                    <span className={`text-[11px] font-extrabold uppercase ${types[e.type].c}`}>
                      {types[e.type].t}
                    </span>
                  </li>
                ))}
              </ol>
              {affiches.length > APERCU && (
                <button
                  type="button"
                  onClick={() => setToutVoir((v) => !v)}
                  className="mt-6 text-sm font-bold text-logo-blue underline underline-offset-4 hover:text-primary"
                >
                  {toutVoir
                    ? "Réduire la liste"
                    : `Afficher les ${affiches.length - APERCU} autres`}
                </button>
              )}
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal
          className="flex flex-col items-start justify-between gap-6 rounded-[2rem] bg-logo-blue p-8 text-white md:flex-row md:items-center md:p-10"
        >
          <div>
            <h2 className="text-3xl md:text-4xl">
              Ton établissement <span className="text-sun">n’a pas encore de club ?</span>
            </h2>
            <p className="mt-2 font-medium text-white/80">
              Parles-en à ton chef d’établissement : l’affiliation se fait auprès de ta DRE et de la
              coordination nationale.
            </p>
          </div>
          <a
            href="/club-sante#adhesion"
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            Voir les règles d’adhésion <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
