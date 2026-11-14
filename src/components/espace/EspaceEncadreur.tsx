import { useRouter } from "@tanstack/react-router";
import { CircleAlert, Hourglass, KeyRound, Loader2, Pencil, Send } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { ChoixEtablissement, type EtablissementChoisi } from "@/components/ChoixEtablissement";
import { ResumeClubSante } from "@/components/clubs/MonClubSante";
import { PointsClub } from "@/components/espace/TableauAnnuel";
import {
  CartesPoints,
  DernieresLignes,
  DialogueMotDePasse,
  EnTeteEspace,
  EtablissementAffiche,
  Info,
  MotDePasseChange,
} from "@/components/espace/commun";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  modifierProfilEncadreur,
  renvoyerDemandeEncadreur,
  type EspaceEncadreur as Espace,
  type Fonction,
  type MonClubSante,
  type PointsDuClub,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { FONCTIONS, LIBELLES_VERIFICATION, libelleFonction } from "@/lib/fonctions";
import { normaliserTelephone, telephoneValide } from "@/lib/telephone";

// L'espace d'un encadreur (spec 018) : en attente, refusé ou actif ; « Mon Club Santé » une fois vérifié (spec 033).
export function EspaceEncadreur({
  espace,
  prenom,
  monClubSante = null,
  pointsClub = null,
}: {
  espace: Espace;
  prenom: string;
  monClubSante?: MonClubSante | null;
  pointsClub?: PointsDuClub | null;
}) {
  const router = useRouter();
  const [profil, setProfil] = useState(false);
  const [motDePasse, setMotDePasse] = useState(false);
  const [motDePasseChange, setMotDePasseChange] = useState(false);

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <EnTeteEspace
          nom={prenom}
          articles={espace.etat === "actif"}
          monClub={monClubSante !== null && monClubSante.statut !== "en_constitution"}
          monClubSante={monClubSante !== null}
        >
          {motDePasseChange && <MotDePasseChange />}
          {espace.etat === "en_attente" && <EnAttente espace={espace} />}
          {espace.etat === "refuse" && <Refuse espace={espace} />}
        </EnTeteEspace>

        {!espace.telephone && (
          <div className="mt-6 flex flex-col gap-4 rounded-3xl bg-sun/25 p-5 ring-1 ring-sun sm:flex-row sm:items-center">
            <p className="flex-1 font-semibold text-ink">
              Ajoute ton téléphone ou ton WhatsApp : l'équipe en a besoin pour te joindre.
            </p>
            <Button onClick={() => setProfil(true)} className="btn-fx rounded-full font-bold">
              Ajouter mon téléphone
            </Button>
          </div>
        )}

        {espace.etat === "actif" && espace.points && <CartesPoints points={espace.points} />}
        {pointsClub && <PointsClub points={pointsClub} />}

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          {espace.etat === "actif" && espace.points ? (
            <div className="space-y-6">
              <DernieresLignes points={espace.points} />
              <ResumeClubSante club={monClubSante} />
            </div>
          ) : (
            <section className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
              <h2 className="text-2xl">
                <span className="text-logo-blue">Et</span>{" "}
                <span className="text-primary">ensuite ?</span>
              </h2>
              <ol className="mt-4 space-y-3 font-medium text-ink/80">
                <li>1. L'équipe vérifie ton nom, ta fonction et ton établissement.</li>
                <li>2. Tu reçois un email dès que ton compte est activé.</li>
                <li>3. Tes points de bienvenue sont crédités à l'activation.</li>
              </ol>
            </section>
          )}

          <section className="rounded-3xl bg-white p-6 shadow-card ring-1 ring-border">
            <h2 className="text-2xl">
              <span className="text-logo-blue">Mon</span>{" "}
              <span className="text-primary">profil</span>
            </h2>
            <dl className="mt-4 grid gap-3 text-sm">
              <Info terme="Statut" valeur={LIBELLES_VERIFICATION[espace.etat]} />
              <Info
                terme="Fonction"
                valeur={libelleFonction(espace.fonction, espace.fonction_precision)}
              />
              <Info
                terme="Établissement"
                valeur={<EtablissementAffiche etablissement={espace.etablissement} />}
              />
              <Info terme="Région (DRE)" valeur={espace.etablissement.dre} />
              <Info terme="Ville du lycée" valeur={espace.etablissement.localite ?? "—"} />
              <Info terme="Discipline" valeur={espace.discipline ?? "—"} />
              <Info terme="Email" valeur={espace.email ?? "Aucun"} />
              <Info terme="Téléphone" valeur={espace.telephone ?? "Aucun"} />
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
              Pour changer ton nom ou ton email, écris à l'équipe nationale.
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

function EnAttente({ espace }: { espace: Espace }) {
  return (
    <div className="mt-6 flex items-start gap-3 rounded-3xl bg-sun/20 p-5 ring-1 ring-sun/60">
      <Hourglass aria-hidden className="mt-0.5 size-6 shrink-0 text-ink" />
      <div>
        <p className="font-bold text-ink">Ton inscription est en cours de vérification.</p>
        <p className="mt-1 font-medium text-ink/80">
          Demande envoyée le {dateCourte(espace.demande_le)}. L'équipe des Clubs Santé vérifie tes
          informations, puis t'écrit à {espace.email}. Tu peux corriger ton profil en attendant.
        </p>
      </div>
    </div>
  );
}

function Refuse({ espace }: { espace: Espace }) {
  const router = useRouter();
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const renvoyer = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      await renvoyerDemandeEncadreur();
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div className="mt-6 rounded-3xl bg-logo-red/10 p-5 ring-1 ring-logo-red/30">
      <div className="flex items-start gap-3">
        <CircleAlert aria-hidden className="mt-0.5 size-6 shrink-0 text-logo-red" />
        <div>
          <p className="font-bold text-ink">L'équipe n'a pas pu valider ton inscription.</p>
          <p className="mt-1 font-medium text-ink/80">Motif : {espace.motif_refus}</p>
          <p className="mt-1 font-medium text-ink/80">
            Corrige ton profil si besoin, puis renvoie ta demande.
          </p>
        </div>
      </div>
      {erreur && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
      <Button onClick={renvoyer} disabled={enCours} className="mt-4 rounded-full font-bold">
        {enCours ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
        Renvoyer ma demande
      </Button>
    </div>
  );
}

function DialogueProfil({
  espace,
  ouvert,
  onOuvert,
}: {
  espace: Espace;
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
}) {
  const router = useRouter();
  const actuel: EtablissementChoisi = {
    id: espace.etablissement.id,
    nom: espace.etablissement.nom,
    detail: `${espace.etablissement.iesg} · ${espace.etablissement.dre}`,
  };
  const [fonction, setFonction] = useState<Fonction>(espace.fonction);
  const [precision, setPrecision] = useState(espace.fonction_precision ?? "");
  const [etablissement, setEtablissement] = useState<EtablissementChoisi | null>(actuel);
  const [telephone, setTelephone] = useState(espace.telephone ?? "");
  const [discipline, setDiscipline] = useState(espace.discipline ?? "");

  return (
    <DialogueFormulaire
      ouvert={ouvert}
      onOuvert={(o) => {
        if (o) {
          setFonction(espace.fonction);
          setPrecision(espace.fonction_precision ?? "");
          setEtablissement(actuel);
          setTelephone(espace.telephone ?? "");
          setDiscipline(espace.discipline ?? "");
        }
        onOuvert(o);
      }}
      titre="Modifier mon profil"
      bouton="Enregistrer"
      onEnvoie={async () => {
        if (!etablissement) throw new ErreurApi(422, "Choisis ton établissement dans la liste.");
        if (fonction === "autre" && !precision.trim())
          throw new ErreurApi(422, "Précise ta fonction.");
        // Un ancien compte sans téléphone n'est pas bloqué ; un téléphone enregistré ne s'efface plus.
        if (espace.telephone && !normaliserTelephone(telephone))
          throw new ErreurApi(422, "Indique ton téléphone ou ton WhatsApp.");
        if (!telephoneValide(telephone))
          throw new ErreurApi(422, "Ce téléphone n'est pas valide : de 8 à 15 chiffres.");
        await modifierProfilEncadreur({
          version: espace.version,
          fonction,
          fonction_precision: fonction === "autre" ? precision.trim() : null,
          etablissement_id: etablissement.id,
          telephone: normaliserTelephone(telephone) || null,
          discipline: discipline.trim() || null,
        });
        await router.invalidate();
      }}
    >
      <Champ libelle="Fonction">
        <select
          value={fonction}
          onChange={(e) => setFonction(e.target.value as Fonction)}
          className={CHAMP_ADMIN}
        >
          {FONCTIONS.map((f) => (
            <option key={f.valeur} value={f.valeur}>
              {f.libelle}
            </option>
          ))}
        </select>
      </Champ>
      {fonction === "autre" && (
        <Champ libelle="Précise ta fonction">
          <input
            value={precision}
            onChange={(e) => setPrecision(e.target.value)}
            maxLength={100}
            className={CHAMP_ADMIN}
          />
        </Champ>
      )}
      <div className="grid gap-1.5 text-sm font-bold">
        Établissement
        <ChoixEtablissement valeur={etablissement} onChoix={setEtablissement} />
      </div>
      <Champ libelle="Discipline, matière ou spécialité (facultatif)">
        <input
          value={discipline}
          onChange={(e) => setDiscipline(e.target.value)}
          maxLength={100}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Téléphone / WhatsApp">
        <input
          type="tel"
          value={telephone}
          onChange={(e) => setTelephone(e.target.value)}
          maxLength={30}
          autoComplete="tel"
          className={CHAMP_ADMIN}
        />
      </Champ>
    </DialogueFormulaire>
  );
}
