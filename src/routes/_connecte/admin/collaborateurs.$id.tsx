import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft, Ban, CheckCheck, KeyRound, Loader2, Mail, Pause, Play } from "lucide-react";
import { useState } from "react";

import { BadgeStatut } from "@/components/admin/BadgeStatut";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { MatriceDroits } from "@/components/admin/MatriceDroits";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cleDroit, dateCourte, dateHeure } from "@/lib/admin";
import {
  annulerInvitation,
  changerStatutCollaborateur,
  chargerCollaborateur,
  ErreurApi,
  marquerRevu,
  MESSAGE_INDISPONIBLE,
  modifierDroits,
  reinitialiserDoubleAuth,
  renvoyerInvitation,
  type Droit,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/collaborateurs/$id")({
  beforeLoad: ({ context }) => {
    if (!context.admin.super_admin) throw redirect({ to: "/admin" });
  },
  loader: ({ params }) => chargerCollaborateur(params.id),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: FicheCollaborateur,
});

type Action = "suspendre" | "reactiver" | "revoquer" | "double-auth" | "annuler";

const DIALOGUES: Record<
  Action,
  { titre: string; description: string; bouton: string; danger: boolean }
> = {
  suspendre: {
    titre: "Suspendre ce collaborateur",
    description: "Ses sessions sont coupées immédiatement. Tu pourras le réactiver.",
    bouton: "Suspendre",
    danger: true,
  },
  reactiver: {
    titre: "Réactiver ce collaborateur",
    description: "Il pourra de nouveau se connecter avec ses droits actuels.",
    bouton: "Réactiver",
    danger: false,
  },
  revoquer: {
    titre: "Révoquer ce collaborateur",
    description: "Retrait définitif : le compte ne pourra plus être réactivé.",
    bouton: "Révoquer",
    danger: true,
  },
  annuler: {
    titre: "Annuler l'invitation",
    description:
      "Le lien envoyé cesse de fonctionner tout de suite. Tu pourras renvoyer une invitation.",
    bouton: "Annuler l'invitation",
    danger: true,
  },
  "double-auth": {
    titre: "Réinitialiser la double authentification",
    description:
      "À utiliser si le téléphone est perdu. Il devra la réactiver à sa prochaine connexion.",
    bouton: "Réinitialiser",
    danger: true,
  },
};

const CHAMP =
  "h-11 w-full rounded-xl border bg-white px-3 text-sm font-semibold outline-none focus:border-logo-blue";

function FicheCollaborateur() {
  const { admin, catalogue } = Route.useRouteContext();
  const c = Route.useLoaderData();
  const router = useRouter();
  const moiMeme = c.identifiant === admin.identifiant;
  const [droits, setDroits] = useState(new Set(c.droits.map(cleDroit)));
  const [perimetre, setPerimetre] = useState(c.perimetre_dre ?? "");
  const [fin, setFin] = useState(c.fin_acces?.slice(0, 10) ?? "");
  const [motif, setMotif] = useState("");
  const [dialogue, setDialogue] = useState<Action | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; texte: string } | null>(null);
  const [enCours, setEnCours] = useState(false);

  const agir = async (fonction: () => Promise<unknown>, succes: string) => {
    setMessage(null);
    setEnCours(true);
    try {
      await fonction();
      setMessage({ ok: true, texte: succes });
      await router.invalidate();
    } catch (e) {
      setMessage({ ok: false, texte: e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE });
    } finally {
      setEnCours(false);
    }
  };

  const enregistrer = () =>
    agir(
      () =>
        modifierDroits(c.id, {
          droits: [...droits].map((cle) => {
            const [module, action] = cle.split(":");
            return { module, action } as Droit;
          }),
          perimetre_dre: perimetre || null,
          fin_acces: fin ? `${fin}T23:59:59Z` : null,
          motif: motif.trim(),
        }).then(() => setMotif("")),
      "Droits enregistrés et inscrits au journal.",
    );

  const invitation = c.statut === "invitation_envoyee" || c.statut === "invitation_expiree";

  return (
    <div className="space-y-6">
      <Link
        to="/admin/collaborateurs"
        className="inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue hover:underline"
      >
        <ArrowLeft className="size-4" /> Tous les collaborateurs
      </Link>

      <section className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl text-logo-blue">
              {c.prenom} {c.nom}
            </h1>
            <p className="mt-1 font-semibold text-muted-foreground">
              {c.email}
              {c.identifiant && <> · {c.identifiant}</>}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <BadgeStatut statut={c.statut} />
              {c.super_admin && (
                <span className="rounded-full bg-night px-2.5 py-0.5 text-xs font-extrabold text-white">
                  Super-administrateur
                </span>
              )}
              <span className="text-xs font-semibold text-muted-foreground">
                {c.double_auth_active
                  ? "Double authentification active"
                  : "Sans double authentification"}
                {" · "}Droits revus le {dateCourte(c.revu_le)}
              </span>
            </div>
            {invitation && (
              <p className="mt-2 text-sm font-medium text-muted-foreground">
                Invitation{" "}
                {c.statut === "invitation_expiree"
                  ? "expirée"
                  : `valable jusqu'au ${dateHeure(c.invitation_expire_le)}`}
                {c.invitation_envoi === "echec" && " · l'e-mail n'a pas pu partir"}
              </p>
            )}
          </div>
          {!moiMeme && (
            <div className="flex flex-wrap gap-2">
              {invitation && (
                <Button
                  variant="outline"
                  className="rounded-full font-bold"
                  disabled={enCours}
                  onClick={() =>
                    agir(
                      () => renvoyerInvitation(c.id),
                      "Nouvelle invitation envoyée : l'ancien lien ne marche plus.",
                    )
                  }
                >
                  <Mail className="size-4" /> Renvoyer l'invitation
                </Button>
              )}
              {c.statut === "invitation_envoyee" && (
                <Button
                  variant="outline"
                  className="rounded-full font-bold text-logo-red"
                  onClick={() => setDialogue("annuler")}
                >
                  <Ban className="size-4" /> Annuler l'invitation
                </Button>
              )}
              {c.statut === "actif" && (
                <>
                  <Button
                    variant="outline"
                    className="rounded-full font-bold"
                    disabled={enCours}
                    onClick={() => agir(() => marquerRevu(c.id), "Droits marqués comme revus.")}
                  >
                    <CheckCheck className="size-4" /> Marquer revu
                  </Button>
                  <Button
                    variant="outline"
                    className="rounded-full font-bold"
                    onClick={() => setDialogue("suspendre")}
                  >
                    <Pause className="size-4" /> Suspendre
                  </Button>
                </>
              )}
              {c.statut === "suspendu" && (
                <Button
                  variant="outline"
                  className="rounded-full font-bold"
                  onClick={() => setDialogue("reactiver")}
                >
                  <Play className="size-4" /> Réactiver
                </Button>
              )}
              {c.double_auth_active && c.statut !== "revoque" && (
                <Button
                  variant="outline"
                  className="rounded-full font-bold"
                  onClick={() => setDialogue("double-auth")}
                >
                  <KeyRound className="size-4" /> Réinitialiser la 2FA
                </Button>
              )}
              {(c.statut === "actif" || c.statut === "suspendu") && (
                <Button
                  variant="outline"
                  className="rounded-full font-bold text-logo-red"
                  onClick={() => setDialogue("revoquer")}
                >
                  <Ban className="size-4" /> Révoquer
                </Button>
              )}
            </div>
          )}
        </div>
        {message && (
          <Alert variant={message.ok ? "default" : "destructive"} className="mt-4">
            <AlertDescription className="font-semibold">{message.texte}</AlertDescription>
          </Alert>
        )}
      </section>

      <section className="space-y-4 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8">
        <h2 className="text-xl text-logo-blue">Droits et périmètre</h2>
        {moiMeme && (
          <p className="text-sm font-semibold text-muted-foreground">
            Tu ne peux pas modifier tes propres droits.
          </p>
        )}
        {c.super_admin ? (
          <p className="text-sm font-medium text-muted-foreground">
            Un super-administrateur a tous les droits, sur tout le territoire.
          </p>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Périmètre
                <select
                  value={perimetre}
                  disabled={moiMeme}
                  onChange={(e) => setPerimetre(e.target.value)}
                  className={CHAMP}
                >
                  <option value="">National</option>
                  {/* Les DRE actives, plus le périmètre actuel même s'il a été désactivé depuis. */}
                  {Object.entries(catalogue.dre)
                    .filter(([id]) => catalogue.dre_actives.includes(id) || id === perimetre)
                    .map(([id, libelle]) => (
                      <option key={id} value={id}>
                        DRE {libelle}
                      </option>
                    ))}
                </select>
              </label>
              <label className="grid gap-1 text-xs font-bold text-muted-foreground">
                Fin d'accès (facultatif)
                <input
                  type="date"
                  value={fin}
                  disabled={moiMeme}
                  onChange={(e) => setFin(e.target.value)}
                  className={CHAMP}
                />
              </label>
            </div>
            <MatriceDroits
              catalogue={catalogue}
              valeur={droits}
              onChange={setDroits}
              lectureSeule={moiMeme || c.statut === "revoque"}
            />
            {!moiMeme && c.statut !== "revoque" && (
              <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
                <label className="grid gap-1.5 text-sm font-bold">
                  Motif de la modification (inscrit au journal)
                  <Textarea
                    value={motif}
                    onChange={(e) => setMotif(e.target.value)}
                    maxLength={500}
                    rows={2}
                    className="font-medium"
                  />
                </label>
                <Button
                  onClick={enregistrer}
                  disabled={enCours || motif.trim().length < 3}
                  className="btn-fx h-11 rounded-full px-6 font-bold"
                >
                  {enCours && <Loader2 className="size-4 animate-spin" />}
                  Enregistrer
                </Button>
              </div>
            )}
          </>
        )}
      </section>

      {dialogue && (
        <DialogueMotif
          ouvert
          onOuvert={(o) => !o && setDialogue(null)}
          {...DIALOGUES[dialogue]}
          onConfirme={async (motifDialogue) => {
            if (dialogue === "double-auth") await reinitialiserDoubleAuth(c.id, motifDialogue);
            else if (dialogue === "annuler") await annulerInvitation(c.id, motifDialogue);
            else await changerStatutCollaborateur(c.id, dialogue, motifDialogue);
            await router.invalidate();
          }}
        />
      )}
    </div>
  );
}
