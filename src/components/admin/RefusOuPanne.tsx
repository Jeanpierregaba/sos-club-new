import { Link, type ErrorComponentProps } from "@tanstack/react-router";
import { ShieldAlert } from "lucide-react";

import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { ErreurApi } from "@/lib/api/client";

const REFUS = new Set([403, 404, 422]);

// Pour une page d'administration : un refus de l'API (droit, périmètre, double authentification, filtre invalide)
// s'affiche avec son message, à sa place ; seule une vraie panne montre « service indisponible ».
export function RefusOuPanne(props: ErrorComponentProps) {
  const { error } = props;
  if (!(error instanceof ErreurApi) || !REFUS.has(error.statut))
    return <ServiceIndisponible {...props} />;
  return (
    <section
      role="alert"
      className="flex flex-wrap items-start gap-3 rounded-3xl bg-white p-6 ring-1 ring-border"
    >
      <ShieldAlert aria-hidden className="size-6 shrink-0 text-logo-red" />
      <div className="min-w-0 flex-1">
        <p className="font-bold text-ink">{error.message}</p>
        <Link
          to="/admin"
          className="mt-2 inline-flex text-sm font-bold text-primary underline-offset-4 hover:underline"
        >
          Retour à l'administration
        </Link>
      </div>
    </section>
  );
}
