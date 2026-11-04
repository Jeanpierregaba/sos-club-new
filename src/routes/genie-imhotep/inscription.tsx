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

export const Route = createFileRoute("/genie-imhotep/inscription")({
  head: () => ({
    meta: [
      { title: "Inscription — Génie Imhotep" },
      {
        name: "description",
        content:
          "Inscris ton établissement au Championnat national Génie Imhotep, au tournoi interclasses ou à la compétition télévisée sur SOS Docteur TV.",
      },
      { property: "og:title", content: "Inscription au Génie Imhotep" },
    ],
  }),
  // Sans l'API, le sélecteur de région reste vide : le formulaire n'est pas encore ouvert de toute façon.
  loader: () => chargerDre().catch(() => []),
  component: Inscription,
});

type Champ = { l: string; ph: string; type?: "text" | "tel" | "email" | "dre" | "texte" };

// `c` : la couleur de la compétition, posée en variable CSS sur son panneau.
const competitions: {
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
}[] = [
  {
    id: "championnat",
    onglet: "Championnat national",
    i: Trophy,
    c: "var(--logo-blue)",
    photo: grandesFinales,
    citation: "C’est ici et maintenant",
    titre: "Championnat national Génie Imhotep",
    intro:
      "Confrontation d’élite entre les meilleurs collèges et lycées du Togo sur la culture générale en santé, les gestes de premiers secours et le sens civique.",
    blocs: [
      {
        t: "Critères d’éligibilité",
        items: [
          "Établissement scolaire homologué par le ministère de tutelle (MEPSTA).",
          "Club Santé officiellement installé avec son bureau de 21 élèves.",
          "Équipe de 4 titulaires et 2 remplaçants (parité filles/garçons encouragée).",
        ],
      },
      {
        t: "Format des épreuves",
        items: [
          "Phase 1 : éliminatoires par inspection (IESG), à l’écrit et en QCM rapide.",
          "Phase 2 : finales régionales au chef-lieu de chaque DRE.",
          "Phase 3 : Grande Finale nationale retransmise en direct à Lomé.",
        ],
      },
      {
        t: "Récompenses & bourses",
        items: [
          "Bourses d’excellence scolaire pour les lauréats et trophée national Imhotep.",
          "Équipements médicaux d’infirmerie et trousses de secours pour l’école.",
          "Attestations officielles d’honneur signées par AIMES-AFRIQUE et les ministères.",
        ],
      },
    ],
    formulaire: {
      sur: "Formulaire officiel national 2026",
      t: "Inscription au championnat national",
      note: "Ce formulaire doit être validé par le chef d’établissement ou le responsable d’encadrement du Club Santé.",
      champs: [
        { l: "Nom de l’établissement", ph: "Ex : Lycée de Tokoin, Lycée d’Aného…" },
        { l: "Direction régionale (DRE)", ph: "", type: "dre" },
        { l: "Ville / localité", ph: "Ex : Lomé, Atakpamé, Kara, Sokodé…" },
        { l: "Nom du proviseur / encadreur", ph: "Ex : M. Koffi Mensah" },
        { l: "Téléphone de contact", ph: "+228 90 00 00 00", type: "tel" },
        { l: "E-mail officiel", ph: "contact@etablissement.tg", type: "email" },
      ],
      accord:
        "Je certifie l’exactitude des informations et déclare adhérer au règlement officiel du Championnat national Génie Imhotep.",
      bouton: "Valider l’inscription au championnat",
    },
  },
  {
    id: "interclasses",
    onglet: "Compétitions interclasses",
    i: School,
    c: "var(--primary)",
    photo: slideClubs,
    citation: "Des bancs de classe aux projecteurs de l’excellence",
    titre: "Les compétitions interclasses",
    intro:
      "L’émulation commence dans les classes ! Affronte les autres niveaux, de la 6e à la Terminale, lors des journées culturelles et scientifiques de ton collège ou de ton lycée.",
    blocs: [
      {
        t: "Règles du tournoi",
        items: [
          "Format d’équipe : chaque classe aligne 4 délégués santé désignés lors de l’assemblée de classe.",
          "Épreuves : speed-quiz santé, démonstration pratique de la PLS (position latérale de sécurité) et sketch de sensibilisation.",
          "Validation : les 3 enseignants encadreurs du Club Santé composent le jury d’évaluation.",
        ],
      },
      {
        t: "Avantages pour la classe gagnante",
        items: [
          "Qualification directe pour représenter l’établissement aux éliminatoires régionales.",
          "Fanion d’honneur « Classe Sentinelle de Santé » et fournitures scolaires.",
          "Mise en avant dans le magazine officiel et sur la page Facebook des Clubs Santé.",
        ],
      },
    ],
    formulaire: {
      sur: "Organisation locale d’établissement",
      t: "Inscrire une classe au tournoi interne",
      // Le contact demandé est celui de l'encadreur, jamais celui d'un élève (docs/RULES.md).
      champs: [
        { l: "Établissement", ph: "Ex : Lycée Bè-Klikamé" },
        { l: "Classe candidate", ph: "Ex : 3e B, 1re D, Tle A4…" },
        { l: "Enseignant encadreur référent", ph: "Nom de l’encadreur du Club Santé" },
        { l: "Téléphone de l’encadreur", ph: "+228 90 00 00 00", type: "tel" },
      ],
      bouton: "Enregistrer l’équipe de la classe",
    },
  },
  {
    id: "television",
    onglet: "Compétition télévisée",
    i: Tv,
    c: "var(--logo-red)",
    photo: story2,
    citation: "La télévision au cœur de l’éducation civique",
    titre: "Compétition télévisée (studio SOS Docteur TV)",
    intro:
      "Participe aux enregistrements officiels en direct des studios de SOS Docteur TV à Lomé : une expérience unique de média, d’éloquence et d’impact national.",
    blocs: [
      {
        t: "Conditions de passage TV",
        items: [
          "Les équipes sélectionnées portent l’uniforme officiel de leur établissement et le tee-shirt aux couleurs du Club Santé SOS Docteur TV.",
        ],
      },
      {
        t: "Autorisation parentale & droit à l’image",
        items: [
          "Chaque élève mineur participant au plateau TV fournit une fiche d’autorisation parentale signée, qui autorise la diffusion télévisée et numérique.",
        ],
      },
      {
        t: "Coaching & préparation studio",
        items: [
          "Une initiation à la prise de parole en public et au fonctionnement d’un plateau télévisé est proposée avant le tournage.",
        ],
      },
    ],
    formulaire: {
      sur: "Postulation au plateau télévisé",
      t: "Candidater pour la compétition télévisée",
      champs: [
        { l: "Nom de l’équipe / du club", ph: "Ex : Les Sentinelles du Lycée de Tokoin" },
        { l: "Établissement représenté", ph: "Ex : Lycée moderne d’Anié" },
        { l: "Nom de l’enseignant tuteur", ph: "Nom de l’encadreur accompagnateur" },
        { l: "Téléphone de l’encadreur", ph: "+228 90 00 00 00", type: "tel" },
        {
          l: "Brève motivation de l’équipe",
          ph: "Pourquoi ton équipe souhaite-t-elle participer à la compétition télévisée ?",
          type: "texte",
        },
      ],
      accord:
        "L’équipe et l’établissement acceptent le droit à l’image pour les retransmissions télévisées et les plateformes officielles SOS Docteur TV.",
      bouton: "Soumettre la candidature",
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
            <FilAriane rubrique="Génie Imhotep" page="Inscription" clair />
            <div data-reveal="left" className="pt-12 lg:pt-16">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                Inscription officielle · Génie Imhotep
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] [text-shadow:0_2px_14px_rgb(0_0_0/0.18)] md:text-7xl">
                <span className="block">Génie Imhotep</span>
                <span className="mt-2 block text-3xl text-sun md:text-5xl">
                  Premier jeu de culture en santé publique
                </span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-semibold text-white/90">
                Promotion de la culture générale en santé publique auprès des adolescents et des
                jeunes. Choisis ta compétition et inscris ton équipe.
              </p>
            </div>
          </div>
          <img
            src={mascotteImhotep}
            alt="La mascotte Génie Imhotep"
            width={1414}
            height={2000}
            data-reveal="right"
            className="mx-auto w-48 self-end drop-shadow-2xl md:w-60 lg:w-72"
          />
        </div>
      </section>

      {/* Sélecteur : une grande carte par compétition, qui chevauche le bas de la bannière. */}
      <div className="relative z-10 mx-auto -mt-10 max-w-7xl px-5">
        <div role="group" aria-label="Compétitions" className="grid gap-3 sm:grid-cols-3">
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
                « {c.citation} »
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
            Les inscriptions en ligne ouvrent bientôt. En attendant, rapproche-toi de ta DRE ou de
            la coordination nationale.
          </p>
          <fieldset disabled className="mt-6 grid gap-4 opacity-80">
            {c.formulaire.champs.map((f) => (
              <Libelle key={f.l} l={f.l}>
                {f.type === "dre" ? (
                  <select className={champCls} defaultValue="">
                    <option value="" disabled>
                      Choisis ta région
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
