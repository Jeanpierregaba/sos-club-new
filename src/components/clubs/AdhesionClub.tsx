import { Link } from "@tanstack/react-router";
import { ArrowRight, CircleAlert, Hourglass, LogOut, UserPlus, Users } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ListeMembres } from "@/components/clubs/ListeMembres";
import { Button } from "@/components/ui/button";
import {
  demanderAdhesion,
  quitterClub,
  type AdhesionResume,
  type ClubPublic,
  type MembresDuClub,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

const ATTENTES: Partial<Record<AdhesionResume["etat"], string>> = {
  en_attente_president: "Ta demande attend la confirmation du président du club.",
  en_attente_validation:
    "Le président a confirmé ta demande : l'équipe de ta DRE doit encore la valider.",
};

// L'affiliation d'un élève au club de son établissement (spec 020) : rejoindre, suivre sa demande, voir les
// membres, quitter le club. `adhesion` est la dernière de l'élève, peut-être pour un autre club.
export function AdhesionClub({
  club,
  adhesion,
  membres,
  onRafraichir,
}: {
  club: ClubPublic;
  adhesion: AdhesionResume | null;
  membres: MembresDuClub | null;
  onRafraichir: () => Promise<unknown>;
}) {
  const [rejoindre, setRejoindre] = useState(false);
  const [quitter, setQuitter] = useState(false);
  const mienne = adhesion?.club_id === club.id ? adhesion : null;
  const attente = mienne ? ATTENTES[mienne.etat] : undefined;

  return (
    <section
      aria-labelledby="titre-club"
      className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="titre-club" className="text-2xl">
            <span className="text-logo-blue">Mon</span> <span className="text-primary">club</span>
          </h2>
          <p className="mt-1 text-lg font-extrabold text-ink">{club.nom}</p>
        </div>
        <Link
          to="/clubs/$id"
          params={{ id: club.id }}
          className="inline-flex items-center gap-1 text-sm font-bold text-logo-blue hover:underline"
        >
          Voir la fiche publique <ArrowRight aria-hidden className="size-4" />
        </Link>
      </div>

      {mienne?.etat === "active" ? (
        <div className="mt-4 space-y-4">
          <p className="flex items-center gap-2 font-semibold text-ink">
            <Users aria-hidden className="size-5 text-primary" />
            Tu es membre de ce club : tes points comptent aussi pour lui.
          </p>
          {membres && <ListeMembres liste={membres} />}
          <Button
            variant="outline"
            onClick={() => setQuitter(true)}
            className="rounded-full font-bold"
          >
            <LogOut className="size-4" /> Quitter le club
          </Button>
        </div>
      ) : attente ? (
        <div className="mt-4 space-y-3">
          <div className="flex items-start gap-3 rounded-2xl bg-sun/20 p-4">
            <Hourglass aria-hidden className="mt-0.5 size-5 shrink-0 text-ink" />
            <p className="font-semibold text-ink">
              {attente} Demande envoyée le {dateCourte(mienne!.demande_le)}.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => setQuitter(true)}
            className="rounded-full font-bold"
          >
            Annuler ma demande
          </Button>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {mienne?.etat === "refusee" && (
            <div className="flex items-start gap-3 rounded-2xl bg-logo-red/10 p-4">
              <CircleAlert aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-red" />
              <div>
                <p className="font-bold text-ink">Ta dernière demande a été refusée</p>
                {mienne.motif_refus && (
                  <p className="mt-1 font-medium text-ink/80">Motif : {mienne.motif_refus}</p>
                )}
              </div>
            </div>
          )}
          {mienne?.etat === "retiree" && mienne.motif_retrait && (
            <p className="rounded-2xl bg-mist-soft px-4 py-3 text-sm font-medium text-ink/80">
              Tu ne fais plus partie du club : {mienne.motif_retrait}
            </p>
          )}
          <p className="max-w-2xl font-medium text-ink/80">
            Ton établissement a un Club Santé actif. Rejoins-le pour participer à ses activités et
            faire compter tes points pour ton club.
          </p>
          <Button onClick={() => setRejoindre(true)} className="h-12 rounded-full px-6 font-bold">
            <UserPlus className="size-4" /> Rejoindre ce club
          </Button>
        </div>
      )}

      <DialogueFormulaire
        ouvert={rejoindre}
        onOuvert={setRejoindre}
        titre={`Rejoindre « ${club.nom} » ?`}
        description="Le président du club confirmera ta demande, puis l'équipe de ta DRE la validera."
        bouton="Envoyer ma demande"
        onEnvoie={async () => {
          await demanderAdhesion(club.id);
          await onRafraichir();
        }}
      />
      <DialogueFormulaire
        ouvert={quitter}
        onOuvert={setQuitter}
        titre={mienne?.etat === "active" ? "Quitter le club ?" : "Annuler ta demande ?"}
        description={
          mienne?.etat === "active"
            ? "Tu ne feras plus partie du club. Tu pourras redemander à le rejoindre plus tard."
            : "Ta demande sera retirée. Tu pourras en envoyer une nouvelle plus tard."
        }
        bouton={mienne?.etat === "active" ? "Quitter le club" : "Annuler ma demande"}
        danger
        onEnvoie={async () => {
          await quitterClub(club.id);
          await onRafraichir();
        }}
      />
    </section>
  );
}
