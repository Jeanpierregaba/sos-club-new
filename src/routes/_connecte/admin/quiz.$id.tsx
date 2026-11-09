import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import {
  ArrowLeft,
  CheckCircle2,
  EyeOff,
  Pencil,
  Play,
  Send,
  ShieldCheck,
  Trash2,
  Undo2,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { DialogueMotif } from "@/components/admin/DialogueMotif";
import { BadgeEtatQuiz } from "@/components/quiz/BadgeEtatQuiz";
import { EditeurQuestion } from "@/components/quiz/EditeurQuestion";
import { PartieQuiz } from "@/components/quiz/PartieQuiz";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  ajouterQuestion,
  approuverQuiz,
  chargerAxes,
  chargerQuizBanque,
  depublierQuiz,
  ErreurApi,
  lancerEssai,
  MESSAGE_INDISPONIBLE,
  modifierQuestion,
  modifierQuiz,
  partieEssai,
  refuserQuiz,
  reprendreQuiz,
  retirerQuestion,
  soumettreQuiz,
  type AxePublic,
  type EtatPartie,
  type QuestionBanque,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/admin/quiz/$id")({
  gcTime: 0,
  loader: async ({ params }) => {
    const [quiz, axes] = await Promise.all([
      chargerQuizBanque(params.id),
      chargerAxes().catch((): AxePublic[] => []),
    ]);
    return { quiz, axes };
  },
  errorComponent: ServiceIndisponible,
  component: FicheQuiz,
});

function FicheQuiz() {
  const { quiz, axes } = Route.useLoaderData();
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [dialogue, setDialogue] = useState<null | "titre" | "approuver" | "refuser" | "depublier">(
    null,
  );
  const [edition, setEdition] = useState<string | null>(null);
  const [essai, setEssai] = useState<EtatPartie | null>(null);
  const [titre, setTitre] = useState(quiz.titre);
  const [description, setDescription] = useState(quiz.description);
  const [axe, setAxe] = useState(quiz.axe_code);
  const [validateurNom, setValidateurNom] = useState("");
  const [validateurQualite, setValidateurQualite] = useState("");

  const rafraichir = () => router.invalidate();
  const libelle = (code: string) => axes.find((a) => a.code === code)?.libelle ?? code;
  const brouillon = quiz.etat === "brouillon";
  const redaction = brouillon && peut(admin, "quiz", "modifier");
  const reserveComplete = quiz.questions_actives >= quiz.questions_requises;

  async function agir(action: () => Promise<unknown>) {
    setErreur(null);
    setEnCours(true);
    try {
      await action();
      await rafraichir();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  async function tester() {
    setErreur(null);
    try {
      setEssai(await lancerEssai(quiz.id));
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    }
  }

  const actions: ReactNode[] = [];
  if (brouillon && peut(admin, "quiz", "modifier"))
    actions.push(
      <Button
        key="titre"
        variant="outline"
        className="rounded-full font-bold"
        onClick={() => setDialogue("titre")}
      >
        <Pencil className="size-4" /> Titre et axe
      </Button>,
    );
  actions.push(
    <Button
      key="tester"
      variant="outline"
      className="rounded-full font-bold"
      disabled={!reserveComplete}
      onClick={() => void tester()}
    >
      <Play className="size-4" /> Tester
    </Button>,
  );
  if (brouillon && peut(admin, "quiz", "soumettre"))
    actions.push(
      <Button
        key="soumettre"
        className="rounded-full font-bold"
        disabled={enCours || !reserveComplete}
        onClick={() => void agir(() => soumettreQuiz(quiz.id))}
      >
        <Send className="size-4" /> Soumettre pour publication
      </Button>,
    );
  if ((quiz.etat === "soumis" || quiz.etat === "depublie") && peut(admin, "quiz", "soumettre"))
    actions.push(
      <Button
        key="reprendre"
        variant="outline"
        className="rounded-full font-bold"
        disabled={enCours}
        onClick={() => void agir(() => reprendreQuiz(quiz.id))}
      >
        <Undo2 className="size-4" /> Reprendre en brouillon
      </Button>,
    );
  if (quiz.etat === "soumis" && peut(admin, "quiz", "approuver")) {
    actions.push(
      <Button
        key="approuver"
        className="rounded-full font-bold"
        disabled={quiz.contributeur}
        onClick={() => setDialogue("approuver")}
      >
        <ShieldCheck className="size-4" /> Publier
      </Button>,
      <Button
        key="refuser"
        variant="outline"
        className="rounded-full font-bold"
        onClick={() => setDialogue("refuser")}
      >
        <X className="size-4" /> Refuser
      </Button>,
    );
  }
  if (quiz.etat === "publie" && peut(admin, "quiz", "depublier"))
    actions.push(
      <Button
        key="depublier"
        variant="outline"
        className="rounded-full font-bold text-logo-red"
        onClick={() => setDialogue("depublier")}
      >
        <EyeOff className="size-4" /> Dépublier
      </Button>,
    );

  return (
    <div className="space-y-5">
      <Link
        to="/admin/quiz"
        className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
      >
        <ArrowLeft className="size-4" /> Banque de quiz
      </Link>

      <section className="space-y-3 rounded-3xl bg-white p-5 shadow-card sm:p-7">
        <div className="flex flex-wrap items-center gap-2">
          <BadgeEtatQuiz etat={quiz.etat} />
          {quiz.contenu_de_test && (
            <span className="rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold">
              Contenu de test
            </span>
          )}
          <span className="text-sm text-muted-foreground">{libelle(quiz.axe_code)}</span>
        </div>
        <h2 className="font-display text-2xl text-ink">{quiz.titre}</h2>
        {quiz.description && <p className="text-muted-foreground">{quiz.description}</p>}
        <p className="text-sm font-semibold">
          {quiz.questions_actives} questions actives sur {quiz.questions_requises} requises
        </p>
        {quiz.etat === "publie" && quiz.validateur_nom && (
          <p className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="size-4 text-primary" /> Validé par {quiz.validateur_nom} (
            {quiz.validateur_qualite})
            {quiz.publie_le && `, en ligne depuis le ${dateCourte(quiz.publie_le)}`}
          </p>
        )}
        {quiz.motif && quiz.etat !== "publie" && (
          <p className="rounded-2xl bg-logo-red/10 p-3 text-sm">
            <strong>Motif :</strong> {quiz.motif}
          </p>
        )}
        {quiz.etat === "soumis" && quiz.contributeur && peut(admin, "quiz", "approuver") && (
          <p className="text-sm text-muted-foreground">
            Tu as préparé ce quiz : un autre membre de l'équipe doit le publier.
          </p>
        )}
        <div className="flex flex-wrap gap-2 pt-2">{actions}</div>
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
      </section>

      {essai && (
        <section className="space-y-4 rounded-3xl bg-white p-5 shadow-card sm:p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl text-ink">Test du quiz</h2>
            <Button variant="ghost" className="rounded-full" onClick={() => setEssai(null)}>
              <X className="size-4" /> Fermer
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Dans les conditions réelles, sans rien enregistrer ni créditer.
          </p>
          <PartieQuiz
            depart={essai}
            appels={partieEssai}
            avecPoints={false}
            onRejouer={async () => setEssai(await lancerEssai(quiz.id))}
          />
        </section>
      )}

      <section className="space-y-3">
        <h2 className="font-display text-xl text-ink">Questions</h2>
        {quiz.questions.length === 0 && (
          <p className="text-sm text-muted-foreground">Aucune question pour l'instant.</p>
        )}
        <ol className="grid gap-3">
          {quiz.questions.map((q, i) => (
            <li key={q.id} className="rounded-2xl bg-white p-4 shadow-card">
              {edition === q.id ? (
                <EditeurQuestion
                  question={q}
                  onAnnule={() => setEdition(null)}
                  onEnregistre={async (entree) => {
                    await modifierQuestion(quiz.id, q.id, entree);
                    setEdition(null);
                    await rafraichir();
                  }}
                />
              ) : (
                <Question
                  numero={i + 1}
                  question={q}
                  actions={
                    // Une question désactivée (remplacée ou retirée après avoir été jouée) ne se modifie plus.
                    redaction &&
                    q.active && (
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Modifier la question ${i + 1}`}
                          onClick={() => setEdition(q.id)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Retirer la question ${i + 1}`}
                          disabled={enCours}
                          onClick={() => {
                            if (window.confirm("Retirer cette question ?"))
                              void agir(() => retirerQuestion(quiz.id, q.id));
                          }}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    )
                  }
                />
              )}
            </li>
          ))}
        </ol>
        {redaction && (
          <EditeurQuestion
            onEnregistre={async (entree) => {
              await ajouterQuestion(quiz.id, entree);
              await rafraichir();
            }}
          />
        )}
      </section>

      <DialogueFormulaire
        ouvert={dialogue === "titre"}
        onOuvert={(o) => setDialogue(o ? "titre" : null)}
        titre="Titre et axe du quiz"
        bouton="Enregistrer"
        onEnvoie={async () => {
          await modifierQuiz(quiz.id, { titre, description, axe_code: axe });
          await rafraichir();
        }}
      >
        <Champ libelle="Titre">
          <input
            className={CHAMP_ADMIN}
            value={titre}
            maxLength={120}
            onChange={(e) => setTitre(e.target.value)}
          />
        </Champ>
        <Champ libelle="Description courte">
          <input
            className={CHAMP_ADMIN}
            value={description}
            maxLength={300}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Champ>
        <Champ libelle="Axe">
          <select className={CHAMP_ADMIN} value={axe} onChange={(e) => setAxe(e.target.value)}>
            {axes.map((a) => (
              <option key={a.code} value={a.code}>
                {a.libelle}
              </option>
            ))}
          </select>
        </Champ>
      </DialogueFormulaire>

      <DialogueFormulaire
        ouvert={dialogue === "approuver"}
        onOuvert={(o) => setDialogue(o ? "approuver" : null)}
        titre="Publier ce quiz"
        description="Nomme la personne qui a validé le contenu médical : son nom reste attaché au quiz."
        bouton="Publier"
        onEnvoie={async () => {
          await approuverQuiz(quiz.id, {
            validateur_nom: validateurNom,
            validateur_qualite: validateurQualite,
          });
          await rafraichir();
        }}
      >
        <Champ libelle="Nom du validateur">
          <input
            className={CHAMP_ADMIN}
            value={validateurNom}
            maxLength={120}
            onChange={(e) => setValidateurNom(e.target.value)}
          />
        </Champ>
        <Champ libelle="Qualité (ex. médecin de santé publique)">
          <input
            className={CHAMP_ADMIN}
            value={validateurQualite}
            maxLength={120}
            onChange={(e) => setValidateurQualite(e.target.value)}
          />
        </Champ>
      </DialogueFormulaire>

      <DialogueMotif
        ouvert={dialogue === "refuser"}
        onOuvert={(o) => setDialogue(o ? "refuser" : null)}
        titre="Refuser ce quiz"
        description="Le quiz revient en brouillon ; le gestionnaire reçoit ton motif."
        bouton="Refuser"
        danger
        onConfirme={async (motif) => {
          await refuserQuiz(quiz.id, motif);
          await rafraichir();
        }}
      />
      <DialogueMotif
        ouvert={dialogue === "depublier"}
        onOuvert={(o) => setDialogue(o ? "depublier" : null)}
        titre="Dépublier ce quiz"
        description="Il disparaît pour les joueurs ; les parties jouées et les points gagnés restent."
        bouton="Dépublier"
        danger
        onConfirme={async (motif) => {
          await depublierQuiz(quiz.id, motif);
          await rafraichir();
        }}
      />
    </div>
  );
}

function Question({
  numero,
  question,
  actions,
}: {
  numero: number;
  question: QuestionBanque;
  actions?: ReactNode;
}) {
  return (
    <div className={question.active ? "" : "opacity-60"}>
      <div className="flex items-start justify-between gap-3">
        <p className="font-bold text-ink">
          {numero}. {question.enonce}
          {!question.active && (
            <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs font-extrabold text-muted-foreground">
              Désactivée
            </span>
          )}
        </p>
        {actions}
      </div>
      <ul className="mt-2 grid gap-1 text-sm">
        {question.choix.map((c, i) => (
          <li
            key={i}
            className={i === question.bonne_reponse ? "font-bold text-primary" : "text-ink"}
          >
            {i === question.bonne_reponse ? "✓ " : "· "}
            {c}
          </li>
        ))}
      </ul>
      {question.explication && (
        <p className="mt-2 text-sm text-muted-foreground">{question.explication}</p>
      )}
    </div>
  );
}
