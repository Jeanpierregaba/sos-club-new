import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { BadgeCheck, Search, ShieldAlert, ShieldX } from "lucide-react";
import { useState, type FormEvent } from "react";

import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErreurApi, verifierCertificat, type VerificationCertificat } from "@/lib/api/client";
import { ETATS_CERTIFICAT, nomPublicEncadreur } from "@/lib/certification";
import { dateCourte } from "@/lib/dates";
import { libelleFonction } from "@/lib/fonctions";

// Vérification publique d'un certificat Génie Imhotep (spec 029), ouverte par le QR code du PDF. Elle dit si le
// certificat est valide et à qui il revient, sans jamais montrer le nom complet d'un élève (RULES).
export const Route = createFileRoute("/certificats/$numero")({
  gcTime: 0,
  loader: async ({ params }) => {
    try {
      return { verification: await verifierCertificat(params.numero) };
    } catch (e) {
      if (e instanceof ErreurApi && e.statut === 404)
        return { verification: null as VerificationCertificat | null };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Vérifier un certificat Génie Imhotep — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: VerifierCertificat,
});

function Titulaire({ titulaire }: { titulaire: VerificationCertificat["titulaire"] }) {
  if (titulaire.type === "eleve") {
    return (
      <>
        <dt className="text-sm text-muted-foreground">Élève</dt>
        <dd className="font-bold text-ink">
          {titulaire.pseudonyme}
          {titulaire.club && (
            <span className="block text-sm font-semibold text-muted-foreground">
              {titulaire.club}
            </span>
          )}
        </dd>
      </>
    );
  }
  return (
    <>
      <dt className="text-sm text-muted-foreground">Encadreur</dt>
      <dd className="font-bold text-ink">
        {nomPublicEncadreur(titulaire.prenom, titulaire.initiale)}
        <span className="block text-sm font-semibold text-muted-foreground">
          {libelleFonction(titulaire.fonction)}
        </span>
      </dd>
    </>
  );
}

function Resultat({ verification }: { verification: VerificationCertificat }) {
  const etat = ETATS_CERTIFICAT[verification.etat];
  const valide = verification.etat === "valide";
  const Icone = valide ? BadgeCheck : verification.etat === "revoque" ? ShieldX : ShieldAlert;
  return (
    <section
      aria-live="polite"
      className={`rounded-3xl bg-white p-6 shadow-card ring-2 sm:p-8 ${valide ? "ring-primary" : "ring-logo-red/40"}`}
    >
      <p className="flex flex-wrap items-center gap-3">
        <Icone
          aria-hidden
          className={`size-10 shrink-0 ${valide ? "text-primary" : "text-logo-red"}`}
        />
        <span className="font-display text-2xl text-ink sm:text-3xl">
          {valide
            ? "Certificat valide"
            : verification.etat === "revoque"
              ? "Certificat révoqué"
              : "Certificat remplacé"}
        </span>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${etat.classe}`}>
          {etat.libelle}
        </span>
      </p>
      <p className="mt-3 text-muted-foreground">
        {valide
          ? "Ce certificat Génie Imhotep a bien été délivré par la plateforme des Clubs Santé."
          : verification.etat === "revoque"
            ? "Ce certificat a été retiré par l'équipe nationale : il n'atteste plus rien."
            : "Ce certificat a été remplacé par un nouveau numéro, qui seul fait foi."}
      </p>
      <dl className="mt-6 grid gap-4 sm:grid-cols-3">
        <div>
          <Titulaire titulaire={verification.titulaire} />
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Délivré le</dt>
          <dd className="font-bold text-ink">{dateCourte(verification.delivre_le)}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Numéro</dt>
          <dd className="break-all font-mono font-bold text-ink">{verification.numero}</dd>
        </div>
      </dl>
      {verification.remplace_par && (
        <p className="mt-6 text-sm">
          Nouveau numéro :{" "}
          <a
            href={`/certificats/${verification.remplace_par}`}
            className="font-mono font-bold text-logo-blue hover:underline"
          >
            {verification.remplace_par}
          </a>
        </p>
      )}
    </section>
  );
}

function VerifierCertificat() {
  const { verification } = Route.useLoaderData();
  const { numero } = Route.useParams();
  const naviguer = useNavigate();
  const [saisie, setSaisie] = useState("");

  function chercher(e: FormEvent) {
    e.preventDefault();
    const propre = saisie.trim().toUpperCase().replace(/\s+/g, "");
    if (propre) void naviguer({ to: "/certificats/$numero", params: { numero: propre } });
  }

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-4 pb-20 pt-8 sm:px-5">
        <FilAriane rubrique="Gamification" page="Vérifier un certificat" />
        <header className="pt-8">
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Certification Génie Imhotep
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Vérifier un</span>{" "}
            <span className="text-primary">certificat</span>
          </h1>
        </header>

        <div className="mt-8 space-y-6">
          {verification ? (
            <Resultat verification={verification} />
          ) : (
            <section
              aria-live="polite"
              className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
            >
              <p className="flex items-center gap-3 font-display text-2xl text-ink">
                <ShieldAlert aria-hidden className="size-9 shrink-0 text-logo-red" />
                Certificat introuvable
              </p>
              <p className="mt-3 break-words text-muted-foreground">
                Aucun certificat ne porte le numéro « {numero} ». Vérifie qu'il est bien recopié (il
                commence par GI-).
              </p>
            </section>
          )}

          <form onSubmit={chercher} className="rounded-3xl bg-card p-5 shadow-card sm:p-6">
            <label htmlFor="numero" className="font-bold text-ink">
              Vérifier un autre numéro
            </label>
            <div className="mt-2 flex flex-col gap-2 sm:flex-row">
              <Input
                id="numero"
                value={saisie}
                onChange={(e) => setSaisie(e.target.value)}
                placeholder="GI-XXXX-XXXX-XXXX"
                autoComplete="off"
                className="h-11 rounded-full font-mono"
              />
              <Button type="submit" className="h-11 rounded-full px-6 font-bold">
                <Search className="size-4" /> Vérifier
              </Button>
            </div>
          </form>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
