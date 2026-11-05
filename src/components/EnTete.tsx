import type { ReactNode } from "react";

// Typographie française : « ? », « ! », « : » et « ; » restent collés au mot précédent (espace fine insécable),
// pour ne jamais partir seuls à la ligne.
const insecable = (texte: string) => texte.replace(/ ([?!:;])/g, "\u202f$1");

// Surtitre rouge en capitales, puis titre en deux couleurs. `sombre` : sur un fond foncé, le titre passe en blanc et jaune.
// `large` : le bloc prend toute la largeur, pour un titre long qui doit tenir sur une ligne.
export function EnTete({
  sur,
  bleu,
  vert,
  children,
  centre = false,
  sombre = false,
  large = false,
}: {
  sur: string;
  bleu: string;
  vert: string;
  children?: ReactNode;
  centre?: boolean;
  sombre?: boolean;
  large?: boolean;
}) {
  return (
    <div
      data-reveal
      className={`${large ? "max-w-5xl" : "max-w-3xl"} ${centre ? "mx-auto text-center" : ""}`}
    >
      <p
        className={`flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest ${sombre ? "text-sun" : "text-logo-red"} ${centre ? "justify-center" : ""}`}
      >
        <span className="h-1 w-8 rounded-full bg-primary" />
        {sur}
      </p>
      <h2 className="mt-3 text-4xl md:text-5xl">
        <span className={sombre ? "text-white" : "text-logo-blue"}>{insecable(bleu)}</span>{" "}
        <span className={sombre ? "text-sun" : "text-primary"}>{insecable(vert)}</span>
      </h2>
      {children && (
        <p
          className={`mt-3 text-lg font-medium ${sombre ? "text-white/80" : "text-muted-foreground"}`}
        >
          {children}
        </p>
      )}
    </div>
  );
}
