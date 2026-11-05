import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, MapPin, Search, X } from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import { chargerAnnuaire, chargerClubsPublics, type TypeEtablissement } from "@/lib/api/client";
import { chercher, compterParType, indexer } from "@/lib/carte-des-clubs";
import { clubsParEtablissement, LIBELLE_SANS_CLUB } from "@/lib/clubs";
import { DRE_PAR_DEFAUT, dessins, regions } from "@/lib/togo-dre";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";

export const Route = createFileRoute("/carte-des-clubs")({
  head: () => ({
    meta: [
      { title: "Carte des clubs — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Carte des Clubs Santé SOS Docteur TV au Togo : les Directions Régionales de l'Éducation, leurs IESG et les collèges et lycées du réseau.",
      },
      { property: "og:title", content: "La carte des Clubs Santé du Togo" },
    ],
  }),
  // L'annuaire et les clubs actifs viennent de l'API (specs 016 et 019). Sans elle, la carte garde ses
  // contours et l'explique ; l'échec des clubs (null) ne doit ni casser l'annuaire ni afficher, à tort,
  // « aucun club » partout.
  loader: async () => {
    const [annuaire, clubs] = await Promise.all([
      chargerAnnuaire().catch(() => null),
      chargerClubsPublics().catch(() => null),
    ]);
    return { annuaire, clubs };
  },
  component: CarteDesClubs,
});

const types: Record<TypeEtablissement, { t: string; c: string }> = {
  lycee: { t: "Lycée", c: "text-sky" },
  college: { t: "Collège", c: "text-primary" },
  complexe: { t: "Complexe", c: "text-tangerine" },
  autre: { t: "Établissement", c: "text-muted-foreground" },
};
const ORDRE_TYPES = Object.keys(types) as TypeEtablissement[];

const APERCU = 30;

function CarteDesClubs() {
  const { annuaire, clubs } = Route.useLoaderData();
  const dres = useMemo(() => regions(annuaire ?? []), [annuaire]);
  const index = useMemo(() => indexer(dres), [dres]);
  const clubParEtablissement = useMemo(
    () => (clubs ? clubsParEtablissement(clubs) : new Map()),
    [clubs],
  );
  const listeClubs = clubs ?? [];
  const totalClubs = dres.reduce((n, r) => n + r.nb_etablissements, 0);
  const chiffres = [
    { n: dres.length, t: "Directions régionales" },
    { n: dres.reduce((n, r) => n + r.iesg.length, 0), t: "Inspections (IESG)" },
    { n: totalClubs, t: "Collèges & lycées" },
    { n: listeClubs.length, t: "Clubs actifs" },
  ];

  const [code, setCode] = useState(DRE_PAR_DEFAUT);
  const [iesgId, setIesgId] = useState<string | null>(null);
  const [type, setType] = useState<TypeEtablissement | null>(null);
  const [toutVoir, setToutVoir] = useState(false);
  const [recherche, setRecherche] = useState("");

  const dre = dres.find((r) => r.code === code) ?? dres[0];
  const iesg = dre?.iesg.find((i) => i.id === iesgId) ?? dre?.iesg[0];
  const clubsDeLaDre = dre
    ? listeClubs.filter((club) => club.etablissement.dre_code === dre.code).length
    : 0;

  const choisir = (codeDre: string, idIesg: string | null = null) => {
    setCode(codeDre);
    setIesgId(idIesg);
    setType(null);
    setToutVoir(false);
    setRecherche("");
  };

  // Amène sous les yeux la colonne où s'affichent la région choisie ou les résultats d'une recherche lancée dans la bannière.
  const montrerExplorateur = () =>
    document.getElementById("explorateur")?.scrollIntoView({ behavior: "smooth" });

  const liste = iesg?.etablissements ?? [];
  const filtres = compterParType(liste, ORDRE_TYPES);
  const affiches = liste.filter((e) => !type || e.type === type);
  const visibles = toutVoir ? affiches : affiches.slice(0, APERCU);

  const q = recherche.trim();
  const resultats = useMemo(() => chercher(index, q), [index, q]);
  const enRecherche = q.replace(/\s/g, "").length >= 2;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : titre, recherche et chiffres à gauche ; les mascottes à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue to-night text-white">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_55%)] motion-safe:animate-defile-motif" />
          <div className="absolute -right-40 top-1/2 size-[46rem] -translate-y-1/2 rounded-full border-[3rem] border-white/5 motion-safe:animate-respire" />
          <div className="absolute -right-8 top-1/2 size-[30rem] -translate-y-1/2 rounded-full border-2 border-dashed border-white/15 motion-safe:animate-[spin_60s_linear_infinite]" />
          <div className="absolute -bottom-24 left-1/4 size-80 rounded-full bg-primary/25 blur-3xl motion-safe:animate-derive" />
        </div>
        <DecorAnime />

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
                Les Clubs Santé actifs de chaque Direction Régionale de l’Éducation et de chaque
                Inspection (IESG). Choisis ta région sur la carte, ou cherche directement ton
                établissement.
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

              {dre && (
                <dl className="mt-8 grid max-w-xl grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
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
              )}
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
            {dre
              ? [...dres.filter((r) => r.code !== dre.code), dre].map((r) => (
                  <path
                    key={r.code}
                    d={r.d}
                    fill={r.couleur}
                    onClick={() => choisir(r.code)}
                    strokeLinejoin="round"
                    className={`cursor-pointer transition-[opacity,stroke-width] duration-200 ${
                      r.code === dre.code
                        ? "stroke-ink stroke-[2.5]"
                        : "stroke-white stroke-[1.5] opacity-35 hover:opacity-70"
                    }`}
                  />
                ))
              : Object.entries(dessins).map(([id, r]) => (
                  <path
                    key={id}
                    d={r.d}
                    fill={r.couleur}
                    strokeLinejoin="round"
                    className="stroke-white stroke-[1.5] opacity-35"
                  />
                ))}
          </svg>
          <ul className="grid gap-0.5">
            {dres.map((r) => {
              const on = r.code === dre?.code;
              return (
                <li key={r.code}>
                  <button
                    type="button"
                    aria-pressed={on}
                    onClick={() => choisir(r.code)}
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
                    <span className="tabular-nums text-muted-foreground">
                      {r.nb_etablissements}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <div id="explorateur" data-reveal="right" className="min-w-0 scroll-mt-24">
          {!dre ? (
            <div className="rounded-[2rem] border bg-white p-6 md:p-10">
              <p role="status" className="font-bold">
                La liste des établissements est momentanément indisponible. Réessaie dans quelques
                instants.
              </p>
            </div>
          ) : enRecherche ? (
            <div className="rounded-[2rem] border bg-white p-6 md:p-8">
              <p aria-live="polite" className="font-bold">
                {resultats.length === 0
                  ? `Aucun établissement ne correspond à « ${q} ».`
                  : `${resultats.length} établissement${resultats.length > 1 ? "s" : ""} pour « ${q} »`}
              </p>
              {resultats.length > 0 && (
                <ul className="mt-5 divide-y border-y">
                  {resultats.slice(0, 50).map((e) => {
                    const club = clubParEtablissement.get(e.id);
                    return (
                      <li key={e.id} className="flex items-center gap-3 py-3.5">
                        <MapPin
                          aria-hidden
                          className="size-4 shrink-0"
                          style={{ color: e.dre.couleur }}
                        />
                        <button
                          type="button"
                          onClick={() => choisir(e.dre.code, e.iesg.id)}
                          className="group min-w-0 flex-1 text-left"
                        >
                          <span className="block font-bold group-hover:text-logo-blue">
                            {e.nom}
                          </span>
                          <span className="block text-sm text-muted-foreground">
                            {e.iesg.nom} · DRE {e.dre.nom}
                          </span>
                          {club ? (
                            <span className="block text-xs font-bold text-primary">{club.nom}</span>
                          ) : clubs ? (
                            <span className="block text-xs font-medium text-muted-foreground">
                              {LIBELLE_SANS_CLUB}
                            </span>
                          ) : null}
                        </button>
                        <span className="flex shrink-0 flex-col items-end gap-1.5">
                          <span className={`text-xs font-extrabold uppercase ${types[e.type].c}`}>
                            {types[e.type].t}
                          </span>
                          {club && (
                            <Link
                              to="/clubs/$id"
                              params={{ id: club.id }}
                              className="inline-flex items-center gap-1 text-xs font-bold text-logo-blue hover:underline"
                            >
                              Fiche <ArrowRight aria-hidden className="size-3.5" />
                            </Link>
                          )}
                        </span>
                      </li>
                    );
                  })}
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
              key={dre.code}
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
                  <strong className="text-ink">{dre.nb_etablissements}</strong> établissements ·{" "}
                  <strong className="text-ink">{dre.iesg.length}</strong> IESG ·{" "}
                  <strong className="text-ink">{clubsDeLaDre}</strong>{" "}
                  {clubsDeLaDre === 1 ? "club actif" : "clubs actifs"} ·{" "}
                  <strong className="text-ink">
                    {Math.round((dre.nb_etablissements / (totalClubs || 1)) * 100)} %
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
                  const on = i.id === iesg?.id;
                  return (
                    <button
                      key={i.id}
                      type="button"
                      aria-pressed={on}
                      onClick={() => choisir(dre.code, i.id)}
                      className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                        on
                          ? "bg-logo-blue text-white"
                          : "bg-mist-soft text-ink ring-1 ring-border hover:ring-logo-blue/40"
                      }`}
                    >
                      {i.nom}{" "}
                      <span className={on ? "text-white/70" : "text-muted-foreground"}>
                        {i.nb_etablissements}
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
                {visibles.map((e, k) => {
                  const club = clubParEtablissement.get(e.id);
                  return (
                    <li
                      key={e.id}
                      className="flex items-start gap-3 border-b border-border/60 py-3"
                    >
                      <span className="w-6 shrink-0 pt-0.5 text-right text-xs font-bold tabular-nums text-muted-foreground">
                        {k + 1}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-baseline justify-between gap-2">
                          <span className="font-semibold leading-snug">{e.nom}</span>
                          <span
                            className={`shrink-0 text-[11px] font-extrabold uppercase ${types[e.type].c}`}
                          >
                            {types[e.type].t}
                          </span>
                        </span>
                        {club ? (
                          <Link
                            to="/clubs/$id"
                            params={{ id: club.id }}
                            className="mt-0.5 inline-flex items-center gap-1 text-xs font-bold text-logo-blue hover:underline"
                          >
                            {club.nom} <ArrowRight aria-hidden className="size-3" />
                          </Link>
                        ) : clubs ? (
                          <span className="mt-0.5 block text-xs font-medium text-muted-foreground">
                            {LIBELLE_SANS_CLUB}
                          </span>
                        ) : null}
                      </span>
                    </li>
                  );
                })}
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
