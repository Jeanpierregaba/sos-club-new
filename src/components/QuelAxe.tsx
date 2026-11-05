import { useState, type CSSProperties } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  Brain,
  Clapperboard,
  Compass,
  Dumbbell,
  HandHeart,
  HeartPulse,
  Leaf,
  Lightbulb,
  Megaphone,
  MessageCircleHeart,
  Mountain,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Sprout,
  Trophy,
  type LucideIcon,
} from "lucide-react";
import { axes, type NumeroAxe } from "@/lib/axes";

// « Quel axe est fait pour toi ? » : 4 questions, une réponse par question, chaque réponse vaut un axe.
// L'axe le plus choisi l'emporte ; à égalité, celui de la réponse la plus récente. Un jeu de découverte :
// rien n'est envoyé à l'API et aucun point n'est gagné.
type Reponse = { t: string; axe: NumeroAxe; i: LucideIcon };

const questions: { q: string; reponses: Reponse[] }[] = [
  {
    q: "Un samedi libre, tu préfères…",
    reponses: [
      { t: "Relever des défis de culture générale", axe: 1, i: Brain },
      { t: "Filmer, monter ou animer une émission", axe: 3, i: Clapperboard },
      { t: "Bouger : match, course ou entraînement", axe: 4, i: Dumbbell },
      { t: "Jardiner ou embellir ton quartier", axe: 7, i: Sprout },
    ],
  },
  {
    q: "Dans ton groupe d’amis, tu es celui ou celle qui…",
    reponses: [
      { t: "Prend les choses en main et organise", axe: 6, i: Compass },
      { t: "Écoute et donne de bons conseils", axe: 2, i: MessageCircleHeart },
      { t: "Vise toujours la meilleure note", axe: 5, i: Award },
      { t: "Garde son sang-froid quand quelqu’un se blesse", axe: 4, i: HeartPulse },
    ],
  },
  {
    q: "Ce qui te rend le plus fier, c’est…",
    reponses: [
      { t: "Apprendre quelque chose de nouveau sur la santé", axe: 1, i: Lightbulb },
      { t: "Aider un ami à mieux connaître son corps et ses droits", axe: 2, i: ShieldCheck },
      { t: "Recevoir un prix pour tes efforts", axe: 5, i: Trophy },
      { t: "Voir ton école plus propre et plus verte", axe: 7, i: Leaf },
    ],
  },
  {
    q: "Ton super-pouvoir, c’est…",
    reponses: [
      { t: "La créativité", axe: 3, i: Sparkles },
      { t: "Le leadership", axe: 6, i: Megaphone },
      { t: "L’empathie", axe: 2, i: HandHeart },
      { t: "La persévérance", axe: 5, i: Mountain },
    ],
  },
];

function axeGagnant(choix: NumeroAxe[]) {
  const votes = new Map<NumeroAxe, number>();
  for (const a of choix) votes.set(a, (votes.get(a) ?? 0) + 1);
  const max = Math.max(...votes.values());
  // À égalité : la réponse la plus récente départage.
  const n = [...choix].reverse().find((a) => votes.get(a) === max)!;
  return axes.find((a) => a.n === n)!;
}

export function QuelAxe() {
  const [choix, setChoix] = useState<NumeroAxe[]>([]);
  const etape = choix.length;
  const fini = etape === questions.length;
  const question = questions[etape];
  const resultat = fini ? axeGagnant(choix) : null;

  return (
    <section
      id="quel-axe"
      className="relative isolate scroll-mt-16 overflow-hidden bg-linear-to-br from-mist to-lilac py-20"
    >
      <div
        aria-hidden
        className="absolute -right-24 -top-24 -z-10 size-96 rounded-full border-[3rem] border-white/60 motion-safe:animate-respire"
      />
      <div className="mx-auto max-w-5xl px-5">
        <div data-reveal className="text-center">
          <p className="text-sm font-extrabold uppercase tracking-widest text-logo-red">
            Mini-test · 30 secondes
          </p>
          <h2 className="mt-3 text-4xl md:text-5xl">
            <span className="text-logo-blue">Quel axe est</span>{" "}
            <span className="text-primary">fait pour toi ?</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-lg font-medium text-muted-foreground">
            Réponds à 4 questions et découvre l’axe, et la mascotte, qui te ressemblent le plus.
          </p>
        </div>

        <div
          data-reveal="zoom"
          className="mt-10 overflow-hidden rounded-[2rem] bg-white shadow-card ring-1 ring-border"
        >
          {/* La progression : un segment par question. */}
          <div aria-hidden className="flex gap-1.5 px-6 pt-6 md:px-10 md:pt-8">
            {questions.map((q, i) => (
              <span
                key={q.q}
                className={`h-2 flex-1 rounded-full transition-colors duration-500 ${i < etape ? "bg-primary" : "bg-mist"}`}
              />
            ))}
          </div>

          {question && (
            <div key={etape} className="p-6 animate-in fade-in slide-in-from-right-4 md:p-10">
              <p className="text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
                Question {etape + 1} sur {questions.length}
              </p>
              <p className="mt-2 font-display text-3xl leading-tight text-logo-blue md:text-4xl">
                {question.q}
              </p>
              <ul className="mt-6 grid gap-3 sm:grid-cols-2">
                {question.reponses.map((r) => (
                  <li key={r.t}>
                    <button
                      type="button"
                      onClick={() => setChoix((c) => [...c, r.axe])}
                      className="group flex h-full w-full items-center gap-4 rounded-2xl border-2 border-border bg-white p-4 text-left font-bold transition duration-200 hover:-translate-y-0.5 hover:border-primary hover:shadow-card active:scale-[0.98]"
                    >
                      <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-xl bg-mist text-logo-blue transition group-hover:bg-primary group-hover:text-primary-foreground">
                        <r.i className="size-6" />
                      </span>
                      {r.t}
                    </button>
                  </li>
                ))}
              </ul>
              {etape > 0 && (
                <button
                  type="button"
                  onClick={() => setChoix((c) => c.slice(0, -1))}
                  className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-muted-foreground transition hover:text-logo-blue"
                >
                  <ArrowLeft className="size-4" /> Question précédente
                </button>
              )}
            </div>
          )}

          {resultat && (
            <div
              role="status"
              style={{ "--axe": resultat.couleur } as CSSProperties}
              className="grid items-center gap-6 p-6 animate-in fade-in zoom-in-95 md:grid-cols-[auto_1fr] md:gap-10 md:p-10"
            >
              <div className="relative mx-auto">
                <span
                  aria-hidden
                  className="absolute inset-x-2 bottom-2 top-10 -z-0 rounded-[2rem] bg-(color:--axe) rotate-3"
                />
                <img
                  src={resultat.img}
                  alt={`La mascotte de l’axe ${resultat.n}`}
                  width={1414}
                  height={2000}
                  className="relative h-64 w-auto drop-shadow-2xl motion-safe:animate-float md:h-72"
                />
              </div>
              <div>
                <p className="text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
                  Ton axe, c’est…
                </p>
                <p
                  className={`mt-3 inline-flex rounded-full bg-(color:--axe) px-4 py-1.5 text-sm font-extrabold uppercase ${resultat.encre}`}
                >
                  Axe {resultat.n}
                </p>
                <p className="mt-3 font-display text-4xl leading-tight text-logo-blue md:text-5xl">
                  {resultat.nom}
                </p>
                <p className="mt-3 font-hand text-2xl text-ink">« {resultat.slogan} »</p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <a
                    href={`/les-7-axes#axe-${resultat.n}`}
                    className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
                  >
                    Découvrir cet axe <ArrowRight className="size-4" />
                  </a>
                  <button
                    type="button"
                    onClick={() => setChoix([])}
                    className="btn-fx inline-flex items-center gap-2 rounded-full border-2 border-logo-blue px-7 py-3 text-[15px] font-bold text-logo-blue hover:bg-logo-blue hover:text-white"
                  >
                    <RotateCcw className="size-4" /> Recommencer
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
