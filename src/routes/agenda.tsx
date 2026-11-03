import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  Landmark,
  MapPin,
  School,
  Stethoscope,
  Users,
  type LucideIcon,
} from "lucide-react";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";

export const Route = createFileRoute("/agenda")({
  head: () => ({
    meta: [
      { title: "Agenda — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "L'agenda officiel des Clubs Santé SOS Docteur TV : concours, formations, campagnes et actions de terrain dans les régions du Togo.",
      },
      { property: "og:title", content: "L'agenda officiel des Clubs Santé" },
    ],
  }),
  component: Agenda,
});

type Section = "stp" | "comite" | "club";

const sections: Record<
  Section,
  { n: string; sur: string; t: string; d: string; i: LucideIcon; c: string }
> = {
  stp: {
    n: "01",
    sur: "Coordination centrale & pilotage",
    t: "Secrétariat technique permanent",
    d: "Programmation stratégique nationale, grands concours Génie Imhotep, cérémonies officielles et directives centrales.",
    i: Landmark,
    c: "var(--logo-blue)",
  },
  comite: {
    n: "02",
    sur: "Encadrement scientifique & régional",
    t: "Comité",
    d: "Séminaires régionaux, missions médicales, supervisions pédagogiques, formations des encadreurs et comités régionaux.",
    i: Stethoscope,
    c: "var(--grape)",
  },
  club: {
    n: "03",
    sur: "Actions terrain & vie des établissements",
    t: "Club Santé SOS Docteur TV",
    d: "Activités de terrain dans les lycées et collèges, campagnes de sensibilisation, salubrité scolaire et vie des clubs.",
    i: School,
    c: "var(--primary)",
  },
};

// Événements repris de l'agenda du site de référence fourni par le porteur du projet (clubsante.ibdastudio.com).
const evenements: {
  section: Section;
  type: string;
  date: string;
  t: string;
  d: string;
  lieu: string;
  region: string;
  inscrits: number;
}[] = [
  {
    section: "comite",
    type: "Formation",
    date: "2026-10-15",
    t: "Séminaire régional de formation des encadreurs – Région des Plateaux",
    d: "Formation des enseignants encadreurs sur les nouveaux modules de santé sexuelle et de secourisme de base élaborés par AIMES-AFRIQUE.",
    lieu: "Hôtel de ville, Kpalimé",
    region: "Plateaux",
    inscrits: 35,
  },
  {
    section: "club",
    type: "Sensibilisation",
    date: "2026-10-18",
    t: "Campagne de sensibilisation « Zéro palu au lycée » – Kara",
    d: "Distribution de moustiquaires imprégnées d’insecticide et conférence-débat animée par les parrains médicaux d’AIMES-AFRIQUE Kara.",
    lieu: "Lycée de Kara 1, Kara",
    region: "Kara",
    inscrits: 150,
  },
  {
    section: "stp",
    type: "Concours",
    date: "2026-10-25",
    t: "Grande Finale nationale du concours « Génie Imhotep » 2026",
    d: "La compétition ultime qui réunit les meilleurs élèves des clubs santé de toutes les régions du Togo : quiz de rapidité, épreuve de secourisme pratique et présentation de projets innovants d’assainissement.",
    lieu: "Palais des Congrès de Lomé & en direct sur SOS Docteur TV",
    region: "Lomé",
    inscrits: 450,
  },
  {
    section: "club",
    type: "Assainissement",
    date: "2026-11-05",
    t: "Opération salubrité publique et tri sélectif des déchets – Sokodé",
    d: "Grande action communautaire de nettoyage et d’installation de bacs de recyclage conçus par les élèves du Lycée de Sokodé 2.",
    lieu: "Quartier Kouloumdè, Sokodé",
    region: "Centrale",
    inscrits: 90,
  },
  {
    section: "comite",
    type: "Campagne",
    date: "2026-11-12",
    t: "Caravane médicale mobile et dépistage scolaire – Savanes",
    d: "Grande campagne de dépistage visuel et de consultations médicales gratuites pour les élèves de la région des Savanes.",
    lieu: "Lycée de Dapaong, Dapaong",
    region: "Savanes",
    inscrits: 310,
  },
  {
    section: "club",
    type: "Sensibilisation",
    date: "2026-11-20",
    t: "Atelier de sensibilisation sur l’hygiène sexuelle et reproductive – Maritime",
    d: "Conférence interactive menée avec SOS Docteur TV pour libérer la parole sur l’hygiène menstruelle et la prévention des grossesses précoces.",
    lieu: "Lycée de Tsévié 1, Tsévié",
    region: "Maritime",
    inscrits: 180,
  },
];

const regions = ["Lomé", "Maritime", "Plateaux", "Centrale", "Kara", "Savanes"];
const types = ["Concours", "Formation", "Sensibilisation", "Assainissement", "Campagne"];

// Les dates sont lues à midi UTC pour que le serveur et le navigateur affichent le même jour.
const jour = (iso: string, o: Intl.DateTimeFormatOptions) =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString("fr-FR", { timeZone: "UTC", ...o });

const selectCls =
  "h-11 rounded-full border bg-white px-4 text-sm font-bold outline-none transition focus:border-logo-blue";

function Agenda() {
  const [section, setSection] = useState<Section | null>(null);
  const [region, setRegion] = useState("");
  const [type, setType] = useState("");
  // La date du jour n'est connue qu'au navigateur : avant, aucun événement n'est marqué comme passé.
  const [aujourdhui, setAujourdhui] = useState("");
  useEffect(() => setAujourdhui(new Date().toISOString().slice(0, 10)), []);

  const liste = evenements
    .filter(
      (e) =>
        (!section || e.section === section) &&
        (!region || e.region === region) &&
        (!type || e.type === type),
    )
    .sort((a, b) => a.date.localeCompare(b.date));
  // Les événements à venir d'abord, mois par mois ; les passés ensuite, du plus récent au plus ancien.
  const avenir = liste.filter((e) => !aujourdhui || e.date >= aujourdhui);
  const passes = liste.filter((e) => aujourdhui && e.date < aujourdhui).reverse();
  const groupes = [
    ...[...new Set(avenir.map((e) => e.date.slice(0, 7)))].map((m) => ({
      titre: jour(`${m}-01`, { month: "long", year: "numeric" }),
      evts: avenir.filter((e) => e.date.startsWith(m)),
    })),
    ...(passes.length > 0 ? [{ titre: "Déjà passés", evts: passes }] : []),
  ];

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière bleu ciel : le titre et les 3 sections de l'agenda, qui servent aussi de filtre. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-sky to-logo-blue text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 bg-[linear-gradient(oklch(1_0_0/0.08)_1px,transparent_1px),linear-gradient(90deg,oklch(1_0_0/0.08)_1px,transparent_1px)] bg-size-[56px_56px] [mask-image:linear-gradient(to_bottom,black,transparent)]"
        />
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 pb-16 pt-8 md:pt-12 lg:grid-cols-[1.1fr_1fr] lg:pb-20">
          <div>
            <FilAriane rubrique="Actualités" page="Agenda" clair />
            <div data-reveal="left" className="pt-12">
              <span className="inline-flex rounded-full bg-sun px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-ink">
                Calendrier officiel en 3 sections
              </span>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">L’agenda officiel</span>
                <span className="block text-sun">des Clubs Santé</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg font-medium text-white/85">
                Retrouve toute la programmation officielle, organisée autour de 3 instances : le
                Secrétariat technique permanent, le Comité et le Club Santé SOS Docteur TV.
              </p>
            </div>
          </div>
          <ul className="grid gap-3">
            {(Object.keys(sections) as Section[]).map((k, i) => {
              const s = sections[k];
              const n = evenements.filter((e) => e.section === k).length;
              const on = section === k;
              return (
                <li key={k} data-reveal="right" style={retard(i)}>
                  <button
                    type="button"
                    aria-pressed={on}
                    onClick={() => setSection(on ? null : k)}
                    className={`flex w-full items-center gap-4 rounded-[1.5rem] p-4 text-left transition duration-300 md:p-5 ${
                      on
                        ? "bg-white text-ink shadow-card"
                        : "bg-white/10 ring-1 ring-white/20 hover:bg-white/20"
                    }`}
                  >
                    <span
                      className="inline-flex size-12 shrink-0 items-center justify-center rounded-2xl text-white"
                      style={{ backgroundColor: s.c }}
                    >
                      <s.i className="size-6" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span
                        className={`block text-[11px] font-extrabold uppercase tracking-wider ${on ? "text-muted-foreground" : "text-white/70"}`}
                      >
                        Section {s.n} · {s.sur}
                      </span>
                      <span className="block font-display text-xl leading-tight">{s.t}</span>
                    </span>
                    <span className={`font-display text-2xl ${on ? "text-logo-blue" : "text-sun"}`}>
                      {n}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      {/* Filtres puis frise des événements, regroupés par mois. */}
      <section className="mx-auto max-w-5xl px-5 py-16">
        <div
          data-reveal
          className="flex flex-wrap items-center gap-3 rounded-[1.75rem] bg-white p-4 shadow-card md:p-5"
        >
          <span className="text-sm font-extrabold">
            {liste.length} événement{liste.length > 1 ? "s" : ""}
            {section && <span className="text-muted-foreground"> · {sections[section].t}</span>}
          </span>
          <span className="ml-auto flex flex-wrap gap-2">
            <select
              aria-label="Région"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className={selectCls}
            >
              <option value="">Toutes les régions</option>
              {regions.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
            <select
              aria-label="Type d’activité"
              value={type}
              onChange={(e) => setType(e.target.value)}
              className={selectCls}
            >
              <option value="">Toutes les activités</option>
              {types.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </span>
        </div>

        {liste.length === 0 && (
          <p className="mt-10 rounded-[1.75rem] border border-dashed p-10 text-center font-semibold text-muted-foreground">
            Aucun événement ne correspond à ces filtres pour le moment.
          </p>
        )}

        {groupes.map((g) => (
          <div key={g.titre} className="mt-12">
            <h2
              data-reveal
              className="flex items-center gap-4 text-3xl capitalize text-logo-blue md:text-4xl"
            >
              {g.titre}
              <span className="h-px flex-1 bg-border" />
            </h2>
            <ol className="relative mt-6 grid gap-5 border-l-2 border-dashed border-logo-blue/20 pl-6 md:pl-10">
              {g.evts.map((e) => {
                const s = sections[e.section];
                const passe = aujourdhui !== "" && e.date < aujourdhui;
                return (
                  <li key={e.t} data-reveal className="relative">
                    <span
                      aria-hidden
                      className="absolute -left-[33px] top-8 size-4 rounded-full ring-4 ring-background md:-left-[49px]"
                      style={{ backgroundColor: passe ? "var(--border)" : s.c }}
                    />
                    <article
                      className={`grid gap-5 rounded-[1.75rem] bg-white p-5 shadow-card ring-1 ring-border transition md:grid-cols-[6rem_1fr] md:p-7 ${passe ? "opacity-70" : ""}`}
                    >
                      <div
                        className="flex flex-row items-baseline gap-2 self-start rounded-2xl px-4 py-3 text-white md:flex-col md:items-center md:gap-0"
                        style={{ backgroundColor: passe ? "var(--muted-foreground)" : s.c }}
                      >
                        <span className="font-display text-4xl leading-none md:text-5xl">
                          {jour(e.date, { day: "numeric" })}
                        </span>
                        <span className="text-sm font-extrabold uppercase">
                          {jour(e.date, { month: "short" })}
                        </span>
                        <span className="text-xs font-semibold capitalize text-white/80">
                          {jour(e.date, { weekday: "long" })}
                        </span>
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className="rounded-full px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-white"
                            style={{ backgroundColor: s.c }}
                          >
                            {s.t}
                          </span>
                          <span className="rounded-full bg-mist px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-logo-blue">
                            {e.type}
                          </span>
                          {aujourdhui && (
                            <span
                              className={`ml-auto text-xs font-extrabold uppercase ${passe ? "text-muted-foreground" : "text-primary"}`}
                            >
                              {passe ? "Terminé" : "Participation ouverte"}
                            </span>
                          )}
                        </div>
                        <h3 className="mt-3 font-sans text-xl font-extrabold leading-snug">
                          {e.t}
                        </h3>
                        <p className="mt-2 font-medium text-muted-foreground">{e.d}</p>
                        <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 border-t pt-4 text-sm font-semibold">
                          <span className="flex items-center gap-1.5">
                            <MapPin className="size-4 text-logo-red" /> {e.lieu}
                          </span>
                          <span className="text-muted-foreground">Région : {e.region}</span>
                          <span className="flex items-center gap-1.5 text-muted-foreground">
                            <Users className="size-4" /> {e.inscrits} inscrits
                          </span>
                          {aujourdhui && !passe && (
                            <a
                              href="/connexion"
                              className="btn-fx ml-auto inline-flex items-center gap-1.5 rounded-full bg-primary px-5 py-2 font-bold text-primary-foreground"
                            >
                              S’inscrire <ArrowRight className="size-4" />
                            </a>
                          )}
                        </div>
                      </div>
                    </article>
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
