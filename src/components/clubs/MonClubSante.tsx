import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  CalendarClock,
  Check,
  Crown,
  HeartPulse,
  Hourglass,
  MapPin,
  UserMinus,
  UserX,
  X,
} from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { Button } from "@/components/ui/button";
import {
  confirmerPassationEncadreur,
  deciderAffiliation,
  ErreurApi,
  proposerPresident,
  refuserPassationEncadreur,
  signalerDesistement,
  type AffiliationDuClub,
  type AffiliationsDuClub,
  type MembreEquipe,
  type MonClubSante,
  type PassationAConfirmer,
} from "@/lib/api/client";
import { STATUTS_CLUB } from "@/lib/clubs";
import { dateCourte } from "@/lib/dates";
import { libelleClasse } from "@/lib/classes";
import { libelleFonction } from "@/lib/fonctions";

const LIBELLES_SIGNALEMENT = {
  en_attente: "En attente de l'équipe",
  confirme: "Confirmé",
  rejete: "Rejeté",
} as const;

function Jauge({ libelle, valeur, seuil }: { libelle: string; valeur: number; seuil: number }) {
  const atteint = valeur >= seuil;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 text-sm font-bold">
        <span className="text-ink">{libelle}</span>
        <span className={atteint ? "text-primary" : "text-ink/70"}>
          {valeur} / {seuil}
        </span>
      </div>
      <div
        className="mt-1 h-2.5 overflow-hidden rounded-full bg-mist"
        role="progressbar"
        aria-label={libelle}
        aria-valuemin={0}
        aria-valuemax={seuil}
        aria-valuenow={Math.min(valeur, seuil)}
      >
        <div
          className={`h-full rounded-full ${atteint ? "bg-primary" : "bg-logo-blue"}`}
          style={{ width: `${Math.min(100, Math.round((valeur / seuil) * 100))}%` }}
        />
      </div>
    </div>
  );
}

function MessageStatut({ club }: { club: MonClubSante }) {
  const { seuils } = club;
  if (club.statut === "en_constitution")
    return (
      <p className="rounded-2xl bg-mist-soft px-4 py-3 text-sm font-medium text-ink/80">
        Le club s'active tout seul dès qu'il réunit {seuils.encadreurs} encadreurs et{" "}
        {seuils.eleves} élèves confirmés. Confirme les élèves de ton établissement pour l'y aider.
      </p>
    );
  if (club.statut === "en_regularisation" && club.regularisation_jusquau)
    return (
      <p className="flex items-start gap-2 rounded-2xl bg-sun/25 px-4 py-3 text-sm font-semibold text-ink">
        <CalendarClock aria-hidden className="mt-0.5 size-4 shrink-0" />
        Le club est passé sous le seuil. Il a jusqu'au {dateCourte(
          club.regularisation_jusquau,
        )}{" "}
        pour retrouver {seuils.encadreurs} encadreurs et {seuils.eleves} élèves, sinon il sera
        suspendu.
      </p>
    );
  if (club.statut === "suspendu")
    return (
      <p className="rounded-2xl bg-logo-red/10 px-4 py-3 text-sm font-semibold text-ink">
        Le club est suspendu : il ne publie plus et ne gagne plus de points. Il redevient actif dès
        qu'il retrouve {seuils.encadreurs} encadreurs et {seuils.eleves} élèves confirmés.
      </p>
    );
  return null;
}

// Le résumé de « Mon Club Santé » dans l'espace de l'encadreur (spec 033).
export function ResumeClubSante({ club }: { club: MonClubSante | null }) {
  if (club === null)
    return (
      <p className="rounded-3xl bg-mist-soft p-6 font-medium text-muted-foreground">
        Ton club n'a pas pu être chargé : recharge la page.
      </p>
    );
  const statut = STATUTS_CLUB[club.statut];
  return (
    <section
      aria-labelledby="titre-mon-club-sante"
      className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 id="titre-mon-club-sante" className="text-2xl">
          <span className="text-logo-blue">Mon Club</span>{" "}
          <span className="text-primary">Santé</span>
        </h2>
        <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${statut.classe}`}>
          {statut.libelle}
        </span>
      </div>
      <p className="mt-1 font-extrabold text-ink">{club.nom}</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Jauge libelle="Encadreurs" valeur={club.nb_encadreurs} seuil={club.seuils.encadreurs} />
        <Jauge libelle="Élèves confirmés" valeur={club.nb_eleves} seuil={club.seuils.eleves} />
      </div>
      <div className="mt-4">
        <MessageStatut club={club} />
      </div>
      <Link
        to="/mon-club-sante"
        className="btn-fx mt-4 inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-sm font-bold text-primary-foreground"
      >
        Ouvrir Mon Club Santé
        {club.a_confirmer > 0 &&
          ` · ${club.a_confirmer} élève${club.a_confirmer > 1 ? "s" : ""} à confirmer`}
        <ArrowRight className="size-4" />
      </Link>
    </section>
  );
}

function Carte({ titre, children }: { titre: [string, string]; children: React.ReactNode }) {
  return (
    <section className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
      <h2 className="text-2xl">
        <span className="text-logo-blue">{titre[0]}</span>{" "}
        <span className="text-primary">{titre[1]}</span>
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

// La page « Mon Club Santé » (spec 033) : fiche, effectifs, équipe, élèves à confirmer, président.
export function EspaceClubSante({
  club,
  affiliations,
  onRafraichir,
}: {
  club: MonClubSante;
  affiliations: AffiliationsDuClub;
  onRafraichir: () => Promise<unknown>;
}) {
  const [aRefuser, setARefuser] = useState<AffiliationDuClub | null>(null);
  const [aRetirer, setARetirer] = useState<AffiliationDuClub | null>(null);
  const [desistement, setDesistement] = useState<MembreEquipe | null>(null);
  const [presidentOuvert, setPresidentOuvert] = useState(false);
  const [choixPresident, setChoixPresident] = useState("");
  const [passationAConfirmer, setPassationAConfirmer] = useState<PassationAConfirmer | null>(null);
  const [passationARefuser, setPassationARefuser] = useState<PassationAConfirmer | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const statut = STATUTS_CLUB[club.statut];
  const enService = club.statut === "actif" || club.statut === "en_regularisation";
  const { etablissement } = club;

  const confirmer = async (affiliation: AffiliationDuClub) => {
    setErreur(null);
    try {
      await deciderAffiliation(affiliation.id, "confirmer", affiliation.version);
      await onRafraichir();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : "La confirmation n'a pas abouti : réessaie.");
    }
  };

  return (
    <div className="mt-6 space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-lg font-extrabold text-ink">{club.nom}</p>
            <p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
              <MapPin aria-hidden className="size-4" />
              {[etablissement.region, etablissement.dre, etablissement.iesg]
                .filter(Boolean)
                .join(" · ")}
            </p>
            {club.actif_le && (
              <p className="mt-1 text-sm font-semibold text-ink/70">
                Activé le {dateCourte(club.actif_le)}
              </p>
            )}
          </div>
          <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${statut.classe}`}>
            {statut.libelle}
          </span>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Jauge libelle="Encadreurs" valeur={club.nb_encadreurs} seuil={club.seuils.encadreurs} />
          <Jauge libelle="Élèves confirmés" valeur={club.nb_eleves} seuil={club.seuils.eleves} />
        </div>
        <div className="mt-4">
          <MessageStatut club={club} />
        </div>
      </section>

      {erreur && (
        <p role="alert" className="rounded-2xl bg-logo-red/10 px-4 py-3 font-semibold text-ink">
          {erreur}
        </p>
      )}

      {club.passations_a_confirmer.length > 0 && (
        <Carte titre={["Président", "à confirmer"]}>
          <ul className="space-y-3">
            {club.passations_a_confirmer.map((p) => (
              <li key={p.id} className="rounded-2xl bg-sun/20 p-4">
                <p className="flex items-start gap-2 font-semibold text-ink">
                  <Crown aria-hidden className="mt-0.5 size-5 shrink-0" />
                  <span>
                    {p.president_sortant_pseudonyme} propose{" "}
                    <strong>{p.successeur_pseudonyme}</strong> comme président. Confirme ce choix
                    avant la validation de l'équipe nationale.
                  </span>
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    onClick={() => setPassationAConfirmer(p)}
                    className="rounded-full font-bold"
                  >
                    Confirmer
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setPassationARefuser(p)}
                    className="rounded-full font-bold"
                  >
                    Refuser
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </Carte>
      )}

      <Carte titre={["Élèves", "à confirmer"]}>
        <p className="text-sm font-medium text-muted-foreground">
          Confirme seulement les élèves que tu sais inscrits dans ton établissement. Tu ne vois que
          leur pseudonyme et leur classe.
        </p>
        {affiliations.a_confirmer.length === 0 ? (
          <p className="mt-3 rounded-2xl bg-mist-soft px-4 py-3 font-medium text-muted-foreground">
            Aucun élève n'attend de confirmation.
          </p>
        ) : (
          <ul className="mt-3 divide-y">
            {affiliations.a_confirmer.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <span>
                  <span className="font-bold text-ink">{a.pseudonyme}</span>{" "}
                  <span className="text-sm font-medium text-muted-foreground">
                    · {libelleClasse(a.classe)} · inscrit le {dateCourte(a.demande_le)}
                  </span>
                </span>
                <span className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => void confirmer(a)}
                    className="rounded-full font-bold"
                    aria-label={`Confirmer ${a.pseudonyme}`}
                  >
                    <Check className="size-4" /> Confirmer
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setARefuser(a)}
                    className="rounded-full font-bold"
                    aria-label={`Refuser ${a.pseudonyme}`}
                  >
                    <X className="size-4" /> Refuser
                  </Button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </Carte>

      <div className="grid gap-6 lg:grid-cols-2">
        <Carte titre={["Équipe", "d'encadrement"]}>
          <ul className="divide-y">
            {club.equipe.map((m) => (
              <li
                key={m.utilisateur_id}
                className="flex flex-wrap items-center justify-between gap-2 py-3"
              >
                <span>
                  <span className="font-bold text-ink">
                    {m.prenom} {m.nom}
                    {m.moi && " (toi)"}
                  </span>
                  <span className="block text-sm font-medium text-muted-foreground">
                    {libelleFonction(m.fonction)}
                    {m.signalement_en_attente && " · désistement signalé"}
                  </span>
                </span>
                {!m.moi && !m.signalement_en_attente && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setDesistement(m)}
                    className="rounded-full font-bold"
                  >
                    <UserX className="size-4" /> Signaler un départ
                  </Button>
                )}
              </li>
            ))}
          </ul>
          {club.mes_signalements.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-extrabold text-ink">Mes signalements</p>
              <ul className="mt-2 space-y-2 text-sm">
                {club.mes_signalements.map((s) => (
                  <li
                    key={s.id}
                    className="rounded-xl bg-mist-soft px-3 py-2 font-medium text-ink/80"
                  >
                    {s.encadreur_prenom} {s.encadreur_nom} · {dateCourte(s.signale_le)} ·{" "}
                    <strong>{LIBELLES_SIGNALEMENT[s.etat]}</strong>
                    {s.motif_decision && ` : ${s.motif_decision}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Carte>

        <Carte titre={["Le", "président"]}>
          {club.president_pseudonyme ? (
            <p className="flex items-center gap-2 font-bold text-ink">
              <Crown aria-hidden className="size-5 text-primary" /> {club.president_pseudonyme}
            </p>
          ) : club.president_propose ? (
            <p className="flex items-start gap-2 rounded-2xl bg-sun/20 p-3 font-semibold text-ink">
              <Hourglass aria-hidden className="mt-0.5 size-5 shrink-0" />
              {club.president_propose} est proposé : l'équipe nationale doit valider.
            </p>
          ) : enService ? (
            <>
              <p className="font-medium text-ink/80">
                Le club n'a pas encore de président. Propose un élève confirmé : l'équipe nationale
                validera ton choix.
              </p>
              <Button
                onClick={() => {
                  setChoixPresident("");
                  setPresidentOuvert(true);
                }}
                className="mt-3 rounded-full font-bold"
              >
                <Crown className="size-4" /> Proposer un président
              </Button>
            </>
          ) : (
            <p className="font-medium text-muted-foreground">
              Un président pourra être proposé dès que le club sera actif.
            </p>
          )}
        </Carte>
      </div>

      <Carte titre={["Élèves", "confirmés"]}>
        {affiliations.confirmees.length === 0 ? (
          <p className="rounded-2xl bg-mist-soft px-4 py-3 font-medium text-muted-foreground">
            Aucun élève confirmé pour l'instant.
          </p>
        ) : (
          <ul className="divide-y">
            {affiliations.confirmees.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <span>
                  <span className="font-bold text-ink">{a.pseudonyme}</span>
                  {a.president && (
                    <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-extrabold text-primary">
                      Président
                    </span>
                  )}
                  <span className="block text-sm font-medium text-muted-foreground">
                    {libelleClasse(a.classe)}
                    {a.depuis && ` · confirmé le ${dateCourte(a.depuis)}`}
                  </span>
                </span>
                {!a.president && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setARetirer(a)}
                    className="rounded-full font-bold"
                    aria-label={`Retirer ${a.pseudonyme}`}
                  >
                    <UserMinus className="size-4" /> Retirer
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Carte>

      <DialogueMotif
        ouvert={aRefuser !== null}
        onOuvert={(o) => !o && setARefuser(null)}
        titre={`Refuser ${aRefuser?.pseudonyme ?? ""} ?`}
        description="L'élève lira ton motif dans son espace."
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!aRefuser) return;
          await deciderAffiliation(aRefuser.id, "refuser", aRefuser.version, motif);
          setARefuser(null);
          await onRafraichir();
        }}
      />
      <DialogueMotif
        ouvert={aRetirer !== null}
        onOuvert={(o) => !o && setARetirer(null)}
        titre={`Retirer ${aRetirer?.pseudonyme ?? ""} du club ?`}
        description="L'élève ne comptera plus dans les effectifs du club. Il lira ton motif dans son espace."
        bouton="Retirer"
        danger
        onConfirme={async (motif) => {
          if (!aRetirer) return;
          await deciderAffiliation(aRetirer.id, "retirer", aRetirer.version, motif);
          setARetirer(null);
          await onRafraichir();
        }}
      />
      <DialogueMotif
        ouvert={desistement !== null}
        onOuvert={(o) => !o && setDesistement(null)}
        titre={`Signaler le départ de ${desistement?.prenom ?? ""} ${desistement?.nom ?? ""} ?`}
        description="L'équipe nationale vérifie ton signalement avant tout changement. Rien ne change tant qu'elle ne l'a pas confirmé."
        bouton="Signaler"
        onConfirme={async (motif) => {
          if (!desistement) return;
          await signalerDesistement(desistement.utilisateur_id, motif);
          setDesistement(null);
          await onRafraichir();
        }}
      />
      <DialogueFormulaire
        ouvert={presidentOuvert}
        onOuvert={setPresidentOuvert}
        titre="Proposer un président"
        description="L'élève choisi gérera l'espace du club avec son compte. L'équipe nationale valide ta proposition."
        bouton="Proposer"
        onEnvoie={async () => {
          if (!choixPresident) throw new ErreurApi(422, "Choisis un élève confirmé.");
          await proposerPresident(choixPresident);
          await onRafraichir();
        }}
      >
        <Champ libelle="Élève proposé">
          <select
            value={choixPresident}
            onChange={(e) => setChoixPresident(e.target.value)}
            className={CHAMP_ADMIN}
          >
            <option value="">Choisis un élève</option>
            {affiliations.confirmees.map((a) => (
              <option key={a.id} value={a.id}>
                {a.pseudonyme} ({libelleClasse(a.classe)})
              </option>
            ))}
          </select>
        </Champ>
      </DialogueFormulaire>
      <DialogueFormulaire
        ouvert={passationAConfirmer !== null}
        onOuvert={(o) => !o && setPassationAConfirmer(null)}
        titre="Confirmer ce président ?"
        description={
          passationAConfirmer
            ? `${passationAConfirmer.successeur_pseudonyme} deviendra président du club après la validation de l'équipe nationale.`
            : ""
        }
        bouton="Confirmer"
        onEnvoie={async () => {
          if (!passationAConfirmer) return;
          await confirmerPassationEncadreur(
            passationAConfirmer.club_id,
            passationAConfirmer.version,
          );
          setPassationAConfirmer(null);
          await onRafraichir();
        }}
      />
      <DialogueMotif
        ouvert={passationARefuser !== null}
        onOuvert={(o) => !o && setPassationARefuser(null)}
        titre="Refuser cette passation ?"
        description="Le président du club lira ton motif. La présidence ne change pas."
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          if (!passationARefuser) return;
          await refuserPassationEncadreur(
            passationARefuser.club_id,
            passationARefuser.version,
            motif,
          );
          setPassationARefuser(null);
          await onRafraichir();
        }}
      />
      <p className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <HeartPulse aria-hidden className="size-4 text-primary" />
        Agenda, rapports d'activité et archives arriveront bientôt dans cet espace.
      </p>
    </div>
  );
}
