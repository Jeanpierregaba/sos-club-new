import { useState, type CSSProperties } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Crown,
  Gamepad2,
  GraduationCap,
  Medal,
  Star,
  UserPlus,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import { DefiQuiz, type Defi } from "@/components/quiz/DefiQuiz";
import { chargerCatalogueJeux, type CatalogueQuiz } from "@/lib/api/client";
import {
  MAX_POINTS_ETOILES,
  MAX_POINTS_QUIZ,
  NIVEAUX_JEUX,
  points,
  type NiveauJeux,
} from "@/lib/bareme";
import { niveauParNumero, poles } from "@/lib/quiz";
import mascottesVs from "@/assets/mascottes-vs.webp";
import mascottesTrophees from "@/assets/mascottes-trophees.webp";

export const Route = createFileRoute("/jeux")({
  head: () => ({
    meta: [
      { title: "Jeux — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "L'arène de gamification des Clubs Santé : 100 quiz officiels en 6 pôles, 922 questions, des points et un classement national.",
      },
      { property: "og:title", content: "Joue, apprends & deviens champion de la santé" },
    ],
  }),
  // Les quiz jouables (spec 031). API en panne : la page reste lisible, sans bouton pour jouer.
  loader: () => chargerCatalogueJeux().catch(() => null),
  component: Jeux,
});

// Numéro de chaque quiz dans le parcours (1 à 100) : les pôles se suivent.
const departs = poles.map((_, i) => poles.slice(0, i).reduce((n, p) => n + p.quiz.length, 1));
const totalQuiz = poles.reduce((n, p) => n + p.quiz.length, 0);

// Spec 034 : 10 000 points de quiz et 6 000 points d'étoiles au plus, pour l'élève ; la moitié pour son club.
const chiffres = [
  { n: totalQuiz, t: "Quiz défis" },
  { n: 922, t: "Questions" },
  { n: NIVEAUX_JEUX.length, t: "Niveaux, 4 étoiles" },
  { n: points(MAX_POINTS_QUIZ + MAX_POINTS_ETOILES), t: "Points à gagner" },
  { n: poles.length, t: "Pôles santé" },
];

const etapes = [
  {
    n: "01",
    sur: "Compte joueur",
    t: "S’inscrire",
    i: UserPlus,
    href: "/connexion",
    c: "bg-sky text-white",
  },
  {
    n: "02",
    sur: "100 quiz interactifs",
    t: "Jouer maintenant",
    i: Gamepad2,
    href: "#quiz",
    c: "bg-primary text-white",
  },
  {
    n: "03",
    sur: "Diplôme officiel",
    t: "Faire la certification",
    i: GraduationCap,
    href: "/certification",
    c: "bg-sun text-ink",
  },
];

// Spec 034 : le niveau fixe les points d'un quiz réussi et l'étoile à laquelle il compte.
const COULEURS: Record<NiveauJeux, string> = {
  debutant: "bg-primary/15 text-primary",
  intermediaire: "bg-sky/15 text-sky",
  avance: "bg-tangerine/15 text-tangerine",
  expert: "bg-grape/15 text-grape",
};
const niveauDe = (code: NiveauJeux) =>
  NIVEAUX_JEUX.find((x) => x.code === code) ?? NIVEAUX_JEUX[0]!;

// Chaque défi a son quiz côté serveur, retrouvé par son numéro dans le parcours officiel (spec 034).
function quizParNumero(catalogue: CatalogueQuiz | null) {
  return new Map(
    (catalogue?.quiz ?? []).flatMap((q) => (q.numero ? [[q.numero, q] as const] : [])),
  );
}

function Jeux() {
  const catalogue = Route.useLoaderData();
  const [pole, setPole] = useState(2);
  const [defi, setDefi] = useState<Defi | null>(null);
  const [niveau, setNiveau] = useState<NiveauJeux | null>(null);
  const p = poles[pole] ?? poles[0]!;
  const jouables = quizParNumero(catalogue);
  const reussis = new Set(catalogue?.progression?.reussis ?? []);
  const quiz = p.quiz
    .map(([t], i) => {
      const n = (departs[pole] ?? 1) + i;
      const serveur = jouables.get(n);
      return {
        t,
        n,
        niveau: serveur?.niveau ?? niveauParNumero.get(n) ?? "debutant",
        quiz: serveur,
        reussi: serveur ? reussis.has(serveur.id) : false,
      };
    })
    .filter((q) => !niveau || q.niveau === niveau);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière « arène » : violet profond, quadrillage lumineux, mascottes en duel. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-grape via-ink to-night text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[linear-gradient(oklch(1_0_0/0.07)_1px,transparent_1px),linear-gradient(90deg,oklch(1_0_0/0.07)_1px,transparent_1px)] bg-size-[40px_40px] [mask-image:radial-gradient(ellipse_at_70%_60%,black_10%,transparent_70%)] motion-safe:animate-defile-motif"
        />
        <div
          aria-hidden
          className="absolute right-[15%] top-1/3 -z-10 size-96 rounded-full bg-rose/30 blur-3xl motion-safe:animate-derive"
        />
        <div
          aria-hidden
          className="absolute bottom-0 left-1/4 -z-10 size-72 rounded-full bg-sky/25 blur-3xl motion-safe:animate-derive [animation-delay:-9s]"
        />
        <DecorAnime />
        <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 pb-16 pt-8 md:pt-12 lg:grid-cols-[1.2fr_1fr]">
          <div>
            <FilAriane rubrique="Gamification" page="Jeux" clair />
            <div data-reveal="left" className="pt-12">
              <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide ring-1 ring-white/25">
                <Gamepad2 className="size-4 text-sun" /> Arène nationale de gamification
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Joue, apprends</span>
                <span className="block text-sun">& deviens champion</span>
                <span className="block text-primary">de la santé</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/80">
                Relève les 100 quiz officiels issus du référentiel des 922 QCM des Clubs Santé SOS
                Docteur TV ! Accumule des points, hisse ton établissement au sommet du classement
                DRE et national, et décroche ta certification.
              </p>
            </div>
          </div>
          <img
            src={mascottesVs}
            alt="Deux mascottes du Club Santé face à face, prêtes pour le duel"
            width={2000}
            height={2000}
            data-reveal="right"
            className="mx-auto w-full max-w-md drop-shadow-2xl"
          />
        </div>
        <dl className="border-t border-white/10 bg-black/20">
          <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px px-5 sm:grid-cols-3 lg:grid-cols-5">
            {chiffres.map((c) => (
              <div key={c.t} className="flex flex-col-reverse py-6 text-center">
                <dt className="mt-2 text-xs font-bold uppercase tracking-wider text-white/60">
                  {c.t}
                </dt>
                <dd className="font-display text-4xl leading-none text-sun">{c.n}</dd>
              </div>
            ))}
          </div>
        </dl>
      </section>

      {/* Les trois étapes pour passer à l'action. */}
      <section className="mx-auto max-w-7xl px-5 pt-16">
        <p
          data-reveal
          className="text-center text-sm font-extrabold uppercase tracking-widest text-logo-red"
        >
          Passe à l’action · Choisis ton défi santé
        </p>
        <ol className="mt-6 grid gap-4 md:grid-cols-3">
          {etapes.map((e, i) => (
            <li key={e.n} data-reveal style={retard(i)}>
              <a
                href={e.href}
                className="card-fx group flex items-center gap-5 rounded-[1.75rem] bg-white p-6 shadow-card"
              >
                <span
                  className={`inline-flex size-14 shrink-0 items-center justify-center rounded-2xl ${e.c}`}
                >
                  <e.i className="size-7" />
                </span>
                <span className="flex-1">
                  <span className="block text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                    Étape {e.n} · {e.sur}
                  </span>
                  <span className="mt-1 block font-display text-2xl text-logo-blue">{e.t}</span>
                </span>
                <ArrowRight className="size-5 text-logo-blue/40 transition group-hover:translate-x-1 group-hover:text-primary" />
              </a>
            </li>
          ))}
        </ol>
      </section>

      {/* Catalogue : les 6 pôles en tuiles, puis les quiz du pôle choisi. */}
      <section id="quiz" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
        <EnTete
          sur="Parcours officiel en 6 pôles"
          bleu={`Les ${totalQuiz} quiz`}
          vert="de gamification"
        >
          {catalogue
            ? `Chaque quiz tire ${catalogue.nb_questions} questions des 922 QCM officiels. Chrono de ${catalogue.temps_ms / 1000} s par question, et ${catalogue.seuil}/${catalogue.nb_questions} minimum pour valider !`
            : "Chaque quiz tire ses questions des 922 QCM officiels, avec un chrono par question."}{" "}
          Réussis tous les quiz d’un niveau pour décrocher son étoile, et les 4 étoiles pour ta
          carte Gold.
        </EnTete>

        {catalogue?.progression && <ProgressionJeux progression={catalogue.progression} />}

        <div
          role="group"
          aria-label="Pôles"
          className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6"
        >
          {poles.map((x, i) => {
            const on = i === pole;
            return (
              <button
                key={x.id}
                type="button"
                aria-pressed={on}
                onClick={() => {
                  setPole(i);
                  setNiveau(null);
                }}
                style={{ "--c": x.couleur } as CSSProperties}
                className={`flex flex-col rounded-[1.5rem] p-4 text-left transition duration-300 ${
                  on
                    ? "-translate-y-1 bg-(color:--c) text-white shadow-card"
                    : "bg-white ring-1 ring-border hover:-translate-y-1"
                }`}
              >
                <span
                  className={`font-display text-3xl leading-none ${on ? "text-white/70" : "text-(color:--c)"}`}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="mt-3 flex-1 text-sm font-extrabold leading-snug">{x.nom}</span>
                <span
                  className={`mt-2 text-xs font-bold ${on ? "text-white/80" : "text-muted-foreground"}`}
                >
                  {x.quiz.length} quiz
                </span>
              </button>
            );
          })}
        </div>

        <div
          key={p.id}
          style={{ "--c": p.couleur } as CSSProperties}
          className="mt-8 overflow-hidden rounded-[2rem] bg-white shadow-card animate-in fade-in duration-500"
        >
          <div className="relative isolate overflow-hidden bg-(color:--c) p-7 text-white md:p-10">
            <span
              aria-hidden
              className="absolute -right-6 -top-10 -z-10 font-display text-[11rem] leading-none text-white/10"
            >
              {String(pole + 1).padStart(2, "0")}
            </span>
            <p className="text-xs font-extrabold uppercase tracking-widest text-white/80">
              Pôle {String(pole + 1).padStart(2, "0")} · {p.sur} · Quiz {departs[pole]} à{" "}
              {(departs[pole] ?? 1) + p.quiz.length - 1}
            </p>
            <h3 className="mt-2 text-3xl md:text-4xl">{p.nom}</h3>
            <p className="mt-3 max-w-3xl font-medium text-white/90">{p.d}</p>
            <ul className="mt-5 flex flex-wrap gap-2">
              {p.themes.map((t) => (
                <li
                  key={t}
                  className="rounded-full bg-white/15 px-3 py-1 text-xs font-bold ring-1 ring-white/25"
                >
                  {t}
                </li>
              ))}
            </ul>
          </div>

          <div className="p-6 md:p-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className="mr-2 text-sm font-extrabold">Difficulté :</span>
              {[null, ...NIVEAUX_JEUX].map((x) => {
                const on = niveau === (x?.code ?? null);
                return (
                  <button
                    key={x?.code ?? "toutes"}
                    type="button"
                    aria-pressed={on}
                    onClick={() => setNiveau(x?.code ?? null)}
                    className={`rounded-full px-3.5 py-1.5 text-sm font-bold transition ${
                      on ? "bg-ink text-white" : "bg-mist-soft ring-1 ring-border hover:ring-ink/30"
                    }`}
                  >
                    {x ? x.nom : "Toutes"}
                  </button>
                );
              })}
            </div>

            <p className="mt-4 rounded-2xl bg-mist-soft px-4 py-3 text-sm font-semibold text-ink/80">
              Un quiz réussi pour la première fois rapporte selon son niveau :{" "}
              {NIVEAUX_JEUX.map((x, i) => (
                <span key={x.code}>
                  {i > 0 && ", "}
                  <strong className="text-ink">
                    {x.nom} {points(x.eleve)}
                  </strong>
                </span>
              ))}
              . Ton Club Santé reçoit la moitié si tu y es affilié. Rejouer un quiz déjà réussi ne
              rapporte rien de plus.
            </p>

            {quiz.length === 0 ? (
              <p className="mt-6 rounded-2xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
                Aucun quiz de ce niveau dans ce pôle.
              </p>
            ) : (
              <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {quiz.map((q) => (
                  <li
                    key={q.n}
                    className="group flex flex-col rounded-[1.5rem] border p-5 transition duration-300 hover:-translate-y-1 hover:border-(color:--c) hover:shadow-card"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-display text-lg text-(color:--c)">
                        Quiz {String(q.n).padStart(2, "0")}
                      </span>
                      <span className="flex items-center gap-1.5">
                        {q.reussi && (
                          <CheckCircle2
                            role="img"
                            aria-label="Déjà réussi"
                            className="size-4 text-primary"
                          />
                        )}
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase ${COULEURS[q.niveau]}`}
                        >
                          {niveauDe(q.niveau).nom}
                        </span>
                      </span>
                    </div>
                    <p className="mt-3 flex-1 font-extrabold leading-snug">{q.t}</p>
                    <p className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                      <Clock className="size-3.5" />{" "}
                      {catalogue
                        ? `${catalogue.nb_questions} QCM · ${catalogue.temps_ms / 1000} s par question`
                        : "QCM chronométrés"}
                    </p>
                    <div className="mt-4 flex items-center justify-between gap-3 border-t pt-4">
                      <span className="leading-tight">
                        <span className="block font-display text-xl text-sun [text-shadow:0_1px_0_var(--ink)]">
                          {points(niveauDe(q.niveau).eleve)} pts
                        </span>
                        <span className="block text-[11px] font-bold text-muted-foreground">
                          {points(niveauDe(q.niveau).eleve / 2)} pour ton club
                        </span>
                      </span>
                      {q.quiz ? (
                        <button
                          type="button"
                          onClick={() =>
                            q.quiz && setDefi({ titre: q.t, numero: q.n, quiz: q.quiz })
                          }
                          className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground transition group-hover:brightness-105"
                        >
                          Relever le défi <ArrowRight className="size-3.5" />
                        </button>
                      ) : (
                        // API injoignable : pas de bouton, sans annoncer à tort une nouveauté.
                        catalogue && (
                          <span className="rounded-full bg-mist-soft px-4 py-2 text-sm font-bold text-muted-foreground">
                            Bientôt
                          </span>
                        )
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      {/* Classement : vide tant que personne n'a joué, avec un podium en attente. */}
      <section className="bg-mist-soft py-20">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 lg:grid-cols-[1fr_1.1fr]">
          <EnTete sur="Émulation & classement" bleu="Le classement" vert="national">
            Les élèves sentinelles et les établissements les plus engagés y apparaîtront, avec leur
            pseudonyme et leur club, dès l’ouverture des quiz. Connecte-toi pour y inscrire ton nom
            !
          </EnTete>
          <div data-reveal="zoom" className="flex items-end justify-center gap-3 sm:gap-5">
            {[
              { r: 2, h: "h-36", c: "bg-[oklch(0.8_0.02_257)]", i: Medal },
              { r: 1, h: "h-52", c: "bg-sun", i: Crown },
              { r: 3, h: "h-28", c: "bg-tangerine", i: Medal },
            ].map((x) => (
              <div key={x.r} className="flex w-24 flex-col items-center sm:w-32">
                <span className="inline-flex size-16 items-center justify-center rounded-full bg-white font-display text-2xl text-muted-foreground shadow-card ring-4 ring-white">
                  ?
                </span>
                <div
                  className={`mt-3 flex w-full flex-col items-center justify-start rounded-t-2xl pt-4 text-ink shadow-card ${x.h} ${x.c}`}
                >
                  <x.i className="size-6" />
                  <span className="mt-1 font-display text-3xl">{x.r}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div
          data-reveal="zoom"
          className="relative isolate grid items-center gap-6 overflow-hidden rounded-[2rem] bg-sun p-8 md:p-12 lg:grid-cols-[1.3fr_1fr]"
        >
          <div>
            <p className="text-sm font-extrabold uppercase tracking-widest text-logo-red">
              Certification & récompenses
            </p>
            <h2 className="mt-3 text-4xl text-ink md:text-5xl">
              Gagne jusqu’à <span className="text-logo-blue">1 million FCFA</span> !
            </h2>
            <p className="mt-4 max-w-xl text-lg font-semibold text-ink/75">
              Relève le défi des 20 quiz santé, décroche ton certificat officiel Génie Imhotep et
              tes badges, et tente de remporter des lots exceptionnels.
            </p>
            <a
              href="/certification"
              className="btn-fx mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
            >
              Obtenir ma certification <ArrowRight className="size-4" />
            </a>
          </div>
          <img
            src={mascottesTrophees}
            alt=""
            loading="lazy"
            width={1122}
            height={1402}
            className="mx-auto -mb-16 w-56 drop-shadow-2xl md:-mb-20 md:w-72"
          />
        </div>
      </section>

      {catalogue && <DefiQuiz defi={defi} catalogue={catalogue} onFermer={() => setDefi(null)} />}

      <SiteFooter />
    </div>
  );
}

// La progression d'un élève connecté (spec 034) : quiz réussis, les 4 étoiles, les deux sous-totaux et la carte Gold.
function ProgressionJeux({
  progression,
}: {
  progression: NonNullable<CatalogueQuiz["progression"]>;
}) {
  return (
    <div className="mt-8 rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-border md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="font-display text-2xl text-logo-blue">
          {progression.quiz_reussis}{" "}
          <span className="text-base text-ink/70">/ {totalQuiz} quiz réussis</span>
        </p>
        {progression.gold && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-sun px-4 py-1.5 text-sm font-extrabold text-ink">
            <Crown className="size-4" /> Carte Gold
          </span>
        )}
      </div>
      <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {progression.niveaux.map((n, i) => (
          <li key={n.niveau} className="flex items-center gap-3 rounded-2xl bg-mist-soft p-4">
            <Star
              aria-hidden
              className={`size-8 shrink-0 ${n.etoile ? "fill-sun text-sun" : "text-ink/25"}`}
            />
            <span className="leading-tight">
              <span className="block text-sm font-extrabold">
                Étoile {i + 1} · {niveauDe(n.niveau).nom}
              </span>
              <span className="block text-xs font-semibold text-muted-foreground">
                {n.etoile ? "Débloquée" : `${n.reussis} / ${n.total} quiz réussis`}
              </span>
            </span>
          </li>
        ))}
      </ul>
      <dl className="mt-5 grid grid-cols-3 gap-3 text-center">
        {[
          { t: "Points des quiz", v: progression.points_quiz, max: MAX_POINTS_QUIZ },
          { t: "Points des étoiles", v: progression.points_etoiles, max: MAX_POINTS_ETOILES },
          { t: "Total Jeux", v: progression.total, max: MAX_POINTS_QUIZ + MAX_POINTS_ETOILES },
        ].map((x) => (
          <div key={x.t} className="rounded-2xl ring-1 ring-border p-3">
            <dt className="text-xs font-bold text-muted-foreground">{x.t}</dt>
            <dd className="font-display text-xl text-ink tabular-nums">
              {points(x.v).slice(1)}{" "}
              <span className="text-xs text-muted-foreground">/ {points(x.max).slice(1)}</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
