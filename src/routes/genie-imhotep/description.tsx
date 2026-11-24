import { useState, type CSSProperties } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  BookOpen,
  Check,
  ClipboardCheck,
  GraduationCap,
  HeartPulse,
  Lightbulb,
  Mic,
  Scale,
  School,
  ShieldCheck,
  Sparkles,
  Star,
  Stethoscope,
  Timer,
  Trophy,
  Tv,
  Users,
  type LucideIcon,
} from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteMotion, retard } from "@/components/SiteMotion";
import { DecorAnime } from "@/components/DecorAnime";
import mascottesVs from "@/assets/mascottes-vs.webp";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascottesLivres from "@/assets/mascottes-livres.webp";
import slideGenie from "@/assets/slide-genie.jpg";
import grandesFinales from "@/assets/agenda-grandes-finales.jpg";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/genie-imhotep/description")({
  head: () => ({
    meta: [
      { title: m.gi_meta_titre() },
      { name: "description", content: m.gi_meta_description() },
      { property: "og:title", content: m.gi_meta_og() },
    ],
  }),
  component: Description,
});

// Contenus repris du document « Académie Génie Imhotep — présentation » remis par AIMES-AFRIQUE. Des fonctions : les
// textes suivent la langue de la page (spec 052).

const chiffres = () => [
  { n: "+5 000", t: m.gi_chiffre_questions() },
  { n: "11", t: m.gi_chiffre_rubriques() },
  { n: "2", t: m.gi_chiffre_categories() },
  { n: "12", t: m.gi_chiffre_matchs() },
];

const roles = () => [
  m.gi_role_architecte(),
  m.gi_role_ingenieur(),
  m.gi_role_pretre(),
  m.gi_role_ecrivain(),
  m.gi_role_medecin(),
];

const reperes = () => [
  { t: m.gi_repere_1(), d: m.gi_repere_1_d() },
  { t: m.gi_repere_2(), d: m.gi_repere_2_d() },
  { t: m.gi_repere_3(), d: m.gi_repere_3_d() },
  { t: m.gi_repere_4(), d: m.gi_repere_4_d() },
  { t: m.gi_repere_5(), d: m.gi_repere_5_d() },
];

const objectifs = (): { i: LucideIcon; c: string; t: string }[] => [
  { i: BookOpen, c: "var(--logo-blue)", t: m.gi_objectif_1() },
  { i: ShieldCheck, c: "var(--primary)", t: m.gi_objectif_2() },
  { i: Lightbulb, c: "var(--tangerine)", t: m.gi_objectif_3() },
  { i: Trophy, c: "var(--logo-red)", t: m.gi_objectif_4() },
];

const fascicules = () => [
  // Vert assombri : sur le vert du site, le texte blanc et le jaune manqueraient de contraste.
  {
    n: "2 000",
    t: m.gi_questions_reponses(),
    pour: m.gi_secondaire_1(),
    c: "color-mix(in oklch, var(--primary) 70%, black)",
  },
  { n: "3 000", t: m.gi_questions_reponses(), pour: m.gi_secondaire_2(), c: "var(--logo-blue)" },
  { n: "EVSS", t: m.gi_questions_reponses(), pour: m.gi_emission_tv(), c: "var(--grape)" },
];

const conditions = () => [
  m.gi_condition_1(),
  m.gi_condition_2(),
  m.gi_condition_3(),
  m.gi_condition_4(),
];

const acteurs = (): { id: string; i: LucideIcon; t: string; d: string; c: string }[] => [
  { id: "bloc", i: Users, t: m.gi_acteur_bloc(), c: "var(--logo-blue)", d: m.gi_acteur_bloc_d() },
  {
    id: "interne",
    i: Mic,
    t: m.gi_acteur_interne(),
    c: "var(--primary)",
    d: m.gi_acteur_interne_d(),
  },
  {
    id: "staff",
    i: Scale,
    t: m.gi_acteur_staff(),
    c: "var(--tangerine)",
    d: m.gi_acteur_staff_d(),
  },
  {
    id: "patient",
    i: HeartPulse,
    t: m.gi_acteur_patient(),
    c: "var(--logo-red)",
    d: m.gi_acteur_patient_d(),
  },
];

const postes = () => [
  m.gi_poste_chirurgien(),
  m.gi_poste_anesthesiste(),
  m.gi_poste_instrumentiste(),
];

// Les rubriques d'un match, dans l'ordre du parcours du patient.
const rubriques = () => [
  { t: m.gi_rub_1(), p: m.gi_rub_1_p(), pts: m.gi_rub_1_pts() },
  { t: m.gi_rub_2(), p: m.gi_rub_2_p(), pts: m.gi_rub_2_pts() },
  { t: m.gi_rub_3(), p: m.gi_rub_3_p(), pts: m.gi_rub_3_pts() },
  { t: m.gi_rub_4(), p: m.gi_rub_4_p(), pts: m.gi_rub_4_pts() },
  { t: m.gi_rub_5(), p: m.gi_rub_5_p(), pts: m.gi_rub_3_pts() },
  { t: m.gi_rub_6(), p: m.gi_rub_6_p(), pts: m.gi_rub_6_pts() },
  { t: m.gi_rub_7(), p: m.gi_rub_7_p(), pts: "+10" },
  { t: m.gi_rub_8(), p: m.gi_rub_8_p(), pts: m.gi_rub_8_pts() },
  { t: m.gi_rub_9(), p: m.gi_rub_9_p(), pts: m.gi_rub_9_pts() },
  { t: m.gi_rub_10(), p: m.gi_rub_10_p(), pts: "+10" },
  { t: m.gi_rub_11(), p: m.gi_rub_11_p(), pts: m.gi_rub_11_pts() },
];

const regles = (): { i: LucideIcon; t: string; d: string }[] => [
  { i: ClipboardCheck, t: m.gi_regle_score(), d: m.gi_regle_score_d() },
  { i: Sparkles, t: m.gi_regle_public(), d: m.gi_regle_public_d() },
  { i: ShieldCheck, t: m.gi_regle_fairplay(), d: m.gi_regle_fairplay_d() },
  { i: Star, t: m.gi_regle_fiche(), d: m.gi_regle_fiche_d() },
];

const composantes = (): {
  id: string;
  i: LucideIcon;
  t: string;
  c: string;
  ou: string;
  qui: string;
  quand: string;
  but: string;
}[] => [
  {
    id: "interclasses",
    i: School,
    t: m.gi_comp_interclasses(),
    c: "var(--primary)",
    ou: m.gi_comp_interclasses_ou(),
    qui: m.gi_comp_interclasses_qui(),
    quand: m.gi_comp_interclasses_quand(),
    but: m.gi_comp_interclasses_but(),
  },
  {
    id: "championnat",
    i: Trophy,
    t: m.gi_comp_championnat(),
    c: "var(--logo-blue)",
    ou: m.gi_comp_championnat_ou(),
    qui: m.gi_comp_championnat_qui(),
    quand: m.gi_comp_championnat_quand(),
    but: m.gi_comp_championnat_but(),
  },
  {
    id: "emission",
    i: Tv,
    t: m.gi_emission_tv(),
    c: "var(--grape)",
    ou: m.gi_comp_emission_ou(),
    qui: m.gi_comp_emission_qui(),
    quand: m.gi_comp_emission_quand(),
    but: m.gi_comp_emission_but(),
  },
];

const phases = () => [
  { t: m.gi_phase_1(), d: m.gi_phase_1_d() },
  { t: m.gi_phase_2(), d: m.gi_phase_2_d() },
  { t: m.gi_phase_3(), d: m.gi_phase_3_d() },
  { t: m.gi_phase_4(), d: m.gi_phase_4_d() },
  { t: m.gi_phase_5(), d: m.gi_phase_5_d() },
];

const emission = () => [m.gi_emission_1(), m.gi_emission_2(), m.gi_emission_3(), m.gi_emission_4()];

const resume = (): { i: LucideIcon; t: string; d: string }[] => [
  { i: BookOpen, t: m.gi_resume_1(), d: m.gi_resume_1_d() },
  { i: School, t: m.gi_resume_2(), d: m.gi_resume_2_d() },
  { i: Trophy, t: m.gi_resume_3(), d: m.gi_resume_3_d() },
  { i: Tv, t: m.gi_resume_4(), d: m.gi_resume_4_d() },
];

const couleur = (c: string) => ({ "--c": c }) as CSSProperties;

function Description() {
  const [etape, setEtape] = useState(0);
  const listeRubriques = rubriques();
  const rubrique = listeRubriques[etape] ?? listeRubriques[0]!;
  const progression = Math.round(((etape + 1) / listeRubriques.length) * 100);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      {/* Bannière : le nom du jeu et sa devise, les mascottes en duel à droite. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-[oklch(0.58_0.22_300)] via-grape to-[oklch(0.5_0.25_285)] text-white">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_55%)] motion-safe:animate-defile-motif" />
          <div className="absolute -right-40 -top-40 size-[44rem] rounded-full border-[3.5rem] border-white/5 motion-safe:animate-respire" />
          <div className="absolute -bottom-32 right-1/4 size-96 rounded-full bg-sun/20 blur-3xl motion-safe:animate-derive" />
        </div>
        <DecorAnime />

        <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 pt-8 md:pt-12 lg:grid-cols-[1.15fr_1fr]">
          <div className="pb-10 lg:pb-20">
            <FilAriane rubrique={m.menu_genie_imhotep()} page={m.menu_description()} clair />
            <div data-reveal="left" className="pt-10 lg:pt-14">
              <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-bold backdrop-blur-sm">
                <span className="size-2 rounded-full bg-sun" /> {m.gi_axe_1()}
              </p>
              <h1 className="mt-5 text-5xl leading-[0.95] md:text-7xl">
                <span className="block">{m.gi_academie()}</span>
                <span className="block text-sun">Génie Imhotep</span>
              </h1>
              <p className="mt-5 text-xl font-extrabold md:text-2xl">{m.gi_sous_titre()}</p>
              <p className="mt-4 max-w-xl text-lg font-medium text-white/80">{m.gi_intro()}</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href={lien("/genie-imhotep/inscription")}
                  className="btn-fx group flex h-12 items-center gap-2 rounded-full bg-primary px-6 text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  {m.gi_inscrire()}
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </a>
                <a
                  href="#match"
                  className="btn-fx flex h-12 items-center gap-2 rounded-full border-2 border-white/60 bg-white/10 px-6 text-[15px] font-bold backdrop-blur-sm"
                >
                  {m.gi_decouvrir_regles()}
                </a>
              </div>
            </div>
          </div>

          <div
            data-reveal="right"
            className="relative mx-auto w-full max-w-md self-end lg:max-w-xl"
          >
            <img
              src={mascottesVs}
              alt={m.gi_mascottes_alt()}
              width={2000}
              height={2000}
              className="w-full drop-shadow-2xl"
            />
            <p className="absolute left-0 top-6 -rotate-6 rounded-2xl bg-sun px-4 py-2 font-display text-lg leading-tight text-ink shadow-card sm:text-xl">
              {m.gi_devise_1()}
              <br />
              {m.gi_devise_2()}
            </p>
          </div>
        </div>
      </section>

      {/* Chiffres clés, à cheval sur le bas de la bannière. */}
      <section className="relative z-10 mx-auto -mt-10 max-w-6xl px-5">
        <dl
          data-reveal
          className="grid grid-cols-2 gap-px overflow-hidden rounded-3xl bg-border shadow-card ring-4 ring-white md:grid-cols-4"
        >
          {chiffres().map((c) => (
            <div key={c.t} className="flex flex-col-reverse bg-white p-5 text-center md:p-6">
              <dt className="mt-1 text-sm font-bold text-muted-foreground">{c.t}</dt>
              <dd className="font-display text-4xl text-logo-blue md:text-5xl">{c.n}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Qui était Imhotep : le récit à gauche, une fiche de repères à droite. */}
      <section id="imhotep" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
        <div className="grid gap-12 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
          <div>
            <EnTete
              sur={m.gi_origines_sur()}
              bleu={m.gi_origines_bleu()}
              vert={m.gi_origines_vert()}
            />
            <div data-reveal className="mt-6 space-y-4 text-lg leading-relaxed text-ink/80">
              <p>
                {m.gi_recit_1_debut()} <strong className="text-ink">{m.gi_recit_1_sens()}</strong>
                {m.gi_recit_1_fin()}
              </p>
              <p>{m.gi_recit_2()}</p>
            </div>
            <ul data-reveal className="mt-6 flex flex-wrap gap-2">
              {roles().map((r) => (
                <li
                  key={r}
                  className="rounded-full bg-white px-4 py-1.5 text-sm font-extrabold text-logo-blue shadow-sm ring-1 ring-logo-blue/15"
                >
                  {r}
                </li>
              ))}
            </ul>

            <div
              data-reveal
              className="relative mt-10 overflow-hidden rounded-[2rem] bg-[color-mix(in_oklch,var(--sun)_22%,white)] p-6 ring-1 ring-sun/50 md:p-8"
            >
              <Sparkles
                aria-hidden
                className="absolute -right-4 -top-4 size-28 rotate-12 text-sun/60"
              />
              <h3 className="relative text-2xl text-logo-blue md:text-3xl">
                {m.gi_pourquoi_titre()}
              </h3>
              <p className="relative mt-3 font-medium text-ink/80">{m.gi_pourquoi_texte()}</p>
            </div>
          </div>

          <aside
            data-reveal="right"
            className="relative self-start overflow-hidden rounded-[2rem] bg-night p-6 text-white shadow-card md:p-8"
          >
            <div
              aria-hidden
              className="absolute -right-20 -top-20 size-64 rounded-full bg-sun/25 blur-3xl"
            />
            <p className="relative text-sm font-extrabold uppercase tracking-widest text-sun">
              {m.gi_fiche_savant()}
            </p>
            <ol className="relative mt-6 space-y-5 border-l-2 border-dashed border-white/20 pl-6">
              {reperes().map((r) => (
                <li key={r.t} className="relative">
                  <span className="absolute -left-[1.95rem] top-1 size-3.5 rounded-full bg-sun ring-4 ring-night" />
                  <p className="font-display text-lg leading-tight">{r.t}</p>
                  <p className="mt-1 text-sm font-medium text-white/70">{r.d}</p>
                </li>
              ))}
            </ol>
            <img
              src={mascotteImhotep}
              alt=""
              loading="lazy"
              width={1414}
              height={2000}
              className="relative -mb-6 ml-auto mt-4 w-32 md:-mb-8 md:w-40"
            />
          </aside>
        </div>
      </section>

      {/* Place du jeu dans le projet : l'axe 1, les objectifs, le fascicule et les conditions de participation. */}
      <section
        id="projet"
        className="scroll-mt-16 bg-[color-mix(in_oklch,var(--sky)_8%,white)] py-20"
      >
        <div className="mx-auto max-w-7xl px-5">
          <EnTete sur={m.gi_projet_sur()} bleu={m.gi_projet_bleu()} vert={m.gi_projet_vert()}>
            {m.gi_projet_texte()}
          </EnTete>

          <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {objectifs().map((o, i) => (
              <li
                key={o.t}
                data-reveal
                style={{ ...couleur(o.c), ...retard(i) }}
                className="card-fx rounded-3xl border-t-4 border-(--c) bg-white p-6 shadow-card"
              >
                <span className="inline-flex size-12 items-center justify-center rounded-2xl bg-[color-mix(in_oklch,var(--c)_14%,white)] text-(--c)">
                  <o.i className="size-6" />
                </span>
                <p className="mt-4 font-semibold leading-snug">{o.t}</p>
              </li>
            ))}
          </ul>

          <div className="mt-16 grid items-center gap-10 lg:grid-cols-[1fr_1.1fr]">
            <img
              data-reveal="left"
              src={mascottesLivres}
              alt={m.gi_livres_alt()}
              loading="lazy"
              width={1122}
              height={1402}
              className="mx-auto w-full max-w-sm"
            />
            <div>
              <div data-reveal>
                <h3 className="text-3xl md:text-4xl">
                  <span className="text-logo-blue">{m.gi_fascicule_bleu()}</span>{" "}
                  <span className="text-primary">{m.gi_fascicule_vert()}</span>
                </h3>
                <p className="mt-3 text-lg font-medium text-muted-foreground">
                  {m.gi_fascicule_texte()}
                </p>
              </div>
              <ul className="mt-6 grid gap-3 sm:grid-cols-3">
                {fascicules().map((f, i) => (
                  <li
                    key={f.pour}
                    data-reveal
                    style={{ ...couleur(f.c), ...retard(i) }}
                    className="relative overflow-hidden rounded-2xl bg-(--c) p-5 pl-7 text-white shadow-card"
                  >
                    {/* Le dos du livre. */}
                    <span aria-hidden className="absolute inset-y-0 left-0 w-3 bg-black/20" />
                    <p className="font-display text-4xl leading-none">{f.n}</p>
                    <p className="mt-1 text-sm font-bold text-white/85">{f.t}</p>
                    <p className="mt-4 text-xs font-extrabold uppercase tracking-wider text-sun">
                      {f.pour}
                    </p>
                  </li>
                ))}
              </ul>
              <p
                data-reveal
                className="mt-4 flex items-start gap-2 text-sm font-semibold text-muted-foreground"
              >
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
                {m.gi_cellule()}
              </p>
            </div>
          </div>

          {/* Qui peut participer. */}
          <div
            data-reveal
            className="mt-16 grid gap-8 rounded-[2rem] bg-logo-blue p-6 text-white shadow-card md:p-10 lg:grid-cols-[1fr_1.2fr] lg:items-center"
          >
            <div>
              <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
                {m.gi_qui_sur()}
              </p>
              <h3 className="mt-3 text-3xl md:text-4xl">
                {m.gi_qui_titre_1()} <span className="text-sun">{m.gi_qui_titre_2()}</span>
              </h3>
              <p className="mt-4 font-medium text-white/80">
                {m.gi_qui_texte_1()} <strong className="text-white">{m.gi_qui_s1()}</strong>{" "}
                {m.gi_qui_et()} <strong className="text-white">{m.gi_qui_s2()}</strong>.
              </p>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {conditions().map((c) => (
                <li
                  key={c}
                  className="flex items-center gap-3 rounded-2xl border border-white/20 bg-white/10 p-4 font-bold backdrop-blur-sm"
                >
                  <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-primary">
                    <Check className="size-4" />
                  </span>
                  {c}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Comment se joue un match : le principe du patient, puis les acteurs. */}
      <section id="match" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
        <div className="grid items-center gap-10 lg:grid-cols-[1.1fr_1fr]">
          <EnTete sur={m.gi_match_sur()} bleu={m.gi_match_bleu()} vert={m.gi_match_vert()}>
            {m.gi_match_texte()}
          </EnTete>
          <figure data-reveal="right" className="relative">
            <img
              src={slideGenie}
              alt={m.gi_pupitre_alt()}
              loading="lazy"
              width={2000}
              height={1600}
              className="aspect-[4/3] w-full rounded-[2rem] object-cover object-[50%_20%] shadow-card"
            />
            <figcaption className="absolute -bottom-5 left-5 flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-extrabold text-logo-blue shadow-card">
              <Timer className="size-4 text-logo-red" /> {m.gi_chrono()}
            </figcaption>
          </figure>
        </div>

        <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {acteurs().map((a, i) => (
            <li
              key={a.id}
              data-reveal
              style={{ ...couleur(a.c), ...retard(i) }}
              className="card-fx relative overflow-hidden rounded-3xl bg-white p-6 shadow-card"
            >
              <span
                aria-hidden
                className="absolute -right-8 -top-8 size-28 rounded-full bg-[color-mix(in_oklch,var(--c)_14%,white)]"
              />
              <span className="relative inline-flex size-12 items-center justify-center rounded-2xl bg-(--c) text-white">
                <a.i className="size-6" />
              </span>
              <h3 className="relative mt-4 text-2xl text-(--c)">{a.t}</h3>
              <p className="relative mt-2 text-sm font-medium leading-relaxed text-ink/75">{a.d}</p>
              {a.id === "bloc" && (
                <ul className="relative mt-4 flex flex-wrap gap-1.5">
                  {postes().map((p) => (
                    <li
                      key={p}
                      className="rounded-full bg-mist px-2.5 py-1 text-xs font-extrabold text-logo-blue"
                    >
                      {p}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Les rubriques : un parcours de soin à explorer étape par étape. */}
      <section
        id="rubriques"
        className="relative isolate scroll-mt-16 overflow-hidden bg-night py-20 text-white"
      >
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-24 top-10 size-96 rounded-full bg-logo-red/25 blur-3xl" />
          <div className="absolute -right-24 bottom-0 size-96 rounded-full bg-primary/20 blur-3xl" />
        </div>
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur={m.gi_rubriques_sur()}
            bleu={m.gi_rubriques_bleu()}
            vert={m.gi_rubriques_vert()}
            sombre
          >
            {m.gi_rubriques_texte()}
          </EnTete>

          <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
            <ol className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-2">
              {listeRubriques.map((r, i) => {
                const on = i === etape;
                return (
                  <li key={r.t}>
                    <button
                      type="button"
                      aria-pressed={on}
                      onClick={() => setEtape(i)}
                      className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left font-bold transition ${
                        on
                          ? "bg-white text-ink shadow-card"
                          : i < etape
                            ? "bg-primary/20 text-white hover:bg-primary/30"
                            : "bg-white/5 text-white/80 ring-1 ring-white/10 hover:bg-white/10"
                      }`}
                    >
                      <span
                        className={`inline-flex size-8 shrink-0 items-center justify-center rounded-full font-display text-sm ${
                          on
                            ? "bg-logo-red text-white"
                            : i < etape
                              ? "bg-primary text-white"
                              : "bg-white/10"
                        }`}
                      >
                        {i < etape ? <Check className="size-4" /> : i + 1}
                      </span>
                      <span className="leading-tight">{r.t}</span>
                    </button>
                  </li>
                );
              })}
            </ol>

            <div className="relative flex flex-col overflow-hidden rounded-[2rem] bg-white p-6 text-ink shadow-card md:p-8">
              {/* Seule la fiche de l'étape est annoncée, d'un bloc, à chaque changement. */}
              <div aria-live="polite" aria-atomic="true" className="flex flex-col">
                <div className="flex items-center justify-between gap-4">
                  <span className="inline-flex items-center gap-2 rounded-full bg-[color-mix(in_oklch,var(--logo-red)_12%,white)] px-3 py-1 text-xs font-extrabold uppercase tracking-wider text-logo-red">
                    <Stethoscope className="size-3.5" />{" "}
                    {m.gi_etape_sur({
                      numero: String(etape + 1),
                      total: String(listeRubriques.length),
                    })}
                  </span>
                  <HeartPulse
                    aria-hidden
                    className="size-8 text-logo-red motion-safe:animate-pulse"
                  />
                </div>
                <h3
                  key={rubrique.t}
                  className="mt-4 text-4xl text-logo-blue animate-in fade-in md:text-5xl"
                >
                  {rubrique.t}
                </h3>
                <p className="mt-3 text-lg font-medium text-ink/80">{rubrique.p}</p>
                <p className="mt-5 inline-flex self-start rounded-2xl bg-sun px-4 py-2 font-display text-lg text-ink">
                  {rubrique.pts}
                </p>
              </div>

              <div className="mt-auto pt-8">
                <div className="flex items-center justify-between text-sm font-bold text-muted-foreground">
                  <span>{m.gi_rub_1()}</span>
                  <span>{m.gi_sortie()}</span>
                </div>
                <div
                  role="progressbar"
                  aria-label={m.gi_avancee()}
                  aria-valuenow={progression}
                  aria-valuetext={m.gi_avancee_texte({
                    numero: String(etape + 1),
                    total: String(listeRubriques.length),
                    rubrique: rubrique.t,
                  })}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  className="mt-2 h-3 overflow-hidden rounded-full bg-mist"
                >
                  <div
                    className="h-full rounded-full bg-linear-to-r from-logo-red via-sun to-primary transition-[width] duration-500"
                    style={{ width: `${progression}%` }}
                  />
                </div>
                {/* aria-disabled plutôt que disabled : le bouton garde le focus clavier aux deux bouts du parcours. */}
                <div className="mt-5 flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEtape((e) => Math.max(e - 1, 0))}
                    aria-disabled={etape === 0}
                    className="rounded-full border-2 border-border px-5 py-2.5 text-sm font-bold transition hover:border-logo-blue aria-disabled:opacity-40"
                  >
                    {m.gi_etape_precedente()}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEtape((e) => Math.min(e + 1, listeRubriques.length - 1))}
                    aria-disabled={etape === listeRubriques.length - 1}
                    className="btn-fx rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground aria-disabled:opacity-40"
                  >
                    {m.gi_etape_suivante()}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Score, public et fair-play. */}
      <section className="mx-auto max-w-7xl px-5 py-20">
        <EnTete sur={m.gi_pendant_sur()} bleu={m.gi_pendant_bleu()} vert={m.gi_pendant_vert()} />
        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {regles().map((r, i) => (
            <li
              key={r.t}
              data-reveal
              style={retard(i)}
              className="rounded-3xl border bg-white p-6 shadow-sm"
            >
              <r.i className="size-7 text-logo-red" />
              <h3 className="mt-4 text-xl text-logo-blue">{r.t}</h3>
              <p className="mt-2 text-sm font-medium leading-relaxed text-ink/75">{r.d}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Les trois composantes : un tableau en cartes, puis le détail de chacune. */}
      <section
        id="composantes"
        className="scroll-mt-16 bg-[color-mix(in_oklch,var(--sun)_10%,white)] py-20"
      >
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur={m.gi_formes_sur()}
            bleu={m.gi_formes_bleu()}
            vert={m.gi_formes_vert()}
            centre
          >
            {m.gi_formes_texte()}
          </EnTete>

          <ul className="mt-10 grid gap-5 lg:grid-cols-3">
            {composantes().map((c, i) => (
              <li
                key={c.id}
                data-reveal
                style={{ ...couleur(c.c), ...retard(i) }}
                className="card-fx flex flex-col overflow-hidden rounded-[2rem] bg-white shadow-card"
              >
                <a
                  href={`#${c.id}`}
                  className="flex items-center gap-3 bg-(--c) px-6 py-5 text-white"
                >
                  <c.i className="size-7 shrink-0" />
                  <span className="font-display text-2xl leading-tight">{c.t}</span>
                </a>
                <dl className="grid flex-1 gap-4 p-6">
                  {[
                    [m.gi_ou(), c.ou],
                    [m.gi_qui(), c.qui],
                    [m.gi_quand(), c.quand],
                    [m.gi_but(), c.but],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-xs font-extrabold uppercase tracking-widest text-(--c)">
                        {k}
                      </dt>
                      <dd className="mt-0.5 font-semibold leading-snug">{v}</dd>
                    </div>
                  ))}
                </dl>
              </li>
            ))}
          </ul>

          {/* Inter-classes. */}
          <article
            id="interclasses"
            data-reveal
            className="mt-16 scroll-mt-24 rounded-[2rem] bg-white p-6 shadow-card md:p-10"
          >
            <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <School className="size-4" /> {m.gi_niveau_base()}
            </p>
            <h3 className="mt-3 text-3xl md:text-4xl">
              <span className="text-logo-blue">{m.gi_interclasses_bleu()}</span>{" "}
              <span className="text-primary">{m.gi_interclasses_vert()}</span>
            </h3>
            <p className="mt-4 max-w-4xl text-lg font-medium text-ink/80">
              {m.gi_interclasses_texte()}
            </p>
          </article>

          {/* Championnat : les étapes, puis la première édition. */}
          <article
            id="championnat"
            data-reveal
            className="mt-6 scroll-mt-24 overflow-hidden rounded-[2rem] bg-logo-blue text-white shadow-card"
          >
            <div className="p-6 md:p-10">
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-sun">
                <Trophy className="size-4" /> {m.gi_inter_etab()}
              </p>
              <h3 className="mt-3 text-3xl md:text-4xl">
                {m.gi_championnat_1()} <span className="text-sun">{m.gi_championnat_2()}</span>
              </h3>
              <p className="mt-4 max-w-4xl text-lg font-medium text-white/80">
                {m.gi_championnat_texte()}
              </p>
              <ol className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {phases().map((p, i, liste) => (
                  <li
                    key={p.t}
                    className={`relative rounded-2xl p-4 ${
                      i === liste.length - 1
                        ? "bg-sun text-ink"
                        : "border border-white/20 bg-white/10 backdrop-blur-sm"
                    }`}
                  >
                    <span className="font-display text-3xl opacity-60">{i + 1}</span>
                    <p className="mt-1 font-display text-lg leading-tight">{p.t}</p>
                    <p
                      className={`mt-1 text-sm font-medium ${i === liste.length - 1 ? "text-ink/75" : "text-white/75"}`}
                    >
                      {p.d}
                    </p>
                    {i < liste.length - 1 && (
                      <ArrowRight
                        aria-hidden
                        className="absolute -right-3 top-1/2 z-10 hidden size-5 -translate-y-1/2 rounded-full bg-sun p-0.5 text-ink lg:block"
                      />
                    )}
                  </li>
                ))}
              </ol>
            </div>
            <div className="grid lg:grid-cols-[1.2fr_1fr]">
              <img
                src={grandesFinales}
                alt={m.gi_finalistes_alt()}
                loading="lazy"
                width={2000}
                height={963}
                className="aspect-[2/1] size-full object-cover lg:aspect-auto"
              />
              <div className="bg-night p-6 md:p-10">
                <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
                  {m.gi_edition_1()}
                </p>
                <p className="mt-4 font-display text-2xl leading-tight md:text-3xl">
                  {m.gi_champion()}
                </p>
                <p className="mt-4 flex items-center gap-4">
                  <span className="font-display text-5xl text-sun">490</span>
                  <span className="text-sm font-bold uppercase text-white/60">{m.gi_a()}</span>
                  <span className="font-display text-5xl text-white/60">360</span>
                </p>
                <p className="mt-1 text-sm font-medium text-white/70">{m.gi_face_kara()}</p>
                <p className="mt-6 text-sm font-medium text-white/80">{m.gi_international()}</p>
                <a
                  href={lien("/genie-imhotep/hall-of-fame")}
                  className="mt-6 inline-flex items-center gap-2 font-bold text-sun hover:underline"
                >
                  {m.gi_voir_hof()} <ArrowRight className="size-4" />
                </a>
              </div>
            </div>
          </article>

          {/* Émission télévisée. */}
          <article
            id="emission"
            data-reveal
            className="mt-6 grid scroll-mt-24 gap-8 rounded-[2rem] bg-grape p-6 text-white shadow-card md:p-10 lg:grid-cols-[1fr_1.2fr]"
          >
            <div>
              <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-widest text-sun">
                <Tv className="size-4" /> {m.gi_sur_tv()}
              </p>
              <h3 className="mt-3 text-3xl md:text-4xl">
                {m.gi_emission_titre_1()}{" "}
                <span className="text-sun">{m.gi_emission_titre_2()}</span>
              </h3>
              <div className="mt-6 inline-flex items-center gap-4 rounded-2xl bg-white p-4 text-ink shadow-card">
                <span className="text-center">
                  <span className="block font-display text-3xl leading-none text-logo-red">
                    {m.gi_samedi()}
                  </span>
                  <span className="block font-display text-xl text-logo-blue">{m.gi_10h()}</span>
                </span>
                <span className="h-12 w-px bg-border" />
                <span className="text-sm font-bold leading-snug">
                  Studio Prof JAMES
                  <br />
                  <span className="text-muted-foreground">{m.gi_saison()}</span>
                </span>
              </div>
              <p className="mt-6 text-sm font-medium text-white/80">{m.gi_chaine()}</p>
            </div>
            <ul className="grid gap-3">
              {emission().map((e) => (
                <li
                  key={e}
                  className="flex gap-3 rounded-2xl border border-white/20 bg-white/10 p-4 font-medium backdrop-blur-sm"
                >
                  <Star className="mt-0.5 size-5 shrink-0 text-sun" />
                  {e}
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      {/* En résumé : les quatre façons de vivre le jeu, puis la devise. */}
      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue to-night py-20 text-white">
        <div
          aria-hidden
          className="absolute -right-24 -top-24 -z-10 size-96 rounded-full bg-sun/20 blur-3xl"
        />
        <div className="mx-auto max-w-7xl px-5">
          <EnTete
            sur={m.gi_resume_sur()}
            bleu={m.gi_resume_bleu()}
            vert={m.gi_resume_vert()}
            sombre
            centre
          >
            {m.gi_resume_texte()}
          </EnTete>
          <ol className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {resume().map((r, i) => (
              <li
                key={r.t}
                data-reveal
                style={retard(i)}
                className="rounded-3xl border border-white/15 bg-white/10 p-6 text-center backdrop-blur-sm"
              >
                <span className="mx-auto inline-flex size-14 items-center justify-center rounded-2xl bg-sun text-ink">
                  <r.i className="size-7" />
                </span>
                <p className="mt-4 font-display text-2xl leading-tight">{r.t}</p>
                <p className="mt-1 font-medium text-white/75">{r.d}</p>
              </li>
            ))}
          </ol>
          <div data-reveal className="mt-14 text-center">
            <p className="font-display text-3xl text-sun md:text-5xl">{m.gi_devise()}</p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <a
                href={lien("/genie-imhotep/inscription")}
                className="btn-fx group flex h-12 items-center gap-2 rounded-full bg-primary px-6 text-[15px] font-bold text-primary-foreground shadow-card"
              >
                <GraduationCap className="size-5" /> {m.gi_inscrire()}
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
              </a>
              <a
                href={lien("/bibliotheque")}
                className="btn-fx flex h-12 items-center gap-2 rounded-full border-2 border-white/60 bg-white/10 px-6 text-[15px] font-bold backdrop-blur-sm"
              >
                <BookOpen className="size-5" /> {m.gi_reviser()}
              </a>
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
