import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft, ExternalLink, Newspaper, PenLine, Trophy, Users } from "lucide-react";
import type { ReactNode } from "react";

import { EtatContenu } from "@/components/articles/EtatContenu";
import { GestionClub } from "@/components/clubs/GestionClub";
import { ListeMembres } from "@/components/clubs/ListeMembres";
import { PropositionFiche } from "@/components/clubs/PropositionFiche";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import {
  chargerAxes,
  chargerEspaceClub,
  chargerEspaceEleve,
  chargerMesClubs,
  chargerMonClub,
  ErreurApi,
  type AxePublic,
  type EspaceClub,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

type Recherche = { club?: string | undefined };

// Le club à ouvrir : celui demandé (un encadreur rattaché à plusieurs clubs), sinon celui de l'élève (président
// ou membre actif), sinon le premier club de l'encadreur. Null : aucun club.
async function clubVise(role: string, demande: string | undefined): Promise<string | null> {
  if (demande) return demande;
  if (role === "eleve") {
    const [monClub, espace] = await Promise.all([chargerMonClub(), chargerEspaceEleve()]);
    if (monClub.club?.etat === "actif") return monClub.club.id;
    return espace.adhesion?.etat === "active" ? espace.adhesion.club_id : null;
  }
  const mesClubs = await chargerMesClubs();
  return mesClubs.rattachements.find((r) => r.etat === "actif")?.club_id ?? null;
}

export const Route = createFileRoute("/_connecte/mon-club/")({
  gcTime: 0,
  validateSearch: (search: Record<string, unknown>): Recherche =>
    typeof search["club"] === "string" ? { club: search["club"] } : {},
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ context, deps }) => {
    const clubId = await clubVise(context.moi.role, deps.club);
    if (!clubId) return { espace: null, axes: [] };
    try {
      const [espace, axes] = await Promise.all([
        chargerEspaceClub(clubId),
        chargerAxes().catch(() => []),
      ]);
      return { espace, axes };
    } catch (e) {
      // Plus membre, ou un club qui n'est pas le sien : la page le dit simplement.
      if (e instanceof ErreurApi && e.statut === 404) return { espace: null, axes: [] };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Mon club — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MonClub,
});

function MonClub() {
  const { espace, axes } = Route.useLoaderData();
  const router = useRouter();
  const rafraichir = () => router.invalidate();

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        {espace ? (
          <Espace espace={espace} axes={axes} onRafraichir={rafraichir} />
        ) : (
          <div className="rounded-3xl bg-card p-8 text-center shadow-card">
            <p className="font-semibold">Tu n'as pas encore de club.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Rejoins le club de ton établissement depuis ton espace pour suivre sa vie ici.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}

function Espace({
  espace,
  axes,
  onRafraichir,
}: {
  espace: EspaceClub;
  axes: AxePublic[];
  onRafraichir: () => Promise<unknown>;
}) {
  const president = espace.role === "president";
  const { club, indicateurs } = espace;
  const libelleAxe = (code: string) => axes.find((a) => a.code === code)?.libelle ?? code;

  return (
    <>
      <header>
        <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
          <span className="h-1 w-8 rounded-full bg-primary" />
          {president ? "Espace du président" : "Mon club"}
        </p>
        <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
          <span className="text-logo-blue">{club.nom}</span>
        </h1>
        <p className="mt-3 text-muted-foreground">
          {club.etablissement.nom}
          {club.actif_le && ` · actif depuis le ${dateCourte(club.actif_le)}`}
        </p>
        {club.axes.length > 0 && (
          <p className="mt-2 flex flex-wrap gap-2">
            {club.axes.map((a) => (
              <span
                key={a}
                className="rounded-full bg-white px-3 py-1 text-xs font-bold text-logo-blue shadow-sm"
              >
                {libelleAxe(a)}
              </span>
            ))}
          </p>
        )}
        <Link
          to="/clubs/$id"
          params={{ id: club.id }}
          className="mt-3 inline-flex items-center gap-1 text-sm font-bold text-logo-blue hover:underline"
        >
          Voir la fiche publique <ExternalLink className="size-3.5" />
        </Link>
      </header>

      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Indicateur
          icone={<Users className="size-5" />}
          valeur={indicateurs.membres}
          libelle="membres"
        />
        <Indicateur
          icone={<Users className="size-5" />}
          valeur={indicateurs.encadreurs}
          libelle="encadreurs"
        />
        <Indicateur
          icone={<Newspaper className="size-5" />}
          valeur={indicateurs.actualites}
          libelle="actualités publiées"
        />
        {indicateurs.demandes !== null ? (
          <Indicateur
            icone={<PenLine className="size-5" />}
            valeur={indicateurs.demandes}
            libelle="demandes à traiter"
          />
        ) : (
          <li className="rounded-3xl bg-card p-4 shadow-card">
            <Trophy className="size-5 text-logo-blue" />
            <p className="mt-2 text-sm text-muted-foreground">Points et rang du club : bientôt</p>
          </li>
        )}
      </ul>

      {president && espace.demandes && (
        <section className="rounded-3xl bg-card p-5 shadow-card sm:p-7">
          <GestionClub
            clubId={club.id}
            demandesAdhesion={espace.demandes.adhesions}
            demandesRattachement={espace.demandes.rattachements}
            membres={espace.membres}
            onRafraichir={onRafraichir}
          />
        </section>
      )}

      <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-xl text-ink">Actualités du club</h2>
          {president && (
            <Link
              to="/mon-club/actualites/nouveau"
              className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-sm font-bold text-primary-foreground"
            >
              <PenLine className="size-4" /> Écrire une actualité
            </Link>
          )}
        </div>
        {espace.actualites.length === 0 ? (
          <p className="text-sm text-muted-foreground">Aucune actualité publiée pour l'instant.</p>
        ) : (
          <ul className="space-y-2">
            {espace.actualites.map((a) => (
              <li key={a.adresse}>
                <Link
                  to="/articles/$adresse"
                  params={{ adresse: a.adresse }}
                  className="font-bold text-logo-blue hover:underline"
                >
                  {a.titre}
                </Link>
                <span className="text-sm text-muted-foreground"> · {dateCourte(a.publie_le)}</span>
              </li>
            ))}
          </ul>
        )}
        {president && espace.suivi && espace.suivi.actualites.length > 0 && (
          <div className="border-t pt-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-muted-foreground">
              Suivi de tes actualités
            </h3>
            <ul className="mt-2 space-y-2">
              {espace.suivi.actualites.map((a) => (
                <li key={a.id} className="flex flex-wrap items-center gap-3">
                  <Link
                    to="/mon-club/actualites/$id"
                    params={{ id: a.id }}
                    className="font-semibold text-ink hover:underline"
                  >
                    {a.titre}
                  </Link>
                  <EtatContenu etat={a.etat} enLigne={a.en_ligne} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {president && espace.suivi && (
        <PropositionFiche
          description={club.description}
          axes={club.axes}
          tousLesAxes={axes}
          propositions={espace.suivi.propositions}
          onRafraichir={onRafraichir}
        />
      )}

      {!president && (
        <section className="rounded-3xl bg-card p-5 shadow-card sm:p-7">
          <h2 className="mb-4 font-display text-xl text-ink">Les membres</h2>
          <ListeMembres liste={espace.membres} />
        </section>
      )}
    </>
  );
}

function Indicateur({
  icone,
  valeur,
  libelle,
}: {
  icone: ReactNode;
  valeur: number;
  libelle: string;
}) {
  return (
    <li className="rounded-3xl bg-card p-4 shadow-card">
      <span className="text-logo-blue">{icone}</span>
      <p className="mt-2 font-display text-3xl text-ink">{valeur}</p>
      <p className="text-sm text-muted-foreground">{libelle}</p>
    </li>
  );
}
