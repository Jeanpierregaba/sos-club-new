import { useEffect, useState, type CSSProperties } from "react";
import { ArrowRight } from "lucide-react";

import { QuelAxeTest } from "@/components/QuelAxeTest";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { axes } from "@/lib/axes";

// Le paramètre ajouté à l'adresse de retour après la connexion : le test s'ouvre dès l'arrivée sur l'accueil.
export const PARAMETRE_TEST = "test";

const QUESTIONS = [
  "Plutôt créatif ?",
  "Passionné de sport ?",
  "Envie d’aider les autres ?",
  "Leader dans l’âme ?",
];

// « Quel axe est fait pour toi ? » (spec 021) : une bande pleine largeur, les sept mascottes officielles en
// rang, chacune sur la couleur de son axe. La présentation reste visible de tous ; le test, réservé aux élèves
// connectés, s'ouvre dans une fenêtre. L'API vérifie le profil et calcule le résultat.
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
    <section
      id="quel-axe"
      className="relative isolate w-full scroll-mt-16 overflow-hidden bg-linear-to-b from-lilac via-white to-mist pt-16 md:pt-20"
    >
      {/* Les sept couleurs des axes, en liseré. */}
      <div aria-hidden className="absolute inset-x-0 top-0 flex h-2">
        {axes.map((a) => (
          <span key={a.n} className="flex-1" style={{ background: a.couleur }} />
        ))}
      </div>
      {/* Des halos aux couleurs des axes, derrière le titre. */}
      <div
        aria-hidden
        className="absolute -left-24 top-10 -z-10 size-80 rounded-full bg-sky/15 blur-3xl"
      />
      <div
        aria-hidden
        className="absolute -right-24 top-24 -z-10 size-96 rounded-full bg-grape/15 blur-3xl"
      />

      <div data-reveal className="mx-auto max-w-4xl px-5 text-center">
        <p className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-sm font-extrabold uppercase tracking-widest text-grape shadow-card ring-1 ring-grape/15">
          Jeu de découverte · 5 questions
        </p>
        <h2 className="mt-5 font-display text-4xl uppercase leading-[0.95] md:text-6xl">
          <span className="text-grape">Quel axe</span>{" "}
          <span className="text-tangerine">est fait pour toi&#8239;?</span>
        </h2>
        <p className="mx-auto mt-5 max-w-2xl text-lg font-semibold text-ink/80">
          7 axes, des talents à révéler. Réponds à cinq questions et découvre l’axe des Clubs Santé
          qui correspond le mieux à tes envies&#8239;!
        </p>
        <ul aria-hidden className="mt-6 flex flex-wrap justify-center gap-2">
          {QUESTIONS.map((q) => (
            <li
              key={q}
              className="rounded-full bg-white px-4 py-2 text-sm font-bold text-ink shadow-card ring-1 ring-border"
            >
              {q}
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => setOuvert(true)}
          className="btn-fx mt-8 inline-flex items-center gap-2 rounded-full bg-grape px-9 py-4 text-lg font-bold text-white shadow-lg shadow-grape/30"
        >
          Commencer le test <ArrowRight className="size-5" />
        </button>
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          Réservé aux élèves inscrits · aucun point en jeu
        </p>
      </div>

      {/* Le rang des sept mascottes officielles, posé sur le bas de la section. */}
      <ul className="mx-auto mt-12 flex max-w-7xl flex-wrap items-end justify-center gap-y-6 px-3 md:mt-16">
        {axes.map((a, i) => (
          <li
            key={a.n}
            style={{ "--axe": a.couleur } as CSSProperties}
            className={`group relative flex w-1/4 flex-col items-center sm:w-1/7 ${i === 3 ? "z-10" : ""}`}
          >
            <span
              aria-hidden
              className="absolute bottom-6 left-1/2 aspect-square w-[85%] -translate-x-1/2 rounded-full bg-(color:--axe) opacity-90 transition duration-300 group-hover:scale-105"
            />
            <img
              src={a.img}
              alt={`La mascotte de l’axe ${a.nom}`}
              width={1414}
              height={2000}
              loading="lazy"
              className={`relative w-auto drop-shadow-xl transition duration-300 group-hover:-translate-y-2 ${
                i === 3
                  ? "h-44 sm:h-56 lg:h-72"
                  : i % 2
                    ? "h-36 sm:h-44 lg:h-60"
                    : "h-40 sm:h-52 lg:h-64"
              }`}
            />
            <span
              className={`relative -mt-2 rounded-full bg-(color:--axe) px-3 py-1 text-[11px] font-extrabold uppercase tracking-wide shadow-md sm:text-xs ${a.encre}`}
            >
              Axe {a.n}
            </span>
          </li>
        ))}
      </ul>
      <div aria-hidden className="h-10 bg-linear-to-b from-transparent to-mist" />

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
