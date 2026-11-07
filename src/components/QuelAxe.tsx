import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascotteLeadership from "@/assets/mascotte-leadership.webp";
import mascotteMedias from "@/assets/mascotte-medias.webp";
import mascotteSecourisme from "@/assets/mascotte-secourisme.webp";
import { QuelAxeTest } from "@/components/QuelAxeTest";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

// Le paramètre ajouté à l'adresse de retour après la connexion : le test s'ouvre dès l'arrivée sur l'accueil.
export const PARAMETRE_TEST = "test";

const VALEURS = [
  "Une génération en bonne santé",
  "Des jeunes responsables",
  "Des talents qui s’expriment",
  "Des communautés qui agissent",
];

// Les trois cartes de la maquette : une mascotte officielle, la couleur de fond et la question de sa bulle.
const CARTES = [
  {
    img: mascotteMedias,
    nom: "Production TV & médias",
    bulle: "Créatif ?",
    fond: "from-sun to-tangerine",
    pente: "-rotate-6",
  },
  {
    img: mascotteSecourisme,
    nom: "Sport & secourisme",
    bulle: "Sportif ?",
    fond: "from-sky to-logo-blue",
    pente: "rotate-0 -translate-y-3",
  },
  {
    img: mascotteLeadership,
    nom: "Leadership & mentorat",
    bulle: "Leader ?",
    fond: "from-leaf to-[oklch(0.6_0.12_200)]",
    pente: "rotate-6",
  },
];

// « Quel axe est fait pour toi ? » (spec 021) : un bandeau pleine largeur d'après la maquette. La présentation
// reste visible de tous ; le test, réservé aux élèves connectés, s'ouvre dans une fenêtre. L'API vérifie le
// profil et calcule le résultat. Seules les mascottes officielles des axes sont utilisées.
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
      className="relative isolate w-full scroll-mt-16 overflow-hidden bg-white"
    >
      {/* Les valeurs du programme, en bandeau. */}
      <ul className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 border-b border-grape/10 px-5 py-3 text-sm font-bold text-ink/80">
        {VALEURS.map((v, i) => (
          <li key={v} className="flex items-center gap-6">
            {i > 0 && <span aria-hidden className="hidden h-4 w-px bg-ink/20 sm:block" />}
            {v}
          </li>
        ))}
      </ul>

      <div className="bg-linear-to-r from-lilac via-[oklch(0.97_0.02_300)] to-lilac">
        <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 py-10 md:py-12 lg:grid-cols-[auto_1fr_auto] lg:gap-10">
          {/* La mascotte Génie Imhotep, pensive, entourée de points d'interrogation. */}
          <div className="relative mx-auto w-36 sm:w-40 lg:w-44">
            <span
              aria-hidden
              className="absolute -left-3 top-0 font-display text-5xl text-sky drop-shadow-sm"
            >
              ?
            </span>
            <span
              aria-hidden
              className="absolute -right-2 top-10 font-display text-4xl text-logo-blue drop-shadow-sm"
            >
              ?
            </span>
            <img
              src={mascotteImhotep}
              alt="La mascotte de l’axe Génie Imhotep, qui réfléchit"
              width={1414}
              height={2000}
              loading="lazy"
              className="relative mt-6 h-56 w-auto drop-shadow-xl lg:h-60"
            />
          </div>

          <div className="text-center lg:text-left">
            <h2 className="font-display text-4xl leading-tight text-ink md:text-5xl">
              Quel{" "}
              <span className="text-grape underline decoration-grape decoration-4 underline-offset-[6px]">
                axe
              </span>{" "}
              est fait pour toi&#8239;?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-lg font-semibold text-ink/75 lg:mx-0">
              Réponds à cinq questions et découvre l’axe des Clubs Santé qui correspond le mieux à
              ta personnalité&#8239;!
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

          {/* Trois cartes inclinées, une mascotte officielle et sa question en bulle. */}
          <ul className="mx-auto flex items-end justify-center -space-x-4 sm:-space-x-2">
            {CARTES.map((c) => (
              <li key={c.bulle} className={`relative ${c.pente}`}>
                <div
                  className={`relative h-52 w-32 overflow-hidden rounded-[1.4rem] border-4 border-white bg-linear-to-br shadow-xl sm:h-60 sm:w-40 ${c.fond}`}
                >
                  <img
                    src={c.img}
                    alt={`La mascotte de l’axe ${c.nom}`}
                    width={1414}
                    height={2000}
                    loading="lazy"
                    className="absolute -bottom-6 left-1/2 h-[115%] w-auto max-w-none -translate-x-1/2 drop-shadow-lg"
                  />
                </div>
                <span className="absolute -top-4 right-1 rounded-2xl rounded-bl-sm bg-white px-3 py-1.5 font-display text-base text-ink shadow-card sm:-right-3 sm:text-lg">
                  {c.bulle}
                </span>
              </li>
            ))}
          </ul>
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
