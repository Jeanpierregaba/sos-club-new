import { createFileRoute, useNavigate, useRouter } from "@tanstack/react-router";
import { Check, ChevronLeft, ChevronRight, Pencil, Plus, Replace, Search } from "lucide-react";
import { useState } from "react";

import {
  BadgeActif,
  CHAMP_ADMIN,
  Champ,
  DialogueFormulaire,
} from "@/components/admin/DialogueFormulaire";
import { ChoixEtablissement, type EtablissementChoisi } from "@/components/ChoixEtablissement";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  adminCreerEtablissement,
  adminListerDre,
  adminListerEtablissements,
  adminModifierEtablissement,
  adminRemplacerEtablissement,
  ErreurApi,
  type DreAdmin,
  type EtablissementAdmin,
  type StatutEtablissement,
  type TypeEtablissement,
} from "@/lib/api/client";

const TYPES: Record<TypeEtablissement, string> = {
  lycee: "Lycée",
  college: "Collège",
  complexe: "Complexe scolaire",
  autre: "Autre",
};
const STATUTS: Record<StatutEtablissement, string> = {
  actif: "Actif",
  inactif: "Désactivé",
  propose: "Proposé",
};

type Recherche = {
  recherche?: string | undefined;
  dre?: string | undefined;
  iesg?: string | undefined;
  type?: TypeEtablissement | undefined;
  statut?: StatutEtablissement | undefined;
  page?: number | undefined;
};

const texte = (s: Record<string, unknown>, cle: string) =>
  typeof s[cle] === "string" && s[cle] ? { [cle]: s[cle] as string } : {};

export const Route = createFileRoute("/_connecte/admin/referentiel/etablissements")({
  validateSearch: (s: Record<string, unknown>): Recherche => ({
    ...texte(s, "recherche"),
    ...texte(s, "dre"),
    ...texte(s, "iesg"),
    ...(typeof s["type"] === "string" && s["type"] in TYPES
      ? { type: s["type"] as TypeEtablissement }
      : {}),
    ...(typeof s["statut"] === "string" && s["statut"] in STATUTS
      ? { statut: s["statut"] as StatutEtablissement }
      : {}),
    ...(Number(s["page"]) > 1 ? { page: Number(s["page"]) } : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [page, dres] = await Promise.all([adminListerEtablissements(deps), adminListerDre()]);
    return { page, dres };
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Etablissements,
});

function Etablissements() {
  const { admin } = Route.useRouteContext();
  const { page, dres } = Route.useLoaderData();
  const filtres = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const filtrer = (changement: Partial<Recherche>) =>
    naviguer({ search: (avant) => ({ ...avant, ...changement, page: undefined }) });
  const pages = Math.max(1, Math.ceil(page.total / page.par_page));
  const [edition, setEdition] = useState<EtablissementAdmin | "nouveau" | null>(null);
  const [proposition, setProposition] = useState<{
    action: "accepter" | "remplacer";
    etablissement: EtablissementAdmin;
  } | null>(null);
  const iesgDeLaDre = dres.find((d) => d.code === filtres.dre)?.iesg ?? dres.flatMap((d) => d.iesg);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        <div className="relative w-full max-w-72">
          <Search
            aria-hidden
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="search"
            key={filtres.recherche ?? ""}
            defaultValue={filtres.recherche ?? ""}
            onKeyDown={(e) => {
              if (e.key === "Enter")
                filtrer({ recherche: e.currentTarget.value.trim() || undefined });
            }}
            onBlur={(e) => {
              // Traverser le champ sans rien changer ne ramène pas à la page 1.
              const valeur = e.currentTarget.value.trim() || undefined;
              if (valeur !== filtres.recherche) filtrer({ recherche: valeur });
            }}
            placeholder="Nom, puis Entrée"
            aria-label="Rechercher un établissement par nom"
            className={`${CHAMP_ADMIN} pl-9`}
          />
        </div>
        {dres.length > 1 && (
          <select
            aria-label="DRE"
            value={filtres.dre ?? ""}
            onChange={(e) => filtrer({ dre: e.target.value || undefined, iesg: undefined })}
            className={`${CHAMP_ADMIN} max-w-52`}
          >
            <option value="">Toutes les DRE</option>
            {dres.map((d) => (
              <option key={d.code} value={d.code}>
                DRE {d.nom}
              </option>
            ))}
          </select>
        )}
        <select
          aria-label="IESG"
          value={filtres.iesg ?? ""}
          onChange={(e) => filtrer({ iesg: e.target.value || undefined })}
          className={`${CHAMP_ADMIN} max-w-56`}
        >
          <option value="">Toutes les IESG</option>
          {iesgDeLaDre.map((i) => (
            <option key={i.id} value={i.id}>
              {i.nom}
            </option>
          ))}
        </select>
        <select
          aria-label="Type"
          value={filtres.type ?? ""}
          onChange={(e) =>
            filtrer({ type: (e.target.value || undefined) as TypeEtablissement | undefined })
          }
          className={`${CHAMP_ADMIN} max-w-44`}
        >
          <option value="">Tous les types</option>
          {Object.entries(TYPES).map(([id, libelle]) => (
            <option key={id} value={id}>
              {libelle}
            </option>
          ))}
        </select>
        <select
          aria-label="Statut"
          value={filtres.statut ?? ""}
          onChange={(e) =>
            filtrer({ statut: (e.target.value || undefined) as StatutEtablissement | undefined })
          }
          className={`${CHAMP_ADMIN} max-w-40`}
        >
          <option value="">Tous les statuts</option>
          {Object.entries(STATUTS).map(([id, libelle]) => (
            <option key={id} value={id}>
              {libelle}
            </option>
          ))}
        </select>
        {peut(admin, "clubs", "creer") && (
          <Button
            onClick={() => setEdition("nouveau")}
            className="btn-fx h-11 rounded-full px-5 font-bold"
          >
            <Plus className="size-4" /> Nouvel établissement
          </Button>
        )}
      </div>

      <p aria-live="polite" className="text-sm font-semibold text-muted-foreground">
        {page.total} établissement{page.total > 1 ? "s" : ""}
      </p>

      <div className="overflow-x-auto rounded-3xl bg-white shadow-sm ring-1 ring-border">
        <table className="w-full min-w-[44rem] text-sm">
          <thead className="bg-mist-soft text-left text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
            <tr>
              <th scope="col" className="px-4 py-3">
                Établissement
              </th>
              <th scope="col" className="px-4 py-3">
                Type
              </th>
              <th scope="col" className="px-4 py-3">
                IESG · DRE
              </th>
              <th scope="col" className="px-4 py-3">
                Localité
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                Élèves
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                Encadreurs
              </th>
              <th scope="col" className="px-4 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {page.etablissements.map((e) => (
              <tr key={e.id} className="border-t hover:bg-mist-soft/60">
                <td className="px-4 py-3 font-bold">
                  {e.nom} <BadgeActif actif={e.statut !== "inactif"} />
                  {e.statut === "propose" && (
                    <span className="ml-1 rounded-full bg-sky/15 px-2.5 py-0.5 text-xs font-extrabold text-sky">
                      Proposé
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">{TYPES[e.type]}</td>
                <td className="px-4 py-3">
                  {e.iesg}
                  <span className="block text-xs text-muted-foreground">DRE {e.dre}</span>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{e.localite ?? "—"}</td>
                <td className="px-4 py-3 text-right font-bold tabular-nums">{e.nb_eleves}</td>
                <td className="px-4 py-3 text-right font-bold tabular-nums">{e.nb_encadreurs}</td>
                <td className="px-4 py-3 text-right">
                  {peut(admin, "clubs", "modifier") && e.statut === "propose" && (
                    <span className="mb-1.5 inline-flex flex-wrap justify-end gap-1.5">
                      <button
                        type="button"
                        onClick={() => setProposition({ action: "accepter", etablissement: e })}
                        className="inline-flex items-center gap-1.5 rounded-full bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground transition hover:bg-primary/90"
                      >
                        <Check className="size-3.5" /> Accepter
                      </button>
                      <button
                        type="button"
                        onClick={() => setProposition({ action: "remplacer", etablissement: e })}
                        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
                      >
                        <Replace className="size-3.5" /> Remplacer par…
                      </button>
                    </span>
                  )}
                  {peut(admin, "clubs", "modifier") && (
                    <button
                      type="button"
                      onClick={() => setEdition(e)}
                      aria-label={`Modifier ${e.nom}`}
                      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
                    >
                      <Pencil className="size-3.5" /> Modifier
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {page.etablissements.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-10 text-center font-semibold text-muted-foreground"
                >
                  Aucun établissement ne correspond à ces filtres.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <nav
          aria-label="Pages"
          className="flex items-center justify-center gap-3 text-sm font-bold"
        >
          <button
            type="button"
            disabled={page.page <= 1}
            onClick={() => naviguer({ search: (avant) => ({ ...avant, page: page.page - 1 }) })}
            className="inline-flex size-10 items-center justify-center rounded-full bg-white ring-1 ring-border disabled:opacity-40"
            aria-label="Page précédente"
          >
            <ChevronLeft className="size-4" />
          </button>
          Page {page.page} sur {pages}
          <button
            type="button"
            disabled={page.page >= pages}
            onClick={() => naviguer({ search: (avant) => ({ ...avant, page: page.page + 1 }) })}
            className="inline-flex size-10 items-center justify-center rounded-full bg-white ring-1 ring-border disabled:opacity-40"
            aria-label="Page suivante"
          >
            <ChevronRight className="size-4" />
          </button>
        </nav>
      )}

      {proposition?.action === "accepter" && (
        <AccepterProposition
          etablissement={proposition.etablissement}
          fermer={() => setProposition(null)}
        />
      )}
      {proposition?.action === "remplacer" && (
        <RemplacerProposition
          etablissement={proposition.etablissement}
          fermer={() => setProposition(null)}
        />
      )}
      {edition && (
        <FormulaireEtablissement
          key={edition === "nouveau" ? "nouveau" : edition.id}
          etablissement={edition === "nouveau" ? null : edition}
          dres={dres}
          iesgParDefaut={filtres.iesg}
          fermer={() => setEdition(null)}
        />
      )}
    </div>
  );
}

function FormulaireEtablissement({
  etablissement,
  dres,
  iesgParDefaut,
  fermer,
}: {
  etablissement: EtablissementAdmin | null;
  dres: DreAdmin[];
  iesgParDefaut: string | undefined;
  fermer: () => void;
}) {
  const router = useRouter();
  const [nom, setNom] = useState(etablissement?.nom ?? "");
  const [type, setType] = useState<TypeEtablissement>(etablissement?.type ?? "college");
  const [iesg, setIesg] = useState(etablissement?.iesg_id ?? iesgParDefaut ?? "");
  const [localite, setLocalite] = useState(etablissement?.localite ?? "");
  const [statut, setStatut] = useState(etablissement?.statut ?? "actif");

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={etablissement ? `Modifier ${etablissement.nom}` : "Nouvel établissement"}
      description={
        etablissement
          ? "Si quelqu'un l'a modifié entre-temps, l'enregistrement est refusé : recharge la page."
          : "Deux établissements ne peuvent pas porter le même nom dans une même IESG."
      }
      bouton="Enregistrer"
      onEnvoie={async () => {
        const champs = { nom, type, iesg_id: iesg, localite: localite || null };
        if (etablissement)
          await adminModifierEtablissement(etablissement.id, {
            version: etablissement.version,
            ...champs,
            ...(statut !== "propose" ? { statut } : {}),
          });
        else await adminCreerEtablissement(champs);
        await router.invalidate();
      }}
    >
      <Champ libelle="Nom">
        <input
          required
          value={nom}
          onChange={(e) => setNom(e.target.value)}
          maxLength={150}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Type">
        <select
          value={type}
          onChange={(e) => setType(e.target.value as TypeEtablissement)}
          className={CHAMP_ADMIN}
        >
          {Object.entries(TYPES).map(([id, libelle]) => (
            <option key={id} value={id}>
              {libelle}
            </option>
          ))}
        </select>
      </Champ>
      <Champ libelle="IESG">
        <select
          required
          value={iesg}
          onChange={(e) => setIesg(e.target.value)}
          className={CHAMP_ADMIN}
        >
          <option value="" disabled>
            Choisis une IESG
          </option>
          {dres.map((d) => (
            <optgroup key={d.code} label={`DRE ${d.nom}`}>
              {d.iesg
                .filter((i) => i.actif || i.id === etablissement?.iesg_id)
                .map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nom}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>
      </Champ>
      <Champ libelle="Localité (facultatif)">
        <input
          value={localite}
          onChange={(e) => setLocalite(e.target.value)}
          maxLength={150}
          className={CHAMP_ADMIN}
        />
      </Champ>
      {etablissement && statut !== "propose" && (
        <Champ libelle="Statut">
          <select
            value={statut}
            onChange={(e) => setStatut(e.target.value as "actif" | "inactif")}
            className={CHAMP_ADMIN}
          >
            <option value="actif">Actif : visible dans les listes et formulaires</option>
            <option value="inactif">Désactivé : masqué, gardé pour l'historique</option>
          </select>
        </Champ>
      )}
    </DialogueFormulaire>
  );
}

// Établissements proposés par des élèves à leur inscription (spec 017).
function AccepterProposition({
  etablissement,
  fermer,
}: {
  etablissement: EtablissementAdmin;
  fermer: () => void;
}) {
  const router = useRouter();
  const [nom, setNom] = useState(etablissement.nom);
  const [type, setType] = useState<TypeEtablissement>(etablissement.type);

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre="Accepter cet établissement"
      description={`Il rejoint la liste publique de l'${etablissement.iesg}. Vérifie son nom et son type avant.`}
      bouton="Accepter"
      onEnvoie={async () => {
        await adminModifierEtablissement(etablissement.id, {
          version: etablissement.version,
          nom,
          type,
          statut: "actif",
        });
        await router.invalidate();
      }}
    >
      <Champ libelle="Nom">
        <input
          required
          value={nom}
          onChange={(e) => setNom(e.target.value)}
          maxLength={150}
          className={CHAMP_ADMIN}
        />
      </Champ>
      <Champ libelle="Type">
        <select
          value={type}
          onChange={(e) => setType(e.target.value as TypeEtablissement)}
          className={CHAMP_ADMIN}
        >
          {Object.entries(TYPES).map(([valeur, libelle]) => (
            <option key={valeur} value={valeur}>
              {libelle}
            </option>
          ))}
        </select>
      </Champ>
    </DialogueFormulaire>
  );
}

function RemplacerProposition({
  etablissement,
  fermer,
}: {
  etablissement: EtablissementAdmin;
  fermer: () => void;
}) {
  const router = useRouter();
  const [cible, setCible] = useState<EtablissementChoisi | null>(null);
  const inscrits = etablissement.nb_eleves + etablissement.nb_encadreurs;

  return (
    <DialogueFormulaire
      ouvert
      onOuvert={(o) => !o && fermer()}
      titre={`Remplacer « ${etablissement.nom} »`}
      description={`Cet établissement existe déjà sous un autre nom ? Choisis-le : ${inscrits} inscrit${inscrits > 1 ? "s" : ""} (élèves et encadreurs) y ser${inscrits > 1 ? "ont" : "a"} rattaché${inscrits > 1 ? "s" : ""}, et la proposition sera désactivée.`}
      bouton="Remplacer"
      onEnvoie={async () => {
        if (!cible) throw new ErreurApi(422, "Choisis un établissement de la liste.");
        await adminRemplacerEtablissement(etablissement.id, {
          version: etablissement.version,
          cible_id: cible.id,
        });
        await router.invalidate();
      }}
    >
      <ChoixEtablissement valeur={cible} onChoix={setCible} exclure={etablissement.id} />
    </DialogueFormulaire>
  );
}
