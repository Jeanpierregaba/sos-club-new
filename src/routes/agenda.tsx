import { createFileRoute, useNavigate } from "@tanstack/react-router";

import { CarteEvenement } from "@/components/agenda/CarteEvenement";
import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { chargerAgenda, chargerAxes, chargerDre } from "@/lib/api/client";
import type { EvenementPublic } from "@/lib/api/client";
import { ContenuEnFrancais } from "@/components/ContenuEnFrancais";
import {
  COULEURS_NIVEAU,
  NIVEAUX,
  TYPES_EVENEMENT,
  dateEvenement,
  typeEvenement,
} from "@/lib/agenda";
import { auSingulier } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

type Niveau = "national" | "regional" | "club";
type Recherche = {
  niveau?: Niveau | undefined;
  dre?: string | undefined;
  club?: string | undefined;
  type?: string | undefined;
  axe?: string | undefined;
};

const texte = (valeur: unknown) => (typeof valeur === "string" && valeur ? valeur : undefined);

export const Route = createFileRoute("/agenda")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const niveau = texte(search["niveau"]);
    const recherche: Recherche = {};
    if (niveau && niveau in NIVEAUX) recherche.niveau = niveau as Niveau;
    for (const cle of ["dre", "club", "type", "axe"] as const) {
      const valeur = texte(search[cle]);
      if (valeur) recherche[cle] = valeur;
    }
    return recherche;
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [avenir, passes, dre, axes] = await Promise.all([
      chargerAgenda({ ...deps, periode: "a_venir" }),
      chargerAgenda({ ...deps, periode: "passe" }),
      chargerDre().catch(() => []),
      chargerAxes().catch(() => []),
    ]);
    return { avenir, passes, dre, axes };
  },
  head: () => ({
    meta: [
      { title: m.agenda_meta_titre() },
      { name: "description", content: m.agenda_meta_description() },
      { property: "og:title", content: m.agenda_meta_og() },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Agenda,
});

const selectCls =
  "h-11 max-w-full rounded-full border bg-white px-4 text-sm font-bold outline-none transition focus:border-logo-blue";

function parMois(evenements: EvenementPublic[]) {
  const groupes: { titre: string; evenements: EvenementPublic[] }[] = [];
  for (const evenement of evenements) {
    const titre = dateEvenement(evenement.debut, { month: "long", year: "numeric" });
    const dernier = groupes.at(-1);
    if (dernier?.titre === titre) dernier.evenements.push(evenement);
    else groupes.push({ titre, evenements: [evenement] });
  }
  return groupes;
}

function Agenda() {
  const { avenir, passes, dre, axes } = Route.useLoaderData();
  const recherche = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const filtrer = (changements: Partial<Recherche>) =>
    void naviguer({ search: (avant) => ({ ...avant, ...changements }), resetScroll: false });

  const total = avenir.total + passes.total;
  const groupes = [
    ...parMois(avenir.evenements).map((g) => ({ ...g, passe: false })),
    ...(passes.evenements.length > 0
      ? [{ titre: m.agenda_deja_passes(), evenements: passes.evenements, passe: true }]
      : []),
  ];

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : le titre et les 3 sections de l'agenda, qui servent aussi de filtre. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-sky to-logo-blue text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[linear-gradient(oklch(1_0_0/0.08)_1px,transparent_1px),linear-gradient(90deg,oklch(1_0_0/0.08)_1px,transparent_1px)] bg-size-[56px_56px] [mask-image:linear-gradient(to_bottom,black,transparent)]"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 pb-16 pt-8 md:pt-12 lg:grid-cols-[1.1fr_1fr] lg:pb-20">
          <div>
            <FilAriane rubrique={m.menu_actualites()} page={m.menu_agenda()} clair />
            <div data-reveal="left" className="pt-12">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                {m.agenda_calendrier()}
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.agenda_titre_1()}</span>
                <span className="block text-sun">{m.agenda_titre_2()}</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">{m.agenda_intro()}</p>
            </div>
          </div>
          <ul className="grid gap-3">
            {(Object.keys(NIVEAUX) as Niveau[]).map((niveau, i) => {
              const { couleur, icone: Icone } = COULEURS_NIVEAU[niveau];
              const actif = recherche.niveau === niveau;
              return (
                <li key={niveau} data-reveal="right" style={retard(i)}>
                  <button
                    type="button"
                    aria-pressed={actif}
                    onClick={() => filtrer({ niveau: actif ? undefined : niveau })}
                    className={`flex w-full items-center gap-4 rounded-[1.5rem] p-4 text-left transition duration-300 md:p-5 ${
                      actif
                        ? "bg-white text-ink shadow-card"
                        : "bg-white/10 ring-1 ring-white/20 hover:bg-white/20"
                    }`}
                  >
                    <span
                      className="inline-flex size-12 shrink-0 items-center justify-center rounded-2xl text-white"
                      style={{ backgroundColor: couleur }}
                    >
                      <Icone className="size-6" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span
                        className={`block text-[11px] font-extrabold uppercase tracking-wider ${actif ? "text-muted-foreground" : "text-white/70"}`}
                      >
                        {m.agenda_section({ numero: `0${i + 1}`, nom: NIVEAUX[niveau].long })}
                      </span>
                      <span className="block font-display text-xl leading-tight">
                        {NIVEAUX[niveau].court}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      {/* Filtres puis frise des événements : à venir par mois, puis les passés. */}
      <section className="mx-auto max-w-5xl px-5 py-16">
        <div
          data-reveal
          className="flex flex-wrap items-center gap-3 rounded-[1.75rem] bg-white p-4 shadow-card md:p-5"
        >
          <span className="text-sm font-extrabold">
            {(auSingulier(total) ? m.agenda_un_evenement : m.agenda_n_evenements)({
              nombre: String(total),
            })}
            {recherche.niveau && (
              <span className="text-muted-foreground"> · {NIVEAUX[recherche.niveau].court}</span>
            )}
          </span>
          <span className="ml-auto flex flex-wrap gap-2">
            <select
              aria-label={m.agenda_region()}
              value={recherche.dre ?? ""}
              onChange={(e) => filtrer({ dre: e.target.value || undefined })}
              className={selectCls}
            >
              <option value="">{m.agenda_toutes_regions()}</option>
              {dre.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.nom}
                </option>
              ))}
            </select>
            <select
              aria-label={m.agenda_type_activite()}
              value={recherche.type ?? ""}
              onChange={(e) => filtrer({ type: e.target.value || undefined })}
              className={selectCls}
            >
              <option value="">{m.agenda_toutes_activites()}</option>
              {Object.keys(TYPES_EVENEMENT).map((code) => (
                <option key={code} value={code}>
                  {typeEvenement(code)}
                </option>
              ))}
            </select>
            <select
              aria-label={m.agenda_axe()}
              value={recherche.axe ?? ""}
              onChange={(e) => filtrer({ axe: e.target.value || undefined })}
              className={selectCls}
            >
              <option value="">{m.biblio_tous_axes()}</option>
              {axes.map((a) => (
                <option key={a.code} value={a.code}>
                  {a.libelle}
                </option>
              ))}
            </select>
          </span>
        </div>

        <ContenuEnFrancais className="mt-4" />
        {total === 0 && (
          <p className="mt-10 rounded-[1.75rem] border border-dashed p-10 text-center font-semibold text-muted-foreground">
            {m.agenda_aucun_filtre()}
          </p>
        )}

        {groupes.map((groupe) => (
          <div key={groupe.titre} className="mt-12">
            <h2 className="flex items-center gap-4 text-3xl capitalize text-logo-blue md:text-4xl">
              {groupe.titre}
              <span className="h-px flex-1 bg-border" />
            </h2>
            <ol className="relative mt-6 grid gap-5 border-l-2 border-dashed border-logo-blue/20 pl-6 md:pl-10">
              {groupe.evenements.map((evenement) => {
                const passe = groupe.passe;
                return (
                  <li key={evenement.id} className="relative">
                    <span
                      aria-hidden
                      className="absolute -left-[33px] top-8 size-4 rounded-full ring-4 ring-background md:-left-[49px]"
                      style={{
                        backgroundColor: passe
                          ? "var(--border)"
                          : COULEURS_NIVEAU[evenement.niveau].couleur,
                      }}
                    />
                    <CarteEvenement evenement={evenement} passe={passe} />
                  </li>
                );
              })}
            </ol>
          </div>
        ))}
      </section>

      <SiteFooter />
    </div>
  );
}
