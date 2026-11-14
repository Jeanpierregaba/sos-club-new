import { Link } from "@tanstack/react-router";
import { ArrowRight, CircleAlert, Crown, Hourglass, ShieldCheck, Users } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Button } from "@/components/ui/button";
import {
  annulerPassation,
  ErreurApi,
  proposerPassation,
  redemanderAffiliation,
  type AdhesionResume,
  type ClubResume,
  type MembresDuClub,
  type PassationApercu,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { SEUIL_ELEVES, SEUIL_ENCADREURS, STATUTS_CLUB } from "@/lib/clubs";

const enAttente = (passation: PassationApercu) =>
  passation.etat === "en_attente" || passation.etat === "en_attente_encadreur";

// Le bloc « Mon club » de l'espace élève (spec 033) : le club de son établissement, né et activé seul au seuil de
// 3 encadreurs et 21 élèves confirmés, l'état de son affiliation, et la passation s'il préside (spec 019).
export function BlocClub({
  club,
  affiliation,
  passation,
  membres = null,
  onRafraichir,
}: {
  club: ClubResume | null;
  affiliation: AdhesionResume | null;
  passation: PassationApercu | null;
  membres?: MembresDuClub | null;
  onRafraichir: () => Promise<unknown>;
}) {
  const [passationOuverte, setPassationOuverte] = useState(false);
  const [annulationOuverte, setAnnulationOuverte] = useState(false);
  const [pseudonyme, setPseudonyme] = useState("");

  if (club === null) {
    return (
      <section
        id="etat-vide"
        aria-labelledby="titre-club"
        className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
      >
        <h2 id="titre-club" className="text-2xl">
          <span className="text-logo-blue">Mon</span> <span className="text-primary">club</span>
        </h2>
        <p className="mt-2 max-w-2xl font-medium text-ink/80">
          Le Club Santé de ton établissement n'est pas encore ouvert sur la plateforme. Il s'ouvre
          tout seul dès que des élèves et des encadreurs de ton établissement s'inscrivent.
        </p>
      </section>
    );
  }

  const statut = STATUTS_CLUB[club.statut];
  const enService = club.statut === "actif" || club.statut === "en_regularisation";
  const successeurs = membres?.membres.filter((m) => !m.president) ?? [];

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
          <p className="text-sm font-medium text-muted-foreground">
            {club.etablissement.iesg} · {club.etablissement.dre}
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${statut.classe}`}>
          {statut.libelle}
        </span>
      </div>

      <EtatAffiliation affiliation={affiliation} onRafraichir={onRafraichir} />

      {club.statut === "en_constitution" && (
        <p className="mt-4 rounded-2xl bg-mist-soft px-4 py-3 text-sm font-medium text-ink/80">
          Ton club s'active tout seul dès que {SEUIL_ENCADREURS} encadreurs et {SEUIL_ELEVES} élèves
          de ton établissement sont confirmés. Invite tes camarades à s'inscrire !
        </p>
      )}
      {club.statut === "en_regularisation" && club.regularisation_jusquau && (
        <p className="mt-4 rounded-2xl bg-sun/25 px-4 py-3 text-sm font-semibold text-ink">
          Ton club est passé sous le seuil de {SEUIL_ENCADREURS} encadreurs et {SEUIL_ELEVES}{" "}
          élèves. Il a jusqu'au {dateCourte(club.regularisation_jusquau)} pour le retrouver, sinon
          il sera suspendu.
        </p>
      )}
      {club.statut === "suspendu" && (
        <p className="mt-4 rounded-2xl bg-logo-red/10 px-4 py-3 text-sm font-semibold text-ink">
          Ton club est suspendu : il ne publie plus et ne gagne plus de points. Tes points à toi
          restent. Il redevient actif dès qu'il retrouve {SEUIL_ENCADREURS} encadreurs et{" "}
          {SEUIL_ELEVES} élèves confirmés.
        </p>
      )}

      {club.statut !== "en_constitution" && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm font-semibold text-muted-foreground">
            {club.actif_le && (
              <span className="inline-flex items-center gap-1.5">
                <ShieldCheck aria-hidden className="size-4 text-primary" />
                Actif depuis le {dateCourte(club.actif_le)}
              </span>
            )}
            <Link
              to="/clubs/$id"
              params={{ id: club.id }}
              className="inline-flex items-center gap-1 font-bold text-logo-blue hover:underline"
            >
              Voir la fiche publique <ArrowRight aria-hidden className="size-4" />
            </Link>
          </div>

          {club.president && (
            <div className="rounded-2xl border p-4">
              <p className="flex items-center gap-2 font-bold text-ink">
                <Crown aria-hidden className="size-5 text-primary" /> Tu présides ce club
              </p>
              <p className="mt-1 text-sm font-medium text-muted-foreground">
                Tu peux transmettre la présidence à un autre membre confirmé du club. Un encadreur
                du club confirme ton choix ; l'équipe nationale le valide ensuite.
              </p>

              {passation && enAttente(passation) && (
                <div className="mt-3 space-y-2">
                  <p className="rounded-xl bg-sun/20 px-3 py-2 text-sm font-semibold text-ink">
                    Passation en attente{" "}
                    {passation.etat === "en_attente_encadreur"
                      ? "de la confirmation d'un encadreur"
                      : "de l'équipe nationale"}{" "}
                    : <strong>{passation.successeur_pseudonyme}</strong>, proposée le{" "}
                    {dateCourte(passation.propose_le)}.
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => setAnnulationOuverte(true)}
                    className="rounded-full font-bold"
                  >
                    Annuler ma proposition
                  </Button>
                  <DialogueFormulaire
                    ouvert={annulationOuverte}
                    onOuvert={setAnnulationOuverte}
                    titre="Annuler cette passation ?"
                    description={`${passation.successeur_pseudonyme} ne deviendra pas président et tu restes président du club.`}
                    bouton="Annuler la proposition"
                    danger
                    onEnvoie={async () => {
                      await annulerPassation();
                      await onRafraichir();
                    }}
                  />
                </div>
              )}

              {passation?.etat === "refusee" && (
                <p className="mt-3 rounded-xl bg-logo-red/10 px-3 py-2 text-sm font-semibold text-ink">
                  Passation vers {passation.successeur_pseudonyme} refusée
                  {passation.decide_le ? ` le ${dateCourte(passation.decide_le)}` : ""}
                  {passation.motif_refus ? ` : ${passation.motif_refus}` : "."}
                </p>
              )}

              {(!passation || !enAttente(passation)) && (
                <Button
                  onClick={() => {
                    setPseudonyme("");
                    setPassationOuverte(true);
                  }}
                  className="mt-3 rounded-full font-bold"
                >
                  <Crown className="size-4" /> Passer la présidence
                </Button>
              )}

              <DialogueFormulaire
                ouvert={passationOuverte}
                onOuvert={setPassationOuverte}
                titre="Passer la présidence"
                description="Choisis un membre confirmé du club. Un encadreur du club confirmera ton choix ; l'équipe nationale le validera ensuite."
                bouton="Proposer cette passation"
                onEnvoie={async () => {
                  if (pseudonyme.trim().length < 1) {
                    throw new ErreurApi(422, "Choisis le membre qui te succède.");
                  }
                  await proposerPassation(pseudonyme.trim(), club.version);
                  await onRafraichir();
                }}
              >
                <Champ libelle="Ton successeur">
                  {successeurs.length > 0 ? (
                    <select
                      value={pseudonyme}
                      onChange={(e) => setPseudonyme(e.target.value)}
                      className={CHAMP_ADMIN}
                    >
                      <option value="">Choisis un membre</option>
                      {successeurs.map((m) => (
                        <option key={m.id} value={m.pseudonyme}>
                          {m.pseudonyme}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <p className="rounded-xl bg-mist-soft px-3 py-2 text-sm font-medium text-muted-foreground">
                      Ton club n'a pas encore d'autre membre confirmé.
                    </p>
                  )}
                </Champ>
              </DialogueFormulaire>
            </div>
          )}

          {(club.president || affiliation?.etat === "active") && (
            <Link
              to="/mon-club"
              className="btn-fx inline-flex h-11 items-center gap-2 self-start rounded-full bg-primary px-5 text-sm font-bold text-primary-foreground"
            >
              {club.president && enService ? "Gérer mon club" : "Voir mon club"}
              <ArrowRight className="size-4" />
            </Link>
          )}
        </div>
      )}
    </section>
  );
}

// L'affiliation de l'élève au club de son établissement : confirmée par un encadreur du club ou par l'équipe.
function EtatAffiliation({
  affiliation,
  onRafraichir,
}: {
  affiliation: AdhesionResume | null;
  onRafraichir: () => Promise<unknown>;
}) {
  const [redemande, setRedemande] = useState(false);
  if (affiliation === null) return null;
  if (affiliation.etat === "active") {
    return (
      <p className="mt-4 flex items-center gap-2 text-sm font-bold text-primary">
        <Users aria-hidden className="size-4" /> Tu es membre confirmé de ce club.
      </p>
    );
  }
  if (affiliation.etat === "en_attente_validation" || affiliation.etat === "en_attente_president") {
    return (
      <div className="mt-4 flex items-start gap-3 rounded-2xl bg-sun/20 p-4">
        <Hourglass aria-hidden className="mt-0.5 size-5 shrink-0 text-ink" />
        <p className="font-semibold text-ink">
          Ton affiliation attend la confirmation d'un encadreur de ton établissement. Tu comptes
          dans les effectifs du club dès qu'il l'a confirmée.
        </p>
      </div>
    );
  }
  const motif =
    affiliation.etat === "refusee" ? affiliation.motif_refus : affiliation.motif_retrait;
  return (
    <div className="mt-4 flex items-start gap-3 rounded-2xl bg-logo-red/10 p-4">
      <CircleAlert aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-red" />
      <div>
        <p className="font-bold text-ink">
          {affiliation.etat === "refusee"
            ? "Affiliation refusée"
            : "Tu ne fais plus partie du club"}
        </p>
        {motif && <p className="mt-1 font-medium text-ink/80">Motif : {motif}</p>}
        <p className="mt-1 text-sm font-medium text-muted-foreground">
          Parles-en à un encadreur de ton établissement, puis redemande ton affiliation : elle
          repartira en attente de confirmation.
        </p>
        <Button
          variant="outline"
          onClick={() => setRedemande(true)}
          className="mt-3 rounded-full font-bold"
        >
          Redemander mon affiliation
        </Button>
        <DialogueFormulaire
          ouvert={redemande}
          onOuvert={setRedemande}
          titre="Redemander ton affiliation ?"
          description="Un encadreur de ton établissement, ou l'équipe, confirmera ta demande."
          bouton="Redemander"
          onEnvoie={async () => {
            await redemanderAffiliation();
            await onRafraichir();
          }}
        />
      </div>
    </div>
  );
}
