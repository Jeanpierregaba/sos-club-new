import { createFileRoute, useNavigate, useRouter } from "@tanstack/react-router";
import { PlusCircle, Search, Undo2 } from "lucide-react";
import { useEffect, useState } from "react";

import { RefusOuPanne } from "@/components/admin/RefusOuPanne";
import { DialogueCorrection } from "@/components/admin/DialogueCorrection";
import { CHAMP_ADMIN, Champ, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Pagination } from "@/components/classements/TableauClassement";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminAnnulerLigne,
  adminListerAnnees,
  adminListerBareme,
  adminListerRegistre,
  adminListerSemestres,
  type FiltresRegistre,
  type LigneRegistre,
} from "@/lib/api/client";
import { formaterPoints } from "@/lib/classements";

const PAR_PAGE = 50;

type Recherche = {
  recherche?: string | undefined;
  beneficiaire?: "eleve" | "encadreur" | undefined;
  correction?: "true" | "false" | undefined;
  semestre_id?: string | undefined;
  annee_id?: string | undefined;
  du?: string | undefined;
  au?: string | undefined;
  action?: string | undefined;
  club_id?: string | undefined;
  page?: number | undefined;
};

const JOUR = /^\d{4}-\d{2}-\d{2}$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export const Route = createFileRoute("/_connecte/admin/points/registre")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const texte = (cle: string) =>
      typeof search[cle] === "string" && search[cle] ? (search[cle] as string) : undefined;
    const beneficiaire = search["beneficiaire"];
    const correction = search["correction"];
    const page = Number(search["page"]);
    return {
      ...(texte("recherche") ? { recherche: texte("recherche") } : {}),
      ...(beneficiaire === "eleve" || beneficiaire === "encadreur" ? { beneficiaire } : {}),
      ...(correction === "true" || correction === "false" ? { correction } : {}),
      ...(UUID.test(texte("semestre_id") ?? "") ? { semestre_id: texte("semestre_id") } : {}),
      ...(UUID.test(texte("annee_id") ?? "") ? { annee_id: texte("annee_id") } : {}),
      ...(JOUR.test(texte("du") ?? "") ? { du: texte("du") } : {}),
      ...(JOUR.test(texte("au") ?? "") ? { au: texte("au") } : {}),
      ...(texte("action") ? { action: texte("action") } : {}),
      ...(UUID.test(texte("club_id") ?? "") ? { club_id: texte("club_id") } : {}),
      ...(Number.isInteger(page) && page > 1 ? { page } : {}),
    };
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const filtres: FiltresRegistre = { ...deps, par_page: PAR_PAGE };
    const [registre, semestres, annees, bareme] = await Promise.all([
      adminListerRegistre(filtres),
      adminListerSemestres().catch(() => []),
      adminListerAnnees().catch(() => []),
      adminListerBareme().catch(() => []),
    ]);
    return { registre, semestres, annees, bareme };
  },
  gcTime: 0,
  errorComponent: RefusOuPanne,
  component: Registre,
});

const dateHeure = (iso: string) =>
  new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });

// Le registre des points (spec 036) : en lecture seule. Une erreur se corrige par une nouvelle ligne motivée,
// jamais en modifiant une ligne.
function Registre() {
  const { registre, semestres, annees, bareme } = Route.useLoaderData();
  const recherche = Route.useSearch();
  const { admin } = Route.useRouteContext();
  const naviguer = useNavigate({ from: Route.fullPath });
  const router = useRouter();
  const correcteur = peut(admin, "points", "modifier") && admin.perimetre_dre === null;
  const [texte, setTexte] = useState(recherche.recherche ?? "");
  const [corriger, setCorriger] = useState(false);
  const [aAnnuler, setAAnnuler] = useState<LigneRegistre | null>(null);
  const page = recherche.page ?? 1;

  const filtrer = (changements: Recherche) =>
    naviguer({
      search: (avant) => {
        const suite: Recherche = { ...avant, ...changements };
        if (!("page" in changements)) delete suite.page;
        for (const cle of Object.keys(suite) as (keyof Recherche)[])
          if (suite[cle] === undefined || suite[cle] === "") delete suite[cle];
        return suite;
      },
    });

  return (
    <section className="space-y-4">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Chaque ligne est un gain, une annulation ou une correction. Aucune ligne ne se modifie : une
        erreur se corrige par une nouvelle ligne motivée, écrite au journal d'audit.
      </p>

      <div className="flex flex-wrap items-end gap-3 rounded-3xl bg-white p-4 ring-1 ring-border">
        <form
          className="flex min-w-0 flex-1 items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            filtrer({ recherche: texte.trim() || undefined });
          }}
        >
          <Champ libelle="Recherche">
            <input
              value={texte}
              onChange={(e) => setTexte(e.target.value)}
              maxLength={100}
              placeholder="Pseudonyme, identifiant, nom"
              className={CHAMP_ADMIN}
            />
          </Champ>
          <Button
            type="submit"
            variant="outline"
            className="h-11 rounded-full"
            aria-label="Chercher"
          >
            <Search className="size-4" />
          </Button>
        </form>
        <Champ libelle="Bénéficiaire">
          <select
            value={recherche.beneficiaire ?? ""}
            onChange={(e) =>
              filtrer({ beneficiaire: (e.target.value || undefined) as Recherche["beneficiaire"] })
            }
            className={CHAMP_ADMIN}
          >
            <option value="">Tous</option>
            <option value="eleve">Élèves</option>
            <option value="encadreur">Encadreurs</option>
          </select>
        </Champ>
        <Champ libelle="Type">
          <select
            value={recherche.correction ?? ""}
            onChange={(e) =>
              filtrer({ correction: (e.target.value || undefined) as Recherche["correction"] })
            }
            className={CHAMP_ADMIN}
          >
            <option value="">Toutes les lignes</option>
            <option value="true">Corrections</option>
            <option value="false">Hors corrections</option>
          </select>
        </Champ>
        <Champ libelle="Semestre">
          <select
            value={recherche.semestre_id ?? ""}
            onChange={(e) => filtrer({ semestre_id: e.target.value || undefined })}
            className={CHAMP_ADMIN}
          >
            <option value="">Tous</option>
            {semestres.map((s) => (
              <option key={s.id} value={s.id}>
                {s.libelle}
              </option>
            ))}
          </select>
        </Champ>
        <Champ libelle="Année académique">
          <select
            value={recherche.annee_id ?? ""}
            onChange={(e) => filtrer({ annee_id: e.target.value || undefined })}
            className={CHAMP_ADMIN}
          >
            <option value="">Toutes</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>
                {a.libelle}
              </option>
            ))}
          </select>
        </Champ>
        <Champ libelle="Action">
          <select
            value={recherche.action ?? ""}
            onChange={(e) => filtrer({ action: e.target.value || undefined })}
            className={CHAMP_ADMIN}
          >
            <option value="">Toutes</option>
            {bareme.map((b) => (
              <option key={b.code} value={b.code}>
                {b.libelle} ({b.beneficiaire === "eleve" ? "élève" : "encadreur"})
              </option>
            ))}
          </select>
        </Champ>
        <Champ libelle="Du">
          <input
            type="date"
            value={recherche.du ?? ""}
            max={recherche.au}
            onChange={(e) => filtrer({ du: e.target.value || undefined })}
            className={CHAMP_ADMIN}
          />
        </Champ>
        <Champ libelle="Au (inclus)">
          <input
            type="date"
            value={recherche.au ?? ""}
            min={recherche.du}
            onChange={(e) => filtrer({ au: e.target.value || undefined })}
            className={CHAMP_ADMIN}
          />
        </Champ>
        {correcteur && (
          <Button onClick={() => setCorriger(true)} className="btn-fx h-11 rounded-full font-bold">
            <PlusCircle className="size-4" /> Corriger un score
          </Button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm font-bold text-ink">
          {registre.total.toLocaleString("fr-FR")} ligne{registre.total > 1 ? "s" : ""}
        </p>
        {recherche.club_id && (
          <button
            type="button"
            onClick={() => filtrer({ club_id: undefined })}
            className="rounded-full bg-mist-soft px-3 py-1 text-sm font-bold hover:ring-1 hover:ring-night/30"
          >
            Club :{" "}
            {registre.lignes.find((l) => l.club?.id === recherche.club_id)?.club?.nom ?? "filtré"} ✕
          </button>
        )}
      </div>

      {registre.lignes.length === 0 ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucune ligne ne correspond à ces filtres.
        </p>
      ) : (
        <ul className="divide-y overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
          {registre.lignes.map((ligne) => (
            <LigneDuRegistre
              key={ligne.id}
              ligne={ligne}
              onAnnuler={correcteur ? () => setAAnnuler(ligne) : null}
              onClub={(clubId) => filtrer({ club_id: clubId })}
            />
          ))}
        </ul>
      )}

      <Pagination
        page={page}
        total={registre.total}
        parPage={PAR_PAGE}
        allerA={(suivante) => filtrer({ page: suivante })}
      />

      <DialogueCorrection
        ouvert={corriger}
        onOuvert={setCorriger}
        onFait={() => router.invalidate()}
      />
      <DialogueAnnulation
        ligne={aAnnuler}
        onFerme={() => setAAnnuler(null)}
        onFait={() => router.invalidate()}
      />
    </section>
  );
}

function LigneDuRegistre({
  ligne,
  onAnnuler,
  onClub,
}: {
  ligne: LigneRegistre;
  onAnnuler: (() => void) | null;
  onClub: (clubId: string) => void;
}) {
  const nom = ligne.pseudonyme
    ? `${ligne.pseudonyme} (${ligne.identifiant})`
    : `${ligne.prenom} ${ligne.nom} (${ligne.identifiant})`;
  return (
    <li id={`ligne-${ligne.id}`} className="flex flex-wrap items-start gap-3 px-4 py-3 sm:px-5">
      <div className="min-w-0 flex-1">
        <p className="break-words font-bold text-ink">
          {nom}
          <span className="ml-2 text-xs font-semibold text-muted-foreground">
            {ligne.role === "eleve" ? "Élève" : "Encadreur"}
          </span>
        </p>
        <p className="break-words text-sm font-semibold text-ink/80">
          {ligne.est_correction && !ligne.est_annulation
            ? "Correction manuelle"
            : ligne.action_libelle}
          {ligne.est_annulation && ligne.annule_id && (
            <>
              {" · annulation de "}
              <a href={`#ligne-${ligne.annule_id}`} className="text-primary underline">
                la ligne {ligne.annule_id.slice(0, 8)}
              </a>
            </>
          )}
          {ligne.annulee && " · annulée"}
        </p>
        <p className="break-words text-xs font-semibold text-muted-foreground">
          {dateHeure(ligne.cree_le)} · {ligne.semestre ?? "hors semestre"} ·{" "}
          {ligne.annee ?? "hors année"}
          {ligne.club && (
            <>
              {" · "}
              <button
                type="button"
                title="Voir les lignes de ce club"
                onClick={() => ligne.club && onClub(ligne.club.id)}
                className="font-bold text-primary underline-offset-4 hover:underline"
              >
                {ligne.club.nom}
              </button>
              {` (${ligne.points_club !== null ? formaterPoints(ligne.points_club) : "0"} pts)`}
            </>
          )}
          {ligne.valide_par && ` · par ${ligne.valide_par.nom}`}
        </p>
        {ligne.motif && (
          <p className="mt-1 break-words text-sm italic text-ink/80">« {ligne.motif} »</p>
        )}
        <p className="break-all text-[11px] font-medium text-muted-foreground">{ligne.cle}</p>
      </div>
      <span
        className={`shrink-0 rounded-full px-3 py-1 text-sm font-extrabold ${ligne.montant > 0 ? "bg-primary/10 text-primary" : "bg-logo-red/10 text-logo-red"}`}
      >
        {ligne.montant > 0 ? "+" : ""}
        {formaterPoints(ligne.montant)}
      </span>
      {onAnnuler && !ligne.est_annulation && !ligne.annulee && (
        <Button variant="outline" size="sm" className="rounded-full" onClick={onAnnuler}>
          <Undo2 className="size-4" /> Annuler
        </Button>
      )}
    </li>
  );
}

function DialogueAnnulation({
  ligne,
  onFerme,
  onFait,
}: {
  ligne: LigneRegistre | null;
  onFerme: () => void;
  onFait: () => Promise<unknown>;
}) {
  const [motif, setMotif] = useState("");

  useEffect(() => {
    if (ligne) setMotif("");
  }, [ligne]);

  return (
    <DialogueFormulaire
      ouvert={ligne !== null}
      onOuvert={(ouvert) => !ouvert && onFerme()}
      titre="Annuler cette ligne"
      danger
      description={
        ligne
          ? `Une ligne de ${formaterPoints(-ligne.montant)} points sera écrite dans le même semestre, avec la part du club d'origine. La ligne d'origine reste dans le registre.`
          : undefined
      }
      bouton="Annuler la ligne"
      onEnvoie={async () => {
        if (!ligne) return;
        await adminAnnulerLigne(ligne.id, motif.trim());
        await onFait();
      }}
    >
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
    </DialogueFormulaire>
  );
}
