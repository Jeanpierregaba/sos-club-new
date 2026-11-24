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
import { nomFonction } from "@/lib/fonctions";
import { lien } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

const ETATS_TRADUITS = {
  valide: m.certificat_etat_valide,
  revoque: m.certificat_etat_revoque,
  remplace: m.certificat_etat_remplace,
};

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
    meta: [{ title: m.certificat_meta_titre() }, { name: "robots", content: "noindex" }],
  }),
  errorComponent: ServiceIndisponible,
  component: VerifierCertificat,
});

function Titulaire({ titulaire }: { titulaire: VerificationCertificat["titulaire"] }) {
  if (titulaire.type === "eleve") {
    return (
      <>
        <dt className="text-sm text-muted-foreground">{m.certificat_eleve()}</dt>
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
      <dt className="text-sm text-muted-foreground">{m.certificat_encadreur()}</dt>
      <dd className="font-bold text-ink">
        {nomPublicEncadreur(titulaire.prenom, titulaire.initiale)}
        <span className="block text-sm font-semibold text-muted-foreground">
          {nomFonction(titulaire.fonction)}
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
            ? m.certificat_valide()
            : verification.etat === "revoque"
              ? m.certificat_revoque()
              : m.certificat_remplace()}
        </span>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${etat.classe}`}>
          {ETATS_TRADUITS[verification.etat]()}
        </span>
      </p>
      <p className="mt-3 text-muted-foreground">
        {valide
          ? m.certificat_valide_texte()
          : verification.etat === "revoque"
            ? m.certificat_revoque_texte()
            : m.certificat_remplace_texte()}
      </p>
      <dl className="mt-6 grid gap-4 sm:grid-cols-3">
        <div>
          <Titulaire titulaire={verification.titulaire} />
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">{m.certificat_delivre_le()}</dt>
          <dd className="font-bold text-ink">{dateCourte(verification.delivre_le)}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">{m.certificat_numero()}</dt>
          <dd className="break-all font-mono font-bold text-ink">{verification.numero}</dd>
        </div>
      </dl>
      {verification.remplace_par && (
        <p className="mt-6 text-sm">
          {m.certificat_nouveau_numero()}{" "}
          <a
            href={lien(`/certificats/${verification.remplace_par}`)}
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
        <FilAriane rubrique={m.menu_gamification()} page={m.certificat_fil()} />
        <header className="pt-8">
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            {m.certificat_surtitre()}
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">{m.certificat_titre_1()}</span>{" "}
            <span className="text-primary">{m.certificat_titre_2()}</span>
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
                {m.certificat_introuvable()}
              </p>
              <p className="mt-3 break-words text-muted-foreground">
                {m.certificat_introuvable_texte({ numero })}
              </p>
            </section>
          )}

          <form onSubmit={chercher} className="rounded-3xl bg-card p-5 shadow-card sm:p-6">
            <label htmlFor="numero" className="font-bold text-ink">
              {m.certificat_autre()}
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
                <Search className="size-4" /> {m.certificat_verifier()}
              </Button>
            </div>
          </form>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
