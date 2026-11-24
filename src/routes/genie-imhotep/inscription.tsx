import { useState, type CSSProperties, type ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { CalendarClock, Check, School, Trophy, Tv, type LucideIcon } from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion } from "@/components/SiteMotion";
import { chargerDre } from "@/lib/api/client";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import grandesFinales from "@/assets/agenda-grandes-finales.jpg";
import slideClubs from "@/assets/slide-clubs.webp";
import story2 from "@/assets/story2.jpg";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/genie-imhotep/inscription")({
  head: () => ({
    meta: [
      { title: m.gins_meta_titre() },
      { name: "description", content: m.gins_meta_description() },
      { property: "og:title", content: m.gins_meta_og() },
    ],
  }),
  // Sans l'API, le sélecteur de région reste vide : le formulaire n'est pas encore ouvert de toute façon.
  loader: () => chargerDre().catch(() => []),
  component: Inscription,
});

type Champ = { l: string; ph: string; type?: "text" | "tel" | "email" | "dre" | "texte" };

// `c` : la couleur de la compétition, posée en variable CSS sur son panneau. Une fonction : les textes suivent la
// langue de la page (spec 052).
const lesCompetitions = (): {
  id: string;
  onglet: string;
  i: LucideIcon;
  c: string;
  photo: string;
  citation: string;
  titre: string;
  intro: string;
  blocs: { t: string; items: string[] }[];
  formulaire: {
    sur: string;
    t: string;
    note?: string;
    champs: Champ[];
    accord?: string;
    bouton: string;
  };
}[] => [
  {
    id: "championnat",
    onglet: m.gins_ch_onglet(),
    i: Trophy,
    c: "var(--logo-blue)",
    photo: grandesFinales,
    citation: m.gins_ch_citation(),
    titre: m.gins_ch_titre(),
    intro: m.gins_ch_intro(),
    blocs: [
      { t: m.gins_ch_b1(), items: [m.gins_ch_b1_1(), m.gins_ch_b1_2(), m.gins_ch_b1_3()] },
      { t: m.gins_ch_b2(), items: [m.gins_ch_b2_1(), m.gins_ch_b2_2(), m.gins_ch_b2_3()] },
      { t: m.gins_ch_b3(), items: [m.gins_ch_b3_1(), m.gins_ch_b3_2(), m.gins_ch_b3_3()] },
    ],
    formulaire: {
      sur: m.gins_ch_sur(),
      t: m.gins_ch_t(),
      note: m.gins_ch_note(),
      champs: [
        { l: m.gins_champ_etablissement(), ph: m.gins_ph_etablissement() },
        { l: m.gins_champ_dre(), ph: "", type: "dre" },
        { l: m.gins_champ_ville(), ph: m.gins_ph_ville() },
        { l: m.gins_champ_proviseur(), ph: m.gins_ph_proviseur() },
        { l: m.gins_champ_telephone(), ph: "+228 90 00 00 00", type: "tel" },
        { l: m.gins_champ_email(), ph: "contact@etablissement.tg", type: "email" },
      ],
      accord: m.gins_ch_accord(),
      bouton: m.gins_ch_bouton(),
    },
  },
  {
    id: "interclasses",
    onglet: m.gins_ic_onglet(),
    i: School,
    c: "var(--primary)",
    photo: slideClubs,
    citation: m.gins_ic_citation(),
    titre: m.gins_ic_titre(),
    intro: m.gins_ic_intro(),
    blocs: [
      { t: m.gins_ic_b1(), items: [m.gins_ic_b1_1(), m.gins_ic_b1_2(), m.gins_ic_b1_3()] },
      { t: m.gins_ic_b2(), items: [m.gins_ic_b2_1(), m.gins_ic_b2_2(), m.gins_ic_b2_3()] },
    ],
    formulaire: {
      sur: m.gins_ic_sur(),
      t: m.gins_ic_t(),
      // Le contact demandé est celui de l'encadreur, jamais celui d'un élève (docs/RULES.md).
      champs: [
        { l: m.gins_champ_etab_court(), ph: m.gins_ph_etab_court() },
        { l: m.gins_champ_classe(), ph: m.gins_ph_classe() },
        { l: m.gins_champ_referent(), ph: m.gins_ph_referent() },
        { l: m.gins_champ_tel_encadreur(), ph: "+228 90 00 00 00", type: "tel" },
      ],
      bouton: m.gins_ic_bouton(),
    },
  },
  {
    id: "television",
    onglet: m.gins_tv_onglet(),
    i: Tv,
    c: "var(--logo-red)",
    photo: story2,
    citation: m.gins_tv_citation(),
    titre: m.gins_tv_titre(),
    intro: m.gins_tv_intro(),
    blocs: [
      { t: m.gins_tv_b1(), items: [m.gins_tv_b1_1()] },
      { t: m.gins_tv_b2(), items: [m.gins_tv_b2_1()] },
      { t: m.gins_tv_b3(), items: [m.gins_tv_b3_1()] },
    ],
    formulaire: {
      sur: m.gins_tv_sur(),
      t: m.gins_tv_t(),
      champs: [
        { l: m.gins_champ_equipe(), ph: m.gins_ph_equipe() },
        { l: m.gins_champ_etab_represente(), ph: m.gins_ph_etab_represente() },
        { l: m.gins_champ_tuteur(), ph: m.gins_ph_tuteur() },
        { l: m.gins_champ_tel_encadreur(), ph: "+228 90 00 00 00", type: "tel" },
        { l: m.gins_champ_motivation(), ph: m.gins_ph_motivation(), type: "texte" },
      ],
      accord: m.gins_tv_accord(),
      bouton: m.gins_tv_bouton(),
    },
  },
];

const champCls =
  "mt-1.5 w-full rounded-xl border bg-mist-soft px-4 py-3 text-[15px] font-semibold outline-none placeholder:font-medium placeholder:text-muted-foreground disabled:cursor-not-allowed";

function Libelle({ l, children }: { l: string; children: ReactNode }) {
  return (
    <label className="block text-xs font-extrabold uppercase tracking-wider text-ink/80">
      {l} <span className="text-logo-red">*</span>
      {children}
    </label>
  );
}

function Inscription() {
  const dres = Route.useLoaderData();
  const [actif, setActif] = useState("championnat");
  const competitions = lesCompetitions();
  const c = competitions.find((x) => x.id === actif) ?? competitions[0]!;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière verte : le slogan du Génie Imhotep et sa mascotte. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-primary to-leaf text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[radial-gradient(oklch(1_0_0/0.16)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_70%)]"
        />
        <div
          aria-hidden
          className="absolute -right-32 -top-32 -z-10 size-[36rem] rounded-full border-[3rem] border-white/10"
        />
        <div className="mx-auto grid max-w-7xl items-end gap-6 px-5 pt-8 md:pt-12 lg:grid-cols-[1.3fr_1fr]">
          <div className="pb-14 lg:pb-20">
            <FilAriane rubrique={m.menu_genie_imhotep()} page={m.gins_inscription()} clair />
            <div data-reveal="left" className="pt-12 lg:pt-16">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                {m.gins_officielle()}
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] [text-shadow:0_2px_14px_rgb(0_0_0/0.18)] md:text-7xl">
                <span className="block">Génie Imhotep</span>
                <span className="mt-2 block text-3xl text-sun md:text-5xl">
                  {m.gins_premier_jeu()}
                </span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-semibold text-white/90">{m.gins_intro()}</p>
            </div>
          </div>
          <img
            src={mascotteImhotep}
            alt={m.gins_mascotte_alt()}
            width={1414}
            height={2000}
            data-reveal="right"
            className="mx-auto w-48 self-end drop-shadow-2xl md:w-60 lg:w-72"
          />
        </div>
      </section>

      {/* Sélecteur : une grande carte par compétition, qui chevauche le bas de la bannière. */}
      <div className="relative z-10 mx-auto -mt-10 max-w-7xl px-5">
        <div role="group" aria-label={m.gins_competitions()} className="grid gap-3 sm:grid-cols-3">
          {competitions.map((x) => {
            const on = x.id === actif;
            return (
              <button
                key={x.id}
                type="button"
                aria-pressed={on}
                onClick={() => setActif(x.id)}
                style={{ "--c": x.c } as CSSProperties}
                className={`flex items-center gap-4 rounded-[1.5rem] p-5 text-left shadow-card transition duration-300 ${
                  on ? "-translate-y-1 bg-(color:--c) text-white" : "bg-white hover:-translate-y-1"
                }`}
              >
                <span
                  className={`inline-flex size-12 shrink-0 items-center justify-center rounded-2xl ${on ? "bg-white/20" : "bg-(color:--c) text-white"}`}
                >
                  <x.i className="size-6" />
                </span>
                <span className="font-display text-xl leading-tight">{x.onglet}</span>
              </button>
            );
          })}
        </div>
      </div>

      <section
        key={c.id}
        style={{ "--c": c.c } as CSSProperties}
        className="mx-auto grid max-w-7xl gap-10 px-5 py-16 animate-in fade-in duration-500 lg:grid-cols-[1.1fr_1fr] lg:gap-14"
      >
        <div>
          <figure className="relative overflow-hidden rounded-[2rem] shadow-card">
            <img
              src={c.photo}
              alt=""
              loading="lazy"
              className="aspect-[16/9] w-full object-cover"
            />
            <figcaption className="absolute inset-0 flex items-end bg-linear-to-t from-night/85 via-night/20 to-transparent p-6">
              <span className="font-hand text-2xl leading-tight text-white md:text-3xl">
                {m.commun_citation({ texte: c.citation })}
              </span>
            </figcaption>
          </figure>
          <h2 className="mt-8 text-4xl text-(color:--c) md:text-5xl">{c.titre}</h2>
          <p className="mt-3 text-lg font-medium text-muted-foreground">{c.intro}</p>
          <ol className="mt-8 grid gap-4">
            {c.blocs.map((b, i) => (
              <li key={b.t} className="rounded-[1.5rem] bg-white p-6 shadow-sm ring-1 ring-border">
                <p className="flex items-center gap-3 font-display text-xl">
                  <span className="inline-flex size-9 items-center justify-center rounded-xl bg-(color:--c) text-white">
                    {i + 1}
                  </span>
                  {b.t}
                </p>
                <ul className="mt-4 grid gap-2.5">
                  {b.items.map((it) => (
                    <li key={it} className="flex gap-3 font-medium leading-snug">
                      <Check className="mt-0.5 size-5 shrink-0 text-(color:--c)" />
                      {it}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ol>
        </div>

        {/* Le formulaire est affiché mais fermé : rien n'est envoyé tant que l'API des inscriptions n'existe pas. */}
        <form
          onSubmit={(e) => e.preventDefault()}
          className="self-start rounded-[2rem] bg-white p-7 shadow-card ring-1 ring-border md:p-9 lg:sticky lg:top-24"
        >
          <p className="text-xs font-extrabold uppercase tracking-widest text-logo-red">
            {c.formulaire.sur}
          </p>
          <h3 className="mt-2 text-3xl leading-tight text-logo-blue">{c.formulaire.t}</h3>
          {c.formulaire.note && (
            <p className="mt-2 text-sm font-medium text-muted-foreground">{c.formulaire.note}</p>
          )}
          <p className="mt-5 flex items-start gap-3 rounded-2xl bg-sun/25 p-4 text-sm font-bold">
            <CalendarClock className="mt-0.5 size-5 shrink-0" />
            {m.gins_bientot()}
          </p>
          <fieldset disabled className="mt-6 grid gap-4 opacity-80">
            {c.formulaire.champs.map((f) => (
              <Libelle key={f.l} l={f.l}>
                {f.type === "dre" ? (
                  <select className={champCls} defaultValue="">
                    <option value="" disabled>
                      {m.gins_choisis_region()}
                    </option>
                    {dres.map((d) => (
                      <option key={d.code} value={d.code}>
                        {d.nom}
                      </option>
                    ))}
                  </select>
                ) : f.type === "texte" ? (
                  <textarea rows={4} placeholder={f.ph} className={champCls} />
                ) : (
                  <input type={f.type ?? "text"} placeholder={f.ph} className={champCls} />
                )}
              </Libelle>
            ))}
            {c.formulaire.accord && (
              <label className="flex items-start gap-3 text-sm font-semibold text-muted-foreground">
                <input type="checkbox" className="mt-1 size-4 shrink-0" />
                {c.formulaire.accord}
              </label>
            )}
            <button
              type="submit"
              className="mt-2 rounded-full bg-primary px-7 py-3.5 font-bold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60"
            >
              {c.formulaire.bouton}
            </button>
          </fieldset>
        </form>
      </section>

      <SiteFooter />
    </div>
  );
}
