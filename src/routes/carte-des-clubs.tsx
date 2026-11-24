import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, MapPin, Search, X } from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import {
  chargerAnnuaire,
  chargerCarteClubs,
  type Carte,
  type CarteEtablissement,
  type TypeEtablissement,
} from "@/lib/api/client";
import { chercher, compterParType, indexer } from "@/lib/carte-des-clubs";
import { libelleSansClub, STATUTS_CARTE } from "@/lib/clubs";
import { auSingulier, lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";
import { DRE_PAR_DEFAUT, dessins, regions } from "@/lib/togo-dre";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { useRechercheSansResultat } from "@/lib/activite";

export const Route = createFileRoute("/carte-des-clubs")({
  head: () => ({
    meta: [
      { title: m.carte_clubs_meta_titre() },
      { name: "description", content: m.carte_clubs_meta_description() },
      { property: "og:title", content: m.carte_clubs_meta_og() },
    ],
  }),
  // L'annuaire et la carte des clubs viennent de l'API (specs 016 et 033). Sans elle, la carte garde ses
  // contours et l'explique ; l'échec des clubs (null) ne doit ni casser l'annuaire, ni afficher de chiffre
  // inventé, ni dire à tort « aucun club » partout.
  loader: async () => {
    const [annuaire, carte] = await Promise.all([
      chargerAnnuaire().catch(() => null),
      chargerCarteClubs().catch(() => null),
    ]);
    return { annuaire, carte };
  },
  component: CarteDesClubs,
});

// Les libellés sont lus à l'affichage, dans la langue de la page (spec 052).
const type = (t: () => string, pluriel: () => string, c: string) => ({
  get t() {
    return t();
  },
  get pluriel() {
    return pluriel();
  },
  c,
});
const types: Record<
  TypeEtablissement,
  { readonly t: string; readonly pluriel: string; c: string }
> = {
  lycee: type(m.carte_clubs_type_lycee, m.carte_clubs_type_lycees, "text-sky"),
  college: type(m.carte_clubs_type_college, m.carte_clubs_type_colleges, "text-primary"),
  complexe: type(m.carte_clubs_type_complexe, m.carte_clubs_type_complexes, "text-tangerine"),
  autre: type(m.carte_clubs_type_autre, m.carte_clubs_type_autres, "text-muted-foreground"),
};
const ORDRE_TYPES = Object.keys(types) as TypeEtablissement[];

const APERCU = 30;

type EtatFiltre = "tous" | "actif" | "en_constitution";
const etats = (): { v: EtatFiltre; t: string }[] => [
  { v: "tous", t: m.carte_clubs_etat_tous() },
  { v: "actif", t: m.carte_clubs_etat_actif() },
  { v: "en_constitution", t: m.carte_clubs_etat_constitution() },
];

// Les statuts des établissements et les clubs actifs de chaque DRE, lus dans la carte de l'API.
function lireCarte(carte: Carte | null) {
  const statuts = new Map<string, CarteEtablissement>();
  const actifsDe = new Map<string, number>();
  for (const region of carte?.regions ?? [])
    for (const dre of region.dres) {
      actifsDe.set(dre.code, dre.nb_actifs);
      for (const iesg of dre.iesg) for (const e of iesg.etablissements) statuts.set(e.id, e);
    }
  return { statuts, actifsDe };
}

function StatutEtablissement({ statut }: { statut: CarteEtablissement | undefined }) {
  if (!statut) return null;
  if (statut.statut === "reference")
    return (
      <span className="mt-0.5 block text-xs font-medium text-muted-foreground">
        {statut.declare_terrain ? m.carte_clubs_declare() : libelleSansClub()}
      </span>
    );
  const pastille = STATUTS_CARTE[statut.statut];
  return (
    <span className="mt-1 flex flex-wrap items-center gap-2">
      <span className={`rounded-full px-2 py-0.5 text-[11px] font-extrabold ${pastille.classe}`}>
        {pastille.libelle}
      </span>
      {statut.club_id && (
        <Link
          to="/clubs/$id"
          params={{ id: statut.club_id }}
          className="inline-flex items-center gap-1 text-xs font-bold text-logo-blue hover:underline"
        >
          {m.carte_clubs_fiche()} <ArrowRight aria-hidden className="size-3" />
        </Link>
      )}
    </span>
  );
}

function CarteDesClubs() {
  const { annuaire, carte } = Route.useLoaderData();
  const toutes = useMemo(() => regions(annuaire ?? []), [annuaire]);
  const { statuts, actifsDe } = useMemo(() => lireCarte(carte), [carte]);
  const dres = toutes;
  const index = useMemo(() => indexer(toutes), [toutes]);
  const totalEtablissements = toutes.reduce((n, r) => n + r.nb_etablissements, 0);
  // Les trois chiffres du cahier des charges (spec 033), tous calculés par l'API ; sans elle, aucun chiffre.
  const chiffres = carte
    ? [
        { n: carte.chiffres.etablissements, t: m.carte_clubs_chiffre_etablissements() },
        { n: carte.chiffres.clubs, t: m.carte_clubs_chiffre_clubs() },
        { n: carte.chiffres.clubs_actifs, t: m.carte_clubs_chiffre_actifs() },
      ]
    : [];

  const [code, setCode] = useState(DRE_PAR_DEFAUT);
  const [iesgId, setIesgId] = useState<string | null>(null);
  const [type, setType] = useState<TypeEtablissement | null>(null);
  const [toutVoir, setToutVoir] = useState(false);
  const [recherche, setRecherche] = useState("");
  // Dans la DRE affichée : la recherche par nom (toutes ses IESG) et l'état du club.
  const [rechercheDre, setRechercheDre] = useState("");
  const [etat, setEtat] = useState<EtatFiltre>("tous");

  const dre = dres.find((r) => r.code === code) ?? dres[0];
  const iesg = dre?.iesg.find((i) => i.id === iesgId) ?? dre?.iesg[0];
  const clubsDeLaDre = dre ? (actifsDe.get(dre.code) ?? 0) : 0;

  const choisir = (codeDre: string, idIesg: string | null = null) => {
    setCode(codeDre);
    setIesgId(idIesg);
    setType(null);
    setToutVoir(false);
    setRecherche("");
    setRechercheDre("");
  };

  // Amène sous les yeux la colonne où s'affichent la région choisie ou les résultats d'une recherche lancée dans la bannière.
  const montrerExplorateur = () =>
    document.getElementById("explorateur")?.scrollIntoView({ behavior: "smooth" });

  const qDre = rechercheDre.trim();
  const rechercheDansDre = qDre.replace(/\s/g, "").length >= 2;
  const trouvesDansDre = useMemo(
    () =>
      rechercheDansDre && dre ? chercher(index, qDre).filter((e) => e.dre.code === dre.code) : [],
    [index, qDre, rechercheDansDre, dre],
  );
  const liste = (rechercheDansDre ? trouvesDansDre : (iesg?.etablissements ?? [])).filter(
    (e) => etat === "tous" || statuts.get(e.id)?.statut === etat,
  );
  const filtres = compterParType(liste, ORDRE_TYPES);
  const affiches = liste.filter((e) => !type || e.type === type);
  const visibles = toutVoir ? affiches : affiches.slice(0, APERCU);

  const q = recherche.trim();
  const resultats = useMemo(() => chercher(index, q), [index, q]);
  const enRecherche = q.replace(/\s/g, "").length >= 2;
  // Spec 051 : les recherches restées sans résultat, dans la bannière ou dans une DRE.
  useRechercheSansResultat(q, enRecherche && resultats.length === 0);
  useRechercheSansResultat(qDre, rechercheDansDre && trouvesDansDre.length === 0);

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
            <FilAriane rubrique={m.menu_vie_du_club()} page={m.menu_carte_des_clubs()} clair />
            <div data-reveal="left" className="pt-10 lg:pt-14">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-bold backdrop-blur-sm">
                <MapPin className="size-4 text-sun" /> {m.carte_clubs_reseau()}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.carte_clubs_titre_1()}</span>
                <span className="block text-sun">{m.carte_clubs_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/80">
                {m.carte_clubs_intro()}
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
                  placeholder={m.carte_clubs_cherche()}
                  aria-label={m.carte_clubs_rechercher()}
                  className="h-14 w-full rounded-full border-2 border-transparent bg-white pl-14 pr-14 text-base font-semibold text-ink shadow-card outline-none transition placeholder:font-medium placeholder:text-muted-foreground focus:border-sun"
                />
                {recherche && (
                  <button
                    type="button"
                    onClick={() => setRecherche("")}
                    aria-label={m.carte_clubs_effacer()}
                    className="absolute right-3 top-1/2 inline-flex size-9 -translate-y-1/2 items-center justify-center rounded-full text-muted-foreground transition hover:bg-mist hover:text-ink"
                  >
                    <X className="size-4" />
                  </button>
                )}
              </form>

              {chiffres.length === 0 && (
                <p className="mt-8 max-w-xl text-sm font-semibold text-white/75">
                  {m.carte_clubs_chiffres_indispo()}
                </p>
              )}
              {carte && carte.chiffres.clubs === 0 && (
                <p className="mt-8 max-w-xl text-sm font-semibold text-white/80">
                  {m.carte_clubs_aucun_club()}
                </p>
              )}
              {chiffres.length > 0 && (
                <dl className="mt-8 grid max-w-xl grid-cols-1 gap-2 sm:grid-cols-3 sm:gap-3">
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
            alt={m.certif_mascottes_alt()}
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
                {m.carte_clubs_liste_indispo()}
              </p>
            </div>
          ) : enRecherche ? (
            <div className="rounded-[2rem] border bg-white p-6 md:p-8">
              <p aria-live="polite" className="font-bold">
                {resultats.length === 0
                  ? m.carte_clubs_aucun_resultat({ q })
                  : (auSingulier(resultats.length)
                      ? m.carte_clubs_un_resultat
                      : m.carte_clubs_n_resultats)({ nombre: String(resultats.length), q })}
              </p>
              {resultats.length > 0 && (
                <ul className="mt-5 divide-y border-y">
                  {resultats.slice(0, 50).map((e) => {
                    const statut = statuts.get(e.id);
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
                        </button>
                        <span className="flex shrink-0 flex-col items-end gap-1.5">
                          <span className={`text-xs font-extrabold uppercase ${types[e.type].c}`}>
                            {types[e.type].t}
                          </span>
                          <StatutEtablissement statut={statut} />
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
              {resultats.length > 50 && (
                <p className="mt-4 text-sm font-semibold text-muted-foreground">
                  {m.carte_clubs_preciser({ nombre: String(resultats.length - 50) })}
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
                    {m.carte_clubs_dre_long()}
                  </p>
                  <h2 className="mt-2 text-4xl md:text-5xl">
                    <span className="text-logo-blue">DRE</span>{" "}
                    <span className="text-primary">{dre.nom}</span>
                  </h2>
                </div>
                <p className="text-sm font-semibold text-muted-foreground">
                  <strong className="text-ink">{dre.nb_etablissements}</strong>{" "}
                  {m.carte_clubs_etablissements()} ·{" "}
                  <strong className="text-ink">{dre.iesg.length}</strong> IESG ·{" "}
                  <strong className="text-ink">{clubsDeLaDre}</strong>{" "}
                  {clubsDeLaDre === 1 ? m.carte_clubs_un_actif() : m.carte_clubs_n_actifs()} ·{" "}
                  <strong className="text-ink">
                    {Math.round((dre.nb_etablissements / (totalEtablissements || 1)) * 100)} %
                  </strong>{" "}
                  {m.carte_clubs_du_reseau()}
                </p>
              </div>

              <div
                role="group"
                aria-label={m.carte_clubs_inspections()}
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

              <div className="relative mt-6 max-w-xl">
                <Search
                  aria-hidden
                  className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                />
                <input
                  type="search"
                  value={rechercheDre}
                  onChange={(e) => {
                    setRechercheDre(e.target.value);
                    setToutVoir(false);
                  }}
                  placeholder={m.carte_clubs_cherche_dre({ dre: dre.nom })}
                  aria-label={m.carte_clubs_rechercher_dre({ dre: dre.nom })}
                  className="h-11 w-full rounded-full border-2 border-border bg-mist-soft pl-11 pr-11 text-sm font-semibold outline-none transition placeholder:font-medium placeholder:text-muted-foreground focus:border-logo-blue focus:bg-white"
                />
                {rechercheDre && (
                  <button
                    type="button"
                    onClick={() => setRechercheDre("")}
                    aria-label={m.carte_clubs_effacer()}
                    className="absolute right-2 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-full text-muted-foreground transition hover:bg-mist hover:text-ink"
                  >
                    <X className="size-4" />
                  </button>
                )}
              </div>
              {rechercheDansDre && (
                <p aria-live="polite" className="mt-3 text-sm font-semibold text-muted-foreground">
                  {trouvesDansDre.length === 0
                    ? m.carte_clubs_aucun_dre({ dre: dre.nom, q: qDre })
                    : m.carte_clubs_resultats_dre({ dre: dre.nom })}
                </p>
              )}

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
                      {f.t ? types[f.t].pluriel : m.carte_clubs_tous()}{" "}
                      <span className="font-semibold">({f.n})</span>
                    </button>
                  );
                })}
                <label className="ml-auto flex items-center gap-2 text-muted-foreground">
                  <span className="sr-only">{m.carte_clubs_etat_club()}</span>
                  <select
                    value={etat}
                    onChange={(e) => {
                      setEtat(e.target.value as EtatFiltre);
                      setType(null);
                      setToutVoir(false);
                    }}
                    className="h-10 rounded-full border-2 border-border bg-white px-4 text-sm font-bold text-ink outline-none transition focus:border-logo-blue"
                  >
                    {etats().map((o) => (
                      <option key={o.v} value={o.v}>
                        {o.t}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <ol className="mt-4 grid border-t sm:grid-cols-2 sm:gap-x-8 xl:grid-cols-3">
                {visibles.map((e, k) => {
                  const statut = statuts.get(e.id);
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
                        <StatutEtablissement statut={statut} />
                      </span>
                    </li>
                  );
                })}
              </ol>
              {affiches.length === 0 && !(rechercheDansDre && trouvesDansDre.length === 0) && (
                <p role="status" className="mt-4 text-sm font-semibold text-muted-foreground">
                  {etat === "actif"
                    ? m.carte_clubs_aucun_actif_ici()
                    : etat === "en_constitution"
                      ? m.carte_clubs_aucun_constitution_ici()
                      : m.carte_clubs_aucun_ici()}
                </p>
              )}
              {affiches.length > APERCU && (
                <button
                  type="button"
                  onClick={() => setToutVoir((v) => !v)}
                  className="mt-6 text-sm font-bold text-logo-blue underline underline-offset-4 hover:text-primary"
                >
                  {toutVoir
                    ? m.carte_clubs_reduire()
                    : m.carte_clubs_afficher_autres({ nombre: String(affiches.length - APERCU) })}
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
              {m.carte_clubs_pas_club_1()}{" "}
              <span className="text-sun">{m.carte_clubs_pas_club_2()}</span>
            </h2>
            <p className="mt-2 font-medium text-white/80">{m.carte_clubs_pas_club_texte()}</p>
          </div>
          <a
            href={lien("/club-sante#adhesion")}
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            {m.carte_clubs_regles()} <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
