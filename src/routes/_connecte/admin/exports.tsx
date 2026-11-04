import { createFileRoute, useRouter } from "@tanstack/react-router";
import { FileSpreadsheet, Loader2, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { PROFILS, dateHeure, peut } from "@/lib/admin";
import {
  apercuExport,
  creerExport,
  ErreurApi,
  historiqueExports,
  MESSAGE_INDISPONIBLE,
  type ExportEntree,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/exports")({
  loader: () => historiqueExports(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Exports,
});

type Colonne = ExportEntree["colonnes"] extends (infer C)[] | undefined ? C : never;

const COLONNES: { id: Colonne; libelle: string; defaut: boolean }[] = [
  { id: "identifiant", libelle: "Identifiant", defaut: true },
  { id: "prenom", libelle: "Prénom", defaut: true },
  { id: "nom", libelle: "Nom", defaut: true },
  { id: "email", libelle: "E-mail", defaut: false },
  { id: "telephone", libelle: "Téléphone", defaut: false },
  { id: "profil", libelle: "Profil", defaut: true },
  { id: "statut", libelle: "Statut", defaut: true },
  { id: "date_inscription", libelle: "Date d'inscription", defaut: true },
  { id: "consentement", libelle: "Consentement", defaut: false },
];

const STATUTS_EXPORT = {
  pret: "Prêt",
  telecharge: "Téléchargé",
  expire: "Expiré",
  echec: "Échec",
} as const;

const CHAMP =
  "h-10 w-full rounded-xl border bg-white px-3 text-sm font-semibold outline-none focus:border-logo-blue";

function Exports() {
  const { admin } = Route.useRouteContext();
  const historique = Route.useLoaderData();
  const router = useRouter();
  const nominatifPossible = peut(admin, "inscrits", "exporter") && admin.perimetre_dre === null;
  const agregePossible = peut(admin, "statistiques", "exporter");

  const [type, setType] = useState<ExportEntree["type"]>(agregePossible ? "agrege" : "nominatif");
  const [format, setFormat] = useState<ExportEntree["format"]>("xlsx");
  const [profil, setProfil] = useState("");
  const [statut, setStatut] = useState("");
  const [depuis, setDepuis] = useState("");
  const [avant, setAvant] = useState("");
  const [colonnes, setColonnes] = useState(
    new Set(COLONNES.filter((c) => c.defaut).map((c) => c.id)),
  );
  const [finalite, setFinalite] = useState("");
  const [volume, setVolume] = useState<number | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const entree = (): ExportEntree => ({
    type,
    format,
    filtres: {
      ...(profil ? { profil: profil as "eleve" } : {}),
      ...(statut ? { statut: statut as "actif" } : {}),
      ...(depuis ? { inscrit_depuis: `${depuis}T00:00:00Z` } : {}),
      ...(avant ? { inscrit_avant: `${avant}T23:59:59Z` } : {}),
    },
    colonnes:
      type === "nominatif" ? COLONNES.filter((c) => colonnes.has(c.id)).map((c) => c.id) : [],
    finalite: type === "nominatif" ? finalite.trim() : null,
  });

  const verifier = async () => {
    setErreur(null);
    if (type === "nominatif" && colonnes.size === 0)
      return setErreur("Choisis au moins une colonne.");
    if (type === "nominatif" && finalite.trim().length < 5)
      return setErreur("Indique la finalité de cet export (5 caractères au moins).");
    setEnCours(true);
    try {
      setVolume((await apercuExport(entree())).nb_lignes);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  const confirmer = async () => {
    setEnCours(true);
    try {
      const cree = await creerExport(entree());
      setVolume(null);
      // Le navigateur télécharge le fichier avec la session : le lien ne sert qu'une fois.
      window.location.assign(cree.lien);
      await router.invalidate();
    } catch (e) {
      setVolume(null);
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div className="space-y-8">
      <EnTeteAdmin sur="Base des inscrits" bleu="Exports" vert="tracés">
        Chaque export est inscrit à l'historique et au journal d'audit. Le lien de téléchargement ne
        sert qu'une fois, pendant 15 minutes.
      </EnTeteAdmin>

      <section className="grid gap-6 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border md:p-8 lg:grid-cols-2">
        <div className="space-y-5">
          <fieldset>
            <legend className="text-sm font-extrabold">Type d'export</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {(
                [
                  [
                    "agrege",
                    "Statistiques agrégées",
                    "Nombre de comptes par profil, statut et mois.",
                    agregePossible,
                  ],
                  [
                    "nominatif",
                    "Liste nominative",
                    "Les colonnes de ton choix, compte par compte.",
                    nominatifPossible,
                  ],
                ] as const
              ).map(([valeur, titre, aide, possible]) => (
                <label
                  key={valeur}
                  className={`flex cursor-pointer gap-3 rounded-2xl p-4 ring-1 ${
                    type === valeur ? "bg-mist-soft ring-logo-blue" : "ring-border"
                  } ${possible ? "" : "cursor-not-allowed opacity-50"}`}
                >
                  <input
                    type="radio"
                    name="type"
                    value={valeur}
                    checked={type === valeur}
                    disabled={!possible}
                    onChange={() => {
                      setType(valeur);
                      setVolume(null);
                    }}
                    className="mt-1 accent-[var(--logo-blue)]"
                  />
                  <span>
                    <span className="block font-bold">{titre}</span>
                    <span className="text-xs font-medium text-muted-foreground">
                      {possible ? aide : "Tu n'as pas ce droit."}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="grid gap-3 sm:grid-cols-2">
            <legend className="mb-2 text-sm font-extrabold">Filtres</legend>
            <label className="grid gap-1 text-xs font-bold text-muted-foreground">
              Profil
              <select value={profil} onChange={(e) => setProfil(e.target.value)} className={CHAMP}>
                <option value="">Tous</option>
                {(["eleve", "encadreur", "admin"] as const).map((p) => (
                  <option key={p} value={p}>
                    {PROFILS[p]}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-xs font-bold text-muted-foreground">
              Statut
              <select value={statut} onChange={(e) => setStatut(e.target.value)} className={CHAMP}>
                <option value="">Tous</option>
                <option value="actif">Actif</option>
                <option value="suspendu">Suspendu</option>
                <option value="revoque">Révoqué</option>
              </select>
            </label>
            <label className="grid gap-1 text-xs font-bold text-muted-foreground">
              Inscrits depuis le
              <input
                type="date"
                value={depuis}
                onChange={(e) => setDepuis(e.target.value)}
                className={CHAMP}
              />
            </label>
            <label className="grid gap-1 text-xs font-bold text-muted-foreground">
              Jusqu'au
              <input
                type="date"
                value={avant}
                onChange={(e) => setAvant(e.target.value)}
                className={CHAMP}
              />
            </label>
          </fieldset>

          <fieldset>
            <legend className="text-sm font-extrabold">Format</legend>
            <div className="mt-2 flex gap-2">
              {(["xlsx", "csv"] as const).map((f) => (
                <label
                  key={f}
                  className={`cursor-pointer rounded-full px-4 py-2 text-sm font-bold ring-1 ${
                    format === f ? "bg-logo-blue text-white ring-logo-blue" : "ring-border"
                  }`}
                >
                  <input
                    type="radio"
                    name="format"
                    value={f}
                    checked={format === f}
                    onChange={() => setFormat(f)}
                    className="sr-only"
                  />
                  {f === "xlsx" ? "Excel (.xlsx)" : "CSV (.csv)"}
                </label>
              ))}
            </div>
          </fieldset>
        </div>

        <div className="space-y-5">
          {type === "nominatif" ? (
            <>
              <fieldset>
                <legend className="text-sm font-extrabold">Colonnes</legend>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {COLONNES.map((c) => (
                    <label key={c.id} className="flex items-center gap-2 text-sm font-semibold">
                      <input
                        type="checkbox"
                        checked={colonnes.has(c.id)}
                        onChange={() => {
                          const suivant = new Set(colonnes);
                          if (suivant.has(c.id)) suivant.delete(c.id);
                          else suivant.add(c.id);
                          setColonnes(suivant);
                        }}
                        className="size-4 accent-[var(--primary)]"
                      />
                      {c.libelle}
                    </label>
                  ))}
                </div>
              </fieldset>
              <label className="grid gap-1.5 text-sm font-extrabold">
                Finalité de l'export (obligatoire)
                <Textarea
                  value={finalite}
                  onChange={(e) => setFinalite(e.target.value)}
                  maxLength={500}
                  rows={3}
                  placeholder="Exemple : bilan trimestriel des inscriptions pour le ministère"
                  className="font-medium"
                />
              </label>
              <p className="flex items-start gap-2 rounded-2xl bg-sun/20 p-3 text-xs font-semibold text-ink">
                <ShieldAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
                Données de mineurs : n'exporte que les colonnes indispensables à cette finalité.
              </p>
            </>
          ) : (
            <p className="rounded-2xl bg-mist-soft p-4 text-sm font-medium text-ink/80">
              Aucune donnée nominative : seulement des nombres de comptes, par profil, statut et
              mois d'inscription.
            </p>
          )}
          {erreur && (
            <Alert variant="destructive">
              <AlertDescription>{erreur}</AlertDescription>
            </Alert>
          )}
          <Button
            onClick={verifier}
            disabled={enCours}
            className="btn-fx h-12 w-full rounded-full text-base font-bold"
          >
            {enCours && <Loader2 className="size-4 animate-spin" />}
            <FileSpreadsheet className="size-5" /> Préparer l'export
          </Button>
        </div>
      </section>

      <Dialog open={volume !== null} onOpenChange={(o) => !o && setVolume(null)}>
        <DialogContent className="rounded-3xl">
          <DialogHeader>
            <DialogTitle className="text-2xl text-logo-blue">Confirmer l'export</DialogTitle>
            <DialogDescription>
              {volume === 0
                ? "Aucun inscrit ne correspond à ces filtres : il n'y a rien à exporter."
                : `${volume} compte${(volume ?? 0) > 1 ? "s" : ""} correspond${(volume ?? 0) > 1 ? "ent" : ""} à ces filtres. L'opération sera inscrite au journal.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" className="rounded-full" onClick={() => setVolume(null)}>
              Annuler
            </Button>
            {volume !== 0 && (
              <Button onClick={confirmer} disabled={enCours} className="rounded-full font-bold">
                {enCours && <Loader2 className="size-4 animate-spin" />}
                Exporter et télécharger
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <section>
        <h2 className="text-xl text-logo-blue">Historique des exports</h2>
        <div className="mt-3 overflow-x-auto rounded-3xl bg-white shadow-sm ring-1 ring-border">
          <table className="w-full min-w-[44rem] text-sm">
            <thead className="bg-mist-soft text-left text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
              <tr>
                <th scope="col" className="px-4 py-3">
                  Date (UTC)
                </th>
                <th scope="col" className="px-4 py-3">
                  Par
                </th>
                <th scope="col" className="px-4 py-3">
                  Type
                </th>
                <th scope="col" className="px-4 py-3">
                  Lignes
                </th>
                <th scope="col" className="px-4 py-3">
                  Finalité
                </th>
                <th scope="col" className="px-4 py-3">
                  État
                </th>
              </tr>
            </thead>
            <tbody>
              {historique.map((e) => (
                <tr key={e.id} className="border-t align-top">
                  <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                    {dateHeure(e.cree_le)}
                  </td>
                  <td className="px-4 py-3 font-semibold">{e.demandeur_libelle ?? "—"}</td>
                  <td className="px-4 py-3">
                    {e.type === "nominatif" ? "Nominatif" : "Agrégé"} · {e.format.toUpperCase()}
                    {e.colonnes.length > 0 && (
                      <span className="block text-xs text-muted-foreground">
                        {e.colonnes.join(", ")}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-display">{e.nb_lignes}</td>
                  <td className="max-w-56 px-4 py-3 text-xs text-muted-foreground">
                    {e.finalite ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-xs font-bold">{STATUTS_EXPORT[e.statut]}</td>
                </tr>
              ))}
              {historique.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center font-semibold text-muted-foreground"
                  >
                    Aucun export pour l'instant.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
