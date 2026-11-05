import { Link } from "@tanstack/react-router";
import { ArrowRight, CircleAlert, Crown, Hourglass, Send, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueDemandeClub } from "@/components/clubs/DialogueDemandeClub";
import { Button } from "@/components/ui/button";
import {
  annulerPassation,
  ErreurApi,
  proposerPassation,
  renvoyerDemandeClub,
  type AxePublic,
  type ClubPublic,
  type ClubResume,
  type EtablissementRattache,
  type PassationApercu,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { ETATS_CLUB } from "@/lib/clubs";

// Le bloc « Club » de l'espace élève (spec 019) : demande, état, passation de présidence.
export function BlocClub({
  club,
  passation,
  etablissement,
  axes,
  clubEtablissement = null,
  onRafraichir,
}: {
  club: ClubResume | null;
  passation: PassationApercu | null;
  etablissement: EtablissementRattache;
  axes: AxePublic[];
  clubEtablissement?: ClubPublic | null;
  onRafraichir: () => Promise<unknown>;
}) {
  const [demandeOuverte, setDemandeOuverte] = useState(false);
  const [renvoiOuvert, setRenvoiOuvert] = useState(false);
  const [passationOuverte, setPassationOuverte] = useState(false);
  const [annulationOuverte, setAnnulationOuverte] = useState(false);
  const [pseudonyme, setPseudonyme] = useState("");

  if (club === null) {
    // Un autre club est déjà actif dans l'établissement : la demande n'est plus proposable (§1).
    if (clubEtablissement) {
      return (
        <section
          aria-labelledby="titre-club"
          className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
        >
          <h2 id="titre-club" className="text-2xl">
            <span className="text-logo-blue">Mon</span> <span className="text-primary">club</span>
          </h2>
          <p className="mt-2 max-w-2xl font-medium text-ink/80">
            Ton établissement a déjà un club actif :{" "}
            <strong className="text-ink">{clubEtablissement.nom}</strong>. Pour le rejoindre ou
            proposer de le présider un jour, adresse-toi à l'équipe nationale.
          </p>
          <Link
            to="/clubs/$id"
            params={{ id: clubEtablissement.id }}
            className="mt-4 inline-flex items-center gap-1 font-bold text-logo-blue hover:underline"
          >
            Voir la fiche publique <ArrowRight aria-hidden className="size-4" />
          </Link>
        </section>
      );
    }
    // L'ancre attendue par le parcours : le formulaire s'ouvre depuis l'état vide de l'espace.
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
          Ton établissement n'a pas encore de Club Santé officiel. Si tu es désigné(e) président(e)
          par ton établissement, tu peux ouvrir son espace : l'équipe nationale vérifiera la demande
          avant l'activation.
        </p>
        <Button
          onClick={() => setDemandeOuverte(true)}
          className="mt-4 h-12 rounded-full px-6 font-bold"
        >
          <Send className="size-4" /> Ouvrir l'espace de mon club
        </Button>
        <DialogueDemandeClub
          ouvert={demandeOuverte}
          onOuvert={setDemandeOuverte}
          etablissement={etablissement}
          axes={axes}
          onCree={async () => {
            await onRafraichir();
          }}
        />
      </section>
    );
  }

  const etat = ETATS_CLUB[club.etat as keyof typeof ETATS_CLUB] ?? ETATS_CLUB.en_attente;

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
        <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${etat.classe}`}>
          {etat.libelle}
        </span>
      </div>

      {club.etat === "en_attente" && (
        <div className="mt-4 flex items-start gap-3 rounded-2xl bg-sun/20 p-4">
          <Hourglass aria-hidden className="mt-0.5 size-5 shrink-0 text-ink" />
          <p className="font-semibold text-ink">
            Ta demande est en attente de vérification par l'équipe nationale. Rien n'est public pour
            l'instant et aucun point n'est crédité.
          </p>
        </div>
      )}

      {club.etat === "refuse" && (
        <div className="mt-4 space-y-3">
          <div className="flex items-start gap-3 rounded-2xl bg-logo-red/10 p-4">
            <CircleAlert aria-hidden className="mt-0.5 size-5 shrink-0 text-logo-red" />
            <div>
              <p className="font-bold text-ink">Demande refusée</p>
              {club.motif_refus && (
                <p className="mt-1 font-medium text-ink/80">Motif : {club.motif_refus}</p>
              )}
            </div>
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            Vérifie les informations auprès de ton établissement, puis renvoie ta demande : elle
            repassera en attente de vérification.
          </p>
          <Button
            variant="outline"
            onClick={() => setRenvoiOuvert(true)}
            className="rounded-full font-bold"
          >
            <Send className="size-4" /> Renvoyer ma demande
          </Button>
          <DialogueFormulaire
            ouvert={renvoiOuvert}
            onOuvert={setRenvoiOuvert}
            titre="Renvoyer cette demande ?"
            description={`« ${club.nom} » repassera en attente de vérification. Le motif du refus précédent reste au journal.`}
            bouton="Renvoyer"
            onEnvoie={async () => {
              await renvoyerDemandeClub();
              await onRafraichir();
            }}
          />
        </div>
      )}

      {club.etat === "actif" && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm font-semibold text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <ShieldCheck aria-hidden className="size-4 text-primary" />
              Club actif
            </span>
            <Link
              to="/clubs/$id"
              params={{ id: club.id }}
              className="inline-flex items-center gap-1 font-bold text-logo-blue hover:underline"
            >
              Voir la fiche publique <ArrowRight aria-hidden className="size-4" />
            </Link>
          </div>

          {club.president ? (
            <div className="rounded-2xl border p-4">
              <p className="flex items-center gap-2 font-bold text-ink">
                <Crown aria-hidden className="size-5 text-primary" /> Tu présides ce club
              </p>
              <p className="mt-1 text-sm font-medium text-muted-foreground">
                Tu peux transmettre la présidence à un autre élève de ton établissement. L'équipe
                nationale valide la passation.
              </p>

              {passation?.etat === "en_attente" && (
                <div className="mt-3 space-y-2">
                  <p className="rounded-xl bg-sun/20 px-3 py-2 text-sm font-semibold text-ink">
                    Passation en attente : <strong>{passation.successeur_pseudonyme}</strong>,
                    proposée le {dateCourte(passation.propose_le)}.
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

              {(!passation || passation.etat !== "en_attente") && (
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
                description="Indique le pseudonyme exact d'un élève actif de ton établissement, puis l'équipe nationale validera cette proposition."
                bouton="Proposer cette passation"
                onEnvoie={async () => {
                  if (pseudonyme.trim().length < 3) {
                    throw new ErreurApi(422, "Indique le pseudonyme du successeur.");
                  }
                  await proposerPassation(pseudonyme.trim(), club.version);
                  await onRafraichir();
                }}
              >
                <Champ libelle="Pseudonyme du successeur">
                  <input
                    value={pseudonyme}
                    onChange={(e) => setPseudonyme(e.target.value)}
                    maxLength={60}
                    placeholder="Ex. : Kofi Curieux"
                    className={CHAMP_ADMIN}
                  />
                </Champ>
              </DialogueFormulaire>
            </div>
          ) : (
            <p className="rounded-2xl bg-mist-soft px-4 py-3 text-sm font-medium text-muted-foreground">
              Tu n'es pas président de ce club : seul le président peut proposer une passation.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
