import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { Check, Copy, Loader2, ShieldCheck, UserPlus } from "lucide-react";
import { useState } from "react";

import { BadgeStatut } from "@/components/admin/BadgeStatut";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { MatriceDroits } from "@/components/admin/MatriceDroits";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { STATUTS_COLLABORATEUR, cleDroit, dateCourte } from "@/lib/admin";
import {
  ErreurApi,
  inviterCollaborateur,
  listerCollaborateurs,
  MESSAGE_INDISPONIBLE,
  type Catalogue,
  type Droit,
  type InvitationCree,
} from "@/lib/api/client";

type Recherche = {
  statut?: string | undefined;
  recherche?: string | undefined;
  role?: string | undefined;
  perimetre?: string | undefined;
};

const texte = (s: Record<string, unknown>, cle: string) =>
  typeof s[cle] === "string" && s[cle] ? { [cle]: s[cle] as string } : {};

export const Route = createFileRoute("/_connecte/admin/collaborateurs/")({
  beforeLoad: ({ context }) => {
    if (!context.admin.super_admin) throw redirect({ to: "/admin" });
  },
  validateSearch: (s: Record<string, unknown>): Recherche => ({
    ...(typeof s["statut"] === "string" && s["statut"] in STATUTS_COLLABORATEUR
      ? { statut: s["statut"] }
      : {}),
    ...texte(s, "recherche"),
    ...texte(s, "role"),
    ...texte(s, "perimetre"),
  }),
  loaderDeps: ({ search }) => search,
  loader: ({ deps }) => listerCollaborateurs({ ...deps }),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Collaborateurs,
});

function Collaborateurs() {
  const { catalogue } = Route.useRouteContext();
  const collaborateurs = Route.useLoaderData();
  const filtres = Route.useSearch();
  const { statut } = filtres;
  const filtrer = (changement: Partial<Recherche>) =>
    navigate({ search: (avant) => ({ ...avant, ...changement }) });
  const navigate = Route.useNavigate();
  const [ouvert, setOuvert] = useState(false);

  return (
    <div className="space-y-6">
      <EnTeteAdmin
        sur="Gestion des accès"
        bleu="Les"
        vert="collaborateurs"
        actions={
          <Button
            onClick={() => setOuvert(true)}
            className="btn-fx h-11 rounded-full px-5 font-bold"
          >
            <UserPlus className="size-4" /> Inviter un collaborateur
          </Button>
        }
      >
        Des accès nominatifs, avec des droits par module et un périmètre. Revois régulièrement les
        droits actifs.
      </EnTeteAdmin>

      <div className="flex flex-wrap gap-2">
        {[undefined, ...Object.keys(STATUTS_COLLABORATEUR)].map((s) => (
          <button
            key={s ?? "tous"}
            type="button"
            aria-pressed={statut === s}
            onClick={() => filtrer({ statut: s })}
            className={`rounded-full px-4 py-2 text-sm font-bold transition ${
              statut === s
                ? "bg-night text-white"
                : "bg-white ring-1 ring-border hover:ring-night/30"
            }`}
          >
            {s ? STATUTS_COLLABORATEUR[s as keyof typeof STATUTS_COLLABORATEUR].libelle : "Tous"}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          type="search"
          defaultValue={filtres.recherche ?? ""}
          onKeyDown={(e) => {
            if (e.key === "Enter")
              filtrer({ recherche: e.currentTarget.value.trim() || undefined });
          }}
          onBlur={(e) => filtrer({ recherche: e.currentTarget.value.trim() || undefined })}
          placeholder="Nom ou e-mail, puis Entrée"
          aria-label="Rechercher un collaborateur par nom ou e-mail"
          className={`${CHAMP} max-w-72`}
        />
        <select
          aria-label="Rôle de départ"
          value={filtres.role ?? ""}
          onChange={(e) => filtrer({ role: e.target.value || undefined })}
          className={`${CHAMP} max-w-72`}
        >
          <option value="">Tous les rôles</option>
          {catalogue.roles.map((r) => (
            <option key={r.id} value={r.id}>
              {r.libelle}
            </option>
          ))}
        </select>
        <select
          aria-label="Périmètre"
          value={filtres.perimetre ?? ""}
          onChange={(e) => filtrer({ perimetre: e.target.value || undefined })}
          className={`${CHAMP} max-w-56`}
        >
          <option value="">Tous les périmètres</option>
          <option value="national">National</option>
          {Object.entries(catalogue.dre).map(([id, libelle]) => (
            <option key={id} value={id}>
              DRE {libelle}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto rounded-3xl bg-white shadow-sm ring-1 ring-border">
        <table className="w-full min-w-[48rem] text-sm">
          <thead className="bg-mist-soft text-left text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
            <tr>
              <th scope="col" className="px-4 py-3">
                Collaborateur
              </th>
              <th scope="col" className="px-4 py-3">
                Rôle
              </th>
              <th scope="col" className="px-4 py-3">
                Périmètre
              </th>
              <th scope="col" className="px-4 py-3">
                Statut
              </th>
              <th scope="col" className="px-4 py-3">
                Sécurité
              </th>
              <th scope="col" className="px-4 py-3">
                Droits revus le
              </th>
            </tr>
          </thead>
          <tbody>
            {collaborateurs.map((c) => (
              <tr key={c.id} className="border-t hover:bg-mist-soft/60">
                <td className="px-4 py-3">
                  <Link
                    to="/admin/collaborateurs/$id"
                    params={{ id: c.id }}
                    className="font-bold text-logo-blue hover:underline"
                  >
                    {c.prenom} {c.nom}
                  </Link>
                  <span className="block text-xs font-medium text-muted-foreground">{c.email}</span>
                </td>
                <td className="px-4 py-3">
                  {c.super_admin
                    ? "Super-administrateur"
                    : (catalogue.roles.find((r) => r.id === c.role_depart)?.libelle ??
                      "Sur mesure")}
                </td>
                <td className="px-4 py-3">
                  {c.perimetre_dre ? `DRE ${catalogue.dre[c.perimetre_dre]}` : "National"}
                </td>
                <td className="px-4 py-3">
                  <BadgeStatut statut={c.statut} />
                </td>
                <td className="px-4 py-3 text-xs font-semibold">
                  {c.double_auth_active ? (
                    <span className="inline-flex items-center gap-1 text-primary">
                      <ShieldCheck className="size-3.5" /> 2FA active
                    </span>
                  ) : (
                    <span className="text-muted-foreground">Sans 2FA</span>
                  )}
                  {c.nb_droits_sensibles > 0 && (
                    <span className="block text-logo-red">
                      {c.nb_droits_sensibles} droit{c.nb_droits_sensibles > 1 ? "s" : ""} sensible
                      {c.nb_droits_sensibles > 1 ? "s" : ""}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{dateCourte(c.revu_le)}</td>
              </tr>
            ))}
            {collaborateurs.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-10 text-center font-semibold text-muted-foreground"
                >
                  Aucun collaborateur ne correspond à ces filtres.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <DialogueInvitation ouvert={ouvert} onOuvert={setOuvert} catalogue={catalogue} />
    </div>
  );
}

const CHAMP =
  "h-11 w-full rounded-xl border bg-white px-3 text-sm font-semibold outline-none focus:border-logo-blue";

function DialogueInvitation({
  ouvert,
  onOuvert,
  catalogue,
}: {
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
  catalogue: Catalogue;
}) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [prenom, setPrenom] = useState("");
  const [nom, setNom] = useState("");
  const [role, setRole] = useState("");
  const [perimetre, setPerimetre] = useState("");
  const [fin, setFin] = useState("");
  const [droits, setDroits] = useState(new Set<string>());
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [resultat, setResultat] = useState<InvitationCree | null>(null);
  const [copie, setCopie] = useState(false);

  const fermer = (o: boolean) => {
    onOuvert(o);
    if (!o) {
      setResultat(null);
      setErreur(null);
      setCopie(false);
    }
  };

  const choisirRole = (id: string) => {
    setRole(id);
    const preset = catalogue.roles.find((r) => r.id === id);
    if (preset) setDroits(new Set(preset.droits.map(cleDroit)));
  };

  const inviter = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const reponse = await inviterCollaborateur({
        email,
        prenom,
        nom,
        role_depart: (role || null) as never,
        perimetre_dre: perimetre || null,
        fin_acces: fin ? `${fin}T23:59:59Z` : null,
        droits: [...droits].map((cle) => {
          const [module, action] = cle.split(":");
          return { module, action } as Droit;
        }),
      });
      setResultat(reponse);
      setEmail("");
      setPrenom("");
      setNom("");
      setRole("");
      setPerimetre("");
      setFin("");
      setDroits(new Set());
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <Dialog open={ouvert} onOpenChange={fermer}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto rounded-3xl">
        <DialogHeader>
          <DialogTitle className="text-2xl text-logo-blue">Inviter un collaborateur</DialogTitle>
          <DialogDescription>
            Un e-mail part avec un lien d'activation valable 72 heures. Aucun mot de passe n'est
            envoyé.
          </DialogDescription>
        </DialogHeader>

        {resultat ? (
          <div className="space-y-4">
            <Alert className="rounded-2xl border-primary/40 bg-primary/10">
              <Check className="size-4" />
              <AlertDescription className="font-semibold">
                Invitation créée pour {resultat.collaborateur.email}.
                {resultat.collaborateur.invitation_envoi === "echec" &&
                  " L'e-mail n'a pas pu partir : renvoie l'invitation depuis sa fiche."}
              </AlertDescription>
            </Alert>
            {resultat.lien_de_test && (
              <div className="rounded-2xl bg-sun/20 p-4 text-sm">
                <p className="font-bold">
                  SMTP non configuré : transmets toi-même ce lien (environnement de test seulement).
                </p>
                <code className="mt-2 block break-all rounded-lg bg-white p-2 font-mono text-xs">
                  {resultat.lien_de_test}
                </code>
                <Button
                  variant="outline"
                  className="mt-2 rounded-full font-bold"
                  onClick={async () => {
                    await navigator.clipboard.writeText(resultat.lien_de_test ?? "");
                    setCopie(true);
                  }}
                >
                  {copie ? <Check className="size-4" /> : <Copy className="size-4" />}
                  {copie ? "Copié" : "Copier le lien"}
                </Button>
              </div>
            )}
            <Button onClick={() => fermer(false)} className="rounded-full font-bold">
              Terminer
            </Button>
          </div>
        ) : (
          <div className="space-y-5">
            {erreur && (
              <Alert variant="destructive">
                <AlertDescription>{erreur}</AlertDescription>
              </Alert>
            )}
            <div className="grid gap-3 sm:grid-cols-3">
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                E-mail
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={CHAMP}
                />
              </label>
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Prénom
                <input
                  value={prenom}
                  onChange={(e) => setPrenom(e.target.value)}
                  className={CHAMP}
                />
              </label>
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Nom
                <input value={nom} onChange={(e) => setNom(e.target.value)} className={CHAMP} />
              </label>
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Rôle de départ (préremplit les droits)
                <select
                  value={role}
                  onChange={(e) => choisirRole(e.target.value)}
                  className={CHAMP}
                >
                  <option value="">Sur mesure</option>
                  {catalogue.roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.libelle}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Périmètre
                <select
                  value={perimetre}
                  onChange={(e) => setPerimetre(e.target.value)}
                  className={CHAMP}
                >
                  <option value="">National</option>
                  {catalogue.dre_actives.map((id) => (
                    <option key={id} value={id}>
                      DRE {catalogue.dre[id]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Fin d'accès (facultatif)
                <input
                  type="date"
                  value={fin}
                  onChange={(e) => setFin(e.target.value)}
                  className={CHAMP}
                />
              </label>
            </div>
            <MatriceDroits catalogue={catalogue} valeur={droits} onChange={setDroits} />
            <Button
              onClick={inviter}
              disabled={enCours || !email || !prenom || !nom}
              className="btn-fx h-12 w-full rounded-full text-base font-bold"
            >
              {enCours && <Loader2 className="size-4 animate-spin" />}
              Envoyer l'invitation
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
