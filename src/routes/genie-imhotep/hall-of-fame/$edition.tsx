import { useState, type CSSProperties } from "react";
import { createFileRoute, notFound } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Crown,
  Flag,
  Gamepad2,
  Hourglass,
  MoveRight,
  Trophy,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { Compteur } from "@/components/Compteur";
import { CompteARebours } from "@/components/CompteARebours";
import { DecorAnime } from "@/components/DecorAnime";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { dessins } from "@/lib/togo-dre";
import {
  CHAMPION,
  inspectorales,
  nationale,
  ordreRegions,
  prefectorales,
  regionales,
  type Equipe,
  type MatchNational,
  nomsRegions,
  type RegionId,
} from "@/lib/genie-imhotep-resultats";
import { libelleSaison, ordinal, trouverEdition, type Edition } from "@/lib/genie-imhotep-editions";
import mascottesVs from "@/assets/mascottes-vs.webp";
import { ContenuEnFrancais } from "@/components/ContenuEnFrancais";
import { auSingulier, lien } from "@/lib/langues";
import { m as t } from "@/paraglide/messages.js";

// La page d'une édition du Hall of Fame : les résultats complets d'une saison jouée, ou le compte à
// rebours d'une saison à venir. Une édition inconnue donne la page 404.
export const Route = createFileRoute("/genie-imhotep/hall-of-fame/$edition")({
  loader: ({ params }) => {
    const edition = trouverEdition(params.edition);
    if (!edition) throw notFound();
    return edition;
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: t.ghed_meta_titre({ saison: loaderData?.id ?? "" }) },
      {
        name: "description",
        content:
          loaderData?.statut === "a-venir"
            ? t.ghed_meta_a_venir({ saison: loaderData.id })
            : t.ghed_meta_terminee({ saison: loaderData?.id ?? "" }),
      },
      { property: "og:title", content: t.ghed_meta_og({ saison: loaderData?.id ?? "" }) },
    ],
  }),
  component: HallOfFameEdition,
});

const region = (id: RegionId) => ({ nom: nomsRegions[id], couleur: dessins[id]!.couleur });

const finale = nationale.find((m) => m.tour === "finale")!;
const champion = finale.a.nom === CHAMPION ? finale.a : finale.b;
const finaliste = finale.a.nom === CHAMPION ? finale.b : finale.a;

const clubsEngages = new Set(prefectorales.flatMap((p) => p.clubs)).size;
// Des fonctions : les textes suivent la langue de la page (spec 052).
const chiffres = () => [
  { n: clubsEngages, t: t.ghed_clubs_engages() },
  { n: prefectorales.length, t: t.ghed_prefectures() },
  { n: inspectorales.length, t: t.ghed_inspections() },
  { n: regionales.length, t: t.gpal_dist_regionaux() },
];

// Le parcours du champion, reconstitué phase par phase à partir des résultats.
const NOMS_TOURS = { quart: t.ghed_quart, demi: t.ghed_demi, finale: t.ghed_finale } as const;
const nomTour = (tour: MatchNational["tour"]) => NOMS_TOURS[tour]();
const adversaire = (eq: [Equipe, Equipe]) => eq.find((e) => e.nom !== CHAMPION);
const leParcours = () => {
  const pref = prefectorales.find((p) => p.qualifie === CHAMPION)!;
  const insp = inspectorales.find((i) => i.gagnant === CHAMPION)!;
  const reg = regionales.find((r) => r.gagnant === CHAMPION)!;
  const nat = nationale.filter((m) => m.a.nom === CHAMPION || m.b.nom === CHAMPION);
  const moi = (m: MatchNational) => (m.a.nom === CHAMPION ? m.a : m.b);
  const lui = (m: MatchNational) => (m.a.nom === CHAMPION ? m.b : m.a);
  return [
    {
      phase: t.gi_phase_1(),
      lieu: pref.prefecture,
      contre: pref.clubs.filter((c) => c !== CHAMPION).join(", "),
      score: null,
      resultat: t.ghed_qualifie(),
    },
    {
      phase: t.gi_phase_2(),
      lieu: `IESG ${insp.iesg}`,
      contre: adversaire(insp.finale)?.nom ?? "",
      score: `${insp.finale.find((e) => e.nom === CHAMPION)?.pts} – ${adversaire(insp.finale)?.pts}`,
      resultat: t.ghed_champion_inspection(),
    },
    {
      phase: t.gi_phase_3(),
      lieu: `DRE ${region(reg.region).nom}`,
      contre: reg.champions
        .filter((c) => c.lycee !== CHAMPION)
        .map((c) => c.lycee)
        .join(", "),
      score: null,
      resultat: t.gpal_champion_regional(),
    },
    ...nat.map((m) => ({
      phase: nomTour(m.tour),
      lieu: t.ghed_jeu({ numero: String(m.jeu) }),
      contre: lui(m).nom,
      score: `${moi(m).pts} – ${lui(m).pts}`,
      resultat: m.tour === "finale" ? t.edition_champion() : t.ghed_qualifie(),
    })),
  ];
};

const quarts = nationale.filter((m) => m.tour === "quart");
const demis = nationale.filter((m) => m.tour === "demi");
const surLeChemin = (m: MatchNational) => m.gagnant === CHAMPION;

// Le meilleur perdant repêché en quart, et le jeu où il avait été battu.
const repeche = quarts.flatMap((m) => [m.a, m.b]).find((e) => e.note);
const defaiteRepeche = quarts.find(
  (m) => [m.a, m.b].some((e) => e.nom === repeche?.nom && !e.note) && m.gagnant !== repeche?.nom,
);

// Le tour le plus loin atteint en phase nationale par un champion régional.
const auNational = (nom: string) => {
  const joue = (tour: MatchNational["tour"]) =>
    nationale.some((m) => m.tour === tour && (m.a.nom === nom || m.b.nom === nom));
  if (nom === CHAMPION) return t.edition_champion();
  if (joue("finale")) return t.gpal_finaliste();
  if (joue("demi")) return t.gpal_demi_finaliste();
  return t.gpal_quart();
};

function Pastille({ id }: { id: RegionId }) {
  return (
    <span
      aria-hidden
      className="size-2.5 shrink-0 rounded-full ring-2 ring-white"
      style={{ backgroundColor: region(id).couleur }}
    />
  );
}

// Un match du tableau final : deux lignes, le vainqueur en gras ; la ligne du champion en rouge.
function CarteMatch({ m }: { m: MatchNational }) {
  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-card ring-1 ring-border">
      <p className="flex items-center justify-between bg-mist-soft px-3 py-1.5 text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
        <span>{nomTour(m.tour)}</span>
        <span>{t.ghed_jeu({ numero: String(m.jeu) })}</span>
      </p>
      {[m.a, m.b].map((e) => {
        const gagne = e.nom === m.gagnant;
        const champion = e.nom === CHAMPION;
        return (
          <div
            key={e.nom}
            className={`flex h-11 items-center gap-2 border-t px-3 text-sm ${
              champion
                ? "border-logo-red bg-logo-red font-extrabold text-white"
                : gagne
                  ? "border-border font-extrabold"
                  : "border-border font-semibold text-muted-foreground"
            }`}
          >
            <Pastille id={e.region} />
            {/* La mention (« Meilleur perdant ») est expliquée sous le tableau : un astérisque suffit ici. */}
            <span className="min-w-0 flex-1 truncate">
              {e.nom}
              {e.note && (
                <>
                  <span aria-hidden className="ml-0.5 text-logo-red">
                    *
                  </span>
                  <span className="sr-only"> ({e.note})</span>
                </>
              )}
              {gagne && <span className="sr-only">{t.ghed_vainqueur()}</span>}
            </span>
            <span className="w-9 shrink-0 text-right font-display text-base tabular-nums">
              {e.pts}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// Les traits qui relient deux matchs au tour suivant ; `haut`, `bas` et `sortie` passent en rouge sur le parcours du champion.
function Liaison({
  haut,
  bas,
  sortie,
  className = "",
  style,
}: {
  haut: boolean;
  bas: boolean;
  sortie: boolean;
  className?: string;
  style?: CSSProperties;
}) {
  // L'épaisseur se donne côté par côté : une largeur globale tracerait aussi les côtés laissés vides.
  const couleur = (rouge: boolean) => (rouge ? "z-10 border-logo-red" : "border-ink/20");
  return (
    <div aria-hidden className={`relative ${className}`} style={style}>
      <span
        className={`absolute left-0 top-1/4 h-1/4 w-1/2 rounded-tr-xl ${haut ? "border-r-[3px] border-t-[3px]" : "border-r-2 border-t-2"} ${couleur(haut)}`}
      />
      <span
        className={`absolute bottom-1/4 left-0 h-1/4 w-1/2 rounded-br-xl ${bas ? "border-b-[3px] border-r-[3px]" : "border-b-2 border-r-2"} ${couleur(bas)}`}
      />
      <span
        className={`absolute right-0 top-1/2 w-1/2 -translate-y-1/2 ${sortie ? "border-t-[3px]" : "border-t-2"} ${couleur(sortie)}`}
      />
    </div>
  );
}

// Une édition à venir : le compte à rebours jusqu'au coup d'envoi, et de quoi s'y préparer.
function EditionAVenir({ edition }: { edition: Edition }) {
  return (
    <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 lg:grid-cols-[1.2fr_1fr]">
      <div className="min-w-0 pb-16 pt-8 lg:pb-24 lg:pt-10">
        <p className="inline-flex items-center gap-2 rounded-full bg-logo-red px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-white">
          <Hourglass className="size-4 text-sun" />{" "}
          {t.edition_titre({ ordinal: ordinal(edition.numero), etat: libelleSaison(edition.id) })}
          {libelleSaison(edition.id)}
        </p>
        <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
          <span className="block">{t.ghed_prochain_1()}</span>
          <span className="block text-sun">{t.ghed_prochain_2()}</span>
        </h1>
        <p className="mt-5 max-w-xl text-lg font-medium text-white/85">
          {t.ghed_a_venir_texte({ saison: edition.id })}
        </p>
        <p className="mt-8 text-xs font-extrabold uppercase tracking-widest text-sun">
          {t.edition_coup_envoi()}
        </p>
        <div className="mt-3">
          {edition.debut ? (
            <CompteARebours cible={edition.debut} clair />
          ) : (
            <p className="font-display text-3xl text-sun">{t.edition_date_bientot()}</p>
          )}
        </div>
        <div className="mt-9 flex flex-wrap gap-3">
          <a
            href={lien("/genie-imhotep/inscription")}
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            {t.gi_inscrire()} <ArrowRight className="size-4" />
          </a>
          <a
            href={lien("/jeux")}
            className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white px-7 py-3 text-[15px] font-bold text-white hover:bg-white hover:text-ink"
          >
            <Gamepad2 className="size-4" /> {t.ghed_entrainer()}
          </a>
        </div>
      </div>
      <div className="relative mx-auto self-end">
        <img
          src={mascottesVs}
          alt={t.ghed_attente_alt()}
          width={2000}
          height={2000}
          className="w-72 drop-shadow-2xl sm:w-96 lg:w-[30rem]"
        />
        <p className="absolute left-0 top-6 -rotate-6 rounded-2xl bg-white px-4 py-2 font-hand text-2xl text-ink shadow-card motion-safe:animate-float">
          {t.ghed_ton_lycee()}
        </p>
      </div>
    </div>
  );
}

function HallOfFameEdition() {
  const edition = Route.useLoaderData();
  const parcours = leParcours();
  const [choix, setChoix] = useState<RegionId>("grand-lome");
  const insp = inspectorales.filter((i) => i.region === choix);
  const pref = prefectorales.filter((p) => p.region === choix);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière claire et dorée : des rayons qui tournent derrière les mascottes, le score de la finale. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-sky via-[oklch(0.52_0.17_252)] to-logo-blue text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-[85%] -z-10 size-[60rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_220_100/0.16)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite] lg:left-[72%] lg:top-[62%] lg:size-[70rem]"
        />
        <div
          aria-hidden
          className="absolute left-1/2 top-[88%] -z-10 size-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sun/40 blur-3xl lg:left-[72%] lg:top-[66%]"
        />
        <DecorAnime />
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 pt-8 md:pt-12">
          <FilAriane
            clair
            rubrique={t.menu_genie_imhotep()}
            parent={{ t: t.menu_hall_of_fame(), href: "/genie-imhotep/hall-of-fame" }}
            page={t.gpal_edition_saison({ saison: libelleSaison(edition.id) })}
          />
          <a
            href={lien("/genie-imhotep/hall-of-fame#editions")}
            className="inline-flex items-center gap-1.5 text-sm font-bold text-white hover:underline"
          >
            <ArrowLeft className="size-4" /> {t.gpal_toutes_editions()}
          </a>
        </div>
        {edition.statut === "a-venir" ? (
          <EditionAVenir edition={edition} />
        ) : (
          <>
            <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 lg:grid-cols-[1.2fr_1fr]">
              <div className="min-w-0 pb-12 lg:pb-20">
                <div data-reveal="left" className="pt-8 lg:pt-10">
                  <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                    <Trophy className="size-4" />{" "}
                    {t.ghed_badge({ ordinal: ordinal(edition.numero) })}
                  </p>
                  <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                    <span className="block">{t.ghed_edition()}</span>
                    <span className="block text-sun">{libelleSaison(edition.id)}</span>
                  </h1>
                  <p className="mt-5 max-w-xl text-lg font-medium text-white/85">
                    {t.ghed_intro()}
                  </p>

                  {/* Le tableau d'affichage de la finale. */}
                  <div className="mt-8 max-w-xl overflow-hidden rounded-3xl bg-white shadow-card ring-1 ring-border">
                    <p className="flex items-center gap-2 bg-logo-red px-5 py-2 text-xs font-extrabold uppercase tracking-widest text-white">
                      <Crown className="size-4 text-sun" />{" "}
                      {t.ghed_grande_finale({ numero: String(finale.jeu) })}
                    </p>
                    {/* Sur mobile, les deux équipes s'empilent de part et d'autre du score. */}
                    <div className="grid items-center gap-3 p-5 text-center sm:grid-cols-[1fr_auto_1fr] sm:text-left">
                      <div>
                        <p className="font-display text-xl leading-tight text-primary md:text-2xl">
                          {CHAMPION}
                        </p>
                        <p className="mt-1 text-xs font-bold text-muted-foreground">
                          DRE {region(champion.region).nom} · {t.ghed_champion_court()}
                        </p>
                      </div>
                      <p className="whitespace-nowrap font-display text-3xl tabular-nums text-ink sm:text-4xl md:text-5xl">
                        {champion.pts} <span className="text-ink/30">–</span> {finaliste.pts}
                      </p>
                      <div className="sm:text-right">
                        <p className="font-display text-xl leading-tight text-logo-blue md:text-2xl">
                          {finaliste.nom}
                        </p>
                        <p className="mt-1 text-xs font-bold text-muted-foreground">
                          DRE {region(finaliste.region).nom} · {t.gpal_finaliste()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <img
                src={mascottesVs}
                alt={t.gi_mascottes_alt()}
                width={2000}
                height={2000}
                data-reveal="zoom"
                className="mx-auto w-72 self-end drop-shadow-2xl sm:w-96 lg:w-[30rem]"
              />
            </div>
            <div className="relative border-y border-border bg-white">
              <dl className="mx-auto grid max-w-7xl grid-cols-2 divide-border px-5 md:grid-cols-4 md:divide-x">
                {chiffres().map((c) => (
                  <div key={c.t} className="flex flex-col-reverse py-6 text-center md:py-8">
                    <dt className="mt-2 text-sm font-bold text-muted-foreground">{c.t}</dt>
                    <dd className="font-display text-4xl leading-none text-primary md:text-5xl">
                      <Compteur value={c.n} />
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </>
        )}
      </section>

      {/* Les résultats détaillés n'existent que pour une édition terminée. */}
      {edition.statut === "terminee" && (
        <>
          {/* Le parcours du champion : une ligne rouge qui relie chaque phase jusqu'au titre. */}
          <section id="parcours" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
            <EnTete
              sur={t.ghed_parcours_sur()}
              bleu={t.ghed_parcours_bleu()}
              vert={t.ghed_parcours_vert()}
            >
              {t.ghed_parcours_texte({ champion: CHAMPION })}
            </EnTete>

            <ol className="relative mt-12 grid gap-4 lg:grid-cols-6 lg:gap-3">
              <span
                aria-hidden
                className="absolute bottom-4 left-[1.1rem] top-4 w-1 rounded-full bg-logo-red lg:bottom-auto lg:left-5 lg:right-[calc((100%-3.75rem)/6-1.25rem)] lg:top-[1.1rem] lg:h-1 lg:w-auto"
              />
              {parcours.map((p, i) => {
                const titre = i === parcours.length - 1;
                return (
                  <li
                    key={p.phase}
                    data-reveal
                    style={retard(i)}
                    className="relative flex gap-4 lg:flex-col lg:gap-0"
                  >
                    <span
                      className={`relative z-10 inline-flex size-10 shrink-0 items-center justify-center rounded-full font-display text-lg ring-4 ring-carnet lg:ring-white ${
                        titre ? "bg-sun text-ink" : "bg-logo-red text-white"
                      }`}
                    >
                      {titre ? <Trophy className="size-5" /> : i + 1}
                    </span>
                    <div
                      className={`flex-1 rounded-2xl p-4 shadow-card lg:mt-4 ${
                        titre ? "bg-logo-red text-white" : "bg-white"
                      }`}
                    >
                      <p
                        className={`text-[11px] font-extrabold uppercase tracking-wider ${titre ? "text-white" : "text-logo-red"}`}
                      >
                        {p.phase}
                      </p>
                      <p
                        className={`mt-0.5 text-xs font-bold ${titre ? "text-white" : "text-muted-foreground"}`}
                      >
                        {p.lieu}
                      </p>
                      {p.score && (
                        <p className="mt-3 font-display text-3xl tabular-nums">{p.score}</p>
                      )}
                      <p
                        className={`text-sm font-semibold leading-snug ${p.score ? "mt-1" : "mt-3"}`}
                      >
                        <span className={titre ? "text-white" : "text-muted-foreground"}>
                          {t.ghed_face_a()}{" "}
                        </span>
                        {p.contre}
                      </p>
                      <p
                        className={`mt-3 inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-extrabold ${
                          titre
                            ? "bg-sun text-ink"
                            : "bg-[color-mix(in_oklch,var(--primary)_14%,white)] text-[color-mix(in_oklch,var(--primary)_70%,black)]"
                        }`}
                      >
                        <Check className="size-3.5" /> {p.resultat}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>

          {/* Le tableau final, comme une phase à élimination directe de coupe de football. */}
          <section id="tableau" className="scroll-mt-16 bg-white py-20">
            <div className="mx-auto max-w-7xl px-5">
              <EnTete
                sur={t.gpal_phase_nationale()}
                bleu={t.ghed_tableau_bleu()}
                vert={t.ghed_tableau_vert()}
              >
                {t.ghed_tableau_texte()}
              </EnTete>
              <p className="mt-4 flex items-center gap-2 text-sm font-bold text-muted-foreground lg:hidden">
                <MoveRight className="size-4" /> {t.ghed_glisser()}
              </p>

              <div className="-mx-5 mt-8 overflow-x-auto px-5 pb-4">
                <div
                  data-reveal
                  className="grid min-w-[60rem] grid-cols-[1fr_2.5rem_1fr_2.5rem_1fr_2.5rem_13rem] grid-rows-4"
                >
                  {quarts.map((m, i) => (
                    <div key={m.jeu} className="col-start-1 py-2" style={{ gridRowStart: i + 1 }}>
                      <CarteMatch m={m} />
                    </div>
                  ))}
                  {[0, 2].map((k) => (
                    <Liaison
                      key={k}
                      className="col-start-2 row-span-2"
                      style={{ gridRowStart: k + 1 }}
                      haut={surLeChemin(quarts[k]!)}
                      bas={surLeChemin(quarts[k + 1]!)}
                      sortie={surLeChemin(quarts[k]!) || surLeChemin(quarts[k + 1]!)}
                    />
                  ))}
                  {demis.map((m, i) => (
                    <div
                      key={m.jeu}
                      className="col-start-3 row-span-2 self-center py-2"
                      style={{ gridRowStart: i * 2 + 1 }}
                    >
                      <CarteMatch m={m} />
                    </div>
                  ))}
                  <Liaison
                    className="col-start-4 row-span-4 row-start-1"
                    haut={surLeChemin(demis[0]!)}
                    bas={surLeChemin(demis[1]!)}
                    sortie
                  />
                  <div className="col-start-5 row-span-4 row-start-1 self-center">
                    <CarteMatch m={finale} />
                  </div>
                  <div
                    aria-hidden
                    className="relative col-start-6 row-span-4 row-start-1 before:absolute before:inset-x-0 before:top-1/2 before:-translate-y-1/2 before:border-t-[3px] before:border-logo-red"
                  />
                  <div className="col-start-7 row-span-4 row-start-1 self-center rounded-3xl bg-logo-red p-5 text-center text-white shadow-card">
                    <Trophy className="mx-auto size-10 text-sun" />
                    <p className="mt-2 text-xs font-extrabold uppercase tracking-widest">
                      {t.edition_champion()}
                    </p>
                    <p className="mt-1 font-display text-xl leading-tight">{CHAMPION}</p>
                    <p className="mt-1 text-xs font-bold">DRE {region(champion.region).nom}</p>
                  </div>
                </div>
              </div>
              {repeche && defaiteRepeche && (
                <p className="mt-2 text-sm font-medium text-muted-foreground">
                  <span className="font-extrabold text-logo-red">*</span>{" "}
                  {t.ghed_repeche({ nom: repeche.nom, jeu: String(defaiteRepeche.jeu) })}
                </p>
              )}
            </div>
          </section>

          {/* Les classements régionaux : un tableau par région, comme les groupes d'un tournoi. */}
          <section id="regions" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
            <EnTete
              sur={t.gpal_phase_regionale()}
              bleu={t.ghed_classements_bleu()}
              vert={t.ghed_classements_vert()}
            >
              {t.ghed_classements_texte()}
            </EnTete>

            <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {ordreRegions.map((id, i) => {
                const r = regionales.find((x) => x.region === id)!;
                const lignes = [...r.champions].sort(
                  (a, b) => Number(b.lycee === r.gagnant) - Number(a.lycee === r.gagnant),
                );
                return (
                  <div
                    key={id}
                    data-reveal
                    style={retard(i % 3)}
                    className="overflow-hidden rounded-3xl bg-white shadow-card ring-1 ring-border"
                  >
                    <p
                      id={`groupe-${id}`}
                      className="flex items-center gap-2 px-5 py-3 font-display text-lg text-white"
                      style={{
                        backgroundColor: `color-mix(in oklch, ${region(id).couleur} 65%, black)`,
                      }}
                    >
                      <Flag className="size-4" /> DRE {region(id).nom}
                    </p>
                    <table aria-labelledby={`groupe-${id}`} className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                          <th scope="col" className="w-10 py-2 pl-5 font-extrabold">
                            #
                          </th>
                          <th scope="col" className="py-2 font-extrabold">
                            {t.ghed_club()}
                          </th>
                          <th scope="col" className="py-2 pr-5 text-right font-extrabold">
                            IESG
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {lignes.map((c) => {
                          const qualifie = c.lycee === r.gagnant;
                          const champion = c.lycee === CHAMPION;
                          return (
                            <tr
                              key={c.lycee}
                              className={`border-t ${
                                champion
                                  ? "border-logo-red bg-logo-red text-white"
                                  : qualifie
                                    ? "border-border bg-[color-mix(in_oklch,var(--primary)_10%,white)]"
                                    : "border-border"
                              }`}
                            >
                              <td className="py-3 pl-5 font-display text-base tabular-nums">
                                {qualifie ? 1 : "–"}
                              </td>
                              <td className="py-3">
                                <span className={qualifie ? "font-extrabold" : "font-semibold"}>
                                  {c.lycee}
                                </span>
                                {qualifie && (
                                  <span
                                    className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-extrabold uppercase ${
                                      champion
                                        ? "bg-sun text-ink"
                                        : "bg-[color-mix(in_oklch,var(--primary)_70%,black)] text-white"
                                    }`}
                                  >
                                    {auNational(c.lycee)}
                                  </span>
                                )}
                              </td>
                              <td
                                className={`py-3 pr-5 text-right text-xs font-bold ${champion ? "text-white" : "text-muted-foreground"}`}
                              >
                                {c.iesg}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Phases inspectorales et préfectorales, région par région. */}
          <section id="phases-locales" className="scroll-mt-16 bg-white py-20">
            <div className="mx-auto max-w-7xl px-5">
              <EnTete
                sur={t.ghed_locales_sur()}
                bleu={t.ghed_locales_bleu()}
                vert={t.ghed_locales_vert()}
              >
                {t.ghed_locales_texte()}
              </EnTete>

              <div data-reveal className="mt-8 flex flex-wrap gap-2">
                {ordreRegions.map((id) => {
                  const on = id === choix;
                  return (
                    <button
                      key={id}
                      type="button"
                      aria-pressed={on}
                      onClick={() => setChoix(id)}
                      className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                        on
                          ? "bg-night text-white shadow-card"
                          : "bg-mist-soft ring-1 ring-border hover:ring-night/30"
                      }`}
                    >
                      <Pastille id={id} />
                      {region(id).nom}
                    </button>
                  );
                })}
              </div>

              <ContenuEnFrancais className="mt-4" />
              <h3 className="mt-10 text-2xl text-logo-blue">{t.ghed_finales_inspection()}</h3>
              <ul className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {insp.map((f) => (
                  <li
                    key={f.iesg}
                    className="flex flex-col overflow-hidden rounded-2xl bg-white ring-1 ring-border"
                  >
                    <p className="bg-white px-4 py-2 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                      IESG {f.iesg}
                    </p>
                    {f.finale.map((e) => {
                      const gagne = e.nom === f.gagnant;
                      const champion = e.nom === CHAMPION;
                      return (
                        <div
                          key={e.nom}
                          className={`flex h-11 items-center gap-2 border-t px-4 text-sm ${
                            champion
                              ? "border-logo-red bg-logo-red font-extrabold text-white"
                              : gagne
                                ? "border-border bg-white font-extrabold"
                                : "border-border bg-white font-semibold text-muted-foreground"
                          }`}
                        >
                          {gagne ? (
                            <Check
                              className={`size-4 shrink-0 ${champion ? "text-sun" : "text-primary"}`}
                            />
                          ) : (
                            <span className="size-4 shrink-0" />
                          )}
                          <span className="min-w-0 flex-1 truncate">
                            {e.nom}
                            {gagne && <span className="sr-only">{t.ghed_vainqueur()}</span>}
                          </span>
                          <span className="shrink-0 font-display text-base tabular-nums">
                            {e.pts ?? "–"}
                          </span>
                        </div>
                      );
                    })}
                    {f.eliminatoires && (
                      <ul className="space-y-1 border-t border-border px-4 py-3 text-xs font-medium text-muted-foreground">
                        {f.eliminatoires.map((e) => (
                          <li key={e}>{e}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>

              <h3 className="mt-12 text-2xl text-logo-blue">{t.ghed_phases_prefectorales()}</h3>
              <ul className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {pref.map((p) => (
                  <li
                    key={p.prefecture}
                    className={`rounded-2xl p-4 ring-1 ${
                      p.qualifie === CHAMPION
                        ? "bg-[color-mix(in_oklch,var(--logo-red)_8%,white)] ring-logo-red"
                        : "bg-white ring-border"
                    }`}
                  >
                    <p className="flex items-baseline justify-between gap-3">
                      <span className="font-display text-lg text-logo-blue">{p.prefecture}</span>
                      <span className="text-xs font-bold text-muted-foreground">
                        IESG {p.iesg} ·{" "}
                        {(auSingulier(p.clubs.length) ? t.ghed_un_club : t.ghed_n_clubs)({
                          nombre: String(p.clubs.length),
                        })}
                      </span>
                    </p>
                    <ul className="mt-3 flex flex-wrap gap-1.5">
                      {p.clubs.map((c) => {
                        const qualifie = c === p.qualifie;
                        return (
                          <li
                            key={c}
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
                              qualifie
                                ? c === CHAMPION
                                  ? "bg-logo-red text-white"
                                  : "bg-[color-mix(in_oklch,var(--primary)_70%,black)] text-white"
                                : "bg-mist-soft text-ink/70"
                            }`}
                          >
                            {qualifie && <Check className="size-3.5" />}
                            {c}
                            {qualifie && (
                              <span className="sr-only">{t.ghed_qualifie_lecteur()}</span>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                    {p.note && (
                      <p className="mt-3 text-xs font-medium text-muted-foreground">{p.note}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </section>
        </>
      )}

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div
          data-reveal="zoom"
          className="flex flex-col items-start justify-between gap-6 rounded-3xl bg-sun p-8 md:flex-row md:items-center md:p-12"
        >
          <div>
            <h2 className="text-3xl text-ink md:text-4xl">
              {t.ghof_et_si_1()} <span className="text-logo-blue">{t.ghof_et_si_2()}</span>
              {t.ghof_et_si_3()}
            </h2>
            <p className="mt-2 max-w-2xl font-semibold text-ink/75">{t.ghof_inscriptions()}</p>
          </div>
          <a
            href={lien("/genie-imhotep/inscription")}
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            {t.ghof_sinscrire()} <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
