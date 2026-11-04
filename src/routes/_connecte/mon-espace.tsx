import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { CalendarRange, KeyRound, LogOut, PartyPopper, Pencil, Star, Trophy } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ChoixEtablissement, type EtablissementChoisi } from "@/components/ChoixEtablissement";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CLE_MOI } from "@/hooks/use-moi";
import {
  changerMotDePasse,
  chargerEspaceEleve,
  deconnecter,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  modifierProfilEleve,
  type Classe,
  type EspaceEleve,
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
    if (context.moi.role !== "eleve") return { espace: null };
    try {
      return { espace: await chargerEspaceEleve() };
    } catch (e) {
      // Un compte élève créé avant la spec 017 n'a pas de profil : il garde l'espace simple.
      if (e instanceof ErreurApi && e.statut === 403) return { espace: null };
      throw e;
    }
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
  const { espace } = Route.useLoaderData();
  return espace ? <EspaceDeLEleve espace={espace} /> : <EspaceSimple />;
}

function useDeconnexion() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const seDeconnecter = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      await deconnecter();
      queryClient.setQueryData(CLE_MOI, null);
      await router.navigate({ to: "/", replace: true });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      setEnCours(false);
    }
  };
  return { seDeconnecter, erreur, enCours };
}

function EspaceSimple() {
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
        <p className="mt-1 text-sm text-muted-foreground">Ton espace s'enrichira bientôt.</p>

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

const dateCourte = (iso: string) =>
  new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });

function EspaceDeLEleve({ espace }: { espace: EspaceEleve }) {
  const { bienvenue } = Route.useSearch();
  const { seDeconnecter, erreur, enCours } = useDeconnexion();
  const [profil, setProfil] = useState(false);
  const [motDePasse, setMotDePasse] = useState(false);
  const [motDePasseChange, setMotDePasseChange] = useState(false);
  const { points } = espace;

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <span className="h-1 w-8 rounded-full bg-primary" />
              Mon espace
            </p>
            <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
              <span className="text-logo-blue">Salut</span>{" "}
              <span className="text-primary">{espace.pseudonyme} !</span>
            </h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/"
              className="inline-flex h-11 items-center rounded-full px-4 text-sm font-bold text-logo-blue hover:bg-white"
            >
              Accueil
            </Link>
            <Button
              variant="outline"
              onClick={seDeconnecter}
              disabled={enCours}
              className="h-11 rounded-full px-5 font-bold"
            >
              <LogOut className="size-4" /> Me déconnecter
            </Button>
          </div>
        </div>

        {erreur && (
          <Alert variant="destructive" className="mt-6">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        {motDePasseChange && (
          <Alert role="status" className="mt-6">
            <AlertDescription>
              Ton mot de passe est changé. Tes autres appareils sont déconnectés.
            </AlertDescription>
          </Alert>
        )}
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

        <section aria-label="Mes points" className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl bg-logo-blue p-6 text-white shadow-card">
            <p className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-white/75">
              <Star aria-hidden className="size-4 text-sun" /> Points du semestre
            </p>
            <p className="mt-2 font-display text-5xl">{points.points_semestre}</p>
            <p className="mt-2 flex items-center gap-1.5 text-sm font-semibold text-white/80">
              <CalendarRange aria-hidden className="size-4" />
              {points.semestre
                ? `${points.semestre.libelle}, jusqu'au ${dateCourte(points.semestre.fin)}`
                : "Aucun semestre en cours"}
            </p>
          </div>
          <div className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
            <p className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-muted-foreground">
              <Trophy aria-hidden className="size-4 text-primary" /> Total depuis ton inscription
            </p>
            <p className="mt-2 font-display text-5xl text-logo-blue">{points.total}</p>
            <p className="mt-2 text-sm font-semibold text-muted-foreground">
              Les classements arrivent bientôt.
            </p>
          </div>
        </section>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          <section className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
            <h2 className="text-2xl">
              <span className="text-logo-blue">Mes derniers</span>{" "}
              <span className="text-primary">points</span>
            </h2>
            {points.lignes.length === 0 ? (
              <p className="mt-3 font-medium text-muted-foreground">Aucun point pour l'instant.</p>
            ) : (
              <ol className="mt-4 divide-y">
                {points.lignes.map((ligne, rang) => (
                  <li key={rang} className="flex items-center justify-between gap-4 py-3">
                    <div className="min-w-0">
                      <p className="font-bold text-ink">{ligne.libelle}</p>
                      <p className="text-sm font-medium text-muted-foreground">
                        {dateCourte(ligne.cree_le)}
                        {ligne.semestre ? ` · ${ligne.semestre}` : " · hors semestre"}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-3 py-1 text-sm font-extrabold ${ligne.montant > 0 ? "bg-primary/10 text-primary" : "bg-logo-red/10 text-logo-red"}`}
                    >
                      {ligne.montant > 0 ? `+${ligne.montant}` : ligne.montant}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </section>

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
                valeur={
                  <>
                    {espace.etablissement.nom}
                    <span className="block font-medium text-muted-foreground">
                      {espace.etablissement.iesg} · {espace.etablissement.dre}
                    </span>
                    {espace.etablissement.statut === "propose" && (
                      <span className="mt-1 inline-flex rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold text-ink">
                        En cours de vérification
                      </span>
                    )}
                  </>
                }
              />
              <Info terme="Club" valeur="Sans club pour l'instant" />
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

function Info({ terme, valeur }: { terme: string; valeur: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[7rem_1fr] gap-3">
      <dt className="font-bold text-muted-foreground">{terme}</dt>
      <dd className="min-w-0 font-semibold text-ink">{valeur}</dd>
    </div>
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

function DialogueMotDePasse({
  ouvert,
  onOuvert,
  onFait,
}: {
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
  onFait: () => void;
}) {
  const [actuel, setActuel] = useState("");
  const [nouveau, setNouveau] = useState("");

  return (
    <>
      <DialogueFormulaire
        ouvert={ouvert}
        onOuvert={(o) => {
          setActuel("");
          setNouveau("");
          onOuvert(o);
        }}
        titre="Changer mon mot de passe"
        description="Tes autres appareils seront déconnectés."
        bouton="Changer"
        onEnvoie={async () => {
          if (nouveau.length < 8)
            throw new ErreurApi(
              422,
              "Le nouveau mot de passe doit contenir au moins 8 caractères.",
            );
          await changerMotDePasse(actuel, nouveau);
          onFait();
        }}
      >
        <Champ libelle="Mot de passe actuel">
          <input
            type="password"
            value={actuel}
            onChange={(e) => setActuel(e.target.value)}
            autoComplete="current-password"
            required
            className={CHAMP_ADMIN}
          />
        </Champ>
        <Champ libelle="Nouveau mot de passe (8 caractères au moins)">
          <input
            type="password"
            value={nouveau}
            onChange={(e) => setNouveau(e.target.value)}
            autoComplete="new-password"
            minLength={8}
            maxLength={256}
            required
            className={CHAMP_ADMIN}
          />
        </Champ>
      </DialogueFormulaire>
    </>
  );
}
