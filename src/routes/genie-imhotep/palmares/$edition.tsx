import { createFileRoute, notFound } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  Crown,
  Hourglass,
  Medal,
  Sparkles,
  Trophy,
  UserRound,
} from "lucide-react";
import { CompteARebours } from "@/components/CompteARebours";
import { DecorAnime } from "@/components/DecorAnime";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { libelleSaison, ordinal, trouverEdition, type Edition } from "@/lib/genie-imhotep-editions";
import {
  CHAMPION,
  nationale,
  nomsRegions,
  ordreRegions,
  regionales,
  type EquipeNationale,
  type JoueurPrime,
  type RegionId,
} from "@/lib/genie-imhotep-resultats";
import { dessins } from "@/lib/togo-dre";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";
import { ContenuEnFrancais } from "@/components/ContenuEnFrancais";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

// Le palmarès d'une édition : podium, joueurs primés et champions régionaux d'une saison jouée, ou le
// compte à rebours d'une saison à venir. Une édition inconnue donne la page 404.
export const Route = createFileRoute("/genie-imhotep/palmares/$edition")({
  loader: ({ params }) => {
    const edition = trouverEdition(params.edition);
    if (!edition) throw notFound();
    return edition;
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: m.gpal_ed_meta_titre({ saison: loaderData?.id ?? "" }) },
      {
        name: "description",
        content: m.gpal_ed_meta_description({ saison: loaderData?.id ?? "" }),
      },
      { property: "og:title", content: m.gpal_ed_meta_og({ saison: loaderData?.id ?? "" }) },
    ],
  }),
  component: PalmaresEdition,
});

const couleur = (id: RegionId) => dessins[id]!.couleur;

// Le podium de l'édition 2025-2026, tiré du tableau final : pas de match pour la 3e place, les deux
// demi-finalistes battus la partagent.
const finale = nationale.find((match) => match.tour === "finale")!;
const equipe = (nom: string) => [finale.a, finale.b].find((e) => e.nom === nom)!;
const champion = equipe(CHAMPION);
const finaliste = [finale.a, finale.b].find((e) => e.nom !== CHAMPION)!;
const demiFinalistes = nationale
  .filter((match) => match.tour === "demi")
  .map((match) => (match.a.nom === match.gagnant ? match.b : match.a));

// Le tour le plus loin atteint au national par chaque champion régional.
const parcoursNational = (nom: string) => {
  if (nom === CHAMPION) return m.edition_champion();
  if (nom === finaliste.nom) return m.gpal_finaliste();
  if (demiFinalistes.some((e) => e.nom === nom)) return m.gpal_demi_finaliste();
  return nationale.some((match) => match.a.nom === nom || match.b.nom === nom)
    ? m.gpal_quart()
    : m.gpal_champion_regional();
};

function Equipe({ e, clair = false }: { e: EquipeNationale; clair?: boolean }) {
  return (
    <span className="block">
      <span className="block font-display text-xl leading-tight md:text-2xl">{e.nom}</span>
      <span
        className={`mt-1 inline-flex items-center gap-1.5 text-xs font-bold ${clair ? "text-white/75" : "text-muted-foreground"}`}
      >
        <span
          aria-hidden
          className="size-2.5 rounded-full ring-2 ring-white"
          style={{ backgroundColor: couleur(e.region) }}
        />
        DRE {nomsRegions[e.region]}
      </span>
    </span>
  );
}

// Le podium : le champion au centre et plus haut, le finaliste à gauche, les demi-finalistes à droite.
function Podium() {
  const marches = [
    {
      rang: "2",
      titre: m.gpal_finaliste(),
      equipes: [finaliste],
      hauteur: "h-28 md:h-36",
      fond: "bg-[color-mix(in_oklch,var(--sky)_85%,white)]",
      ordre: "md:order-1",
      icone: Medal,
    },
    {
      rang: "1",
      titre: m.edition_champion(),
      equipes: [champion],
      hauteur: "h-40 md:h-52",
      fond: "bg-sun",
      ordre: "order-first md:order-2",
      icone: Crown,
    },
    {
      rang: "3",
      titre: m.gpal_demi_finalistes(),
      equipes: demiFinalistes,
      hauteur: "h-20 md:h-24",
      fond: "bg-[color-mix(in_oklch,var(--tangerine)_80%,white)]",
      ordre: "md:order-3",
      icone: Award,
    },
  ];
  return (
    <ol className="mx-auto grid max-w-5xl items-end gap-6 md:grid-cols-3 md:gap-4">
      {marches.map((marche, i) => (
        <li
          key={marche.rang}
          data-reveal
          style={retard(i)}
          className={`flex flex-col ${marche.ordre}`}
        >
          <div className="rounded-t-3xl bg-white p-5 text-center shadow-card ring-1 ring-border">
            <marche.icone
              aria-hidden
              className={`mx-auto size-8 ${marche.rang === "1" ? "text-sun motion-safe:animate-float" : "text-logo-blue"}`}
            />
            <p className="mt-2 text-xs font-extrabold uppercase tracking-widest text-logo-red">
              {marche.titre}
            </p>
            <div className="mt-3 grid gap-3">
              {marche.equipes.map((e) => (
                <Equipe key={e.nom} e={e} />
              ))}
            </div>
          </div>
          <div
            aria-hidden
            className={`flex items-start justify-center rounded-b-xl pt-3 font-display text-5xl text-ink/80 md:text-6xl ${marche.hauteur} ${marche.fond}`}
          >
            {marche.rang}
          </div>
        </li>
      ))}
    </ol>
  );
}

// Les joueurs primés : leur pseudonyme et leur établissement, jamais leur nom (docs/RULES.md). Tant que la
// liste n'est pas transmise, des cartes « bientôt dévoilé » gardent leur place.
function JoueursPrimes({ joueurs }: { joueurs: JoueurPrime[] }) {
  if (joueurs.length > 0)
    return (
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {joueurs.map((j, i) => (
          <li
            key={`${j.pseudonyme}-${j.distinction}`}
            data-reveal
            style={retard(i)}
            className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
          >
            <span className="inline-flex size-12 items-center justify-center rounded-2xl bg-sun text-ink">
              <Trophy className="size-6" />
            </span>
            <p className="mt-4 text-xs font-extrabold uppercase tracking-widest text-logo-red">
              {j.distinction}
            </p>
            <p className="mt-1 font-display text-2xl text-logo-blue">{j.pseudonyme}</p>
            <p className="mt-1 text-sm font-bold text-muted-foreground">{j.etablissement}</p>
          </li>
        ))}
      </ul>
    );
  return (
    <ul className="grid gap-5 sm:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <li
          key={i}
          data-reveal
          style={retard(i)}
          className="relative overflow-hidden rounded-3xl bg-white p-6 text-center shadow-card ring-1 ring-border"
        >
          <span
            aria-hidden
            className="absolute inset-0 bg-[radial-gradient(circle_at_50%_25%,color-mix(in_oklch,var(--sun)_30%,transparent),transparent_60%)]"
          />
          <span className="relative mx-auto flex size-20 items-center justify-center rounded-full border-2 border-dashed border-tangerine/60 bg-mist-soft">
            <UserRound aria-hidden className="size-10 text-logo-blue/30" />
            <span className="absolute -right-1 -top-1 inline-flex size-8 items-center justify-center rounded-full bg-sun font-display text-lg text-ink shadow-card">
              ?
            </span>
          </span>
          <p className="relative mt-4 font-display text-2xl text-logo-blue">{m.gpal_bientot()}</p>
          <p className="relative mt-1 text-sm font-semibold text-muted-foreground">
            {m.gpal_bientot_d()}
          </p>
        </li>
      ))}
    </ul>
  );
}

function PalmaresAVenir({ edition }: { edition: Edition }) {
  return (
    <div className="mx-auto grid max-w-7xl items-end gap-8 px-5 pt-10 lg:grid-cols-[1.2fr_1fr]">
      <div className="pb-16 lg:pb-24">
        <p className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-logo-red">
          <Hourglass className="size-4" />{" "}
          {m.edition_titre({ ordinal: ordinal(edition.numero), etat: libelleSaison(edition.id) })}
        </p>
        <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
          <span className="block">{m.gpal_a_ecrire_1()}</span>
          <span className="block text-sun">{m.gpal_a_ecrire_2()}</span>
        </h1>
        <p className="mt-5 max-w-xl text-lg font-medium text-white/85">
          {m.gpal_a_venir_texte({ saison: edition.id })}
        </p>
        <div className="mt-6">
          {edition.debut ? (
            <CompteARebours cible={edition.debut} clair />
          ) : (
            <p className="font-display text-3xl text-sun">{m.edition_date_bientot()}</p>
          )}
        </div>
        <a
          href={lien("/genie-imhotep/inscription")}
          className="btn-fx mt-9 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
        >
          {m.gi_inscrire()} <ArrowRight className="size-4" />
        </a>
      </div>
      <img
        src={mascottesTrophees}
        alt={m.gpal_attente_alt()}
        width={1122}
        height={1402}
        className="mx-auto w-56 drop-shadow-2xl sm:w-72 lg:w-[24rem]"
      />
    </div>
  );
}

function PalmaresEdition() {
  const edition = Route.useLoaderData();
  const terminee = edition.statut === "terminee";

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière claire : des rayons dorés derrière les mascottes aux trophées, le titre de la saison. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-[oklch(0.66_0.21_30)] via-logo-red to-[oklch(0.47_0.19_25)] text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-full -z-10 size-[60rem] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_220_100/0.16)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite] lg:left-[75%] lg:top-[70%]"
        />
        <DecorAnime />
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 pt-8 md:pt-12">
          <FilAriane
            clair
            rubrique={m.menu_genie_imhotep()}
            parent={{ t: m.menu_palmares(), href: "/genie-imhotep/palmares" }}
            page={m.gpal_edition_saison({ saison: libelleSaison(edition.id) })}
          />
          <a
            href={lien("/genie-imhotep/palmares#editions")}
            className="inline-flex items-center gap-1.5 text-sm font-bold text-white hover:underline"
          >
            <ArrowLeft className="size-4" /> {m.gpal_toutes_editions()}
          </a>
        </div>
        {terminee ? (
          <div className="mx-auto grid max-w-7xl items-end gap-8 px-5 pt-6 lg:grid-cols-[1.2fr_1fr]">
            <div data-reveal="left" className="pb-16 lg:pb-20">
              <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                <Sparkles className="size-4" />{" "}
                {m.gpal_badge_edition({ ordinal: ordinal(edition.numero) })}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.gpal_laureats()}</span>
                <span className="block text-sun">{libelleSaison(edition.id)}</span>
              </h1>
              <p className="mt-5 max-w-2xl text-lg font-medium text-white/85">
                {m.gpal_laureats_texte()}
              </p>
              <p className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-white px-5 py-3 shadow-card ring-1 ring-border">
                <Crown aria-hidden className="size-6 text-tangerine" />
                <span>
                  <span className="block text-xs font-extrabold uppercase tracking-widest text-muted-foreground">
                    {m.edition_champion()}
                  </span>
                  <span className="font-display text-2xl text-logo-blue">{edition.champion}</span>
                </span>
              </p>
            </div>
            <img
              src={mascottesTrophees}
              alt={m.gpal_mascottes_alt()}
              width={1122}
              height={1402}
              data-reveal="zoom"
              className="mx-auto w-64 drop-shadow-2xl sm:w-80 lg:w-[26rem]"
            />
          </div>
        ) : (
          <PalmaresAVenir edition={edition} />
        )}
      </section>

      {terminee && (
        <>
          <section className="mx-auto max-w-7xl px-5 py-20">
            <EnTete
              sur={m.gpal_phase_nationale()}
              bleu={m.gpal_podium_bleu()}
              vert={m.gpal_podium_vert()}
            >
              {m.gpal_podium_texte()}
            </EnTete>
            <ContenuEnFrancais className="mt-4" />
            <div className="mt-12">
              <Podium />
            </div>
          </section>

          <section className="bg-white py-20">
            <div className="mx-auto max-w-7xl px-5">
              <EnTete
                sur={m.gpal_talents_sur()}
                bleu={m.gpal_talents_bleu()}
                vert={m.gpal_talents_vert()}
              >
                {m.gpal_talents_texte()}
              </EnTete>
              <div className="mt-10">
                <JoueursPrimes joueurs={edition.joueursPrimes ?? []} />
              </div>
            </div>
          </section>

          <section className="mx-auto max-w-7xl px-5 py-20">
            <EnTete
              sur={m.gpal_phase_regionale()}
              bleu={m.gpal_regionaux_bleu()}
              vert={m.gpal_regionaux_vert()}
            >
              {m.gpal_regionaux_texte()}
            </EnTete>
            <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {ordreRegions.map((id, i) => {
                const r = regionales.find((x) => x.region === id);
                if (!r) return null;
                const titre = parcoursNational(r.gagnant);
                return (
                  <li
                    key={id}
                    data-reveal
                    style={retard(i % 4)}
                    className="relative overflow-hidden rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
                  >
                    <span
                      aria-hidden
                      className="absolute inset-x-0 top-0 h-2"
                      style={{ backgroundColor: couleur(id) }}
                    />
                    <p className="text-xs font-extrabold uppercase tracking-widest text-muted-foreground">
                      DRE {nomsRegions[id]}
                    </p>
                    <p className="mt-2 font-display text-2xl leading-tight text-logo-blue">
                      {r.gagnant}
                    </p>
                    <p
                      className={`mt-4 inline-flex rounded-full px-3 py-1 text-xs font-extrabold uppercase ${
                        r.gagnant === CHAMPION ? "bg-sun text-ink" : "bg-mist text-logo-blue"
                      }`}
                    >
                      {titre}
                    </p>
                  </li>
                );
              })}
            </ul>
          </section>
        </>
      )}

      {terminee && (
        <section className="mx-auto max-w-7xl px-5 pb-20">
          <div
            data-reveal="zoom"
            className="flex flex-col items-start justify-between gap-6 rounded-3xl bg-sun p-8 md:flex-row md:items-center md:p-12"
          >
            <div>
              <h2 className="text-3xl text-ink md:text-4xl">
                {m.gpal_tous_matchs_1()}{" "}
                <span className="text-logo-blue">{m.gpal_tous_matchs_2()}</span>
              </h2>
              <p className="mt-2 max-w-2xl font-semibold text-ink/75">
                {m.gpal_tous_matchs_texte()}
              </p>
            </div>
            <a
              href={lien(`/genie-imhotep/hall-of-fame/${edition.id}`)}
              className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
            >
              {m.gi_voir_hof()} <ArrowRight className="size-4" />
            </a>
          </div>
        </section>
      )}

      <SiteFooter />
    </div>
  );
}
