import { Link } from "@tanstack/react-router";
import { ArrowRight, Crown, Hourglass, LogOut, Map, Send, Users } from "lucide-react";
import { useState } from "react";

import { DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { ListeMembres } from "@/components/clubs/ListeMembres";
import { Button } from "@/components/ui/button";
import {
  confirmerPassationEncadreur,
  demanderRattachement,
  quitterClubEncadre,
  refuserPassationEncadreur,
  type ClubPublic,
  type MembresDuClub,
  type MesClubs,
  type PassationAConfirmer,
  type RattachementResume,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

const EN_COURS: RattachementResume["etat"][] = [
  "en_attente_president",
  "en_attente_validation",
  "actif",
];

const ETATS: Record<RattachementResume["etat"], { libelle: string; classe: string }> = {
  en_attente_president: { libelle: "Attend le président", classe: "bg-sun/30 text-ink" },
  en_attente_validation: { libelle: "Attend la validation", classe: "bg-sun/30 text-ink" },
  actif: { libelle: "Rattaché", classe: "bg-primary/15 text-primary" },
  refuse: { libelle: "Refusé", classe: "bg-logo-red/10 text-logo-red" },
  retire: { libelle: "Terminé", classe: "bg-mist text-muted-foreground" },
};

// « Mes clubs » dans l'espace d'un encadreur actif (spec 020) : les passations à confirmer (Q19), les
// rattachements et leur état, les membres de ses clubs (lecture seule) et la demande de rattachement au club
// de son établissement. Les autres clubs se demandent depuis leur fiche publique.
export function MesClubsEncadreur({
  mesClubs,
  clubEtablissement,
  membres,
  onRafraichir,
}: {
  mesClubs: MesClubs;
  clubEtablissement: ClubPublic | null;
  membres: Record<string, MembresDuClub>;
  onRafraichir: () => Promise<unknown>;
}) {
  const [demander, setDemander] = useState<ClubPublic | null>(null);
  const [quitter, setQuitter] = useState<RattachementResume | null>(null);
  const [aConfirmer, setAConfirmer] = useState<PassationAConfirmer | null>(null);
  const [aRefuser, setARefuser] = useState<PassationAConfirmer | null>(null);
  const [ouvert, setOuvert] = useState<string | null>(null);
  const enCours = mesClubs.rattachements.filter((r) => EN_COURS.includes(r.etat));
  const proposerEtablissement =
    clubEtablissement && !enCours.some((r) => r.club_id === clubEtablissement.id);

  return (
    <section
      aria-labelledby="titre-mes-clubs"
      className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
    >
      <h2 id="titre-mes-clubs" className="text-2xl">
        <span className="text-logo-blue">Mes</span> <span className="text-primary">clubs</span>
      </h2>

      {mesClubs.passations.length > 0 && (
        <div className="mt-4 space-y-3">
          {mesClubs.passations.map((p) => (
            <div key={p.id} className="rounded-2xl bg-sun/20 p-4">
              <p className="flex items-start gap-2 font-semibold text-ink">
                <Crown aria-hidden className="mt-0.5 size-5 shrink-0" />
                <span>
                  {p.club_nom} : {p.president_sortant_pseudonyme} propose{" "}
                  <strong>{p.successeur_pseudonyme}</strong> comme président. Confirme ce choix
                  avant la validation de l'équipe nationale.
                </span>
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button onClick={() => setAConfirmer(p)} className="rounded-full font-bold">
                  Confirmer
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setARefuser(p)}
                  className="rounded-full font-bold"
                >
                  Refuser
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {proposerEtablissement && (
        <div className="mt-4 rounded-2xl border p-4">
          <p className="font-medium text-ink/80">
            Ton établissement a un Club Santé actif :{" "}
            <strong className="text-ink">{clubEtablissement.nom}</strong>. Demande ton rattachement
            pour suivre ses élèves et ses activités.
          </p>
          <Button
            onClick={() => setDemander(clubEtablissement)}
            className="mt-3 rounded-full font-bold"
          >
            <Send className="size-4" /> Demander mon rattachement
          </Button>
        </div>
      )}

      {mesClubs.rattachements.length === 0 && !proposerEtablissement && (
        <p className="mt-4 rounded-2xl bg-mist-soft px-4 py-3 font-medium text-muted-foreground">
          Tu n'es rattaché à aucun club pour l'instant.
        </p>
      )}

      {mesClubs.rattachements.length > 0 && (
        <ul className="mt-4 space-y-3">
          {mesClubs.rattachements.map((r) => {
            const etat = ETATS[r.etat];
            const liste = membres[r.club_id];
            return (
              <li key={r.id} className="rounded-2xl border p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-bold text-ink">{r.club_nom}</p>
                    <p className="text-sm font-medium text-muted-foreground">
                      Demande du {dateCourte(r.demande_le)}
                      {r.supplementaire && r.etat !== "actif"
                        ? " · club supplémentaire : l'équipe nationale doit l'autoriser"
                        : ""}
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${etat.classe}`}>
                    {etat.libelle}
                  </span>
                </div>
                {r.etat === "refuse" && r.motif_refus && (
                  <p className="mt-2 text-sm font-medium text-ink/80">Motif : {r.motif_refus}</p>
                )}
                {r.etat === "retire" && r.motif_retrait && (
                  <p className="mt-2 text-sm font-medium text-ink/80">{r.motif_retrait}</p>
                )}
                {r.etat.startsWith("en_attente") && (
                  <p className="mt-2 flex items-center gap-2 text-sm font-semibold text-ink">
                    <Hourglass aria-hidden className="size-4" />
                    {r.etat === "en_attente_president"
                      ? "Le président du club doit confirmer ta demande."
                      : "Le président a confirmé : l'équipe valide ta demande."}
                  </p>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  {r.etat === "actif" && liste && (
                    <Button
                      variant="outline"
                      size="sm"
                      aria-expanded={ouvert === r.club_id}
                      onClick={() => setOuvert(ouvert === r.club_id ? null : r.club_id)}
                      className="rounded-full font-bold"
                    >
                      <Users className="size-4" />{" "}
                      {ouvert === r.club_id
                        ? "Masquer les membres"
                        : `Voir les membres (${liste.membres.length})`}
                    </Button>
                  )}
                  <Link
                    to="/clubs/$id"
                    params={{ id: r.club_id }}
                    className="inline-flex items-center gap-1 text-sm font-bold text-logo-blue hover:underline"
                  >
                    Fiche du club <ArrowRight aria-hidden className="size-4" />
                  </Link>
                  {r.etat === "actif" && (
                    <Link
                      to="/mon-club"
                      search={{ club: r.club_id }}
                      className="inline-flex items-center gap-1 text-sm font-bold text-logo-blue hover:underline"
                    >
                      Espace du club <ArrowRight aria-hidden className="size-4" />
                    </Link>
                  )}
                  {EN_COURS.includes(r.etat) && (
                    <button
                      type="button"
                      onClick={() => setQuitter(r)}
                      className="inline-flex items-center gap-1 text-sm font-bold text-logo-red hover:underline"
                    >
                      <LogOut aria-hidden className="size-4" />
                      {r.etat === "actif" ? "Quitter ce club" : "Annuler la demande"}
                    </button>
                  )}
                </div>
                {ouvert === r.club_id && liste && (
                  <div className="mt-4">
                    <ListeMembres liste={liste} />
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <Link
        to="/carte-des-clubs"
        className="mt-4 inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue hover:underline"
      >
        <Map aria-hidden className="size-4" /> Encadrer un autre club : trouve-le sur la carte
      </Link>

      <DialogueFormulaire
        ouvert={demander !== null}
        onOuvert={(o) => !o && setDemander(null)}
        titre={`Te rattacher à « ${demander?.nom ?? ""} » ?`}
        description="Le président du club confirmera ta demande, puis l'équipe la validera."
        bouton="Envoyer ma demande"
        onEnvoie={async () => {
          if (!demander) return;
          await demanderRattachement(demander.id);
          setDemander(null);
          await onRafraichir();
        }}
      />
      <DialogueFormulaire
        ouvert={quitter !== null}
        onOuvert={(o) => !o && setQuitter(null)}
        titre={quitter?.etat === "actif" ? "Quitter ce club ?" : "Annuler ta demande ?"}
        description={
          quitter?.etat === "actif"
            ? `Tu ne seras plus rattaché à ${quitter.club_nom}. Tu pourras redemander plus tard.`
            : "Ta demande sera retirée."
        }
        bouton={quitter?.etat === "actif" ? "Quitter le club" : "Annuler la demande"}
        danger
        onEnvoie={async () => {
          if (!quitter) return;
          await quitterClubEncadre(quitter.club_id);
          setQuitter(null);
          await onRafraichir();
        }}
      />
      <DialogueFormulaire
        ouvert={aConfirmer !== null}
        onOuvert={(o) => !o && setAConfirmer(null)}
        titre="Confirmer ce président ?"
        description={
          aConfirmer
            ? `${aConfirmer.successeur_pseudonyme} deviendra président de ${aConfirmer.club_nom} après la validation de l'équipe nationale.`
            : ""
        }
        bouton="Confirmer"
        onEnvoie={async () => {
          if (!aConfirmer) return;
          await confirmerPassationEncadreur(aConfirmer.club_id, aConfirmer.version);
          setAConfirmer(null);
          await onRafraichir();
        }}
      />
      <DialogueMotif
        ouvert={aRefuser !== null}
        onOuvert={(o) => !o && setARefuser(null)}
        titre="Refuser cette passation ?"
        description="Le président du club lira ton motif. La présidence ne change pas."
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!aRefuser) return;
          await refuserPassationEncadreur(aRefuser.club_id, aRefuser.version, motif);
          setARefuser(null);
          await onRafraichir();
        }}
      />
    </section>
  );
}
