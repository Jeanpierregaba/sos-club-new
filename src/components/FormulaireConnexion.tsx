import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ChampCode } from "@/components/admin/ChampCode";
import { ConfirmationEmail } from "@/components/inscription/ConfirmationEmail";
import { connecter, connecterAvecCode, ErreurApi, type Moi } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

// Une fonction : les messages de validation suivent la langue de la page (spec 052).
const schema = () =>
  z.object({
    identifiant: z
      .string()
      .trim()
      .min(1, m.cnx_identifiant_requis())
      .max(254, m.cnx_identifiant_long()),
    motDePasse: z.string().min(1, m.cnx_mdp_requis()).max(256, m.cnx_mdp_long()),
  });

export function FormulaireConnexion({ onConnecte }: { onConnecte: (moi: Moi) => void }) {
  // Jeton de l'étape « code » : le mot de passe était juste, la double authentification est active.
  const [etape, setEtape] = useState<string | null>(null);
  // Visiteur au bon mot de passe, adresse non confirmée (spec 030) : un code vient de partir.
  const [confirmation, setConfirmation] = useState<{ email: string; test: string | null } | null>(
    null,
  );
  const [erreur, setErreur] = useState<string | null>(null);
  const [afficher, setAfficher] = useState(false);
  const form = useForm<z.infer<ReturnType<typeof schema>>>({
    resolver: zodResolver(schema()),
    defaultValues: { identifiant: "", motDePasse: "" },
  });

  const envoyer = form.handleSubmit(async ({ identifiant, motDePasse }) => {
    setErreur(null);
    try {
      const reponse = await connecter(identifiant, motDePasse);
      if (!("etape" in reponse)) onConnecte(reponse);
      else if (reponse.etape === "code") setEtape(reponse.jeton);
      else setConfirmation({ email: reponse.email, test: reponse.code_de_test ?? null });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : m.erreur_indisponible());
    }
  });
  const enCours = form.formState.isSubmitting;

  if (confirmation) {
    return (
      <ConfirmationEmail
        email={confirmation.email}
        codeDeTest={confirmation.test}
        onConfirme={onConnecte}
        onRetour={() => {
          setConfirmation(null);
          form.resetField("motDePasse");
        }}
      />
    );
  }

  if (etape) {
    return (
      <EtapeCode
        jeton={etape}
        onConnecte={onConnecte}
        onRetour={(message) => {
          setEtape(null);
          setErreur(message);
          form.resetField("motDePasse");
        }}
      />
    );
  }

  return (
    <Form {...form}>
      <form onSubmit={envoyer} noValidate className="space-y-5">
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        <FormField
          control={form.control}
          name="identifiant"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{m.cnx_identifiant()}</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  autoComplete="username"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  className="h-12 text-base"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="motDePasse"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{m.cnx_mdp()}</FormLabel>
              <div className="relative">
                <FormControl>
                  <Input
                    {...field}
                    type={afficher ? "text" : "password"}
                    autoComplete="current-password"
                    className="h-12 pr-12 text-base"
                  />
                </FormControl>
                <button
                  type="button"
                  onClick={() => setAfficher((valeur) => !valeur)}
                  aria-pressed={afficher}
                  aria-label={afficher ? m.cnx_masquer() : m.cnx_afficher()}
                  className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-md text-muted-foreground transition hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {afficher ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          type="submit"
          disabled={enCours}
          className="btn-fx h-12 w-full rounded-full text-base font-bold"
        >
          {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
          {m.cnx_me_connecter()}
        </Button>
      </form>
    </Form>
  );
}

// Seconde étape : le code à 6 chiffres de l'application, ou un code de secours.
function EtapeCode({
  jeton,
  onConnecte,
  onRetour,
}: {
  jeton: string;
  onConnecte: (moi: Moi) => void;
  onRetour: (message: string | null) => void;
}) {
  const [code, setCode] = useState("");
  const [secours, setSecours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const verifier = async (saisie: string) => {
    if (enCours || !saisie.trim()) return;
    setErreur(null);
    setEnCours(true);
    try {
      onConnecte(await connecterAvecCode(jeton, saisie));
    } catch (e) {
      const message = e instanceof ErreurApi ? e.message : m.erreur_indisponible();
      // Délai dépassé : il faut reprendre depuis le mot de passe.
      if (e instanceof ErreurApi && e.statut === 401 && message === m.erreur_delai_depasse()) {
        onRetour(message);
        return;
      }
      setErreur(message);
      setCode("");
      setEnCours(false);
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
        <ShieldCheck aria-hidden className="mt-0.5 size-5 shrink-0 text-primary" />
        <p className="text-sm font-medium text-ink/80">
          {secours ? m.cnx_code_secours_aide() : m.cnx_code_app_aide()}
        </p>
      </div>
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      {secours ? (
        <div className="space-y-2">
          <label htmlFor="code-secours" className="text-sm font-medium">
            {m.cnx_code_secours()}
          </label>
          <Input
            id="code-secours"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
            placeholder="xxxx-xxxx-xxxx-xxxx"
            className="h-12 font-mono text-base"
          />
        </div>
      ) : (
        <div className="space-y-2">
          <label htmlFor="code-application" className="block text-center text-sm font-medium">
            {m.cnx_code_verification()}
          </label>
          <ChampCode
            id="code-application"
            valeur={code}
            onChange={setCode}
            onComplet={(valeur) => void verifier(valeur)}
            desactive={enCours}
          />
        </div>
      )}
      <Button
        type="submit"
        disabled={enCours}
        className="btn-fx h-12 w-full rounded-full text-base font-bold"
      >
        {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
        {m.cnx_verifier()}
      </Button>
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm font-bold">
        <button
          type="button"
          onClick={() => onRetour(null)}
          className="inline-flex items-center gap-1 text-muted-foreground hover:text-ink"
        >
          <ArrowLeft className="size-4" /> {m.cnx_retour()}
        </button>
        <button
          type="button"
          onClick={() => {
            setSecours(!secours);
            setCode("");
            setErreur(null);
          }}
          className="text-logo-blue underline-offset-4 hover:underline"
        >
          {secours ? m.cnx_utiliser_app() : m.cnx_utiliser_secours()}
        </button>
      </div>
    </form>
  );
}
