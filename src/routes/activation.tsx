import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";

import logo from "@/assets/logo.webp";
import mascottesEquipe from "@/assets/mascottes-equipe.webp";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CLE_MOI } from "@/hooks/use-moi";
import {
  activerInvitation,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  voirInvitation,
  type ActivationInfo,
} from "@/lib/api/client";

export const Route = createFileRoute("/activation")({
  validateSearch: (s: Record<string, unknown>): { jeton?: string } =>
    typeof s["jeton"] === "string" ? { jeton: s["jeton"] } : {},
  loaderDeps: ({ search }) => ({ jeton: search.jeton }),
  // Lien inconnu, déjà utilisé ou expiré : la page l'explique au lieu d'afficher une erreur.
  loader: async ({ deps }): Promise<ActivationInfo | { invalide: string }> => {
    if (!deps.jeton) return { invalide: "Ce lien d'invitation est incomplet." };
    try {
      return await voirInvitation(deps.jeton);
    } catch (e) {
      return { invalide: e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE };
    }
  },
  gcTime: 0,
  head: () => ({
    meta: [
      { title: "Activer mon compte — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
      // Le jeton est dans l'adresse : il ne doit pas partir vers un autre site.
      { name: "referrer", content: "no-referrer" },
    ],
  }),
  component: Activation,
});

function Activation() {
  const info = Route.useLoaderData();
  const { jeton } = Route.useSearch();

  return (
    <main className="grid min-h-screen bg-carnet lg:grid-cols-[1fr_1.05fr]">
      <section className="flex flex-col items-center justify-center px-4 py-10 sm:px-8">
        <Link to="/" aria-label="Retour à l'accueil" className="transition hover:scale-105">
          <img
            src={logo}
            alt="Club Santé SOS Docteur TV"
            width={1014}
            height={195}
            className="h-11 w-auto"
          />
        </Link>
        <div className="mt-8 w-full max-w-md">
          {"invalide" in info ? (
            <div className="rounded-3xl bg-white p-6 text-center shadow-card ring-1 ring-border sm:p-8">
              <h1 className="text-3xl text-logo-blue">
                Lien <span className="text-primary">invalide</span>
              </h1>
              <p className="mt-3 font-medium text-muted-foreground">{info.invalide}</p>
              <Link to="/" className="mt-6 inline-block font-bold text-logo-blue hover:underline">
                Retour à l'accueil
              </Link>
            </div>
          ) : (
            <FormulaireActivation info={info} jeton={jeton ?? ""} />
          )}
        </div>
      </section>
      <section className="relative isolate hidden overflow-hidden bg-linear-to-br from-logo-blue to-night p-12 text-white lg:flex lg:flex-col lg:justify-center">
        <div
          aria-hidden
          className="absolute -right-40 -top-40 -z-10 size-[36rem] rounded-full border-[3rem] border-white/5"
        />
        <p className="font-display text-5xl leading-[0.95]">
          <span className="block">Bienvenue dans</span>
          <span className="block text-sun">l'espace admin</span>
        </p>
        <p className="mt-6 max-w-md text-lg font-medium text-white/80">
          Tu rejoins l'équipe qui fait vivre les Clubs Santé SOS Docteur TV partout au Togo.
        </p>
        <img
          src={mascottesEquipe}
          alt=""
          width={1122}
          height={1402}
          className="mx-auto mt-10 w-full max-w-xs drop-shadow-[0_24px_40px_oklch(0_0_0/0.35)]"
        />
      </section>
    </main>
  );
}

function FormulaireActivation({ info, jeton }: { info: ActivationInfo; jeton: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [identifiant, setIdentifiant] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [afficher, setAfficher] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const activer = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null);
    if (!/^[a-z0-9._-]{3,30}$/.test(identifiant.trim().toLowerCase()))
      return setErreur(
        "L'identifiant contient de 3 à 30 lettres, chiffres, points, tirets ou « _ ».",
      );
    if (motDePasse.length < 8) return setErreur("Le mot de passe contient au moins 8 caractères.");
    if (motDePasse !== confirmation) return setErreur("Les deux mots de passe sont différents.");
    setEnCours(true);
    try {
      const moi = await activerInvitation(jeton, identifiant.trim(), motDePasse);
      queryClient.setQueryData(CLE_MOI, moi);
      await router.navigate({
        to: info.double_auth_requise ? "/admin/double-authentification" : "/admin",
        replace: true,
      });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      setEnCours(false);
    }
  };

  return (
    <>
      <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
        <span className="h-1 w-8 rounded-full bg-primary" />
        Invitation
      </p>
      <h1 className="mt-3 text-4xl leading-tight">
        <span className="text-logo-blue">Bonjour</span>{" "}
        <span className="text-primary">{info.prenom} !</span>
      </h1>
      <p className="mt-2 mb-8 text-lg font-medium text-muted-foreground">
        Choisis ton identifiant et ton mot de passe pour activer ton compte {info.email}.
      </p>
      <form
        onSubmit={activer}
        noValidate
        className="space-y-5 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
      >
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        <label className="grid gap-1.5 text-sm font-medium">
          Identifiant
          <Input
            value={identifiant}
            onChange={(e) => setIdentifiant(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            className="h-12 text-base"
          />
        </label>
        <label className="grid gap-1.5 text-sm font-medium">
          Mot de passe (8 caractères au moins)
          <div className="relative">
            <Input
              type={afficher ? "text" : "password"}
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              autoComplete="new-password"
              className="h-12 pr-12 text-base"
            />
            <button
              type="button"
              onClick={() => setAfficher(!afficher)}
              aria-pressed={afficher}
              aria-label={afficher ? "Masquer le mot de passe" : "Afficher le mot de passe"}
              className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-muted-foreground hover:text-foreground"
            >
              {afficher ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
            </button>
          </div>
        </label>
        <label className="grid gap-1.5 text-sm font-medium">
          Confirme le mot de passe
          <Input
            type={afficher ? "text" : "password"}
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            autoComplete="new-password"
            className="h-12 text-base"
          />
        </label>
        {info.double_auth_requise && (
          <p className="flex items-start gap-3 rounded-2xl bg-mist-soft p-4 text-sm font-medium text-ink/80">
            <ShieldCheck aria-hidden className="mt-0.5 size-4 shrink-0 text-primary" />
            Tes droits sont sensibles : tu activeras ensuite la double authentification avec ton
            téléphone.
          </p>
        )}
        <Button
          type="submit"
          disabled={enCours}
          className="btn-fx h-12 w-full rounded-full text-base font-bold"
        >
          {enCours && <Loader2 className="size-5 animate-spin" />}
          Activer mon compte
        </Button>
      </form>
    </>
  );
}
