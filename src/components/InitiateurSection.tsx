import {
  Facebook,
  Globe,
  GraduationCap,
  HeartHandshake,
  Hospital,
  Mail,
  Newspaper,
  Stethoscope,
  Tv,
} from "lucide-react";
import { retard } from "@/components/SiteMotion";
import { TikTokIcon } from "@/components/TikTokIcon";
import photo from "@/assets/initiateur-kodom.webp";
import { m } from "@/paraglide/messages.js";

// Des fonctions : les textes suivent la langue de la page.
const titres = () => [
  { i: Stethoscope, a: m.initiateur_titre_specialiste(), t: m.initiateur_titre_medecine_interne() },
  { i: GraduationCap, a: m.initiateur_diplome_en(), t: m.initiateur_titre_education_sante() },
  { i: Newspaper, a: m.initiateur_diplome_en(), t: m.initiateur_titre_journalisme() },
  { i: Globe, a: m.initiateur_diplome_en(), t: m.initiateur_titre_diplomatie() },
];

const fonctions = () => [
  {
    i: HeartHandshake,
    role: m.initiateur_role_president(),
    org: "AIMES-AFRIQUE",
    tag: m.initiateur_tag_ong(),
    c: "bg-tangerine",
  },
  {
    i: Tv,
    role: m.initiateur_role_directeur(),
    org: "SOS DOCTEUR TV",
    tag: m.initiateur_tag_tv(),
    c: "bg-primary",
  },
  {
    i: Hospital,
    role: m.initiateur_role_directeur(),
    org: "Clinique Internationale Dr KODOM – Lomé",
    tag: m.initiateur_tag_medical(),
    c: "bg-logo-blue",
  },
];

// Adresse et liens à renseigner : ils pointent vers « # » en attendant.
const reseaux = () => [
  { i: Mail, t: m.initiateur_mail(), href: "#" },
  { i: Facebook, t: "Facebook", href: "#" },
  { i: TikTokIcon, t: "TikTok", href: "#" },
];

export function InitiateurSection() {
  return (
    <section id="initiateur" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
      <div data-reveal className="mx-auto max-w-3xl text-center">
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">{m.initiateur_bloc_titre_1()}</span>{" "}
          <span className="text-primary">{m.initiateur_bloc_titre_2()}</span>
        </h2>
        <p className="mt-4 text-muted-foreground">{m.initiateur_bloc_texte()}</p>
      </div>

      <div
        data-reveal
        className="mt-10 grid overflow-hidden rounded-[2rem] bg-logo-blue text-primary-foreground shadow-card lg:grid-cols-[2fr_3fr]"
      >
        {/* Le fond bleu de la photo se fond dans le panneau : vers le bas sur mobile, vers la droite à partir de lg. */}
        <div className="relative aspect-[4/5] lg:aspect-auto">
          <img
            src={photo}
            alt={m.initiateur_photo()}
            loading="lazy"
            width={1097}
            height={1434}
            className="absolute inset-0 h-full w-full object-cover object-top"
          />
          <div className="absolute inset-0 bg-linear-to-b from-transparent from-70% to-logo-blue lg:bg-linear-to-r lg:from-75%" />
        </div>

        <div className="min-w-0 p-6 pb-20 md:p-10 md:pb-24 lg:pl-6">
          <h3 className="text-3xl md:text-4xl">{m.initiateur_nom()}</h3>
          <p className="mt-4 md:text-lg">{m.initiateur_presentation()}</p>

          <p className="mt-6 text-sm font-extrabold uppercase text-sun">{m.initiateur_titres()}</p>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {titres().map((x) => (
              <li
                key={x.t}
                className="group flex items-center gap-3 rounded-2xl border border-white/20 bg-white/10 p-3 transition duration-300 hover:bg-white/20"
              >
                <x.i className="h-6 w-6 shrink-0 text-sun transition duration-300 group-hover:-rotate-6 group-hover:scale-110" />
                <span className="min-w-0">
                  <span className="block text-xs font-medium">{x.a}</span>
                  <span className="block font-extrabold leading-tight">{x.t}</span>
                </span>
              </li>
            ))}
          </ul>

          <ul className="mt-6 flex gap-3 sm:gap-6">
            {reseaux().map((r) => (
              <li key={r.t}>
                <a
                  href={r.href}
                  className="group inline-flex items-center gap-1.5 text-sm font-bold sm:gap-3 sm:text-base"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary transition group-hover:scale-105 sm:h-11 sm:w-11">
                    <r.i className="h-4 w-4 sm:h-5 sm:w-5" />
                  </span>
                  {/* Sous 375 px, les trois libellés ne tiennent plus sur une ligne : seules les icônes restent visibles. */}
                  <span className="sr-only min-[375px]:not-sr-only">{r.t}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Les fonctions chevauchent le bas du panneau. */}
      <div className="relative -mt-14 px-3 md:px-8">
        <p className="mx-auto w-fit rounded-full bg-sun px-4 py-1.5 text-center text-xs font-extrabold uppercase text-ink">
          {m.initiateur_fonctions()}
        </p>
        <ol className="mt-3 grid gap-4 md:grid-cols-3">
          {fonctions().map((f, i) => (
            <li
              key={f.org}
              data-reveal
              style={retard(i)}
              className="card-fx flex flex-col items-start rounded-2xl bg-card p-5 shadow-card"
            >
              <span
                className={`${f.c} flex h-11 w-11 items-center justify-center rounded-full text-primary-foreground`}
              >
                <f.i className="h-5 w-5" />
              </span>
              <p className="mt-3 text-xs font-bold uppercase text-muted-foreground">{f.role}</p>
              <p className="mt-0.5 mb-3 flex-1 font-display text-xl leading-tight text-logo-blue">
                {f.org}
              </p>
              <span className="rounded-full bg-mist px-2.5 py-0.5 text-xs font-bold text-logo-blue">
                {f.tag}
              </span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
