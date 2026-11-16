import { MailCheck, Users } from "lucide-react";
import { useState } from "react";

import { PageCompte } from "@/components/comptes/PageCompte";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { demanderLienMotDePasse, ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

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
      setEnvoye((await demanderLienMotDePasse(email.trim())).message);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <PageCompte
      titre="Mot de passe"
      accent="oublié ?"
      intro="Pas de panique : on t'aide à retrouver l'accès à ton compte."
    >
      <section className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4 text-sm font-medium text-ink/80">
        <Users aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-blue" />
        <p>
          <strong>Tu es élève ?</strong> Demande à un encadreur de ton club : il peut te donner un
          nouveau mot de passe depuis son espace.
        </p>
      </section>

      {envoye ? (
        <p role="status" className="mt-6 flex items-start gap-3 font-semibold text-ink">
          <MailCheck aria-hidden className="mt-0.5 size-5 shrink-0 text-leaf" />
          {envoye} Pense à regarder dans tes courriers indésirables.
        </p>
      ) : (
        <form onSubmit={envoyer} className="mt-6 space-y-4">
          <p className="font-bold text-ink">Tu es encadreur ou visiteur ?</p>
          <div className="space-y-1.5">
            <Label htmlFor="email" className="font-bold">
              Ton adresse e-mail
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
            Recevoir un lien
          </Button>
        </form>
      )}
    </PageCompte>
  );
}
