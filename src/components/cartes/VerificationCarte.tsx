import { BadgeCheck, ShieldAlert } from "lucide-react";

import type { VerificationCarte as Verification } from "@/lib/api/client";
import { TYPES_CARTE } from "@/lib/cartes";
import { dateHeure } from "@/lib/dates";

// Le résultat de la vérification d'une carte par son QR (spec 040, Q30) : type, numéro, club et statut. Aucun nom.
export function VerificationCarte({ resultat }: { resultat: Verification | null }) {
  if (resultat === null) {
    return (
      <section
        aria-live="polite"
        className="rounded-3xl bg-white p-6 shadow-card ring-2 ring-logo-red/40 sm:p-8"
      >
        <p className="flex items-center gap-3 font-display text-3xl text-ink">
          <ShieldAlert aria-hidden className="size-10 shrink-0 text-logo-red" />
          Cette carte n'existe pas
        </p>
        <p className="mt-3 text-muted-foreground">
          Ce QR code ne correspond à aucune carte des Clubs Santé : ne la considère pas comme
          valide.
        </p>
      </section>
    );
  }
  const { valide } = resultat;
  return (
    <section
      aria-live="polite"
      className={`rounded-3xl bg-white p-6 shadow-card ring-2 sm:p-8 ${valide ? "ring-primary" : "ring-logo-red/40"}`}
    >
      <p className="flex items-center gap-3">
        {valide ? (
          <BadgeCheck aria-hidden className="size-12 shrink-0 text-primary" />
        ) : (
          <ShieldAlert aria-hidden className="size-12 shrink-0 text-logo-red" />
        )}
        <span
          className={`font-display text-4xl ${valide ? "text-primary" : "text-logo-red"}`}
          data-testid="statut-carte"
        >
          {valide ? "Valide" : "Non valide"}
        </span>
      </p>
      <p className="mt-3 text-muted-foreground">
        {valide
          ? "Cette carte a bien été délivrée par la plateforme des Clubs Santé et elle est valide aujourd'hui."
          : "Cette carte n'est pas valide aujourd'hui : elle n'atteste plus l'appartenance aux Clubs Santé."}
      </p>
      <dl className="mt-6 grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-sm text-muted-foreground">Type</dt>
          <dd className="font-bold text-ink">{TYPES_CARTE[resultat.type]}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Numéro</dt>
          <dd className="font-mono font-bold text-ink">{resultat.numero}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Club</dt>
          <dd className="font-bold text-ink">{resultat.club ?? "Non affilié"}</dd>
        </div>
      </dl>
      <p className="mt-6 text-xs text-muted-foreground">
        Vérifiée le {dateHeure(resultat.verifiee_le)}
      </p>
    </section>
  );
}
