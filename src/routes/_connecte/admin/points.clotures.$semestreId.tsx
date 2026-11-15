import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

import { ActionsCloture, DetailCloture } from "@/components/admin/DetailCloture";
import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { RefusOuPanne } from "@/components/admin/RefusOuPanne";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminAnnulerValidation,
  adminCloture,
  adminEcarterCandidat,
  adminGelerSemestre,
  adminListerClotures,
  adminPublierCloture,
  adminReintegrerCandidat,
  adminValiderCloture,
  ErreurApi,
  type CandidatAdmin,
} from "@/lib/api/client";
import { ETATS_CLOTURE } from "@/lib/clotures";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/admin/points/clotures/$semestreId")({
  loader: async ({ params }) => {
    // Un semestre terminé mais jamais gelé n'a pas encore de clôture : l'écran propose alors le gel.
    const [cloture, semestres] = await Promise.all([
      adminCloture(params.semestreId).catch((erreur: unknown) => {
        if (erreur instanceof ErreurApi && erreur.statut === 404) return null;
        throw erreur;
      }),
      adminListerClotures(),
    ]);
    const semestre = semestres.find((s) => s.semestre_id === params.semestreId);
    if (!semestre) throw new ErreurApi(404, "Ce semestre est introuvable.");
    return { cloture, semestre };
  },
  gcTime: 0,
  errorComponent: RefusOuPanne,
  component: EcranCloture,
});

type Dialogue =
  | { type: "gel" }
  | { type: "ecart"; candidat: CandidatAdmin }
  | { type: "validation" }
  | { type: "annulation" }
  | { type: "publication" }
  | null;

// La clôture d'un semestre (spec 037) : photo du classement, contrôle des candidats, validation et publication du
// Top 3. Chaque étape est journalisée ; l'API vérifie l'état et les droits à chaque action.
function EcranCloture() {
  const { cloture, semestre } = Route.useLoaderData();
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  const modificateur = peut(admin, "points", "modifier") && admin.perimetre_dre === null;
  const [dialogue, setDialogue] = useState<Dialogue>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const recharger = () => router.invalidate();
  const etat = cloture?.etat ?? "ouvert";

  const reintegrer = async (candidat: CandidatAdmin) => {
    setErreur(null);
    try {
      await adminReintegrerCandidat(semestre.semestre_id, candidat.utilisateur_id);
      await recharger();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : "La réintégration a échoué.");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button asChild variant="outline" className="rounded-full font-bold">
          <Link to="/admin/points/clotures">
            <ArrowLeft className="size-4" /> Clôtures
          </Link>
        </Button>
        <h2 className="font-display text-2xl text-logo-blue">{semestre.libelle}</h2>
        <span
          className={`rounded-full px-3 py-1 text-sm font-extrabold ${ETATS_CLOTURE[etat].classe}`}
        >
          {ETATS_CLOTURE[etat].libelle}
        </span>
        <p className="text-sm font-semibold text-muted-foreground">
          du {dateCourte(semestre.debut)} au {dateCourte(semestre.fin)}
        </p>
      </div>

      {erreur && (
        <p role="alert" className="font-semibold text-logo-red">
          {erreur}
        </p>
      )}

      {modificateur && (
        <ActionsCloture
          etat={etat}
          termine={semestre.termine}
          onAction={(type) => setDialogue({ type })}
        />
      )}

      {cloture === null ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Le classement de ce semestre n'est pas encore gelé. Le gel enregistre les 50 premiers
          élèves du classement national ; tu pourras ensuite les contrôler.
        </p>
      ) : (
        <DetailCloture
          cloture={cloture}
          modificateur={modificateur}
          onEcarter={(candidat) => setDialogue({ type: "ecart", candidat })}
          onReintegrer={reintegrer}
        />
      )}

      <Dialogues
        dialogue={dialogue}
        fermer={() => setDialogue(null)}
        semestreId={semestre.semestre_id}
        recharger={recharger}
      />
    </section>
  );
}

function Dialogues({
  dialogue,
  fermer,
  semestreId,
  recharger,
}: {
  dialogue: Dialogue;
  fermer: () => void;
  semestreId: string;
  recharger: () => Promise<unknown>;
}) {
  const [motif, setMotif] = useState("");
  useEffect(() => {
    if (dialogue) setMotif("");
  }, [dialogue]);

  const commun = {
    ouvert: dialogue !== null,
    onOuvert: (ouvert: boolean) => !ouvert && fermer(),
  };
  const champMotif = (
    <Champ libelle="Motif (10 à 500 caractères)">
      <textarea
        required
        minLength={10}
        maxLength={500}
        value={motif}
        onChange={(e) => setMotif(e.target.value)}
        className={`${CHAMP_ADMIN} h-24 py-2`}
      />
    </Champ>
  );

  switch (dialogue?.type) {
    case "gel":
      return (
        <DialogueFormulaire
          {...commun}
          titre="Geler le classement"
          description="La photo enregistre les 50 premiers élèves du classement national du semestre. Tant que rien n'est validé, tu peux regeler : les candidats écartés le restent."
          bouton="Geler"
          onEnvoie={async () => {
            await adminGelerSemestre(semestreId);
            await recharger();
          }}
        />
      );
    case "ecart":
      return (
        <DialogueFormulaire
          {...commun}
          titre={`Écarter ${dialogue.candidat.pseudonyme}`}
          description="Le candidat suivant monte dans le Top 3 proposé. Aucun point n'est retiré : pour cela, passe par le registre puis regèle. Le motif reste interne."
          bouton="Écarter"
          danger
          onEnvoie={async () => {
            await adminEcarterCandidat(semestreId, dialogue.candidat.utilisateur_id, motif.trim());
            await recharger();
          }}
        >
          {champMotif}
        </DialogueFormulaire>
      );
    case "validation":
      return (
        <DialogueFormulaire
          {...commun}
          titre="Valider le Top 3"
          description="Les places sont figées dans l'ordre proposé. Rien n'est encore public : la publication reste à faire."
          bouton="Valider"
          onEnvoie={async () => {
            await adminValiderCloture(semestreId);
            await recharger();
          }}
        />
      );
    case "annulation":
      return (
        <DialogueFormulaire
          {...commun}
          titre="Annuler la validation"
          description="La clôture revient à l'état gelé : tu pourras de nouveau écarter, réintégrer ou regeler."
          bouton="Annuler la validation"
          danger
          onEnvoie={async () => {
            await adminAnnulerValidation(semestreId, motif.trim());
            await recharger();
          }}
        >
          {champMotif}
        </DialogueFormulaire>
      );
    case "publication":
      return (
        <DialogueFormulaire
          {...commun}
          titre="Publier le palmarès"
          description="Le Top 3 apparaît sur le Hall of Fame et chaque lauréat reçoit une notification. Une fois publié, le palmarès ne change plus."
          bouton="Publier"
          onEnvoie={async () => {
            await adminPublierCloture(semestreId);
            await recharger();
          }}
        />
      );
    default:
      return null;
  }
}
