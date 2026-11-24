import aimesAfrique from "@/assets/partenaires/aimes-afrique.webp";
import clubSante from "@/assets/partenaires/club-sante-sos-docteur-tv.webp";
import ministereAdministration from "@/assets/partenaires/ministere-administration-territoriale.webp";
import ministereEducation from "@/assets/partenaires/ministere-education-nationale.webp";
import ministereSante from "@/assets/partenaires/ministere-sante.webp";
import ministereSolidarites from "@/assets/partenaires/ministere-solidarites.webp";
import unfpa from "@/assets/partenaires/unfpa.svg";
import { m } from "@/paraglide/messages.js";

const PARTENAIRES = [
  { src: clubSante, nom: "Club Santé SOS Docteur TV" },
  { src: aimesAfrique, nom: "AIMES-AFRIQUE, Santé et éducation pour tous en Afrique" },
  { src: ministereEducation, nom: "Ministère de l'Éducation nationale" },
  {
    src: ministereSante,
    nom: "Ministère de la Santé, de l'Hygiène publique, de la Couverture sanitaire universelle et des Assurances",
  },
  {
    src: ministereSolidarites,
    nom: "Ministère des Solidarités, du Genre, de la Famille et de la Protection de l'enfance",
  },
  {
    src: ministereAdministration,
    nom: "Ministère de l'Administration territoriale, de la Gouvernance locale et des Affaires culturelles",
  },
  { src: unfpa, nom: "UNFPA, Fonds des Nations unies pour la population" },
];

// Le défilement n'est continu que si une liste dépasse la largeur de l'écran : les logos sont répétés deux fois.
const partenaires = [...PARTENAIRES, ...PARTENAIRES];

function Logos({ masque = false }: { masque?: boolean }) {
  return (
    <ul aria-hidden={masque || undefined} className="flex shrink-0 gap-6 pr-6">
      {partenaires.map((p, i) => (
        <li
          key={`${p.nom}-${i}`}
          aria-hidden={(!masque && i >= PARTENAIRES.length) || undefined}
          className="flex h-40 w-56 items-center justify-center rounded-2xl border bg-white p-2 shadow-sm transition duration-300 hover:scale-105 hover:border-primary"
        >
          <img
            src={p.src}
            alt={p.nom}
            title={p.nom}
            loading="lazy"
            decoding="async"
            className="max-h-full max-w-full object-contain"
          />
        </li>
      ))}
    </ul>
  );
}

export function PartenairesSection() {
  return (
    <section id="partenaires" className="scroll-mt-16 py-20">
      <div data-reveal className="mx-auto max-w-3xl px-5 text-center">
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">{m.partenaires_titre_1()}</span>{" "}
          <span className="text-primary">{m.partenaires_titre_2()}</span>
        </h2>
        <p className="mt-4 text-muted-foreground">{m.partenaires_texte()}</p>
      </div>
      {/* La seconde liste, identique, prend le relais quand la première sort de l'écran. Sans animation, le visiteur fait défiler à la main. */}
      <div
        data-reveal
        className="mt-10 overflow-hidden py-2 [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)] motion-reduce:overflow-x-auto"
      >
        <div className="flex w-max animate-marquee hover:[animation-play-state:paused] motion-reduce:animate-none">
          <Logos />
          <div className="contents motion-reduce:hidden">
            <Logos masque />
          </div>
        </div>
      </div>
    </section>
  );
}
