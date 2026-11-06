import { useEffect, useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";

import mascotteArcEnCiel from "@/assets/mascot.png";
import mascottesAxes from "@/assets/mascottes-axes.webp";
import { QuelAxeTest } from "@/components/QuelAxeTest";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

// Le paramètre ajouté à l'adresse de retour après la connexion : le test s'ouvre dès l'arrivée sur l'accueil.
export const PARAMETRE_TEST = "test";

const BULLES = [
  "Plutôt créatif ?",
  "Passionné de sport ?",
  "Envie d’aider les autres ?",
  "Leader dans l’âme ?",
];

// « Quel axe est fait pour toi ? » (spec 021) : la présentation reste visible de tous ; le test, réservé aux
// élèves connectés, s'ouvre dans une fenêtre. L'API vérifie le profil et calcule le résultat.
export function QuelAxe() {
  const [ouvert, setOuvert] = useState(false);

  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.get(PARAMETRE_TEST) !== "quel-axe") return;
    url.searchParams.delete(PARAMETRE_TEST);
    window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    setOuvert(true);
  }, []);

  return (
    <section id="quel-axe" className="relative isolate scroll-mt-16 overflow-hidden py-16 md:py-20">
      <div className="mx-auto max-w-6xl px-5">
        <div
          data-reveal="zoom"
          className="relative overflow-hidden rounded-[2rem] bg-linear-to-br from-lilac via-white to-lilac px-6 py-10 shadow-card ring-1 ring-grape/10 md:px-10 lg:py-12"
        >
          {/* Les petits dessins de la maquette : couronne, éclair, étincelles. */}
          <Gribouillis />

          <div className="relative grid items-center gap-8 lg:grid-cols-[auto_1fr_auto] lg:gap-10">
            <div className="relative mx-auto w-40 sm:w-48 lg:w-52">
              <span
                aria-hidden
                className="absolute -left-2 top-2 font-display text-5xl text-sky motion-safe:animate-float"
              >
                ?
              </span>
              <span
                aria-hidden
                className="absolute -right-1 top-12 font-display text-4xl text-logo-blue motion-safe:animate-float [animation-delay:-2s]"
              >
                ?
              </span>
              <img
                src={mascotteArcEnCiel}
                alt="Le caméléon des Clubs Santé, qui change de couleur selon les axes"
                width={1024}
                height={1024}
                loading="lazy"
                className="relative mt-8 w-full drop-shadow-xl"
              />
            </div>

            <div className="text-center lg:text-left">
              <h2 className="font-display text-4xl uppercase leading-[0.95] md:text-5xl lg:text-6xl">
                <span className="block text-grape">Quel axe</span>
                <span className="block text-tangerine">est fait pour toi&#8239;?</span>
              </h2>
              <p className="mx-auto mt-5 max-w-xl text-lg font-semibold text-ink/80 lg:mx-0">
                Réponds à cinq questions et découvre l’axe des Clubs Santé qui correspond le mieux à
                tes envies&#8239;!
              </p>
              <button
                type="button"
                onClick={() => setOuvert(true)}
                className="btn-fx mt-7 inline-flex items-center gap-2 rounded-full bg-grape px-8 py-4 text-base font-bold text-white shadow-lg shadow-grape/30"
              >
                Commencer le test <ArrowRight className="size-5" />
              </button>
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                Réservé aux élèves inscrits · aucun point en jeu
              </p>
            </div>

            <Telephone />
          </div>
        </div>
      </div>

      <Dialog open={ouvert} onOpenChange={setOuvert}>
        <DialogContent className="max-h-[100dvh] w-full max-w-2xl overflow-y-auto rounded-none p-0 sm:max-h-[92dvh] sm:rounded-[2rem]">
          <DialogTitle className="sr-only">Quel axe est fait pour toi ?</DialogTitle>
          <DialogDescription className="sr-only">
            Cinq questions pour découvrir l’axe des Clubs Santé qui te ressemble.
          </DialogDescription>
          {ouvert && <QuelAxeTest />}
        </DialogContent>
      </Dialog>
    </section>
  );
}

// Le téléphone de la maquette, avec les mascottes des axes et les questions en bulles.
function Telephone() {
  return (
    <div className="relative mx-auto w-full max-w-sm lg:w-80">
      <p
        aria-hidden
        className="absolute -top-2 right-0 z-10 -rotate-6 font-hand text-2xl text-grape lg:-right-4"
      >
        Découvre ton axe&#8239;!
      </p>
      <div className="relative ml-2 mt-8 w-52 rotate-[-4deg] rounded-[2.2rem] border-[6px] border-white bg-linear-to-br from-sun via-tangerine to-grape p-2 shadow-2xl sm:w-56">
        <span aria-hidden className="mx-auto mb-1 block h-1.5 w-12 rounded-full bg-white/70" />
        <img
          src={mascottesAxes}
          alt=""
          width={1122}
          height={1402}
          loading="lazy"
          className="w-full rounded-[1.6rem] bg-white/25 drop-shadow-lg"
        />
      </div>
      <ul aria-hidden className="absolute -right-1 top-24 space-y-2.5 sm:right-2 lg:-right-8">
        {BULLES.map((b, i) => (
          <li
            key={b}
            style={{ animationDelay: `${i * -1.2}s` }}
            className="rounded-full bg-white px-4 py-2 text-sm font-bold text-ink shadow-card motion-safe:animate-float"
          >
            {b}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Gribouillis() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      <Sparkles className="absolute left-[34%] top-8 size-7 text-sun motion-safe:animate-scintille" />
      <svg
        viewBox="0 0 40 40"
        className="absolute bottom-8 left-[24%] size-9 text-grape/60 motion-safe:animate-flotte-tourne"
      >
        <circle cx="20" cy="20" r="9" fill="none" stroke="currentColor" strokeWidth="3" />
        <path d="M20 4v6M20 30v6M4 20h6M30 20h6" stroke="currentColor" strokeWidth="3" />
      </svg>
      <svg
        viewBox="0 0 40 40"
        className="absolute right-[34%] top-10 hidden size-9 text-rose/70 motion-safe:animate-scintille lg:block"
      >
        <path
          d="M6 30 10 12l8 10 4-14 4 14 8-10 4 18Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
