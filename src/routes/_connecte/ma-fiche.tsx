import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft, CheckCircle2, Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  SectionClub,
  SectionFamille,
  SectionLieu,
  SectionToi,
} from "@/components/inscription/ChampsFiche";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import {
  chargerAxes,
  chargerMaFiche,
  enregistrerMaFiche,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
} from "@/lib/api/client";
import { FICHE_VIDE, ficheDepuisApi, ficheVersApi, schemaFiche } from "@/lib/fiche";

const schema = z.object({ fiche: schemaFiche });

export const Route = createFileRoute("/_connecte/ma-fiche")({
  // Rien en cache : des données personnelles.
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role !== "eleve") throw redirect({ to: "/mon-espace" });
  },
  loader: async () => {
    const [fiche, axes] = await Promise.all([chargerMaFiche(), chargerAxes().catch(() => [])]);
    return { fiche, axes };
  },
  head: () => ({
    meta: [
      { title: "Ma fiche d'adhésion — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MaFiche,
});

// La fiche d'adhésion de l'élève (spec 030) : il la complète ou la corrige. Elle n'est jamais publique.
function MaFiche() {
  const { fiche, axes } = Route.useLoaderData();
  const router = useRouter();
  const haut = useRef<HTMLDivElement>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enregistree, setEnregistree] = useState(false);
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { fiche: fiche ? ficheDepuisApi(fiche) : FICHE_VIDE },
  });

  const envoyer = form.handleSubmit(
    async (v) => {
      setErreur(null);
      setEnregistree(false);
      try {
        await enregistrerMaFiche({ ...ficheVersApi(v.fiche), version: fiche?.version ?? null });
        setEnregistree(true);
        await router.invalidate();
        haut.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (e) {
        setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
        haut.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    },
    () => haut.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
  );
  const enCours = form.formState.isSubmitting;

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <p className="mt-6 text-sm font-extrabold uppercase tracking-widest text-logo-red">
          Club Santé SOS Docteur TV
        </p>
        <h1 className="mt-1 text-4xl">
          <span className="text-logo-blue">Ma fiche</span>{" "}
          <span className="text-primary">d'adhésion</span>
        </h1>
        <p className="mt-2 font-medium text-muted-foreground">
          Ces informations restent privées : seule l'équipe nationale habilitée peut les lire. Elles
          l'aident à soutenir les membres actifs, notamment pour les bourses.
        </p>
        {fiche && (
          <p className="mt-2 text-sm font-semibold text-ink/70">
            Année scolaire {fiche.annee_scolaire}
          </p>
        )}

        <div ref={haut} className="mt-6 space-y-3">
          {erreur && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{erreur}</AlertDescription>
            </Alert>
          )}
          {enregistree && (
            <p
              role="status"
              className="flex items-center gap-2 rounded-2xl bg-primary/10 p-4 font-semibold text-ink"
            >
              <CheckCircle2 className="size-5 text-primary" /> Ta fiche est enregistrée.
            </p>
          )}
        </div>

        <Form {...form}>
          <form
            onSubmit={envoyer}
            noValidate
            className="mt-6 space-y-10 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
          >
            <SectionLieu />
            <SectionToi />
            <SectionFamille />
            <SectionClub axes={axes} />
            <Button
              type="submit"
              disabled={enCours}
              className="btn-fx h-12 w-full rounded-full text-base font-bold"
            >
              {enCours && <Loader2 className="h-5 w-5 animate-spin" />}
              Enregistrer ma fiche
            </Button>
          </form>
        </Form>
      </div>
    </main>
  );
}
