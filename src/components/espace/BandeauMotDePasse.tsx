import { KeyRound } from "lucide-react";

import { Button } from "@/components/ui/button";

// Après une réinitialisation (spec 039) : le mot de passe provisoire est connu de celui qui l'a créé. Le bandeau
// conseille d'en choisir un nouveau, sans rien bloquer.
export function BandeauMotDePasse({ onChanger }: { onChanger: () => void }) {
  return (
    <div
      role="status"
      className="mt-6 flex flex-col gap-4 rounded-3xl bg-sun/25 p-5 ring-1 ring-sun sm:flex-row sm:items-center"
    >
      <KeyRound aria-hidden className="size-6 shrink-0 text-logo-blue" />
      <p className="flex-1 font-semibold text-ink">
        Ton mot de passe a été réinitialisé. Choisis maintenant ton propre mot de passe : tu seras
        la seule personne à le connaître.
      </p>
      <Button onClick={onChanger} className="btn-fx rounded-full font-bold">
        Choisir mon mot de passe
      </Button>
    </div>
  );
}
