import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
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
import { connecter, ErreurApi, MESSAGE_INDISPONIBLE, type Moi } from "@/lib/api/client";

const schema = z.object({
  identifiant: z
    .string()
    .trim()
    .min(1, "Indique ton identifiant ou ton email.")
    .max(254, "Cet identifiant est trop long."),
  motDePasse: z
    .string()
    .min(1, "Indique ton mot de passe.")
    .max(256, "Ce mot de passe est trop long."),
});

export function FormulaireConnexion({ onConnecte }: { onConnecte: (moi: Moi) => void }) {
  const [erreur, setErreur] = useState<string | null>(null);
  const [afficher, setAfficher] = useState(false);
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { identifiant: "", motDePasse: "" },
  });

  const envoyer = form.handleSubmit(async ({ identifiant, motDePasse }) => {
    setErreur(null);
    try {
      onConnecte(await connecter(identifiant, motDePasse));
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    }
  });
  const enCours = form.formState.isSubmitting;

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
              <FormLabel>Identifiant ou email</FormLabel>
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
              <FormLabel>Mot de passe</FormLabel>
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
                  aria-label={afficher ? "Masquer le mot de passe" : "Afficher le mot de passe"}
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
          Me connecter
        </Button>
      </form>
    </Form>
  );
}
