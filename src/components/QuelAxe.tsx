import { type CSSProperties, useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import mascotteEnvironnement from "@/assets/mascotte-environnement.webp";
import mascotteLeadership from "@/assets/mascotte-leadership.webp";
import mascotteMedias from "@/assets/mascotte-medias.webp";
import mascotteSecourisme from "@/assets/mascotte-secourisme.webp";
import { QuelAxeTest } from "@/components/QuelAxeTest";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { axes } from "@/lib/axes";

// Le paramètre ajouté à l'adresse de retour après la connexion : le test s'ouvre dès l'arrivée sur l'accueil.
export const PARAMETRE_TEST = "test";

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

const delai = (s: number) => ({ animationDelay: `${s}s` }) as CSSProperties;

// Fond immersif : taches de couleur qui dérivent, trame de points qui glisse, points d'interrogation et croix
// « santé » qui flottent. Purement décoratif, figé si l'utilisateur réduit les animations.
function DecorQuelAxe() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <span className="absolute -left-24 -top-24 size-80 rounded-full bg-sky/25 blur-3xl motion-safe:animate-derive" />
      <span
        style={delai(-6)}
        className="absolute -right-20 top-1/4 size-96 rounded-full bg-grape/20 blur-3xl motion-safe:animate-derive"
      />
      <span
        style={delai(-3)}
        className="absolute bottom-0 left-1/3 size-72 rounded-full bg-sun/30 blur-3xl motion-safe:animate-respire"
      />
      <span className="absolute inset-0 bg-[radial-gradient(circle,oklch(0.45_0.24_295/0.12)_1.5px,transparent_1.5px)] bg-size-[22px_22px] mask-[linear-gradient(to_bottom,black,transparent_85%)] motion-safe:animate-defile-motif" />
      {[
        "left-[30%] top-[10%] text-3xl text-grape/30",
        "right-[36%] top-[14%] text-4xl text-sky/40",
        "left-[8%] bottom-[22%] text-2xl text-logo-red/30",
        "right-[6%] bottom-[30%] text-5xl text-grape/20",
        "left-[52%] bottom-[18%] text-2xl text-tangerine/40",
      ].map((position, i) => (
        <span
          key={position}
          style={delai(-i * 2.3)}
          className={`absolute hidden font-display md:block motion-safe:animate-flotte-tourne ${position}`}
        >
          ?
        </span>
      ))}
      {["left-[22%] top-[38%] text-leaf/50", "right-[24%] bottom-[40%] text-logo-red/40"].map(
        (position, i) => (
          <svg
            key={position}
            viewBox="0 0 24 24"
            style={delai(-i * 1.7)}
            className={`absolute size-5 motion-safe:animate-scintille ${position}`}
          >
            <path
              d="M12 3v18M3 12h18"
              stroke="currentColor"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
          </svg>
        ),
      )}
    </div>
  );
}

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
      className="relative isolate w-full scroll-mt-16 overflow-hidden bg-linear-to-br from-lilac via-[oklch(0.97_0.02_300)] to-mist"
    >
      <DecorQuelAxe />

      <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)] items-center gap-10 px-5 pb-10 pt-14 md:grid-cols-[auto_1fr] md:pt-16 lg:gap-12 xl:grid-cols-[auto_1fr_auto]">
        {/* La mascotte Santé & environnement flotte devant un halo pointillé, entourée de points d'interrogation. */}
        <div data-reveal="left" className="relative mx-auto w-48 sm:w-52 lg:w-60">
          <svg
            aria-hidden
            viewBox="0 0 100 100"
            className="absolute left-1/2 top-1/2 size-64 -translate-x-1/2 -translate-y-1/2 text-grape/25 motion-safe:animate-[spin_40s_linear_infinite] lg:size-72"
          >
            <circle
              cx="50"
              cy="50"
              r="46"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeDasharray="4 7"
              strokeLinecap="round"
            />
          </svg>
          <span
            aria-hidden
            className="absolute left-1/2 top-1/2 size-48 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/70 blur-2xl lg:size-56"
          />
          <span
            aria-hidden
            className="absolute -left-4 top-0 font-display text-6xl text-sky drop-shadow-sm motion-safe:animate-flotte-tourne"
          >
            ?
          </span>
          <span
            aria-hidden
            style={delai(-4)}
            className="absolute -right-3 top-12 font-display text-5xl text-logo-blue drop-shadow-sm motion-safe:animate-flotte-tourne"
          >
            ?
          </span>
          <span
            aria-hidden
            style={delai(-2)}
            className="absolute -left-1 bottom-10 font-display text-3xl text-grape/70 motion-safe:animate-scintille"
          >
            ?
          </span>
          <img
            src={mascotteEnvironnement}
            alt="La mascotte de l’axe Santé & environnement"
            width={1414}
            height={2000}
            loading="lazy"
            className="relative mx-auto mt-4 h-64 w-auto drop-shadow-xl motion-safe:animate-float lg:h-80"
          />
        </div>

        <div data-reveal className="text-center md:text-left">
          <p className="font-hand text-2xl text-logo-red">Fais le test&#8239;!</p>
          <h2 className="mt-1 font-display text-4xl leading-tight text-ink md:text-5xl xl:text-6xl">
            Quel{" "}
            <span className="relative inline-block text-grape">
              axe
              <svg
                aria-hidden
                viewBox="0 0 120 14"
                preserveAspectRatio="none"
                className="absolute -bottom-2 left-0 h-3 w-full text-grape"
              >
                <path
                  d="M3 9 C 30 2, 60 13, 117 5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="5"
                  strokeLinecap="round"
                  pathLength={1}
                  className="trait-axe"
                />
              </svg>
            </span>{" "}
            est fait pour toi&#8239;?
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-lg font-semibold text-ink/75 md:mx-0">
            Réponds à cinq questions et découvre l’axe des Clubs Santé qui correspond le mieux à ta
            personnalité&#8239;!
          </p>
          <div className="relative mt-8 inline-flex">
            <span
              aria-hidden
              className="absolute inset-0 rounded-full bg-grape/40 motion-safe:animate-halo"
            />
            <button
              type="button"
              onClick={() => setOuvert(true)}
              className="btn-fx group relative inline-flex items-center gap-2 rounded-full bg-grape px-8 py-4 text-base font-bold text-white shadow-lg shadow-grape/30"
            >
              Commencer le test{" "}
              <ArrowRight className="size-5 transition-transform group-hover:translate-x-1" />
            </button>
          </div>
          <p className="mt-3 text-sm font-medium text-muted-foreground">
            Réservé aux élèves inscrits · aucun point en jeu
          </p>
        </div>

        {/* Trois cartes inclinées qui flottent chacune à son rythme ; au survol, la carte se redresse. */}
        <ul
          data-reveal="right"
          className="mx-auto flex items-end justify-center -space-x-4 pt-4 sm:-space-x-2 md:col-span-2 xl:col-span-1"
        >
          {CARTES.map((c, i) => (
            <li
              key={c.bulle}
              className={`group relative transition-[rotate,translate,scale] duration-300 hover:z-10 hover:-translate-y-4 hover:rotate-0 hover:scale-105 ${c.pente}`}
            >
              <div style={delai(-i * 1.6)} className="motion-safe:animate-float">
                <div
                  className={`relative h-48 w-30 overflow-hidden rounded-[1.4rem] border-4 border-white bg-linear-to-br shadow-xl sm:h-64 sm:w-42 ${c.fond}`}
                >
                  <span
                    aria-hidden
                    className="absolute inset-0 bg-[radial-gradient(circle,white_1.5px,transparent_1.5px)] bg-size-[14px_14px] opacity-25"
                  />
                  <img
                    src={c.img}
                    alt={`La mascotte de l’axe ${c.nom}`}
                    width={1414}
                    height={2000}
                    loading="lazy"
                    className="absolute -bottom-6 left-1/2 h-[115%] w-auto max-w-none -translate-x-1/2 drop-shadow-lg transition-transform duration-300 group-hover:scale-105"
                  />
                </div>
                <span
                  style={delai(i * 1.5)}
                  className="absolute -top-4 right-1 origin-bottom-left rounded-2xl rounded-bl-sm bg-white px-3 py-1.5 font-display text-base text-ink shadow-card motion-safe:animate-bulle sm:-right-3 sm:text-lg"
                >
                  {c.bulle}
                </span>
              </div>
            </li>
          ))}
        </ul>
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

// Les 7 axes qui défilent, en bande pleine largeur (placée après « Et si ton lycée devenait N°1 du Togo ? »).
export function BandeAxes() {
  return (
    <div className="group/axes relative w-full overflow-hidden border-y border-white/70 bg-linear-to-r from-lilac via-[oklch(0.97_0.02_300)] to-mist py-4">
      <div className="flex w-max motion-safe:animate-marquee group-hover/axes:[animation-play-state:paused]">
        {[0, 1].map((copie) => (
          <ul
            key={copie}
            aria-label={copie === 0 ? "Les 7 axes des Clubs Santé" : undefined}
            aria-hidden={copie === 1 || undefined}
            className="flex shrink-0 gap-3 pr-3"
          >
            {[...axes, ...axes].map((a, j) => (
              <li
                key={`${a.n}-${j}`}
                aria-hidden={j >= axes.length || undefined}
                className={`flex items-center gap-2 rounded-full py-1 pl-1 pr-4 text-sm font-bold shadow-sm ${a.encre}`}
                style={{ background: a.couleur }}
              >
                <img
                  src={a.img}
                  alt=""
                  width={1414}
                  height={2000}
                  loading="lazy"
                  className="size-8 rounded-full bg-white/90 object-cover object-top"
                />
                {a.nom}
              </li>
            ))}
          </ul>
        ))}
      </div>
    </div>
  );
}
