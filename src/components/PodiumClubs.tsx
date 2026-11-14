import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { BarChart3, Gamepad2, MessageCircleQuestion, Trophy } from "lucide-react";

import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascotteMedias from "@/assets/mascotte-medias.webp";
import { chargerPodiumClubs, type ClubPodium } from "@/lib/api/client";

const MEDAILLES = [
  "bg-linear-to-br from-sun to-[oklch(0.75_0.16_75)] text-ink",
  "bg-linear-to-br from-white to-[oklch(0.82_0.02_260)] text-ink",
  "bg-linear-to-br from-[oklch(0.72_0.13_55)] to-[oklch(0.58_0.13_45)] text-white",
];
const LIGNES = [
  "bg-linear-to-r from-sun to-[oklch(0.9_0.12_90)] text-ink",
  "bg-white/85 text-ink",
  "bg-white/70 text-ink",
];

// Le podium de l'accueil (spec 021, spec 034) : les trois lycées dont le Club Santé a le plus de points. Un club reçoit la
// moitié de chaque gain de ses élèves (« 2,5 » possible) ; tant que personne n'a de points, la carte annonce le classement.
export function PodiumClubs() {
  const { data: podium = [] } = useQuery({
    queryKey: ["podium-clubs"],
    queryFn: chargerPodiumClubs,
    retry: false,
    staleTime: 5 * 60_000,
  });

  return (
    <section
      aria-labelledby="titre-podium"
      className="relative isolate overflow-hidden bg-linear-to-br from-[oklch(0.28_0.12_265)] via-[oklch(0.32_0.15_270)] to-[oklch(0.25_0.1_255)] py-12 text-white md:py-14"
    >
      {/* Les carreaux du site, plus marqués au centre et fondus vers les bords. */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-carnet-sombre [mask-image:radial-gradient(ellipse_at_center,black_35%,transparent_85%)]"
      />
      <div
        aria-hidden
        className="absolute -left-32 top-0 -z-10 size-[28rem] rounded-full bg-[oklch(0.65_0.15_200)]/25 blur-3xl motion-safe:animate-respire"
      />
      <div
        aria-hidden
        className="absolute -bottom-40 right-0 -z-10 size-[32rem] rounded-full bg-grape/40 blur-3xl motion-safe:animate-derive"
      />

      <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 lg:grid-cols-[auto_minmax(0,1.3fr)_minmax(0,1fr)] lg:gap-8">
        {/* La mascotte de l'axe Génie Imhotep, en pied, sur un halo bleu. */}
        <div className="relative mx-auto lg:self-end">
          <span
            aria-hidden
            className="absolute bottom-6 left-1/2 aspect-square w-[115%] -translate-x-1/2 rounded-full bg-sky/35 blur-sm"
          />
          <img
            src={mascotteImhotep}
            alt="La mascotte de l’axe Génie Imhotep"
            width={1414}
            height={2000}
            loading="lazy"
            className="relative h-64 w-auto drop-shadow-[0_25px_35px_rgba(0,0,0,0.45)] lg:h-[24rem]"
          />
        </div>

        <div data-reveal="left" className="relative text-center lg:text-left">
          <p className="inline-flex items-center gap-2 rounded-full border-2 border-sun/80 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide">
            <Gamepad2 aria-hidden className="size-5 text-sun" /> Jeux & classement
          </p>
          <h2 id="titre-podium" className="mt-5 font-display text-4xl leading-tight md:text-5xl">
            Et si ton lycée devenait <span className="text-sun">N°1 du Togo&#8239;?</span>
          </h2>
          <p className="mt-4 max-w-lg text-lg font-medium text-white/85">
            Teste tes connaissances en santé et fais grimper ton Club Santé dans le classement
            national&#8239;!
          </p>
          <div className="mt-6 grid gap-3 text-left sm:grid-cols-2">
            <Atout
              icone={MessageCircleQuestion}
              titre="Des quiz santé"
              texte="Apprends en t’amusant"
            />
            <Atout
              icone={BarChart3}
              titre="Un classement national"
              texte="Fais progresser ton club"
            />
          </div>
          <Link
            to="/jeux"
            className="btn-fx mt-8 inline-flex rounded-full bg-sun px-10 py-4 text-lg font-extrabold text-ink shadow-lg shadow-sun/20"
          >
            Découvrir les jeux
          </Link>
        </div>

        {/* La mascotte de l'axe Production TV & médias, accoudée au-dessus du podium. */}
        <div data-reveal="right" className="relative mx-auto w-full max-w-md pt-40 sm:pt-44">
          <img
            src={mascotteMedias}
            alt="La mascotte de l’axe Production TV & médias"
            width={1414}
            height={2000}
            loading="lazy"
            className="absolute right-0 top-0 z-10 h-56 w-auto drop-shadow-[0_20px_30px_rgba(0,0,0,0.45)] sm:-right-4 sm:h-60"
          />
          <div className="relative rounded-[2rem] bg-white/10 p-6 ring-1 ring-white/25 backdrop-blur-md md:p-8">
            <Trophy aria-hidden className="mx-auto size-10 text-sun drop-shadow" />
            <p className="mt-2 text-center font-display text-3xl">Top 3 des lycées</p>
            {podium.length > 0 ? <Classement podium={podium} /> : <BientotLa />}
          </div>
        </div>
      </div>
    </section>
  );
}

function Classement({ podium }: { podium: ClubPodium[] }) {
  return (
    <ol className="mt-4 space-y-2.5">
      {podium.map((club, i) => (
        <li
          key={club.id}
          className={`flex items-center gap-4 rounded-2xl px-4 py-3 shadow-lg ${LIGNES[i]}`}
        >
          <span
            aria-hidden
            className={`inline-flex size-11 shrink-0 items-center justify-center rounded-full font-display text-xl ring-2 ring-white/70 ${MEDAILLES[i]}`}
          >
            {club.rang}
          </span>
          <span className="sr-only">{`${club.rang}${club.rang === 1 ? "er" : "e"}`}</span>
          <Link to="/clubs/$id" params={{ id: club.id }} className="min-w-0 flex-1 hover:underline">
            <span className="block truncate font-extrabold">{club.etablissement}</span>
            <span className="block truncate text-sm font-medium opacity-75">
              {club.nom} · {club.dre}
            </span>
          </Link>
          <span className="shrink-0 font-display text-xl">
            {club.points.toLocaleString("fr-FR")} <span className="text-sm">pts</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

function BientotLa() {
  return (
    <div className="mt-4 space-y-2.5">
      {[1, 2, 3].map((rang, i) => (
        <div
          key={rang}
          aria-hidden
          className="flex items-center gap-4 rounded-2xl bg-white/10 px-4 py-3 ring-1 ring-white/15"
        >
          <span
            className={`inline-flex size-11 shrink-0 items-center justify-center rounded-full font-display text-xl opacity-80 ${MEDAILLES[i]}`}
          >
            {rang}
          </span>
          <span className="h-3 flex-1 rounded-full bg-white/20" />
          <span className="font-display text-xl text-white/60">? pts</span>
        </div>
      ))}
      <p className="pt-2 text-center font-bold">Le classement arrive bientôt&#8239;!</p>
      <p className="text-center text-sm font-medium text-white/75">
        Les points des Clubs Santé s’afficheront ici : ton lycée peut prendre la première place.
      </p>
    </div>
  );
}

function Atout({
  icone: Icone,
  titre,
  texte,
}: {
  icone: typeof Trophy;
  titre: string;
  texte: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl bg-white/10 p-4 ring-1 ring-white/20">
      <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-xl bg-white/15 text-sun">
        <Icone aria-hidden className="size-6" />
      </span>
      <span>
        <span className="block font-extrabold">{titre}</span>
        <span className="block text-sm font-medium text-white/75">{texte}</span>
      </span>
    </div>
  );
}
