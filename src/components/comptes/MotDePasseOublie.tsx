import { MailCheck, Users } from "lucide-react";
import { useState } from "react";

import { PageCompte } from "@/components/comptes/PageCompte";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { demanderLienMotDePasse, ErreurApi } from "@/lib/api/client";
import { traduireMessageApi } from "@/lib/erreurs";
import { m } from "@/paraglide/messages.js";

// Mot de passe oublié (spec 039) : l'élève passe par un encadreur de son club ; l'encadreur et le visiteur reçoivent
// un lien par e-mail. La réponse est la même que l'adresse corresponde à un compte ou non.
export function MotDePasseOublie() {
  const [email, setEmail] = useState("");
  const [envoye, setEnvoye] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const envoyer = async (evenement: React.FormEvent) => {
    evenement.preventDefault();
    setErreur(null);
    setEnCours(true);
    try {
      setEnvoye(traduireMessageApi((await demanderLienMotDePasse(email.trim())).message));
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : m.erreur_indisponible());
    } finally {
      setEnCours(false);
    }
  };

  return (
    <PageCompte
      titre={m.mdp_oublie_titre()}
      accent={m.mdp_oublie_accent()}
      intro={m.mdp_oublie_intro()}
    >
      <section className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4 text-sm font-medium text-ink/80">
        <Users aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-blue" />
        <p>
          <strong>{m.mdp_eleve_titre()}</strong> {m.mdp_eleve_texte()}
        </p>
      </section>

      {envoye ? (
        <p role="status" className="mt-6 flex items-start gap-3 font-semibold text-ink">
          <MailCheck aria-hidden className="mt-0.5 size-5 shrink-0 text-leaf" />
          {envoye} {m.mdp_indesirables()}
        </p>
      ) : (
        <form onSubmit={envoyer} className="mt-6 space-y-4">
          <p className="font-bold text-ink">{m.mdp_encadreur_visiteur()}</p>
          <div className="space-y-1.5">
            <Label htmlFor="email" className="font-bold">
              {m.mdp_ton_email()}
            </Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              maxLength={254}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          {erreur && (
            <p role="alert" className="font-semibold text-logo-red">
              {erreur}
            </p>
          )}
          <Button type="submit" disabled={enCours} className="btn-fx w-full rounded-full font-bold">
            {m.mdp_recevoir()}
          </Button>
        </form>
      )}
    </PageCompte>
  );
}
