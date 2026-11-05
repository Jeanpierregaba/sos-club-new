import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { KeyRound, LogOut, PartyPopper, Pencil } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ChoixEtablissement, type EtablissementChoisi } from "@/components/ChoixEtablissement";
import { BlocClub } from "@/components/clubs/BlocClub";
import {
  CartesPoints,
  DernieresLignes,
  DialogueMotDePasse,
  EnTeteEspace,
  EtablissementAffiche,
  Info,
  MotDePasseChange,
} from "@/components/espace/commun";
import { EspaceEncadreur } from "@/components/espace/EspaceEncadreur";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useDeconnexion } from "@/hooks/use-deconnexion";
import {
  chargerAxes,
  chargerClubParEtablissement,
  chargerEspaceEleve,
  chargerEspaceEncadreur,
  chargerMonClub,
  ErreurApi,
  modifierProfilEleve,
  type AxePublic,
  type Classe,
  type ClubPublic,
  type EspaceEleve,
  type MonClub,
} from "@/lib/api/client";
import { CLASSES, libelleClasse } from "@/lib/classes";

const LIBELLES_ROLE = { eleve: "Élève", encadreur: "Encadreur", admin: "Admin" } as const;

export const Route = createFileRoute("/_connecte/mon-espace")({
  validateSearch: (search: Record<string, unknown>): { bienvenue?: boolean } =>
    search["bienvenue"] === true || search["bienvenue"] === "true" ? { bienvenue: true } : {},
  // Rien en cache : les données d'un compte ne doivent pas s'afficher, même un instant, au compte suivant.
  gcTime: 0,
  // Un collaborateur a son propre espace (spec 015).
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: async ({ context }) => {
    try {
      if (context.moi.role === "eleve") {
        const [espace, club, axes] = await Promise.all([
          chargerEspaceEleve(),
          chargerMonClub(),
          chargerAxes().catch(() => []),
        ]);
        // Quand l'élève n'a pas lui-même de demande, l'établissement peut déjà avoir un club actif :
        // le formulaire ne doit pas être proposé (§1 de la spec).
        const clubEtablissement =
          club.club === null
            ? await chargerClubParEtablissement(espace.etablissement.id).catch(() => undefined)
            : null;
        return { eleve: espace, club, axes, clubEtablissement, encadreur: null };
      }
      if (context.moi.role === "encadreur")
        return {
          eleve: null,
          club: null,
          axes: [],
          clubEtablissement: null,
          encadreur: await chargerEspaceEncadreur(),
        };
    } catch (e) {
      // Un compte créé avant les specs 017 et 018 n'a pas de profil : il garde l'espace simple.
      if (e instanceof ErreurApi && (e.statut === 403 || e.statut === 404))
        return {
          eleve: null,
          club: null,
          axes: [],
          clubEtablissement: null,
          encadreur: null,
          message: e.message,
        };
      throw e;
    }
    return { eleve: null, club: null, axes: [], clubEtablissement: null, encadreur: null };
  },
  head: () => ({
    meta: [
      { title: "Mon espace — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MonEspace,
});

function MonEspace() {
  const donnees = Route.useLoaderData();
  const { moi } = Route.useRouteContext();
  if (donnees.eleve)
    return (
      <EspaceDeLEleve
        espace={donnees.eleve}
        club={donnees.club}
        axes={donnees.axes}
        clubEtablissement={donnees.clubEtablissement ?? null}
      />
    );
  if (donnees.encadreur) return <EspaceEncadreur espace={donnees.encadreur} prenom={moi.prenom} />;
  return <EspaceSimple message={"message" in donnees ? donnees.message : undefined} />;
}

function EspaceSimple({ message }: { message?: string | undefined }) {
  const { moi } = Route.useRouteContext();
  const { seDeconnecter, erreur, enCours } = useDeconnexion();

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist-soft px-4 py-10">
      <section className="w-full max-w-lg rounded-3xl bg-card p-6 text-center shadow-card sm:p-8">
        <h1 className="text-3xl text-logo-blue">
          Salut <span className="text-primary">{moi.prenom} !</span>
        </h1>
        <p className="mt-2 text-muted-foreground">
          Rôle : <strong className="text-foreground">{LIBELLES_ROLE[moi.role]}</strong>
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          {message ?? "Ton espace s'enrichira bientôt."}
        </p>

        {erreur && (
          <Alert variant="destructive" className="mt-6 text-left">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}

        <div className="mt-6 flex flex-col items-center gap-4">
          <Button
            variant="outline"
            onClick={seDeconnecter}
            disabled={enCours}
            className="h-12 rounded-full px-6 font-bold"
          >
            <LogOut className="h-5 w-5" />
            Me déconnecter
          </Button>
          <Link
            to="/"
            className="text-sm font-bold text-logo-blue underline-offset-4 hover:underline"
          >
            Retour à l'accueil
          </Link>
        </div>
      </section>
    </main>
  );
}

function EspaceDeLEleve({
  espace,
  club,
  axes,
  clubEtablissement,
}: {
  espace: EspaceEleve;
  club: MonClub;
  axes: AxePublic[];
  clubEtablissement: ClubPublic | null;
}) {
  const { bienvenue } = Route.useSearch();
  const router = useRouter();
  const [profil, setProfil] = useState(false);
  const [motDePasse, setMotDePasse] = useState(false);
  const [motDePasseChange, setMotDePasseChange] = useState(false);
  const { points } = espace;

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <EnTeteEspace nom={espace.pseudonyme}>
          {motDePasseChange && <MotDePasseChange />}
        </EnTeteEspace>
        {bienvenue && (
          <div className="mt-6 flex items-start gap-3 rounded-3xl bg-primary/10 p-5 ring-1 ring-primary/30">
            <PartyPopper aria-hidden className="mt-0.5 size-6 shrink-0 text-primary" />
            <p className="font-semibold text-ink">
              Bienvenue dans les Clubs Santé !{" "}
              {points.total > 0 && (
                <>
                  Tes <strong>{points.total} points de bienvenue</strong> sont crédités.{" "}
                </>
              )}
              Réussis des quiz et publie des articles pour gagner des points.
            </p>
          </div>
        )}

        <CartesPoints points={points} />

        <BlocClub
          club={club.club}
          passation={club.passation ?? null}
          etablissement={espace.etablissement}
          axes={axes}
          clubEtablissement={clubEtablissement}
          onRafraichir={async () => {
            await router.invalidate();
          }}
        />

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          <DernieresLignes points={points} />

          <section className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
            <h2 className="text-2xl">
              <span className="text-logo-blue">Mon</span>{" "}
              <span className="text-primary">profil</span>
            </h2>
            <dl className="mt-4 grid gap-3 text-sm">
              <Info terme="Pseudonyme" valeur={espace.pseudonyme} />
              <Info terme="Classe" valeur={libelleClasse(espace.classe)} />
              <Info
                terme="Établissement"
                valeur={<EtablissementAffiche etablissement={espace.etablissement} />}
              />
              <Info terme="Club" valeur={club.club ? club.club.nom : "Aucun pour l'instant"} />
              <Info terme="Email" valeur={espace.email ?? "Aucun"} />
            </dl>
            <div className="mt-6 flex flex-wrap gap-2">
              <Button onClick={() => setProfil(true)} className="rounded-full font-bold">
                <Pencil className="size-4" /> Modifier
              </Button>
              <Button
                variant="outline"
                onClick={() => setMotDePasse(true)}
                className="rounded-full font-bold"
              >
                <KeyRound className="size-4" /> Mot de passe
              </Button>
            </div>
            <p className="mt-4 text-xs font-medium text-muted-foreground">
              Pour changer de pseudonyme, demande-le à l'équipe nationale.
            </p>
          </section>
        </div>
      </div>

      <DialogueProfil espace={espace} ouvert={profil} onOuvert={setProfil} />
      <DialogueMotDePasse
        ouvert={motDePasse}
        onOuvert={setMotDePasse}
        onFait={() => setMotDePasseChange(true)}
      />
    </main>
  );
}

function DialogueProfil({
  espace,
  ouvert,
  onOuvert,
}: {
  espace: EspaceEleve;
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
}) {
  const router = useRouter();
  const actuel: EtablissementChoisi = {
    id: espace.etablissement.id,
    nom: espace.etablissement.nom,
    detail: `${espace.etablissement.iesg} · ${espace.etablissement.dre}`,
  };
  const [classe, setClasse] = useState<Classe>(espace.classe);
  const [etablissement, setEtablissement] = useState<EtablissementChoisi | null>(actuel);
  const [email, setEmail] = useState(espace.email ?? "");

  return (
    <DialogueFormulaire
      ouvert={ouvert}
      onOuvert={(o) => {
        if (o) {
          setClasse(espace.classe);
          setEtablissement(actuel);
          setEmail(espace.email ?? "");
        }
        onOuvert(o);
      }}
      titre="Modifier mon profil"
      description="Ton pseudonyme ne change pas ici : demande-le à l'équipe nationale."
      bouton="Enregistrer"
      onEnvoie={async () => {
        if (!etablissement) throw new ErreurApi(422, "Choisis ton établissement dans la liste.");
        await modifierProfilEleve({
          version: espace.version,
          classe,
          etablissement_id: etablissement.id,
          email: email.trim(),
        });
        await router.invalidate();
      }}
    >
      <Champ libelle="Classe">
        <select
          value={classe}
          onChange={(e) => setClasse(e.target.value as Classe)}
          className={CHAMP_ADMIN}
        >
          {CLASSES.map((c) => (
            <option key={c.valeur} value={c.valeur}>
              {c.libelle}
            </option>
          ))}
        </select>
      </Champ>
      <div className="grid gap-1.5 text-sm font-bold">
        Établissement
        <ChoixEtablissement valeur={etablissement} onChoix={setEtablissement} />
      </div>
      <Champ libelle="Email (facultatif)">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          maxLength={254}
          autoComplete="email"
          className={CHAMP_ADMIN}
        />
      </Champ>
    </DialogueFormulaire>
  );
}
