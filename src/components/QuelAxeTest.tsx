import { useCallback, useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  Lock,
  RotateCcw,
  Share2,
  UserPlus,
} from "lucide-react";

import mascotteMedias from "@/assets/mascotte-medias.webp";
import { useMoi } from "@/hooks/use-moi";
import {
  calculerQuelAxe,
  chargerQuelAxe,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type QuestionQuelAxe,
  type ResultatQuelAxe,
} from "@/lib/api/client";
import { axeDecouverte, type AxeDecouverte } from "@/lib/axes-decouverte";

// L'adresse de retour après la connexion : l'accueil, qui rouvre le test (voir `QuelAxe`).
const RETOUR = "/?test=quel-axe#quel-axe";

type Acces = "chargement" | "visiteur" | "reserve" | "eleve" | "indisponible";

// Le contenu de la fenêtre du test (spec 021) : les cas du document (élève connecté, visiteur, autre profil),
// les cinq questions, puis le résultat calculé par l'API.
export function QuelAxeTest() {
  const { data: moi, isPending, isError } = useMoi();
  const [refus, setRefus] = useState<Acces | null>(null);
  const acces: Acces =
    refus ??
    (isPending
      ? "chargement"
      : isError
        ? "indisponible"
        : !moi
          ? "visiteur"
          : moi.role === "eleve"
            ? "eleve"
            : "reserve");

  // L'API a le dernier mot : une session expirée (401) ou un profil refusé (403) change l'écran.
  const surErreur = useCallback(
    (e: unknown) =>
      setRefus(
        e instanceof ErreurApi && e.statut === 401
          ? "visiteur"
          : e instanceof ErreurApi && e.statut === 403
            ? "reserve"
            : "indisponible",
      ),
    [],
  );

  if (acces === "chargement") return <Chargement />;
  if (acces === "visiteur") return <Visiteur />;
  if (acces === "reserve")
    return (
      <Message titre="Ce jeu est réservé aux élèves inscrits.">
        Il se joue depuis un compte Élève. Les sept axes restent ouverts à tous sur la page{" "}
        <a href="/les-7-axes" className="font-bold text-logo-blue underline">
          Les 7 axes
        </a>
        .
      </Message>
    );
  if (acces === "indisponible")
    return <Message titre="Le test est indisponible">{MESSAGE_INDISPONIBLE}</Message>;
  return <Questionnaire surErreur={surErreur} />;
}

function Questionnaire({ surErreur }: { surErreur: (e: unknown) => void }) {
  const questions = useQuery({
    queryKey: ["quel-axe"],
    queryFn: chargerQuelAxe,
    retry: false,
    staleTime: Infinity,
  });
  const [etape, setEtape] = useState(0);
  const [reponses, setReponses] = useState<(string | undefined)[]>([]);
  const [resultat, setResultat] = useState<ResultatQuelAxe | null>(null);
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => {
    if (questions.isError) surErreur(questions.error);
  }, [questions.isError, questions.error, surErreur]);

  if (questions.isPending || questions.isError) return <Chargement />;
  const liste = questions.data.questions;

  const recommencer = () => {
    setResultat(null);
    setReponses([]);
    setEtape(0);
  };
  if (resultat) return <Resultat resultat={resultat} onRecommencer={recommencer} />;

  const question = liste[etape]!;
  const choisie = reponses[etape];
  const derniere = etape === liste.length - 1;
  const suivant = async () => {
    if (!choisie) return;
    if (!derniere) return setEtape(etape + 1);
    setEnvoi(true);
    try {
      setResultat(await calculerQuelAxe(reponses as string[]));
    } catch (e) {
      surErreur(e);
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <div className="p-6 md:p-10">
      <div aria-hidden className="flex gap-1.5 pr-8">
        {liste.map((q) => (
          <span
            key={q.numero}
            className={`h-2 flex-1 rounded-full transition-colors duration-500 ${q.numero <= etape + 1 ? "bg-grape" : "bg-mist"}`}
          />
        ))}
      </div>
      <div key={etape} className="animate-in fade-in slide-in-from-right-4">
        <p className="mt-6 text-sm font-extrabold uppercase tracking-widest text-grape">
          Question {etape + 1} / {liste.length}
        </p>
        <p className="mt-2 font-display text-2xl leading-tight text-ink md:text-3xl">
          {question.libelle}
        </p>
        <Reponses
          question={question}
          choisie={choisie}
          onChoisir={(id) =>
            setReponses((r) => {
              const suite = [...r];
              suite[etape] = id;
              return suite;
            })
          }
        />
      </div>
      <div className="mt-8 flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={etape === 0}
          onClick={() => setEtape(etape - 1)}
          className="inline-flex items-center gap-2 rounded-full px-4 py-2.5 font-bold text-muted-foreground transition hover:text-grape disabled:invisible"
        >
          <ArrowLeft className="size-4" /> Précédent
        </button>
        <button
          type="button"
          disabled={!choisie || envoi}
          onClick={suivant}
          className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-7 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          {envoi ? <Loader2 className="size-4 animate-spin" /> : null}
          {derniere ? "Voir mon axe" : "Suivant"} <ArrowRight className="size-4" />
        </button>
      </div>
    </div>
  );
}

function Reponses({
  question,
  choisie,
  onChoisir,
}: {
  question: QuestionQuelAxe;
  choisie: string | undefined;
  onChoisir: (id: string) => void;
}) {
  return (
    <div role="radiogroup" aria-label={question.libelle} className="mt-6 grid gap-3 sm:grid-cols-2">
      {question.reponses.map((r) => {
        const active = r.id === choisie;
        return (
          <button
            key={r.id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChoisir(r.id)}
            className={`flex h-full items-start gap-3 rounded-2xl border-2 p-4 text-left font-semibold transition duration-200 hover:-translate-y-0.5 hover:shadow-card ${
              active ? "border-grape bg-grape/5 text-ink" : "border-border bg-white text-ink/85"
            }`}
          >
            <span
              className={`inline-flex size-8 shrink-0 items-center justify-center rounded-full font-display text-lg ${
                active ? "bg-grape text-white" : "bg-mist text-grape"
              }`}
            >
              {active ? <Check className="size-4" /> : r.id}
            </span>
            {r.libelle}
          </button>
        );
      })}
    </div>
  );
}

function Resultat({
  resultat,
  onRecommencer,
}: {
  resultat: ResultatQuelAxe;
  onRecommencer: () => void;
}) {
  const axe = axeDecouverte(resultat.principal);
  const autres = resultat.autres.map(axeDecouverte);
  const [partage, setPartage] = useState<string | null>(null);

  const partager = async () => {
    const texte = `Mon axe Clubs Santé SOS Docteur TV : ${axe.nom} ! Et toi, quel axe est fait pour toi ?`;
    const url = `${window.location.origin}/#quel-axe`;
    try {
      if (navigator.share)
        await navigator.share({ title: "Quel axe est fait pour toi ?", text: texte, url });
      else {
        await navigator.clipboard.writeText(`${texte} ${url}`);
        setPartage("Texte copié : colle-le où tu veux le partager.");
      }
    } catch {
      // Partage annulé : rien à signaler.
    }
  };

  return (
    <div
      style={{ "--axe": axe.couleur } as CSSProperties}
      className="animate-in fade-in zoom-in-95"
    >
      <div className="relative overflow-hidden bg-(color:--axe) px-6 pb-6 pt-10 md:px-10">
        <div className="grid items-end gap-4 sm:grid-cols-[auto_1fr]">
          <img
            src={axe.img}
            alt={`La mascotte de l’axe ${axe.nom}`}
            width={1414}
            height={2000}
            className="mx-auto h-44 w-auto drop-shadow-2xl motion-safe:animate-float sm:h-52"
          />
          {/* Seul le titre est annoncé aux lecteurs d'écran, pas tout l'écran de résultat. */}
          <div role="status" className={axe.encre}>
            <p className="text-sm font-extrabold uppercase tracking-widest opacity-90">
              Ton axe principal
            </p>
            <p className="mt-1 font-display text-3xl leading-tight md:text-4xl">{axe.nom}</p>
          </div>
        </div>
      </div>
      <div className="p-6 md:p-10">
        <p className="font-display text-2xl text-ink">{axe.titre}</p>
        <p className="mt-2 font-medium text-ink/80">{axe.texte}</p>
        <p className="mt-3 inline-flex rounded-full bg-(color:--axe)/15 px-4 py-1.5 font-bold text-ink">
          Ta force : {axe.force}
        </p>

        <p className="mt-8 text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
          Deux autres axes à explorer
        </p>
        <ul className="mt-3 grid gap-3 sm:grid-cols-2">
          {autres.map((a) => (
            <AutreAxe key={a.code} axe={a} />
          ))}
        </ul>

        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={`/les-7-axes#axe-${axe.n}`}
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-6 py-3 font-bold text-white"
          >
            Découvrir cet axe <ArrowRight className="size-4" />
          </a>
          <button
            type="button"
            onClick={partager}
            className="inline-flex items-center gap-2 rounded-full border-2 border-grape px-6 py-3 font-bold text-grape transition hover:bg-grape hover:text-white"
          >
            <Share2 className="size-4" /> Partager mon résultat
          </button>
          <button
            type="button"
            onClick={onRecommencer}
            className="inline-flex items-center gap-2 rounded-full px-4 py-3 font-bold text-muted-foreground transition hover:text-grape"
          >
            <RotateCcw className="size-4" /> Refaire le test
          </button>
        </div>
        {partage && <p className="mt-3 text-sm font-semibold text-ink">{partage}</p>}
        <p className="mt-6 text-sm font-medium text-muted-foreground">
          Ce test t’oriente, il ne te classe pas : les sept axes te restent ouverts.
        </p>
      </div>
    </div>
  );
}

function AutreAxe({ axe }: { axe: AxeDecouverte }) {
  return (
    <li>
      <a
        href={`/les-7-axes#axe-${axe.n}`}
        style={{ "--axe": axe.couleur } as CSSProperties}
        className="flex items-center gap-3 rounded-2xl border-2 border-(color:--axe)/40 p-3 font-bold text-ink transition hover:-translate-y-0.5 hover:shadow-card"
      >
        <span className="size-12 shrink-0 overflow-hidden rounded-xl bg-(color:--axe)">
          <img
            src={axe.img}
            alt=""
            width={1414}
            height={2000}
            className="size-full scale-150 object-cover object-top"
          />
        </span>
        {axe.nom}
      </a>
    </li>
  );
}

function Visiteur() {
  return (
    <Message titre="Connecte-toi à ton compte Élève pour découvrir ton axe !">
      <span className="mt-5 flex flex-wrap justify-center gap-3">
        <Link
          to="/connexion"
          search={{ redirection: RETOUR }}
          className="btn-fx inline-flex items-center gap-2 rounded-full bg-grape px-6 py-3 font-bold text-white"
        >
          <Lock className="size-4" /> Se connecter
        </Link>
        <Link
          to="/inscription"
          search={{ profil: "eleve" }}
          className="inline-flex items-center gap-2 rounded-full border-2 border-grape px-6 py-3 font-bold text-grape transition hover:bg-grape hover:text-white"
        >
          <UserPlus className="size-4" /> Créer mon compte Élève
        </Link>
      </span>
    </Message>
  );
}

function Message({ titre, children }: { titre: string; children: ReactNode }) {
  return (
    <div role="status" className="p-8 text-center md:p-12">
      <img
        src={mascotteMedias}
        alt=""
        width={1414}
        height={2000}
        className="mx-auto h-40 w-auto drop-shadow-xl"
      />
      <p className="mt-4 font-display text-2xl leading-tight text-grape md:text-3xl">{titre}</p>
      <div className="mt-3 font-medium text-ink/80">{children}</div>
    </div>
  );
}

function Chargement() {
  return (
    <div className="flex justify-center p-16" aria-label="Chargement">
      <Loader2 className="size-8 animate-spin text-grape" />
    </div>
  );
}
