import type { ReactNode } from "react";

// Surtitre rouge en capitales, puis titre en deux couleurs. `sombre` : sur un fond foncé, le titre passe en blanc et jaune.
export function EnTete({
  sur,
  bleu,
  vert,
  children,
  centre = false,
  sombre = false,
}: {
  sur: string;
  bleu: string;
  vert: string;
  children?: ReactNode;
  centre?: boolean;
  sombre?: boolean;
}) {
  return (
    <div data-reveal className={centre ? "mx-auto max-w-3xl text-center" : "max-w-3xl"}>
      <p
        className={`flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest ${sombre ? "text-sun" : "text-logo-red"} ${centre ? "justify-center" : ""}`}
      >
        <span className="h-1 w-8 rounded-full bg-primary" />
        {sur}
      </p>
      <h2 className="mt-3 text-4xl md:text-5xl">
        <span className={sombre ? "text-white" : "text-logo-blue"}>{bleu}</span>{" "}
        <span className={sombre ? "text-sun" : "text-primary"}>{vert}</span>
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
