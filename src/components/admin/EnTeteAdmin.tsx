import type { ReactNode } from "react";

// En-tête d'une page de l'espace admin : surtitre rouge, titre en deux couleurs, actions à droite.
export function EnTeteAdmin({
  sur,
  bleu,
  vert,
  children,
  actions,
}: {
  sur: string;
  bleu: string;
  vert: string;
  children?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl">
        <p className="flex items-center gap-3 text-xs font-extrabold uppercase tracking-widest text-logo-red">
          <span className="h-1 w-6 rounded-full bg-primary" />
          {sur}
        </p>
        <h1 className="mt-2 text-3xl leading-tight md:text-4xl">
          <span className="text-logo-blue">{bleu}</span>{" "}
          <span className="text-primary">{vert}</span>
        </h1>
        {children && <p className="mt-2 font-medium text-muted-foreground">{children}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
