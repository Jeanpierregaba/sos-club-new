import { createFileRoute, Link } from "@tanstack/react-router";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";

import { PageCompte } from "@/components/comptes/PageCompte";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  choisirMotDePasse,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  verifierLienMotDePasse,
} from "@/lib/api/client";

const LONGUEUR_MIN = 8;

export const Route = createFileRoute("/mot-de-passe/nouveau")({
  validateSearch: (search: Record<string, unknown>): { jeton?: string } =>
    typeof search["jeton"] === "string" && /^[A-Za-z0-9_-]{20,100}$/.test(search["jeton"])
      ? { jeton: search["jeton"] }
      : {},
  loaderDeps: ({ search }) => ({ jeton: search.jeton }),
  loader: async ({ deps }) =>
    deps.jeton ? (await verifierLienMotDePasse(deps.jeton)).valide : false,
  head: () => ({
    meta: [
      { title: "Nouveau mot de passe — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
      // Le jeton est dans l'adresse : aucune page suivante ne doit le recevoir.
      { name: "referrer", content: "no-referrer" },
    ],
  }),
  component: NouveauMotDePasse,
});

// Choisir un nouveau mot de passe depuis le lien reçu par e-mail (spec 039) : valable 30 minutes, une seule fois.
function NouveauMotDePasse() {
  const valide = Route.useLoaderData();
  const { jeton } = Route.useSearch();
  const [nouveau, setNouveau] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [fait, setFait] = useState(false);
  const [enCours, setEnCours] = useState(false);

  const envoyer = async (evenement: React.FormEvent) => {
    evenement.preventDefault();
    if (!jeton) return;
    if (nouveau.length < LONGUEUR_MIN) {
      setErreur(`Ton mot de passe doit contenir au moins ${LONGUEUR_MIN} caractères.`);
      return;
    }
    if (nouveau !== confirmation) {
      setErreur("Les deux mots de passe ne sont pas identiques.");
      return;
    }
    setErreur(null);
    setEnCours(true);
    try {
      await choisirMotDePasse(jeton, nouveau);
      setFait(true);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <PageCompte
      titre="Nouveau"
      accent="mot de passe"
      intro="Choisis un mot de passe que tu es seul à connaître."
    >
      {fait ? (
        <div className="space-y-4">
          <p role="status" className="flex items-start gap-3 font-semibold text-ink">
            <CheckCircle2 aria-hidden className="mt-0.5 size-5 shrink-0 text-leaf" />
            Ton mot de passe est changé. Tes autres connexions ont été fermées.
          </p>
          <Link
            to="/connexion"
            className="btn-fx inline-flex h-11 items-center rounded-full bg-primary px-6 font-bold text-primary-foreground"
          >
            Me connecter
          </Link>
        </div>
      ) : !valide ? (
        <div className="space-y-4">
          <p role="alert" className="font-semibold text-ink">
            Ce lien a expiré ou a déjà servi. Un lien n'est valable que 30 minutes, une seule fois.
          </p>
          <Link
            to="/mot-de-passe-oublie"
            className="font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            Demander un nouveau lien
          </Link>
        </div>
      ) : (
        <form onSubmit={envoyer} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="nouveau" className="font-bold">
              Nouveau mot de passe
            </Label>
            <Input
              id="nouveau"
              type="password"
              autoComplete="new-password"
              required
              maxLength={128}
              value={nouveau}
              onChange={(e) => setNouveau(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirmation" className="font-bold">
              Répète-le
            </Label>
            <Input
              id="confirmation"
              type="password"
              autoComplete="new-password"
              required
              maxLength={128}
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
            Enregistrer
          </Button>
        </form>
      )}
    </PageCompte>
  );
}
