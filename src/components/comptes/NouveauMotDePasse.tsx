import { Link } from "@tanstack/react-router";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";

import { PageCompte } from "@/components/comptes/PageCompte";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { choisirMotDePasse, ErreurApi } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

const LONGUEUR_MIN = 8;

// Choisir un nouveau mot de passe depuis le lien reçu par e-mail (spec 039) : valable 30 minutes, une seule fois.
export function NouveauMotDePasse({
  jeton,
  valide,
  onFait,
}: {
  jeton: string | undefined;
  valide: boolean;
  onFait?: () => Promise<unknown> | void;
}) {
  const [nouveau, setNouveau] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [fait, setFait] = useState(false);
  const [enCours, setEnCours] = useState(false);

  const envoyer = async (evenement: React.FormEvent) => {
    evenement.preventDefault();
    if (!jeton) return;
    if (nouveau.length < LONGUEUR_MIN) {
      setErreur(m.mdp_trop_court({ nombre: String(LONGUEUR_MIN) }));
      return;
    }
    if (nouveau !== confirmation) {
      setErreur(m.mdp_differents());
      return;
    }
    setErreur(null);
    setEnCours(true);
    try {
      await choisirMotDePasse(jeton, nouveau);
      setFait(true);
      await onFait?.();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : m.erreur_indisponible());
    } finally {
      setEnCours(false);
    }
  };

  return (
    <PageCompte
      titre={m.mdp_nouveau_titre()}
      accent={m.mdp_nouveau_accent()}
      intro={m.mdp_nouveau_intro()}
    >
      {fait ? (
        <div className="space-y-4">
          <p role="status" className="flex items-start gap-3 font-semibold text-ink">
            <CheckCircle2 aria-hidden className="mt-0.5 size-5 shrink-0 text-leaf" />
            {m.mdp_change()}
          </p>
          <Link
            to="/connexion"
            className="btn-fx inline-flex h-11 items-center rounded-full bg-primary px-6 font-bold text-primary-foreground"
          >
            {m.cnx_me_connecter()}
          </Link>
        </div>
      ) : !valide ? (
        <div className="space-y-4">
          <p role="alert" className="font-semibold text-ink">
            {m.mdp_lien_invalide()}
          </p>
          <Link
            to="/mot-de-passe-oublie"
            className="font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            {m.mdp_demander_lien()}
          </Link>
        </div>
      ) : (
        <form onSubmit={envoyer} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="nouveau" className="font-bold">
              {m.mdp_nouveau_label()}
            </Label>
            <Input
              id="nouveau"
              type="password"
              autoComplete="new-password"
              required
              maxLength={256}
              value={nouveau}
              onChange={(e) => setNouveau(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirmation" className="font-bold">
              {m.mdp_repete()}
            </Label>
            <Input
              id="confirmation"
              type="password"
              autoComplete="new-password"
              required
              maxLength={256}
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
            />
          </div>
          {erreur && (
            <p role="alert" className="font-semibold text-logo-red">
              {erreur}
            </p>
          )}
          <Button type="submit" disabled={enCours} className="btn-fx w-full rounded-full font-bold">
            {m.mdp_enregistrer()}
          </Button>
        </form>
      )}
    </PageCompte>
  );
}
