import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { AlertTriangle, ArrowLeft, Award, Snowflake, Undo2, UserX } from "lucide-react";
import { useEffect, useState } from "react";

import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { RefusOuPanne } from "@/components/admin/RefusOuPanne";
import { REGLE_EX_AEQUO } from "@/components/classements/Palmares";
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
  type ClotureDetail,
} from "@/lib/api/client";
import { formaterPoints } from "@/lib/classements";
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

const dateHeure = (iso: string) =>
  new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });

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

      {modificateur && etat !== "publie" && (
        <div className="flex flex-wrap gap-2 rounded-3xl bg-white p-4 ring-1 ring-border">
          {(etat === "ouvert" || etat === "gele") && (
            <Button
              onClick={() => setDialogue({ type: "gel" })}
              variant={etat === "ouvert" ? "default" : "outline"}
              className="rounded-full font-bold"
            >
              <Snowflake className="size-4" />{" "}
              {etat === "ouvert" ? "Geler le classement" : "Regeler"}
            </Button>
          )}
          {etat === "gele" && (
            <Button
              onClick={() => setDialogue({ type: "validation" })}
              className="btn-fx rounded-full font-bold"
            >
              <Award className="size-4" /> Valider le Top 3
            </Button>
          )}
          {etat === "valide" && (
            <>
              <Button
                onClick={() => setDialogue({ type: "publication" })}
                className="btn-fx rounded-full font-bold"
              >
                <Award className="size-4" /> Publier le palmarès
              </Button>
              <Button
                variant="outline"
                onClick={() => setDialogue({ type: "annulation" })}
                className="rounded-full font-bold"
              >
                <Undo2 className="size-4" /> Annuler la validation
              </Button>
            </>
          )}
        </div>
      )}

      {cloture === null ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Le classement de ce semestre n'est pas encore gelé. Le gel enregistre les 50 premiers
          élèves du classement national ; tu pourras ensuite les contrôler.
        </p>
      ) : (
        <Detail
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

function Detail({
  cloture,
  modificateur,
  onEcarter,
  onReintegrer,
}: {
  cloture: ClotureDetail;
  modificateur: boolean;
  onEcarter: (candidat: CandidatAdmin) => void;
  onReintegrer: (candidat: CandidatAdmin) => void;
}) {
  const controle = modificateur && cloture.etat === "gele";
  const ecart = cloture.ecart_actuel;
  return (
    <>
      <div className="space-y-3 rounded-3xl bg-white p-5 ring-1 ring-border">
        <h3 className="font-display text-xl text-logo-blue">
          {cloture.etat === "gele" ? "Top 3 proposé" : "Top 3"}
        </h3>
        {cloture.top3.length === 0 ? (
          <p className="font-semibold text-muted-foreground">Aucun candidat retenu.</p>
        ) : (
          <ol className="grid gap-3 sm:grid-cols-3">
            {cloture.top3.map((laureat, index) => (
              <li key={laureat.utilisateur_id} className="rounded-2xl bg-mist-soft p-4">
                <p className="text-xs font-extrabold uppercase tracking-wider text-logo-blue">
                  {laureat.distinction}
                </p>
                <p className="mt-1 break-words font-bold text-ink">{laureat.pseudonyme}</p>
                <p className="text-xs font-semibold text-muted-foreground">
                  {[laureat.club, laureat.dre].filter(Boolean).join(" · ")} ·{" "}
                  {formaterPoints(laureat.points)} pts
                </p>
                <span className="sr-only">Place {index + 1}</span>
              </li>
            ))}
          </ol>
        )}
        <p className="text-xs font-medium text-muted-foreground">{REGLE_EX_AEQUO}</p>
      </div>

      {(ecart.top3_different || ecart.changements.length > 0) && (
        <div
          role="status"
          className="flex gap-3 rounded-3xl bg-sun/25 p-4 text-sm font-semibold text-ink ring-1 ring-sun"
        >
          <AlertTriangle aria-hidden className="size-5 shrink-0 text-logo-red" />
          <div>
            <p className="font-bold">
              Le classement actuel diffère de la photo
              {ecart.top3_different ? " et le Top 3 changerait" : ""}.
            </p>
            <ul className="mt-1 list-disc pl-5">
              {ecart.changements.map((c) => (
                <li key={c.pseudonyme}>
                  {c.pseudonyme} : {c.points_gel ?? "absent"} → {c.points_actuels ?? "sorti"}
                </li>
              ))}
            </ul>
            {cloture.etat === "gele" && <p className="mt-1">Regèle pour en tenir compte.</p>}
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
        <p className="border-b px-5 py-3 text-sm font-bold text-ink">
          Photo du {dateHeure(cloture.etapes.gele_le)} par {cloture.etapes.gele_par} ·{" "}
          {cloture.candidats.length} candidat{cloture.candidats.length > 1 ? "s" : ""}
          {cloture.etapes.valide_le &&
            ` · validé le ${dateHeure(cloture.etapes.valide_le)} par ${cloture.etapes.valide_par}`}
          {cloture.etapes.publie_le &&
            ` · publié le ${dateHeure(cloture.etapes.publie_le)} par ${cloture.etapes.publie_par}`}
        </p>
        {cloture.candidats.length === 0 ? (
          <p className="p-6 text-center font-semibold text-muted-foreground">
            Aucun élève classé ce semestre.
          </p>
        ) : (
          <ol className="divide-y">
            {cloture.candidats.map((c) => (
              <li
                key={c.utilisateur_id}
                className={`flex flex-wrap items-start gap-3 px-4 py-3 sm:px-5 ${c.ecarte ? "bg-logo-red/5" : ""}`}
              >
                <span className="w-14 shrink-0 text-center font-display text-lg text-logo-blue">
                  {c.rang}
                  {c.rang_brut !== c.rang && (
                    <span className="block text-[11px] font-semibold text-muted-foreground">
                      ex æquo {c.rang_brut}
                    </span>
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="break-words font-bold text-ink">
                    {c.pseudonyme}{" "}
                    <span className="text-xs font-semibold text-muted-foreground">
                      ({c.identifiant}) · {c.statut}
                    </span>
                  </p>
                  <p className="break-words text-xs font-semibold text-muted-foreground">
                    {[c.club, c.dre].filter(Boolean).join(" · ")} · total atteint le{" "}
                    {dateHeure(c.atteint_le)} · {c.corrections} correction
                    {c.corrections > 1 ? "s" : ""}, {c.annulations} annulation
                    {c.annulations > 1 ? "s" : ""}
                  </p>
                  {c.motif_ecart && (
                    <p className="mt-1 break-words text-sm italic text-logo-red">
                      Écarté : « {c.motif_ecart} »
                    </p>
                  )}
                </div>
                <span className="shrink-0 font-extrabold text-ink">
                  {formaterPoints(c.points)} pts
                </span>
                {controle &&
                  (c.ecarte ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                      onClick={() => onReintegrer(c)}
                    >
                      <Undo2 className="size-4" /> Réintégrer
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                      onClick={() => onEcarter(c)}
                    >
                      <UserX className="size-4" /> Écarter
                    </Button>
                  ))}
              </li>
            ))}
          </ol>
        )}
      </div>
    </>
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
