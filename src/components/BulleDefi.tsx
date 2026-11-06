import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Loader2, X } from "lucide-react";
import mascotteBourses from "@/assets/mascotte-bourses.webp";

import { useMoi } from "@/hooks/use-moi";
import { BAREME, points } from "@/lib/bareme";

import {
  chargerDefiDuJour,
  corrigerDefi,
  MESSAGE_INDISPONIBLE,
  type CorrectionDefi,
  type DefiDuJour,
} from "@/lib/api/client";

// Le défi du jour, en bulle flottante en bas à droite de l'accueil, comme un assistant de discussion :
// la tête de la mascotte ouvre une fenêtre avec la question. Le bouton « Retour en haut » remonte au-dessus.
// La question vient de la banque de l'API (spec 021) : la même pour tous, elle change à minuit ; la bonne
// réponse n'arrive qu'avec la correction. Sans défi (banque vide, API arrêtée), la bulle ne s'affiche pas.
// Spec 022 : un élève connecté répond une fois par jour et gagne +20 (et +10 pour son club) si c'est juste ;
// sa réponse reste affichée ensuite. Un visiteur joue sans points.

function TeteMascotte({ className }: { className: string }) {
  return (
    <span className={`block overflow-hidden rounded-full bg-sun ${className}`}>
      <img
        src={mascotteBourses}
        alt=""
        width={1414}
        height={2000}
        className="size-full scale-[1.9] object-cover object-[50%_9%] [transform-origin:50%_18%]"
      />
    </span>
  );
}

type Joueur = "eleve" | "visiteur" | "autre";

export function BulleDefi() {
  const { data: moi, isPending } = useMoi();
  // La question dépend du compte : un élève qui a déjà répondu la reçoit avec sa réponse.
  const cle = ["defi-du-jour", moi?.id ?? null];
  const { data: defi } = useQuery({
    queryKey: cle,
    queryFn: chargerDefiDuJour,
    retry: false,
    staleTime: 10 * 60_000,
    enabled: !isPending,
  });
  const joueur: Joueur = !moi ? "visiteur" : moi.role === "eleve" ? "eleve" : "autre";
  return defi ? <Bulle key={`${defi.id}-${joueur}`} defi={defi} joueur={joueur} cle={cle} /> : null;
}

function Bulle({ defi, joueur, cle }: { defi: DefiDuJour; joueur: Joueur; cle: unknown[] }) {
  const clientRequetes = useQueryClient();
  const [ouverte, setOuverte] = useState(false);
  const [vue, setVue] = useState(false);
  const [invite, setInvite] = useState(false);
  const [choix, setChoix] = useState<number | null>(defi.ma_reponse?.choix ?? null);
  const [correction, setCorrection] = useState<CorrectionDefi | null>(defi.ma_reponse ?? null);
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const valide = correction !== null;
  const bonne = correction?.bonne_reponse;

  const valider = async () => {
    if (choix === null) return;
    setEnvoi(true);
    setErreur(null);
    try {
      const reponse = await corrigerDefi(defi.id, choix);
      setCorrection(reponse);
      setChoix(reponse.choix);
      // Rouverte plus tard, la bulle montre la réponse comptée.
      if (joueur === "eleve")
        clientRequetes.setQueryData<DefiDuJour>(cle, (d) => d && { ...d, ma_reponse: reponse });
    } catch {
      setErreur(MESSAGE_INDISPONIBLE);
    } finally {
      setEnvoi(false);
    }
  };
  const bouton = useRef<HTMLButtonElement>(null);
  const fermer = useRef<HTMLButtonElement>(null);

  // Le bouton « Retour en haut » se place au-dessus de la bulle tant qu'elle est sur la page.
  useEffect(() => {
    const racine = document.documentElement.style;
    racine.setProperty("--retour-bas", "6rem");
    racine.setProperty("--retour-bas-md", "7rem");
    // Une invitation discrète quelques secondes après l'arrivée, tant que la bulle n'a pas été ouverte.
    const minuterie = window.setTimeout(() => setInvite(true), 4000);
    return () => {
      racine.removeProperty("--retour-bas");
      racine.removeProperty("--retour-bas-md");
      window.clearTimeout(minuterie);
    };
  }, []);

  useEffect(() => {
    if (!ouverte) return;
    fermer.current?.focus({ preventScroll: true });
    const touche = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setOuverte(false);
      bouton.current?.focus({ preventScroll: true });
    };
    window.addEventListener("keydown", touche);
    return () => window.removeEventListener("keydown", touche);
  }, [ouverte]);

  const basculer = () => {
    setOuverte((o) => !o);
    setVue(true);
    setInvite(false);
  };

  const couleur = (i: number) => {
    if (valide && i === bonne) return "border-leaf bg-leaf text-primary-foreground";
    if (valide && i === choix)
      return "animate-shake border-logo-red bg-logo-red text-primary-foreground";
    if (i === choix) return "border-logo-blue bg-logo-blue text-primary-foreground";
    return valide ? "border-border opacity-60" : "border-border hover:border-logo-blue";
  };
  const pastille = (i: number) =>
    (valide && i === bonne) || i === choix ? "bg-white/25" : "bg-mist text-logo-blue";

  return (
    <div className="print:hidden">
      {/* La fenêtre du défi, qui se déploie depuis la bulle. */}
      <div
        id="bulle-defi"
        role="dialog"
        aria-modal="false"
        aria-labelledby="bulle-defi-titre"
        hidden={!ouverte}
        className="fixed bottom-24 right-4 z-50 w-[min(24rem,calc(100vw-2rem))] origin-bottom-right overflow-hidden rounded-[1.75rem] bg-card text-foreground shadow-2xl ring-1 ring-border animate-in fade-in zoom-in-90 slide-in-from-bottom-4 duration-300 md:bottom-28 md:right-8"
      >
        <div className="relative flex items-center gap-3 bg-logo-blue p-4 text-white">
          <TeteMascotte className="size-12 shrink-0 ring-2 ring-white" />
          <div className="min-w-0">
            <p id="bulle-defi-titre" className="font-display text-xl leading-tight">
              Le défi <span className="text-sun">du jour</span>
            </p>
            <p className="text-xs font-semibold text-white/80">
              Une nouvelle question santé chaque jour
            </p>
          </div>
          <button
            ref={fermer}
            type="button"
            onClick={() => {
              setOuverte(false);
              bouton.current?.focus({ preventScroll: true });
            }}
            aria-label="Fermer le défi du jour"
            className="ml-auto inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-white/10 transition hover:bg-white hover:text-ink"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="p-5">
          <span className="rounded-full bg-rose px-3 py-1 text-[11px] font-extrabold uppercase text-primary-foreground">
            {defi.categorie}
          </span>
          {/* La question, comme un message de la mascotte. */}
          <p className="mt-3 rounded-2xl rounded-tl-sm bg-mist-soft p-4 font-display text-xl leading-tight text-logo-blue">
            {defi.question}
          </p>
          <div className="mt-4 grid gap-2">
            {defi.options.map((o, i) => (
              <button
                key={o}
                type="button"
                disabled={valide}
                aria-pressed={i === choix}
                onClick={() => setChoix(i)}
                className={`flex items-center gap-3 rounded-2xl border-2 p-2.5 text-left text-sm font-bold transition duration-200 active:scale-95 ${couleur(i)}`}
              >
                <span
                  className={`inline-flex size-8 shrink-0 items-center justify-center rounded-xl font-display ${pastille(i)}`}
                >
                  {"ABCD"[i]}
                </span>
                {o}
              </button>
            ))}
          </div>
          {!valide && <Gains joueur={joueur} />}
          <div className="mt-4 flex items-center justify-between gap-3">
            <p role="status" className="text-sm font-bold">
              {correction ? <Verdict correction={correction} /> : erreur}
            </p>
            {!valide && (
              <button
                type="button"
                disabled={choix === null || envoi}
                onClick={valider}
                className="btn-fx ml-auto inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-6 py-2.5 text-sm font-bold text-primary-foreground disabled:opacity-50"
              >
                {envoi && <Loader2 aria-hidden className="size-4 animate-spin" />}
                Valider
              </button>
            )}
          </div>
          {correction && (
            <div className="mt-3 rounded-2xl bg-leaf/10 p-3 text-sm font-medium text-ink">
              <p>{correction.explication}</p>
              <p className="mt-2 font-bold text-logo-blue">Reviens demain pour un nouveau défi !</p>
            </div>
          )}
        </div>
      </div>

      {/* L'invitation, une seule fois, à côté de la bulle. */}
      {invite && !ouverte && (
        <p
          aria-hidden
          className="fixed bottom-8 right-24 z-40 rounded-2xl rounded-br-sm bg-white px-4 py-2 text-sm font-bold text-ink shadow-card ring-1 ring-border animate-in fade-in slide-in-from-right-2 md:bottom-11 md:right-28"
        >
          Le défi du jour t’attend !
        </p>
      )}

      {/* La bulle : la tête de la mascotte, un halo qui pulse et une pastille tant que le défi n'a pas été ouvert. */}
      <button
        ref={bouton}
        type="button"
        onClick={basculer}
        aria-expanded={ouverte}
        aria-controls="bulle-defi"
        aria-label={ouverte ? "Fermer le défi du jour" : "Ouvrir le défi du jour"}
        className="fixed bottom-5 right-4 z-50 size-16 rounded-full shadow-card transition hover:scale-105 active:scale-95 md:bottom-8 md:right-8"
      >
        {!vue && (
          <span
            aria-hidden
            className="absolute inset-0 rounded-full bg-sun motion-safe:animate-ping"
          />
        )}
        <TeteMascotte className="relative size-full ring-4 ring-white" />
        {ouverte ? (
          <span className="absolute -right-1 -top-1 inline-flex size-6 items-center justify-center rounded-full bg-ink text-white ring-2 ring-white">
            <X aria-hidden className="size-3.5" />
          </span>
        ) : (
          !vue && (
            <span
              aria-hidden
              className="absolute -right-1 -top-1 inline-flex size-6 items-center justify-center rounded-full bg-logo-red text-xs font-extrabold text-white ring-2 ring-white"
            >
              1
            </span>
          )
        )}
      </button>
    </div>
  );
}

// Ce que rapporte une bonne réponse, selon qui joue.
function Gains({ joueur }: { joueur: Joueur }) {
  if (joueur === "eleve")
    return (
      <p className="mt-3 text-xs font-semibold text-muted-foreground">
        Bonne réponse :{" "}
        <strong className="text-leaf">{points(BAREME.questionDuJour.eleve)} points</strong> pour
        toi, {points(BAREME.questionDuJour.club)} pour ton club. Une seule réponse par jour.
      </p>
    );
  if (joueur === "visiteur")
    return (
      <p className="mt-3 text-xs font-semibold text-muted-foreground">
        <Link
          to="/connexion"
          search={{ redirection: "/" }}
          className="font-bold text-logo-blue underline"
        >
          Connecte-toi à ton compte Élève
        </Link>{" "}
        pour gagner {points(BAREME.questionDuJour.eleve)} points avec une bonne réponse.
      </p>
    );
  return (
    <p className="mt-3 text-xs font-semibold text-muted-foreground">
      Les points du défi du jour sont réservés aux élèves.
    </p>
  );
}

function Verdict({ correction }: { correction: CorrectionDefi }) {
  if (correction.deja_repondu)
    return correction.points > 0
      ? `Tu as déjà répondu aujourd'hui : déjà récompensée, ${points(correction.points)} points.`
      : "Tu as déjà répondu aujourd'hui : la bonne réponse est en vert.";
  if (!correction.correcte) return "Pas tout à fait : la bonne réponse est en vert.";
  return correction.points > 0
    ? `Bravo ! ${points(correction.points)} points pour toi.`
    : "Bravo, c'est la bonne réponse !";
}
