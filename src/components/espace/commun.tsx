import { Link } from "@tanstack/react-router";
import { CalendarRange, LogOut, MessageCircle, PenLine, Star, Trophy } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useDeconnexion } from "@/hooks/use-deconnexion";
import { changerMotDePasse, ErreurApi, type ResumePoints } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

// Les morceaux communs aux espaces de l'élève (spec 017) et de l'encadreur (spec 018).

export function EnTeteEspace({
  nom,
  articles = false,
  children,
}: {
  nom: string;
  // Les liens « Mes articles » et « Mes commentaires » : élève, ou encadreur vérifié (specs 023 et 025).
  articles?: boolean;
  children?: ReactNode;
}) {
  const { seDeconnecter, erreur, enCours } = useDeconnexion();
  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Mon espace
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Salut</span>{" "}
            <span className="text-primary">{nom} !</span>
          </h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/"
            className="inline-flex h-11 items-center rounded-full px-4 text-sm font-bold text-logo-blue hover:bg-white"
          >
            Accueil
          </Link>
          {articles && (
            <Link
              to="/mes-articles"
              className="inline-flex h-11 items-center gap-2 rounded-full bg-white px-4 text-sm font-bold text-logo-blue shadow-sm hover:bg-mist"
            >
              <PenLine className="size-4" /> Mes articles
            </Link>
          )}
          {articles && (
            <Link
              to="/mes-commentaires"
              className="inline-flex h-11 items-center gap-2 rounded-full bg-white px-4 text-sm font-bold text-logo-blue shadow-sm hover:bg-mist"
            >
              <MessageCircle className="size-4" /> Mes commentaires
            </Link>
          )}
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
      {children}
    </>
  );
}

export function CartesPoints({ points }: { points: ResumePoints }) {
  return (
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
  );
}

export function DernieresLignes({ points }: { points: ResumePoints }) {
  return (
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
  );
}

export function Info({ terme, valeur }: { terme: string; valeur: ReactNode }) {
  return (
    <div className="grid grid-cols-[7rem_1fr] gap-3">
      <dt className="font-bold text-muted-foreground">{terme}</dt>
      <dd className="min-w-0 font-semibold text-ink">{valeur}</dd>
    </div>
  );
}

export function DialogueMotDePasse({
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
          throw new ErreurApi(422, "Le nouveau mot de passe doit contenir au moins 8 caractères.");
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
  );
}

export function MotDePasseChange() {
  return (
    <Alert role="status" className="mt-6">
      <AlertDescription>
        Ton mot de passe est changé. Tes autres appareils sont déconnectés.
      </AlertDescription>
    </Alert>
  );
}

export function EtablissementAffiche({
  etablissement,
}: {
  etablissement: { nom: string; iesg: string; dre: string; statut: string };
}) {
  return (
    <>
      {etablissement.nom}
      <span className="block font-medium text-muted-foreground">
        {etablissement.iesg} · {etablissement.dre}
      </span>
      {etablissement.statut === "propose" && (
        <span className="mt-1 inline-flex rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold text-ink">
          En cours de vérification
        </span>
      )}
    </>
  );
}
