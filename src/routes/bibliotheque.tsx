import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowRight, LibraryBig } from "lucide-react";

import { ALaUne } from "@/components/bibliotheque/ALaUne";
import { CarteRessource } from "@/components/bibliotheque/CarteRessource";
import { DecorAnime } from "@/components/DecorAnime";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion, retard } from "@/components/SiteMotion";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascottesLivres from "@/assets/mascottes-livres.webp";
import { chargerAxes, chargerBibliotheque, type CategorieRessource } from "@/lib/api/client";
import { CATEGORIES, estCategorie, ORDRE_CATEGORIES } from "@/lib/bibliotheque";
import { ContenuEnFrancais } from "@/components/ContenuEnFrancais";
import { auSingulier, formatDeLaLangue, lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

type Recherche = { categorie?: CategorieRessource; axe?: string };

export const Route = createFileRoute("/bibliotheque")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const categorie = search["categorie"];
    const axe = typeof search["axe"] === "string" ? search["axe"] : undefined;
    return {
      ...(estCategorie(categorie) ? { categorie } : {}),
      ...(axe ? { axe } : {}),
    };
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [bibliotheque, axes] = await Promise.all([
      chargerBibliotheque(deps),
      chargerAxes().catch(() => []),
    ]);
    return { bibliotheque, axes };
  },
  head: () => ({
    meta: [
      { title: m.biblio_meta_titre() },
      { name: "description", content: m.biblio_meta_description() },
      { property: "og:title", content: m.biblio_meta_og() },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Bibliotheque,
});

const nombre = (n: number) => n.toLocaleString(formatDeLaLangue());

// Un filtre vide disparaît de l'adresse.
const filtres = (categorie?: CategorieRessource, axe?: string): Recherche => ({
  ...(categorie ? { categorie } : {}),
  ...(axe ? { axe } : {}),
});

function Bibliotheque() {
  const { bibliotheque, axes } = Route.useLoaderData();
  const { categorie, axe } = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const { ressources, a_la_une, chiffres } = bibliotheque;
  const filtre = Boolean(categorie || axe);
  const chiffresAffiches = [
    {
      n: nombre(chiffres.documents),
      t: auSingulier(chiffres.documents) ? m.biblio_document() : m.biblio_documents(),
    },
    { n: nombre(chiffres.telechargements), t: m.biblio_telechargements() },
  ];

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
            <FilAriane rubrique={m.menu_vie_du_club()} page={m.menu_bibliotheque()} />
            <div data-reveal="left" className="pt-12 lg:pt-16">
              <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
                <span className="h-1 w-8 rounded-full bg-primary" />
                AIMES-AFRIQUE · SOS Docteur TV
              </p>
              <h1 className="mt-4 text-5xl leading-[0.95] md:text-7xl">
                <span className="block text-logo-blue">{m.biblio_titre_1()}</span>
                <span className="block text-primary">{m.biblio_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-ink/75">{m.biblio_intro()}</p>
              <dl className="mt-8 grid max-w-sm grid-cols-2 gap-3">
                {chiffresAffiches.map((c) => (
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
            alt={m.biblio_mascottes_alt()}
            width={1122}
            height={1402}
            data-reveal="right"
            className="mx-auto w-3/4 max-w-md self-end drop-shadow-2xl lg:w-full"
          />
        </div>
      </section>

      <ALaUne magazines={a_la_une} />

      {/* Rayonnages : un filtre par catégorie et par axe, puis les documents. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <EnTete
            sur={m.biblio_rayons_sur()}
            bleu={m.biblio_rayons_bleu()}
            vert={m.biblio_rayons_vert()}
          >
            {m.biblio_rayons_texte()}
          </EnTete>
          {axes.length > 0 && (
            <label data-reveal className="grid gap-1 text-sm font-bold text-ink">
              {m.biblio_axe()}
              <select
                value={axe ?? ""}
                onChange={(e) =>
                  void naviguer({
                    search: (s) => filtres(s.categorie, e.target.value),
                    resetScroll: false,
                  })
                }
                className="h-11 rounded-full bg-white px-4 font-semibold ring-1 ring-border"
              >
                <option value="">{m.biblio_tous_axes()}</option>
                {axes.map((a) => (
                  <option key={a.code} value={a.code}>
                    {a.libelle}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <nav aria-label={m.biblio_categories()} data-reveal className="mt-8 flex flex-wrap gap-2">
          {([undefined, ...ORDRE_CATEGORIES] as (CategorieRessource | undefined)[]).map((c) => (
            <Link
              key={c ?? "tous"}
              from={Route.fullPath}
              search={(s) => filtres(c, s.axe)}
              resetScroll={false}
              aria-current={categorie === c ? "page" : undefined}
              className={`rounded-full px-4 py-2 text-sm font-bold transition active:scale-95 ${
                categorie === c
                  ? "bg-logo-blue text-white shadow-card"
                  : "bg-white text-ink ring-1 ring-border hover:ring-logo-blue/40"
              }`}
            >
              {c ? CATEGORIES[c].pluriel : m.biblio_tous_documents()}
            </Link>
          ))}
        </nav>

        <ContenuEnFrancais className="mt-4" />
        {ressources.length > 0 ? (
          <ul className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {ressources.map((r, i) => (
              <CarteRessource key={r.id} ressource={r} style={retard(i)} />
            ))}
          </ul>
        ) : (
          <div className="mt-10 flex flex-col items-center gap-4 rounded-[1.75rem] bg-white p-10 text-center shadow-card">
            <LibraryBig aria-hidden className="size-12 text-logo-blue" />
            <p className="max-w-md font-semibold">
              {filtre ? m.biblio_aucun_filtre() : m.biblio_vide()}
            </p>
            {filtre && (
              <Link
                to="/bibliotheque"
                resetScroll={false}
                className="font-bold text-logo-blue hover:underline"
              >
                {m.biblio_voir_tous()}
              </Link>
            )}
          </div>
        )}
      </section>

      {/* Passerelle vers la certification : les fascicules servent à réviser les 20 quiz. */}
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
              {m.biblio_reviser_sur()}
            </p>
            <h2 className="mt-3 text-4xl md:text-5xl">
              {m.biblio_reviser_titre_1()}{" "}
              <span className="text-primary">{m.biblio_reviser_titre_2()}</span>
            </h2>
            <p className="mt-4 max-w-2xl text-lg font-medium text-white/80">
              {m.biblio_reviser_texte()}
            </p>
            <a
              href={lien("/certification")}
              className="btn-fx mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground"
            >
              {m.biblio_decouvrir_certif()} <ArrowRight className="size-4" />
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
