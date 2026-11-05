import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  BookOpen,
  CirclePlay,
  Download,
  GraduationCap,
  Image as ImageIcon,
  type LucideIcon,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import mascottesLivres from "@/assets/mascottes-livres.webp";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";

export const Route = createFileRoute("/bibliotheque")({
  head: () => ({
    meta: [
      { title: "Bibliothèque — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Fascicules, guides d'action, affiches, modules et vidéos pour animer ton Club Santé SOS Docteur TV, en libre accès.",
      },
      { property: "og:title", content: "La bibliothèque des Clubs Santé" },
    ],
  }),
  component: Bibliotheque,
});

type Genre = "guide" | "affiche" | "video" | "module";

// `c` : la couleur de la couverture du document.
const genres: Record<Genre, { t: string; un: string; i: LucideIcon; c: string }> = {
  guide: { t: "Guides d’action", un: "Guide d’action", i: BookOpen, c: "bg-logo-blue" },
  affiche: { t: "Affiches", un: "Affiche", i: ImageIcon, c: "bg-rose" },
  video: { t: "Vidéos SOS", un: "Vidéo SOS", i: CirclePlay, c: "bg-grape" },
  module: { t: "Modules", un: "Module", i: GraduationCap, c: "bg-primary" },
};

// Documents et compteurs repris de la bibliothèque du site de référence fourni par le porteur du projet (clubsante.ibdastudio.com).
// Les fichiers ne sont pas encore en ligne : les liens de téléchargement pointent vers « # ».
const documents: { genre: Genre; t: string; taille: string; telechargements: number }[] = [
  {
    genre: "guide",
    t: "Guide méthodologique de gestion d’un Club Santé scolaire",
    taille: "4,2 Mo",
    telechargements: 145,
  },
  {
    genre: "affiche",
    t: "Affiche de sensibilisation : les 10 étapes du lavage des mains",
    taille: "1,8 Mo",
    telechargements: 320,
  },
  {
    genre: "module",
    t: "Module de formation animée : prévention du paludisme en milieu scolaire",
    taille: "12,5 Mo",
    telechargements: 98,
  },
  {
    genre: "video",
    t: "Vidéo : gestes de premiers secours face à un évanouissement",
    taille: "24,1 Mo",
    telechargements: 215,
  },
];

const chiffres = [
  { n: "4+", t: "Documents" },
  { n: "1", t: "Fiche pratique" },
  { n: "2", t: "Supports médias" },
  { n: "778", t: "Téléchargements" },
];

function Bibliotheque() {
  const [genre, setGenre] = useState<Genre | null>(null);
  const affiches = documents.filter((d) => !genre || d.genre === genre);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : un fond soleil, le titre à gauche et les mascottes plongées dans leurs livres à droite. */}
      <section className="relative isolate overflow-hidden bg-[color-mix(in_oklch,var(--sun)_24%,white)]">
        <div
          aria-hidden
          className="absolute -right-24 top-1/2 -z-10 size-[34rem] -translate-y-1/2 rounded-full bg-sun/40 motion-safe:animate-respire"
        />
        <div
          aria-hidden
          className="absolute -right-10 top-1/2 -z-10 size-[44rem] -translate-y-1/2 rounded-full border-2 border-dashed border-tangerine/30 motion-safe:animate-[spin_70s_linear_infinite]"
        />
        <DecorAnime ton="clair" />
        <div className="mx-auto grid max-w-7xl items-end gap-8 px-5 pt-8 md:pt-12 lg:grid-cols-[1.2fr_1fr]">
          <div className="pb-14 lg:pb-24">
            <FilAriane rubrique="Vie du club" page="Bibliothèque" />
            <div data-reveal="left" className="pt-12 lg:pt-16">
              <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
                <span className="h-1 w-8 rounded-full bg-primary" />
                AIMES-AFRIQUE · SOS Docteur TV
              </p>
              <h1 className="mt-4 text-5xl leading-[0.95] md:text-7xl">
                <span className="block text-logo-blue">La bibliothèque</span>
                <span className="block text-primary">des Clubs Santé</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-ink/75">
                Accède librement aux fascicules, outils, affiches et guides pratiques pour bien
                animer ton Club Santé SOS Docteur TV.
              </p>
              <dl className="mt-8 grid max-w-xl grid-cols-2 gap-3 sm:grid-cols-4">
                {chiffres.map((c) => (
                  <div
                    key={c.t}
                    className="flex flex-col-reverse rounded-2xl bg-white/80 p-4 shadow-sm backdrop-blur"
                  >
                    <dt className="mt-1.5 text-xs font-bold text-muted-foreground">{c.t}</dt>
                    <dd className="font-display text-3xl leading-none text-logo-blue">{c.n}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
          <img
            src={mascottesLivres}
            alt="Les mascottes du Club Santé, livres en main"
            width={1122}
            height={1402}
            data-reveal="right"
            className="mx-auto w-3/4 max-w-md self-end drop-shadow-2xl lg:w-full"
          />
        </div>
      </section>

      {/* Rayonnages : un filtre par type, puis les documents en couvertures colorées. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete sur="Ressources en libre accès" bleu="Tous les" vert="documents">
            Guides, affiches, modules et vidéos validés par l’équipe nationale.
          </EnTete>
          <div data-reveal className="flex flex-wrap gap-2">
            {([null, ...Object.keys(genres)] as (Genre | null)[]).map((g) => (
              <button
                key={g ?? "tous"}
                type="button"
                aria-pressed={genre === g}
                onClick={() => setGenre(g)}
                className={`rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                  genre === g
                    ? "bg-logo-blue text-white shadow-card"
                    : "bg-white text-ink ring-1 ring-border hover:ring-logo-blue/40"
                }`}
              >
                {g ? genres[g].t : "Tous les documents"}
              </button>
            ))}
          </div>
        </div>

        <ul className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {affiches.map((d, i) => {
            const g = genres[d.genre];
            return (
              <li
                key={d.t}
                data-reveal
                style={retard(i)}
                className="card-fx group flex flex-col overflow-hidden rounded-[1.75rem] bg-white shadow-card"
              >
                <div
                  className={`relative isolate flex aspect-[4/3] items-center justify-center overflow-hidden ${g.c} text-white`}
                >
                  <span aria-hidden className="absolute inset-y-0 left-5 -z-10 w-3 bg-black/15" />
                  <span
                    aria-hidden
                    className="absolute -bottom-10 -right-10 -z-10 size-40 rounded-full bg-white/10"
                  />
                  <g.i className="size-16 transition duration-300 group-hover:scale-110" />
                  <span className="absolute right-4 top-4 rounded-full bg-white/20 px-3 py-1 text-xs font-extrabold">
                    {d.taille}
                  </span>
                </div>
                <div className="flex flex-1 flex-col p-6">
                  <p className="text-xs font-extrabold uppercase tracking-wider text-logo-red">
                    {g.un}
                  </p>
                  <h3 className="mt-2 flex-1 font-sans text-lg font-extrabold leading-snug">
                    {d.t}
                  </h3>
                  <div className="mt-5 flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-muted-foreground">
                      {d.telechargements} téléchargements
                    </span>
                    <a
                      href="#"
                      aria-label={`Télécharger : ${d.t}`}
                      className="btn-fx inline-flex size-11 items-center justify-center rounded-full bg-primary text-primary-foreground"
                    >
                      <Download className="size-5" />
                    </a>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      {/* Passerelle vers la certification : les fascicules servent à réviser les 12 quiz. */}
      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div
          data-reveal="zoom"
          className="relative isolate grid items-center gap-8 overflow-hidden rounded-[2rem] bg-linear-to-br from-logo-blue to-night p-8 text-white shadow-card md:p-12 lg:grid-cols-[1fr_auto]"
        >
          <div
            aria-hidden
            className="absolute inset-0 -z-10 bg-[radial-gradient(oklch(1_0_0/0.12)_1.5px,transparent_1.5px)] bg-size-[22px_22px]"
          />
          <div>
            <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
              Réviser avant de jouer
            </p>
            <h2 className="mt-3 text-4xl md:text-5xl">
              Prépare ta <span className="text-primary">certification</span>
            </h2>
            <p className="mt-4 max-w-2xl text-lg font-medium text-white/80">
              Avant de passer les quiz, consulte et télécharge gratuitement les fascicules
              pédagogiques : apprends, révise, puis lance-toi dans les 12 quiz du parcours.
            </p>
            <a
              href="/certification"
              className="btn-fx mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
            >
              Découvrir la certification <ArrowRight className="size-4" />
            </a>
          </div>
          <img
            src={mascotteImhotep}
            alt=""
            loading="lazy"
            width={1414}
            height={2000}
            className="mx-auto -mb-12 w-40 drop-shadow-2xl md:-mb-14 lg:w-52"
          />
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
