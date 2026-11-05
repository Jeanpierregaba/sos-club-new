import { createFileRoute } from "@tanstack/react-router";
import {
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
import { FriseEditions } from "@/components/FriseEditions";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { editionDe, ordinal, type Edition } from "@/lib/genie-imhotep-editions";
import {
  CHAMPION,
  joueursPrimes,
  nationale,
  nomsRegions,
  ordreRegions,
  regionales,
  type EquipeNationale,
  type RegionId,
} from "@/lib/genie-imhotep-resultats";
import { dessins } from "@/lib/togo-dre";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";

export const Route = createFileRoute("/genie-imhotep/palmares")({
  head: () => ({
    meta: [
      { title: "Palmarès — Génie Imhotep" },
      {
        name: "description",
        content:
          "Le palmarès du Championnat national Génie Imhotep, saison par saison : le podium national, les champions régionaux et les joueurs primés.",
      },
      { property: "og:title", content: "Le palmarès du Génie Imhotep" },
    ],
  }),
  // ?edition=2026-2027 : la saison affichée ; sans paramètre, la dernière édition terminée.
  validateSearch: (search: Record<string, unknown>): { edition?: string } =>
    typeof search["edition"] === "string" ? { edition: search["edition"] } : {},
  component: Palmares,
});

const couleur = (id: RegionId) => dessins[id]!.couleur;

// Le podium de l'édition 2025-2026, tiré du tableau final : pas de match pour la 3e place, les deux
// demi-finalistes battus la partagent.
const finale = nationale.find((m) => m.tour === "finale")!;
const equipe = (nom: string) => [finale.a, finale.b].find((e) => e.nom === nom)!;
const champion = equipe(CHAMPION);
const finaliste = [finale.a, finale.b].find((e) => e.nom !== CHAMPION)!;
const demiFinalistes = nationale
  .filter((m) => m.tour === "demi")
  .map((m) => (m.a.nom === m.gagnant ? m.b : m.a));

// Le tour le plus loin atteint au national par chaque champion régional.
const parcoursNational = (nom: string) => {
  if (nom === CHAMPION) return "Champion national";
  if (nom === finaliste.nom) return "Finaliste";
  if (demiFinalistes.some((e) => e.nom === nom)) return "Demi-finaliste";
  return nationale.some((m) => m.a.nom === nom || m.b.nom === nom)
    ? "Quart-de-finaliste"
    : "Champion régional";
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
      titre: "Finaliste",
      equipes: [finaliste],
      hauteur: "h-28 md:h-36",
      fond: "bg-[color-mix(in_oklch,var(--sky)_85%,white)]",
      ordre: "md:order-1",
      icone: Medal,
    },
    {
      rang: "1",
      titre: "Champion national",
      equipes: [champion],
      hauteur: "h-40 md:h-52",
      fond: "bg-sun",
      ordre: "order-first md:order-2",
      icone: Crown,
    },
    {
      rang: "3",
      titre: "Demi-finalistes",
      equipes: demiFinalistes,
      hauteur: "h-20 md:h-24",
      fond: "bg-[color-mix(in_oklch,var(--tangerine)_80%,white)]",
      ordre: "md:order-3",
      icone: Award,
    },
  ];
  return (
    <ol className="mx-auto grid max-w-5xl items-end gap-6 md:grid-cols-3 md:gap-4">
      {marches.map((m, i) => (
        <li key={m.rang} data-reveal style={retard(i)} className={`flex flex-col ${m.ordre}`}>
          <div className="rounded-t-3xl bg-white p-5 text-center shadow-card ring-1 ring-border">
            <m.icone
              aria-hidden
              className={`mx-auto size-8 ${m.rang === "1" ? "text-sun motion-safe:animate-float" : "text-logo-blue"}`}
            />
            <p className="mt-2 text-xs font-extrabold uppercase tracking-widest text-logo-red">
              {m.titre}
            </p>
            <div className="mt-3 grid gap-3">
              {m.equipes.map((e) => (
                <Equipe key={e.nom} e={e} />
              ))}
            </div>
          </div>
          <div
            aria-hidden
            className={`flex items-start justify-center rounded-b-xl pt-3 font-display text-5xl text-ink/80 md:text-6xl ${m.hauteur} ${m.fond}`}
          >
            {m.rang}
          </div>
        </li>
      ))}
    </ol>
  );
}

// Les joueurs primés : leur pseudonyme et leur établissement, jamais leur nom (docs/RULES.md). Tant que la
// liste n'est pas transmise, des cartes « bientôt dévoilé » gardent leur place.
function JoueursPrimes() {
  if (joueursPrimes.length > 0)
    return (
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {joueursPrimes.map((j, i) => (
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
          className="relative overflow-hidden rounded-3xl bg-night p-6 text-center text-white shadow-card"
        >
          <span
            aria-hidden
            className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgb(255_210_80/0.25),transparent_60%)]"
          />
          <span className="relative mx-auto flex size-20 items-center justify-center rounded-full bg-white/10 ring-2 ring-dashed ring-sun/60">
            <UserRound aria-hidden className="size-10 text-white/40" />
            <span className="absolute -right-1 -top-1 inline-flex size-8 items-center justify-center rounded-full bg-sun font-display text-lg text-ink">
              ?
            </span>
          </span>
          <p className="relative mt-4 font-display text-2xl text-sun">Bientôt dévoilé</p>
          <p className="relative mt-1 text-sm font-semibold text-white/70">
            Pseudonyme et établissement du joueur primé
          </p>
        </li>
      ))}
    </ul>
  );
}

function PalmaresAVenir({ edition }: { edition: Edition }) {
  return (
    <div className="mx-auto max-w-7xl px-5 pb-16 pt-8 lg:pb-24">
      <p className="inline-flex items-center gap-2 rounded-full bg-logo-red px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide">
        <Hourglass className="size-4 text-sun" /> {ordinal(edition.numero)} édition · {edition.id}
      </p>
      <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
        <span className="block">Un palmarès</span>
        <span className="block text-sun">encore à écrire</span>
      </h1>
      <p className="mt-5 max-w-xl text-lg font-medium text-white/80">
        Les lauréats de la saison {edition.id} seront inscrits ici à la fin du championnat. Le coup
        d’envoi approche :
      </p>
      <div className="mt-6">
        {edition.debut ? (
          <CompteARebours cible={edition.debut} />
        ) : (
          <p className="font-display text-3xl text-sun">Date bientôt annoncée</p>
        )}
      </div>
      <a
        href="/genie-imhotep/inscription"
        className="btn-fx mt-9 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
      >
        Inscrire mon établissement <ArrowRight className="size-4" />
      </a>
    </div>
  );
}

function Palmares() {
  const { edition: id } = Route.useSearch();
  const edition = editionDe(id);
  const terminee = edition.statut === "terminee";

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : un ciel de nuit doré, la frise des saisons, puis le titre de la saison choisie. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue via-ink to-night text-white">
        <div
          aria-hidden
          className="absolute left-1/2 top-full -z-10 size-[60rem] lg:left-[75%] lg:top-[70%] -translate-x-1/2 -translate-y-1/2 bg-[repeating-conic-gradient(rgb(255_210_80/0.10)_0deg_6deg,transparent_6deg_18deg)] [mask-image:radial-gradient(circle,black_20%,transparent_65%)] motion-safe:animate-[spin_120s_linear_infinite]"
        />
        <DecorAnime />
        <div className="mx-auto max-w-7xl px-5 pt-8 md:pt-12">
          <FilAriane rubrique="Génie Imhotep" page="Palmarès" clair />
          <div className="mt-8">
            <FriseEditions actuelle={edition} vers="/genie-imhotep/palmares" />
          </div>
        </div>
        {terminee ? (
          <div className="mx-auto grid max-w-7xl items-end gap-8 px-5 pt-6 lg:grid-cols-[1.2fr_1fr]">
            <div data-reveal="left" className="pb-16 lg:pb-20">
              <p className="inline-flex items-center gap-2 rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                <Sparkles className="size-4" /> {ordinal(edition.numero)} édition · {edition.id}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Le palmarès</span>
                <span className="block text-sun">des lauréats</span>
              </h1>
              <p className="mt-5 max-w-2xl text-lg font-medium text-white/80">
                Ils ont buzzé plus vite, répondu plus juste et porté haut les couleurs de leur
                établissement : honneur aux lauréats du Championnat national Génie Imhotep.
              </p>
              <p className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-white/10 px-5 py-3 ring-1 ring-white/15 backdrop-blur-sm">
                <Crown aria-hidden className="size-6 text-sun" />
                <span>
                  <span className="block text-xs font-extrabold uppercase tracking-widest text-white/60">
                    Champion national
                  </span>
                  <span className="font-display text-2xl">{CHAMPION}</span>
                </span>
              </p>
            </div>
            <img
              src={mascottesTrophees}
              alt="Des mascottes des Clubs Santé brandissent leurs trophées"
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
            <EnTete sur="Phase nationale" bleu="Le podium" vert="national">
              Les meilleurs établissements du tableau final, de la grande finale aux demi-finales.
            </EnTete>
            <div className="mt-12">
              <Podium />
            </div>
          </section>

          <section className="bg-white py-20">
            <div className="mx-auto max-w-7xl px-5">
              <EnTete sur="Les talents de la saison" bleu="Les joueurs" vert="primés">
                Les meilleurs joueurs de l’édition, présentés par leur pseudonyme et leur
                établissement.
              </EnTete>
              <div className="mt-10">
                <JoueursPrimes />
              </div>
            </div>
          </section>

          <section className="mx-auto max-w-7xl px-5 py-20">
            <EnTete sur="Phase régionale" bleu="Les 7 champions" vert="régionaux">
              Un champion par Direction Régionale de l’Éducation, qualifié pour la phase nationale.
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

      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal="zoom"
          className="flex flex-col items-start justify-between gap-6 rounded-3xl bg-sun p-8 md:flex-row md:items-center md:p-12"
        >
          <div>
            <h2 className="text-3xl text-ink md:text-4xl">
              Tous les matchs, <span className="text-logo-blue">phase par phase</span>
            </h2>
            <p className="mt-2 max-w-2xl font-semibold text-ink/75">
              Le parcours du champion, le tableau final et les résultats de chaque région sont dans
              le Hall of Fame.
            </p>
          </div>
          <a
            href={`/genie-imhotep/hall-of-fame?edition=${edition.id}`}
            className="btn-fx inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
          >
            Voir le Hall of Fame <ArrowRight className="size-4" />
          </a>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
