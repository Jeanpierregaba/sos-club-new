import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useState } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { BadgeEtatQuiz, ETATS_QUIZ } from "@/components/quiz/BadgeEtatQuiz";
import { ChampsParcours } from "@/components/quiz/ChampsParcours";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  chargerAxes,
  chargerBanque,
  creerQuiz,
  type AxePublic,
  type EtatQuiz,
  type Parcours,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { chargerFascicules, useParcours } from "@/lib/parcours";

type Recherche = { etat?: EtatQuiz; parcours?: Parcours };
const ETATS = Object.keys(ETATS_QUIZ) as EtatQuiz[];
const PARCOURS: { valeur: Parcours; libelle: string }[] = [
  { valeur: "jeux", libelle: "Jeux" },
  { valeur: "certification", libelle: "Certification" },
];

export const Route = createFileRoute("/_connecte/admin/quiz/")({
  gcTime: 0,
  validateSearch: (search: Record<string, unknown>): Recherche => ({
    ...(ETATS.includes(search["etat"] as EtatQuiz) ? { etat: search["etat"] as EtatQuiz } : {}),
    ...(search["parcours"] === "jeux" || search["parcours"] === "certification"
      ? { parcours: search["parcours"] }
      : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [banque, axes, fascicules] = await Promise.all([
      chargerBanque(deps),
      chargerAxes().catch((): AxePublic[] => []),
      chargerFascicules(),
    ]);
    return { banque, axes, fascicules };
  },
  errorComponent: ServiceIndisponible,
  component: Banque,
});

function Banque() {
  const { banque, axes, fascicules } = Route.useLoaderData();
  const { etat, parcours } = Route.useSearch();
  const champsParcours = useParcours();
  const { admin } = Route.useRouteContext();
  const naviguer = useNavigate();
  const [ouvert, setOuvert] = useState(false);
  const [titre, setTitre] = useState("");
  const [description, setDescription] = useState("");
  const [axe, setAxe] = useState(axes[0]?.code ?? "");
  const libelle = (code: string) => axes.find((a) => a.code === code)?.libelle ?? code;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2">
          <nav aria-label="Filtrer par parcours" className="flex flex-wrap gap-2">
            <Filtre
              recherche={etat ? { etat } : {}}
              libelle="Tous les parcours"
              actif={!parcours}
            />
            {PARCOURS.map((p) => (
              <Filtre
                key={p.valeur}
                recherche={{ ...(etat ? { etat } : {}), parcours: p.valeur }}
                libelle={p.libelle}
                actif={parcours === p.valeur}
              />
            ))}
          </nav>
          <nav aria-label="Filtrer par état" className="flex flex-wrap gap-2">
            <Filtre recherche={parcours ? { parcours } : {}} libelle="Tous" actif={!etat} />
            {ETATS.map((e) => (
              <Filtre
                key={e}
                recherche={{ ...(parcours ? { parcours } : {}), etat: e }}
                libelle={ETATS_QUIZ[e].libelle}
                actif={etat === e}
              />
            ))}
          </nav>
        </div>
        {peut(admin, "quiz", "creer") && (
          <Button className="rounded-full font-bold" onClick={() => setOuvert(true)}>
            <Plus className="size-4" /> Nouveau quiz
          </Button>
        )}
      </div>
      <p className="text-sm text-muted-foreground">
        Un quiz se soumet avec au moins {banque.questions_requises} questions actives.
      </p>

      {banque.quiz.length === 0 ? (
        <p className="rounded-3xl bg-white p-8 text-center font-semibold shadow-card">
          Aucun quiz ici pour l'instant.
        </p>
      ) : (
        <ul className="grid gap-3">
          {banque.quiz.map((q) => (
            <li key={q.id}>
              <Link
                to="/admin/quiz/$id"
                params={{ id: q.id }}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow-card ring-1 ring-transparent hover:ring-logo-blue/30"
              >
                <span>
                  <span className="block font-bold text-ink">{q.titre}</span>
                  <span className="text-sm text-muted-foreground">
                    {libelle(q.axe_code)} · {q.questions_actives} questions · modifié le{" "}
                    {dateCourte(q.modifie_le)}
                  </span>
                </span>
                <span className="flex flex-wrap gap-2">
                  {q.place !== null && (
                    <span className="rounded-full bg-logo-blue/10 px-2.5 py-0.5 text-xs font-extrabold text-logo-blue">
                      Certification · quiz {q.place}
                    </span>
                  )}
                  {q.contenu_de_test && (
                    <span className="rounded-full bg-sun/30 px-2.5 py-0.5 text-xs font-extrabold">
                      Contenu de test
                    </span>
                  )}
                  <BadgeEtatQuiz etat={q.etat} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <DialogueFormulaire
        ouvert={ouvert}
        onOuvert={setOuvert}
        titre="Nouveau quiz"
        description="Il reste en brouillon tant que tu ne le soumets pas."
        bouton="Créer le quiz"
        onEnvoie={async () => {
          const quiz = await creerQuiz({
            titre,
            description,
            axe_code: axe,
            ...champsParcours.entree,
          });
          await naviguer({ to: "/admin/quiz/$id", params: { id: quiz.id } });
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
        <ChampsParcours etat={champsParcours} fascicules={fascicules} />
      </DialogueFormulaire>
    </div>
  );
}

function Filtre({
  recherche,
  libelle,
  actif,
}: {
  recherche: Recherche;
  libelle: string;
  actif: boolean;
}) {
  return (
    <Link
      to="/admin/quiz"
      search={recherche}
      aria-current={actif ? "page" : undefined}
      className={`rounded-full px-3 py-1.5 text-sm font-semibold ring-1 transition ${
        actif ? "bg-night text-white ring-night" : "bg-white ring-border"
      }`}
    >
      {libelle}
    </Link>
  );
}
