import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  BarChart3,
  Brain,
  Gamepad2,
  Landmark,
  MessageCircleQuestion,
  School,
  Trophy,
  User,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

import { Compteur } from "@/components/Compteur";
import mascotte from "@/assets/mascotte-bourses.webp";
import {
  chargerChiffresAccueil,
  chargerClassementPublic,
  type ClassementClubsPublic,
  type ClassementPersonnesPublic,
  type ClassementPublic,
  type PeriodeClassement,
} from "@/lib/api/client";

const MEDAILLES = [
  "bg-linear-to-br from-sun to-[oklch(0.75_0.16_75)] text-ink",
  "bg-linear-to-br from-white to-[oklch(0.82_0.02_260)] text-ink",
  "bg-linear-to-br from-[oklch(0.72_0.13_55)] to-[oklch(0.58_0.13_45)] text-white",
];
const MEDAILLE_SIMPLE = "bg-white/15 text-white";

const TUILES: {
  cle: "eleves" | "clubs" | "quiz" | "points";
  libelle: string;
  icone: LucideIcon;
  fond: string;
}[] = [
  {
    cle: "eleves",
    libelle: "Élèves inscrits",
    icone: Users,
    fond: "from-[oklch(0.5_0.17_258)] to-[oklch(0.38_0.15_262)]",
  },
  {
    cle: "clubs",
    libelle: "Clubs Santé (établissements)",
    icone: Landmark,
    fond: "from-[oklch(0.55_0.11_200)] to-[oklch(0.4_0.1_210)]",
  },
  {
    cle: "quiz",
    libelle: "Quiz réalisés",
    icone: Brain,
    fond: "from-[oklch(0.5_0.2_300)] to-[oklch(0.38_0.18_295)]",
  },
  {
    cle: "points",
    libelle: "Points gagnés",
    icone: Trophy,
    fond: "from-[oklch(0.55_0.1_60)] to-[oklch(0.4_0.08_50)]",
  },
];

type Onglet = "eleves" | "clubs";

// Le Top 5 du semestre en cours ; sans semestre en cours ou sans point ce semestre, celui depuis le début.
async function top5(categorie: Onglet): Promise<ClassementPublic | null> {
  const charger = (periode: PeriodeClassement) =>
    chargerClassementPublic({ categorie, niveau: "national", periode, par_page: 5 });
  const semestre = await charger("semestre").catch(() => null);
  if (semestre && semestre.lignes.length > 0) return semestre;
  const historique = await charger("historique");
  return historique.lignes.length > 0 ? historique : null;
}

// La section « Jeux & classement » de l'accueil (spec 021, spec 034, spec 036) : les chiffres nationaux du programme et
// le Top 5 national des élèves (par leur seul pseudonyme, RULES) ou des Clubs Santé. Tant que personne n'a de points,
// le classement s'annonce.
export function PodiumClubs() {
  const [onglet, setOnglet] = useState<Onglet>("eleves");
  const { data: chiffres } = useQuery({
    queryKey: ["chiffres-accueil"],
    queryFn: chargerChiffresAccueil,
    retry: false,
    staleTime: 5 * 60_000,
  });
  const { data: classement } = useQuery({
    queryKey: ["top5-accueil", onglet],
    queryFn: () => top5(onglet),
    retry: false,
    staleTime: 5 * 60_000,
  });

  return (
    <section
      aria-labelledby="titre-podium"
      className="relative isolate overflow-hidden bg-linear-to-br from-[oklch(0.28_0.12_265)] via-[oklch(0.32_0.15_270)] to-[oklch(0.3_0.17_290)] py-14 text-white md:py-16"
    >
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

      <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)] items-center gap-10 px-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] xl:gap-12">
        <div
          data-reveal="left"
          className="relative grid items-end gap-6 md:grid-cols-[15rem_minmax(0,1fr)]"
        >
          <img
            src={mascotte}
            alt=""
            aria-hidden
            width={1414}
            height={2000}
            loading="lazy"
            className="pointer-events-none mx-auto w-32 drop-shadow-[0_20px_30px_rgba(0,0,0,0.45)] motion-safe:animate-respire md:w-60"
          />
          <div className="text-center md:text-left">
            <p className="inline-flex items-center gap-2 rounded-full border-2 border-sun/80 bg-ink/20 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide">
              <Gamepad2 aria-hidden className="size-5 text-sun" /> Jeux & classement
            </p>
            <h2 id="titre-podium" className="mt-5 font-display text-4xl leading-tight md:text-5xl">
              Et si ton lycée devenait{" "}
              <span className="mt-2 inline-block -rotate-1 rounded-2xl bg-sun px-4 py-1 text-ink shadow-lg shadow-sun/20">
                N°1 du Togo&#8239;?
              </span>
            </h2>
            <p className="mt-5 max-w-lg text-lg font-semibold text-white/90 max-md:mx-auto">
              Teste tes connaissances en santé et fais grimper ton Club Santé dans le classement
              national&#8239;!
            </p>
          </div>

          <ul
            className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:col-span-2"
            aria-label="Le programme en chiffres"
          >
            {TUILES.map(({ cle, libelle, icone: Icone, fond }) => (
              <li
                key={cle}
                className={`flex flex-col items-center rounded-2xl bg-linear-to-b px-3 py-4 text-center shadow-lg ring-1 ring-white/25 ${fond}`}
              >
                <Icone aria-hidden className="size-8 text-sun" />
                <span className="mt-2 font-display text-3xl leading-none">
                  <Compteur key={chiffres?.[cle] ?? 0} value={chiffres?.[cle] ?? 0} />
                </span>
                <span className="mt-1.5 text-sm font-semibold leading-tight text-white/90">
                  {libelle}
                </span>
              </li>
            ))}
          </ul>

          <div className="grid gap-3 rounded-2xl bg-white/10 p-4 ring-1 ring-white/20 sm:grid-cols-2 sm:divide-x sm:divide-white/20 md:col-span-2">
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

          <div className="flex flex-wrap justify-center gap-3 md:col-span-2 md:justify-start">
            <Link
              to="/jeux"
              className="btn-fx inline-flex items-center gap-2 rounded-full bg-sun px-7 py-3.5 text-lg font-extrabold text-ink shadow-lg shadow-sun/20"
            >
              <Gamepad2 aria-hidden className="size-6" /> Découvrir les jeux
              <ArrowRight aria-hidden className="size-5" />
            </Link>
            <Link
              to="/hall-of-fame"
              className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-white/80 px-7 py-3.5 text-lg font-extrabold text-white hover:bg-white hover:text-ink"
            >
              <Trophy aria-hidden className="size-6 text-sun" /> Découvrir le classement
              <ArrowRight aria-hidden className="size-5" />
            </Link>
          </div>
        </div>

        <div
          data-reveal="right"
          className="mx-auto w-full min-w-0 max-w-xl rounded-[2rem] bg-[oklch(0.25_0.11_268)]/80 p-4 shadow-[0_0_40px_oklch(0.6_0.2_285/0.45)] ring-2 ring-[oklch(0.7_0.15_280)]/60 backdrop-blur-md sm:p-6"
        >
          <p className="flex items-center justify-center gap-3 text-center font-display text-2xl md:text-3xl">
            <Trophy aria-hidden className="size-8 text-sun drop-shadow" /> Classement national
          </p>

          <div
            role="tablist"
            aria-label="Classement à afficher"
            className="mt-5 grid grid-cols-2 rounded-full p-1 ring-2 ring-white/30"
          >
            <BoutonOnglet
              actif={onglet === "eleves"}
              onClick={() => setOnglet("eleves")}
              icone={User}
            >
              Élèves
            </BoutonOnglet>
            <BoutonOnglet
              actif={onglet === "clubs"}
              onClick={() => setOnglet("clubs")}
              icone={School}
            >
              Clubs
            </BoutonOnglet>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm">
            <p className="font-bold">
              Top 5 –{" "}
              {classement?.periode === "historique"
                ? "Depuis le début"
                : (classement?.semestre?.libelle ?? "Semestre en cours")}
            </p>
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 font-semibold text-white/90">
              <span
                aria-hidden
                className="size-2.5 rounded-full bg-[oklch(0.75_0.2_145)] motion-safe:animate-pulse"
              />
              Classement en temps réel
            </p>
          </div>

          <div
            role="tabpanel"
            aria-label={onglet === "eleves" ? "Top 5 des élèves" : "Top 5 des clubs"}
          >
            {classement && classement.categorie === "clubs" && onglet === "clubs" ? (
              <TopClubs lignes={classement.lignes} />
            ) : classement && classement.categorie === "eleves" && onglet === "eleves" ? (
              <TopEleves lignes={classement.lignes} />
            ) : (
              <BientotLa
                texte={
                  onglet === "eleves"
                    ? "Les meilleurs élèves s’afficheront ici : joue aux quiz pour y figurer."
                    : "Les points des Clubs Santé s’afficheront ici : ton lycée peut prendre la première place."
                }
              />
            )}
          </div>

          <Link
            to="/hall-of-fame"
            className="btn-fx mt-5 flex items-center justify-center gap-2 rounded-full border-2 border-sun px-6 py-3 text-lg font-extrabold text-white hover:bg-sun hover:text-ink"
          >
            <Trophy aria-hidden className="size-6 text-sun" /> Voir tout le classement
            <ArrowRight aria-hidden className="size-5" />
          </Link>
        </div>
      </div>
    </section>
  );
}

function BoutonOnglet({
  actif,
  onClick,
  icone: Icone,
  children,
}: {
  actif: boolean;
  onClick: () => void;
  icone: LucideIcon;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={actif}
      onClick={onClick}
      className={`inline-flex items-center justify-center gap-2 rounded-full px-4 py-2.5 font-extrabold transition ${
        actif ? "bg-sun text-ink shadow-lg" : "text-white hover:bg-white/10"
      }`}
    >
      <Icone aria-hidden className="size-5" /> {children}
    </button>
  );
}

function Ligne({
  rang,
  index,
  initiale,
  children,
  points,
}: {
  rang: number;
  index: number;
  initiale: React.ReactNode;
  children: React.ReactNode;
  points: number;
}) {
  const premier = index === 0;
  return (
    <li
      className={`flex items-center gap-3 rounded-2xl px-3 py-2.5 sm:gap-4 sm:px-4 ${
        premier
          ? "bg-linear-to-r from-sun to-[oklch(0.9_0.12_90)] text-ink shadow-lg"
          : "bg-white/10 ring-1 ring-white/15"
      }`}
    >
      <span
        aria-hidden
        className={`inline-flex size-9 shrink-0 items-center justify-center rounded-full font-display text-lg ring-2 ring-white/60 ${MEDAILLES[index] ?? MEDAILLE_SIMPLE}`}
      >
        {rang}
      </span>
      <span className="sr-only">{`${rang}${rang === 1 ? "er" : "e"}`}</span>
      <span
        aria-hidden
        className={`hidden size-10 shrink-0 items-center justify-center rounded-full font-display text-lg sm:inline-flex ${
          premier ? "bg-ink/10" : "bg-white/15"
        }`}
      >
        {initiale}
      </span>
      <span className="min-w-0 flex-1">{children}</span>
      <span className="shrink-0 font-display text-lg sm:text-xl">
        {points.toLocaleString("fr-FR")} <span className="text-sm">pts</span>
      </span>
    </li>
  );
}

function TopEleves({ lignes }: { lignes: ClassementPersonnesPublic["lignes"] }) {
  return (
    <ol className="mt-3 space-y-2" aria-label="Top 5 des élèves">
      {lignes.map((eleve, i) => (
        <Ligne
          key={`${eleve.rang}-${eleve.nom}`}
          rang={eleve.rang}
          index={i}
          initiale={eleve.nom.charAt(0).toUpperCase()}
          points={eleve.points}
        >
          <span className="block truncate font-extrabold">{eleve.nom}</span>
          <span className="block truncate text-sm font-medium opacity-80">
            {eleve.club ? `${eleve.club} · ${eleve.dre}` : eleve.dre}
          </span>
        </Ligne>
      ))}
    </ol>
  );
}

function TopClubs({ lignes }: { lignes: ClassementClubsPublic["lignes"] }) {
  return (
    <ol className="mt-3 space-y-2" aria-label="Top 5 des clubs">
      {lignes.map((club, i) => (
        <Ligne
          key={club.club_id}
          rang={club.rang}
          index={i}
          initiale={<School className="size-5" />}
          points={club.points}
        >
          <Link to="/clubs/$id" params={{ id: club.club_id }} className="block hover:underline">
            <span className="block truncate font-extrabold">{club.etablissement}</span>
            <span className="block truncate text-sm font-medium opacity-80">
              {club.nom} · {club.dre}
            </span>
          </Link>
        </Ligne>
      ))}
    </ol>
  );
}

function BientotLa({ texte }: { texte: string }) {
  return (
    <div className="mt-3 space-y-2">
      {[1, 2, 3, 4, 5].map((rang, i) => (
        <div
          key={rang}
          aria-hidden
          className="flex items-center gap-4 rounded-2xl bg-white/10 px-4 py-2.5 ring-1 ring-white/15"
        >
          <span
            className={`inline-flex size-9 shrink-0 items-center justify-center rounded-full font-display text-lg opacity-80 ${MEDAILLES[i] ?? MEDAILLE_SIMPLE}`}
          >
            {rang}
          </span>
          <span className="h-3 flex-1 rounded-full bg-white/20" />
          <span className="font-display text-lg text-white/60">? pts</span>
        </div>
      ))}
      <p className="pt-2 text-center font-bold">Le classement arrive bientôt&#8239;!</p>
      <p className="text-center text-sm font-medium text-white/75">{texte}</p>
    </div>
  );
}

function Atout({
  icone: Icone,
  titre,
  texte,
}: {
  icone: LucideIcon;
  titre: string;
  texte: string;
}) {
  return (
    <div className="flex items-center gap-3 sm:px-3 sm:first:pl-0">
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
