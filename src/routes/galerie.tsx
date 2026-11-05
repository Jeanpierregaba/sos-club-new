import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, Expand, X } from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import { axes, photos, type NumeroAxe } from "@/lib/galerie";

export const Route = createFileRoute("/galerie")({
  head: () => ({
    meta: [
      { title: "Galerie — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Les Clubs Santé en images, classées par axe d’intervention : Génie Imhotep, secourisme, médias, environnement et sensibilisation.",
      },
      { property: "og:title", content: "La galerie des Clubs Santé" },
    ],
  }),
  component: Galerie,
});

// Trois photos posées en éventail dans la bannière.
const collage = [
  { p: photos[1], c: "-rotate-6 left-0 top-6" },
  { p: photos[6], c: "rotate-3 left-[22%] top-0 z-10" },
  { p: photos[2], c: "rotate-6 right-0 top-10" },
];

function Galerie() {
  const [axe, setAxe] = useState<NumeroAxe | null>(null);
  const [ouverte, setOuverte] = useState<number | null>(null);
  const liste = photos.filter((p) => !axe || p.axe === axe);
  const photo = ouverte === null ? undefined : liste[ouverte];
  const aller = (pas: number) =>
    setOuverte((i) => (i === null ? i : (i + pas + liste.length) % liste.length));

  // Visionneuse : Échap ferme, les flèches du clavier passent d'une photo à l'autre.
  useEffect(() => {
    if (ouverte === null) return;
    const touche = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOuverte(null);
      if (e.key === "ArrowRight") aller(1);
      if (e.key === "ArrowLeft") aller(-1);
    };
    window.addEventListener("keydown", touche);
    return () => window.removeEventListener("keydown", touche);
  });

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : fond encre, titre à gauche et un éventail de photos à droite. */}
      <section className="relative isolate overflow-hidden bg-ink text-white">
        <div
          aria-hidden
          className="absolute -left-24 bottom-0 -z-10 size-96 rounded-full bg-grape/40 blur-3xl motion-safe:animate-derive"
        />
        <div
          aria-hidden
          className="absolute right-0 top-0 -z-10 size-96 rounded-full bg-tangerine/25 blur-3xl motion-safe:animate-derive [animation-delay:-9s]"
        />
        <DecorAnime />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-8 md:pt-12 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <FilAriane rubrique="Vie du club" page="Galerie" clair />
            <div data-reveal="left" className="pt-12">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                {photos.length} photos · {axes.length} axes
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">Les Clubs Santé</span>
                <span className="block text-sun">en images</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/80">
                Compétitions, formations, émissions et actions de terrain : revis les moments forts
                des Clubs Santé SOS Docteur TV partout au Togo.
              </p>
            </div>
          </div>
          <div
            data-reveal="right"
            aria-hidden
            className="relative mx-auto h-72 w-full max-w-xl sm:h-96"
          >
            {collage.map(
              ({ p, c }) =>
                p && (
                  <img
                    key={p.img}
                    src={p.img}
                    alt=""
                    className={`absolute aspect-[4/5] w-[46%] rounded-2xl border-[6px] border-white object-cover shadow-2xl ${p.pos} ${c}`}
                  />
                ),
            )}
          </div>
        </div>
      </section>

      {/* Mur de photos en colonnes, filtrable par axe d'intervention ; un clic ouvre la visionneuse. */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <div data-reveal className="flex flex-wrap gap-2">
          {[null, ...axes].map((a) => {
            const n = a?.n ?? null;
            return (
              <button
                key={n ?? "tous"}
                type="button"
                aria-pressed={axe === n}
                aria-label={a ? `Axe ${a.n} : ${a.nom}` : undefined}
                title={a?.nom}
                onClick={() => setAxe(n)}
                className={`rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                  axe === n
                    ? "bg-logo-blue text-white shadow-card"
                    : "bg-white ring-1 ring-border hover:ring-logo-blue/40"
                }`}
              >
                {a ? `Axe ${a.n}` : "Toutes"}
              </button>
            );
          })}
        </div>
        {axe !== null && (
          <p className="mt-4 text-sm font-bold text-muted-foreground">
            Axe {axe} : {axes[axe - 1]?.nom}
          </p>
        )}
        {liste.length === 0 && (
          <p className="mt-8 rounded-2xl bg-white p-6 text-center font-semibold text-muted-foreground ring-1 ring-border">
            Pas encore de photo pour cet axe : reviens bientôt !
          </p>
        )}

        <ul className="mt-8 columns-1 gap-4 sm:columns-2 lg:columns-3">
          {liste.map((p, i) => (
            <li key={p.img} className="mb-4 break-inside-avoid">
              <button
                type="button"
                onClick={() => setOuverte(i)}
                className="group relative block w-full overflow-hidden rounded-[1.5rem] shadow-card"
              >
                <img
                  src={p.img}
                  alt={p.alt}
                  loading="lazy"
                  width={p.w}
                  height={p.h}
                  className="w-full transition duration-700 group-hover:scale-105"
                />
                <span className="absolute inset-0 flex items-end justify-between gap-3 bg-linear-to-t from-night/70 via-transparent to-transparent p-4 text-left text-white opacity-0 transition duration-300 group-hover:opacity-100 group-focus-visible:opacity-100">
                  <span className="text-sm font-bold leading-snug">{p.alt}</span>
                  <Expand className="size-5 shrink-0" />
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      {photo && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={photo.alt}
          className="fixed inset-0 z-50 flex items-center justify-center bg-night/90 p-4 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={() => setOuverte(null)}
        >
          <figure className="max-h-full max-w-5xl" onClick={(e) => e.stopPropagation()}>
            <img
              src={photo.img}
              alt={photo.alt}
              width={photo.w}
              height={photo.h}
              className="max-h-[78vh] w-auto rounded-2xl object-contain shadow-2xl"
            />
            <figcaption className="mt-4 flex items-center justify-between gap-4 text-white">
              <span className="font-semibold">
                <span className="mr-2 rounded-full bg-sun px-2.5 py-0.5 text-xs font-extrabold uppercase text-ink">
                  Axe {photo.axe}
                </span>
                {photo.alt}
              </span>
              <span className="shrink-0 text-sm font-bold text-white/60">
                {(ouverte ?? 0) + 1} / {liste.length}
              </span>
            </figcaption>
          </figure>
          <button
            type="button"
            onClick={() => setOuverte(null)}
            aria-label="Fermer"
            autoFocus
            className="absolute right-4 top-4 inline-flex size-11 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white hover:text-ink"
          >
            <X className="size-5" />
          </button>
          {liste.length > 1 && (
            <>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  aller(-1);
                }}
                aria-label="Photo précédente"
                className="absolute left-3 top-1/2 inline-flex size-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white hover:text-ink"
              >
                <ChevronLeft className="size-5" />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  aller(1);
                }}
                aria-label="Photo suivante"
                className="absolute right-3 top-1/2 inline-flex size-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white hover:text-ink"
              >
                <ChevronRight className="size-5" />
              </button>
            </>
          )}
        </div>
      )}

      <SiteFooter />
    </div>
  );
}
