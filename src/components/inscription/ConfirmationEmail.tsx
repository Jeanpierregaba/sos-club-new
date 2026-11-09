import { ArrowLeft, Loader2, MailCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { ChampCode } from "@/components/admin/ChampCode";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  confirmerEmail,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  renvoyerCode,
  type Moi,
} from "@/lib/api/client";

// Un nouveau code ne part qu'une fois par minute (spec 030).
const ATTENTE_SECONDES = 60;

// La saisie du code reçu par e-mail : après l'inscription d'un visiteur, ou à sa connexion s'il n'a pas
// encore confirmé son adresse (spec 030).
export function ConfirmationEmail({
  email,
  codeDeTest,
  onConfirme,
  onRetour,
  retour = "Retour",
}: {
  email: string;
  codeDeTest?: string | null | undefined;
  onConfirme: (moi: Moi) => void;
  onRetour?: () => void;
  retour?: string;
}) {
  const [code, setCode] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [attente, setAttente] = useState(ATTENTE_SECONDES);
  const [test, setTest] = useState(codeDeTest ?? null);

  useEffect(() => {
    if (attente <= 0) return;
    const minuteur = setTimeout(() => setAttente((s) => s - 1), 1000);
    return () => clearTimeout(minuteur);
  }, [attente]);

  const verifier = async (saisie: string) => {
    if (enCours || saisie.length < 6) return;
    setErreur(null);
    setEnCours(true);
    try {
      onConfirme(await confirmerEmail(email, saisie));
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      setCode("");
      setEnCours(false);
    }
  };

  const renvoyer = async () => {
    setErreur(null);
    setAttente(ATTENTE_SECONDES);
    try {
      const reponse = await renvoyerCode(email);
      setTest(reponse.code_de_test ?? null);
      setInfo("Si ton adresse attend une confirmation, un nouveau code vient de partir.");
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    }
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void verifier(code);
      }}
      className="space-y-5"
    >
      <div className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4">
        <MailCheck aria-hidden className="mt-0.5 size-5 shrink-0 text-primary" />
        <p className="text-sm font-medium text-ink/80">
          Nous t'avons envoyé un code à 6 chiffres à <strong className="text-ink">{email}</strong>.
          Il est valable 15 minutes. Regarde aussi dans tes courriers indésirables.
        </p>
      </div>
      {test && (
        <p className="rounded-2xl border-2 border-dashed border-sun p-3 text-center text-sm font-bold text-ink">
          Contenu de test — e-mail non envoyé en local. Code :{" "}
          <span className="font-mono">{test}</span>
        </p>
      )}
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      {info && !erreur && (
        <p role="status" className="text-center text-sm font-semibold text-muted-foreground">
          {info}
        </p>
      )}
      <div className="space-y-2">
        <label htmlFor="code-email" className="block text-center text-sm font-medium">
          Code de confirmation
        </label>
        <ChampCode
          id="code-email"
          valeur={code}
          onChange={setCode}
          onComplet={(valeur) => void verifier(valeur)}
          desactive={enCours}
        />
      </div>
      <Button
        type="submit"
        disabled={enCours || code.length < 6}
        className="btn-fx h-12 w-full rounded-full text-base font-bold"
      >
        {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
        Confirmer mon adresse
      </Button>
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm font-bold">
        {onRetour ? (
          <button
            type="button"
            onClick={onRetour}
            className="inline-flex items-center gap-1 text-muted-foreground hover:text-ink"
          >
            <ArrowLeft className="size-4" /> {retour}
          </button>
        ) : (
          <span />
        )}
        <button
          type="button"
          disabled={attente > 0}
          onClick={() => void renvoyer()}
          className="text-logo-blue underline-offset-4 hover:underline disabled:cursor-not-allowed disabled:text-muted-foreground disabled:no-underline"
        >
          {attente > 0 ? `Renvoyer un code (${attente} s)` : "Renvoyer un code"}
        </button>
      </div>
    </form>
  );
}
