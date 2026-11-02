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

const titres = [
  { i: Stethoscope, a: "Médecin spécialiste en", t: "Médecine interne" },
  { i: GraduationCap, a: "Diplômé en", t: "Éducation pour la santé" },
  { i: Newspaper, a: "Diplômé en", t: "Journalisme médical" },
  { i: Globe, a: "Diplômé en", t: "Diplomatie de la santé" },
];

const fonctions = [
  {
    i: HeartHandshake,
    role: "Président Fondateur",
    org: "AIMES-AFRIQUE",
    tag: "ONG humanitaire",
    c: "bg-tangerine",
  },
  {
    i: Tv,
    role: "Directeur Général",
    org: "SOS DOCTEUR TV",
    tag: "1ère télévision santé Afrique",
    c: "bg-primary",
  },
  {
    i: Hospital,
    role: "Directeur Général",
    org: "Clinique Internationale Dr KODOM – Lomé",
    tag: "Pôle médical",
    c: "bg-logo-blue",
  },
];

// Adresse et liens à renseigner : ils pointent vers « # » en attendant.
const reseaux = [
  { i: Mail, t: "Mail", href: "#" },
  { i: Facebook, t: "Facebook", href: "#" },
  { i: TikTokIcon, t: "TikTok", href: "#" },
];

export function InitiateurSection() {
  return (
    <section id="initiateur" className="mx-auto max-w-7xl scroll-mt-16 px-5 py-20">
      <div data-reveal className="mx-auto max-w-3xl text-center">
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">L’Initiateur</span>{" "}
          <span className="text-primary">du Projet</span>
        </h2>
        <p className="mt-4 text-muted-foreground">
          L’engagement médical, humanitaire et pédagogique au cœur du déploiement national des Clubs
          Santé SOS DOCTEUR TV à travers tous les établissements scolaires du Togo.
        </p>
      </div>

      <div
        data-reveal
        className="mt-10 grid overflow-hidden rounded-[2rem] bg-logo-blue text-primary-foreground shadow-card lg:grid-cols-[2fr_3fr]"
      >
        {/* Le fond bleu de la photo se fond dans le panneau : vers le bas sur mobile, vers la droite à partir de lg. */}
        <div className="relative aspect-[4/5] lg:aspect-auto">
          <img
            src={photo}
            alt="Prof Honoraire Dr KODOM Serge Michel en blouse blanche, un stéthoscope autour du cou"
            loading="lazy"
            width={1097}
            height={1434}
            className="absolute inset-0 h-full w-full object-cover object-top"
          />
          <div className="absolute inset-0 bg-linear-to-b from-transparent from-70% to-logo-blue lg:bg-linear-to-r lg:from-75%" />
        </div>

        <div className="min-w-0 p-6 pb-20 md:p-10 md:pb-24 lg:pl-6">
          <h3 className="text-3xl md:text-4xl">Prof Honoraire Dr KODOM Serge Michel</h3>
          <p className="mt-4 md:text-lg">
            Pionnier de la santé communautaire et de la télémédecine en Afrique, le Prof. Hon. Dr
            KODOM Serge Michel consacre son engagement au service de l’éducation sanitaire des
            élèves et de l’autonomie citoyenne de la jeunesse togolaise.
          </p>

          <p className="mt-6 text-sm font-extrabold uppercase text-sun">
            Titres honorifiques & spécialités médicales
          </p>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {titres.map((x) => (
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
            {reseaux.map((r) => (
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
          Gouvernance & hautes fonctions
        </p>
        <ol className="mt-3 grid gap-4 md:grid-cols-3">
          {fonctions.map((f, i) => (
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
