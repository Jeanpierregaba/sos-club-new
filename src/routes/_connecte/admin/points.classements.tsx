import { createFileRoute, useNavigate, useRouter } from "@tanstack/react-router";
import { ArrowLeft, PenLine, Search, Users } from "lucide-react";
import { useState } from "react";

import { DialogueCorrection } from "@/components/admin/DialogueCorrection";
import { RefusOuPanne } from "@/components/admin/RefusOuPanne";
import { CHAMP_ADMIN, Champ } from "@/components/admin/DialogueFormulaire";
import { Choix, ListeClassement, Pagination } from "@/components/classements/TableauClassement";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import { STATUTS_CLUB } from "@/lib/clubs";
import {
  adminClassements,
  adminSuiviClubs,
  chargerDre,
  type CategorieClassement,
  type ClassementAdmin,
  type PeriodeClassement,
} from "@/lib/api/client";
import {
  CATEGORIES,
  estCategorie,
  estPeriode,
  formaterPoints,
  PERIODES,
  sousTitre,
} from "@/lib/classements";

const PAR_PAGE = 50;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

type Recherche = {
  categorie?: CategorieClassement | undefined;
  dre?: string | undefined;
  periode?: PeriodeClassement | undefined;
  club_id?: string | undefined;
  page?: number | undefined;
};

export const Route = createFileRoute("/_connecte/admin/points/classements")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const texte = (cle: string) =>
      typeof search[cle] === "string" && search[cle] ? (search[cle] as string) : undefined;
    const page = Number(search["page"]);
    return {
      ...(estCategorie(search["categorie"]) ? { categorie: search["categorie"] } : {}),
      ...(texte("dre") ? { dre: texte("dre") } : {}),
      ...(estPeriode(search["periode"]) ? { periode: search["periode"] } : {}),
      ...(UUID.test(texte("club_id") ?? "") ? { club_id: texte("club_id") } : {}),
      ...(Number.isInteger(page) && page > 1 ? { page } : {}),
    };
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const categorie = deps.club_id && deps.categorie === "clubs" ? "eleves" : deps.categorie;
    const [classement, dres] = await Promise.all([
      adminClassements({
        categorie: categorie ?? "eleves",
        periode: deps.periode ?? "semestre",
        page: deps.page ?? 1,
        par_page: PAR_PAGE,
        ...(deps.club_id
          ? { club_id: deps.club_id }
          : deps.dre
            ? { niveau: "dre" as const, dre: deps.dre }
            : { niveau: "national" as const }),
      }),
      chargerDre().catch(() => []),
    ]);
    return { classement, dres };
  },
  gcTime: 0,
  errorComponent: RefusOuPanne,
  component: ClassementsAdmin,
});

// Les classements vus par l'équipe (spec 036) : les mêmes que le public, avec les identifiants pour corriger, et le
// classement interne d'un club, même suspendu. Ni gel ni Top 3 ici : c'est R14.
function ClassementsAdmin() {
  const { classement, dres } = Route.useLoaderData();
  const recherche = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const periode = recherche.periode ?? "semestre";
  const page = recherche.page ?? 1;
  const interne = "statut" in classement;
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  const correcteur = peut(admin, "points", "modifier") && admin.perimetre_dre === null;
  const [aCorriger, setACorriger] = useState<{ id: string; libelle: string } | null>(null);

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
      {interne ? (
        <EnTeteClub
          classement={classement}
          retour={() => filtrer({ club_id: undefined, categorie: undefined })}
        />
      ) : (
        <ChoixDuClub ouvrir={(id) => filtrer({ club_id: id, categorie: "eleves" })} />
      )}

      <div className="flex flex-wrap items-center gap-3 rounded-3xl bg-white p-4 ring-1 ring-border">
        <Choix
          libelle="Catégorie"
          options={interne ? CATEGORIES.filter((c) => c.valeur !== "clubs") : CATEGORIES}
          valeur={classement.categorie}
          choisir={(valeur) => filtrer({ categorie: valeur })}
        />
        <Choix
          libelle="Période"
          options={PERIODES}
          valeur={periode}
          choisir={(valeur) => filtrer({ periode: valeur })}
        />
        {!interne && (
          <select
            aria-label="Niveau"
            value={recherche.dre ?? ""}
            onChange={(e) => filtrer({ dre: e.target.value || undefined })}
            className="rounded-full border bg-white px-4 py-2 text-sm font-semibold"
          >
            <option value="">National</option>
            {dres.map((dre) => (
              <option key={dre.code} value={dre.code}>
                DRE {dre.nom}
              </option>
            ))}
          </select>
        )}
      </div>

      {periode === "semestre" && !classement.semestre ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucun semestre en cours : le total historique reste consultable.
        </p>
      ) : classement.lignes.length === 0 ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Personne n'est classé sur cette période.
        </p>
      ) : (
        <ListeClassement
          libelle="Classement"
          lignes={lignesAffichees(classement, filtrer, correcteur ? setACorriger : null)}
        />
      )}

      <Pagination
        page={page}
        total={classement.total}
        parPage={PAR_PAGE}
        allerA={(suivante) => filtrer({ page: suivante })}
      />

      <DialogueCorrection
        ouvert={aCorriger !== null}
        onOuvert={(ouvert) => !ouvert && setACorriger(null)}
        onFait={() => router.invalidate()}
        beneficiaire={aCorriger}
      />
    </section>
  );
}

type Corriger = ((beneficiaire: { id: string; libelle: string }) => void) | null;

function BoutonCorriger({
  id,
  libelle,
  corriger,
}: {
  id: string;
  libelle: string;
  corriger: Corriger;
}) {
  if (!corriger) return null;
  return (
    <Button
      variant="outline"
      size="sm"
      className="rounded-full"
      onClick={() => corriger({ id, libelle })}
    >
      <PenLine className="size-4" /> Corriger
    </Button>
  );
}

function lignesAffichees(
  classement: ClassementAdmin,
  filtrer: (r: Recherche) => void,
  corriger: Corriger,
) {
  if ("statut" in classement)
    return classement.lignes.map((ligne, index) => ({
      cle: String(index),
      rang: ligne.rang,
      nom: ligne.nom,
      sousTitre: ligne.utilisateur_id,
      points: ligne.points,
      action: (
        <BoutonCorriger
          id={ligne.utilisateur_id}
          libelle={`${ligne.nom} · ${formaterPoints(ligne.points)} pts`}
          corriger={corriger}
        />
      ),
    }));
  return classement.lignes.map((ligne, index) => {
    const clubId = "club_id" in ligne ? ligne.club_id : null;
    const utilisateurId = "utilisateur_id" in ligne ? ligne.utilisateur_id : null;
    return {
      cle: String(index),
      rang: ligne.rang,
      nom: ligne.nom,
      sousTitre: utilisateurId ? `${sousTitre(ligne)} · ${utilisateurId}` : sousTitre(ligne),
      points: ligne.points,
      action: (
        <span className="flex flex-wrap gap-2">
          {utilisateurId && (
            <BoutonCorriger
              id={utilisateurId}
              libelle={`${ligne.nom} · ${formaterPoints(ligne.points)} pts`}
              corriger={corriger}
            />
          )}
          {clubId && (
            <Button
              variant="outline"
              size="sm"
              className="rounded-full"
              onClick={() => filtrer({ club_id: clubId, categorie: "eleves" })}
            >
              <Users className="size-4" /> Club
            </Button>
          )}
        </span>
      ),
    };
  });
}

function EnTeteClub({
  classement,
  retour,
}: {
  classement: Extract<ClassementAdmin, { statut: string }>;
  retour: () => void;
}) {
  const statut = STATUTS_CLUB[classement.statut as keyof typeof STATUTS_CLUB];
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-3xl bg-mist-soft p-4">
      <Button variant="outline" className="rounded-full font-bold" onClick={retour}>
        <ArrowLeft className="size-4" /> Classements du réseau
      </Button>
      <p className="font-display text-xl text-logo-blue">{classement.club.nom}</p>
      {statut && (
        <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${statut.classe}`}>
          {statut.libelle}
        </span>
      )}
      <p className="text-sm font-semibold text-muted-foreground">
        Classement interne, privé : jamais publié.
      </p>
    </div>
  );
}

function ChoixDuClub({ ouvrir }: { ouvrir: (id: string) => void }) {
  const [texte, setTexte] = useState("");
  const [clubs, setClubs] = useState<{ id: string; nom: string }[] | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  return (
    <form
      className="flex flex-wrap items-end gap-2 rounded-3xl bg-white p-4 ring-1 ring-border"
      onSubmit={async (e) => {
        e.preventDefault();
        setErreur(null);
        try {
          const page = await adminSuiviClubs({ recherche: texte.trim() || undefined });
          setClubs(page.clubs.map((c) => ({ id: c.id, nom: c.nom })));
        } catch {
          setErreur("La liste des clubs demande le droit de consulter les clubs.");
        }
      }}
    >
      <Champ libelle="Classement interne d'un club">
        <input
          value={texte}
          onChange={(e) => setTexte(e.target.value)}
          maxLength={100}
          placeholder="Nom du club ou de l'établissement"
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Button type="submit" variant="outline" className="h-11 rounded-full">
        <Search className="size-4" /> Chercher
      </Button>
      {erreur && <p className="w-full text-sm font-semibold text-logo-red">{erreur}</p>}
      {clubs && clubs.length === 0 && (
        <p className="w-full text-sm font-semibold text-muted-foreground">Aucun club trouvé.</p>
      )}
      {clubs && clubs.length > 0 && (
        <ul className="flex w-full flex-wrap gap-2">
          {clubs.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => ouvrir(c.id)}
                className="rounded-full bg-mist-soft px-3 py-1.5 text-sm font-bold hover:ring-1 hover:ring-night/30"
              >
                {c.nom}
              </button>
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}
