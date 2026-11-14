import { Link, useNavigate } from "@tanstack/react-router";
import { CalendarClock, Flag, Loader2, Search } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Champ, CHAMP_ADMIN, DialogueFormulaire } from "@/components/admin/DialogueFormulaire";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import {
  adminDeclarerTerrain,
  adminFicheSuivi,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type ClubSuivi,
  type FicheSuivi,
  type PageSuivi,
  type RegionScolaire,
  type Seuils,
  type StatutClub,
} from "@/lib/api/client";
import { REGIONS_SCOLAIRES, STATUTS_CLUB } from "@/lib/clubs";
import { dateCourte } from "@/lib/dates";

const CAUSES: Record<string, string> = {
  affiliation_confirmee: "élève confirmé",
  affiliation_retiree: "élève retiré",
  changement_etablissement: "changement d'établissement",
  encadreur_verifie: "encadreur vérifié",
  compte_suspendu: "compte suspendu",
  compte_reactive: "compte réactivé",
  desistement_confirme: "désistement confirmé",
  echeance: "échéance de 15 jours",
  migration: "reprise des données",
};

type Filtres = { statut?: StatutClub; region?: RegionScolaire; q?: string; page?: number };
type Changement = { [K in keyof Filtres]?: Filtres[K] | undefined };

// Les paramètres d'adresse sans valeur vide : l'adresse reste propre et les types exacts.
function nettoyer(f: Changement): Filtres {
  const resultat: Filtres = {};
  if (f.statut) resultat.statut = f.statut;
  if (f.region) resultat.region = f.region;
  if (f.q) resultat.q = f.q;
  if (f.page && f.page > 1) resultat.page = f.page;
  return resultat;
}

// Le suivi des clubs par l'équipe (spec 033) : statuts calculés par l'API, effectifs, échéances, et la fiche de
// chaque club avec son journal. Les élèves n'y apparaissent que par leur pseudonyme.
export function SuiviClubs({
  page,
  seuils,
  filtres,
  decideur,
}: {
  page: PageSuivi;
  seuils: Seuils;
  filtres: Filtres;
  decideur: boolean;
}) {
  const naviguer = useNavigate({ from: "/admin/clubs" });
  const [recherche, setRecherche] = useState(filtres.q ?? "");
  const [ouvert, setOuvert] = useState<ClubSuivi | null>(null);
  const pages = Math.max(1, Math.ceil(page.total / page.par_page));

  const filtrer = (changement: Changement) =>
    void naviguer({ search: nettoyer({ ...filtres, ...changement, page: undefined }) });

  const chercher = (e: FormEvent) => {
    e.preventDefault();
    filtrer({ q: recherche.trim() || undefined });
  };

  return (
    <div className="space-y-4">
      <p className="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-ink ring-1 ring-border">
        Seuils fixés par le cahier des charges : {seuils.encadreurs} encadreurs et {seuils.eleves}{" "}
        élèves confirmés pour être actif, {seuils.delai_jours} jours pour régulariser.
      </p>

      <div className="flex flex-wrap items-end gap-3 rounded-2xl bg-white p-4 shadow-card ring-1 ring-border">
        <label className="grid gap-1 text-sm font-bold text-ink">
          Statut
          <select
            value={filtres.statut ?? ""}
            onChange={(e) => filtrer({ statut: (e.target.value || undefined) as StatutClub })}
            className={CHAMP_ADMIN}
          >
            <option value="">Tous</option>
            {(Object.keys(STATUTS_CLUB) as StatutClub[]).map((s) => (
              <option key={s} value={s}>
                {STATUTS_CLUB[s].libelle}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-bold text-ink">
          Région
          <select
            value={filtres.region ?? ""}
            onChange={(e) => filtrer({ region: (e.target.value || undefined) as RegionScolaire })}
            className={CHAMP_ADMIN}
          >
            <option value="">Toutes</option>
            {REGIONS_SCOLAIRES.map((r) => (
              <option key={r.code} value={r.code}>
                {r.nom}
              </option>
            ))}
          </select>
        </label>
        <form onSubmit={chercher} className="flex min-w-[14rem] flex-1 items-end gap-2">
          <label className="grid flex-1 gap-1 text-sm font-bold text-ink">
            Établissement
            <input
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              placeholder="Nom de l'établissement"
              className={CHAMP_ADMIN}
              maxLength={100}
            />
          </label>
          <Button type="submit" variant="outline" className="h-11 rounded-full font-bold">
            <Search className="size-4" /> Chercher
          </Button>
        </form>
      </div>

      {page.clubs.length === 0 ? (
        <p className="rounded-3xl bg-white p-6 font-medium text-muted-foreground ring-1 ring-border">
          Aucun club ne correspond à ces filtres.
        </p>
      ) : (
        <ul className="divide-y rounded-3xl bg-white shadow-card ring-1 ring-border">
          {page.clubs.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => setOuvert(c)}
                className="flex w-full flex-wrap items-center gap-3 px-5 py-4 text-left hover:bg-mist-soft"
              >
                <span className="min-w-0 flex-1">
                  <span className="block font-bold text-ink">{c.etablissement}</span>
                  <span className="block text-sm font-medium text-muted-foreground">
                    {c.region} · {c.dre} · {c.iesg}
                  </span>
                </span>
                <span className="text-sm font-bold text-ink/80">
                  {c.nb_encadreurs}/{seuils.encadreurs} enc. · {c.nb_eleves}/{seuils.eleves} élèves
                  {c.a_confirmer > 0 && ` · ${c.a_confirmer} à confirmer`}
                </span>
                {c.declare_terrain && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-mist px-2.5 py-0.5 text-xs font-extrabold text-ink">
                    <Flag aria-hidden className="size-3" /> Terrain
                  </span>
                )}
                <span
                  className={`rounded-full px-3 py-1 text-xs font-extrabold ${STATUTS_CLUB[c.statut].classe}`}
                >
                  {STATUTS_CLUB[c.statut].libelle}
                  {c.regularisation_jusquau && ` · ${dateCourte(c.regularisation_jusquau)}`}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {pages > 1 && (
        <nav
          aria-label="Pages"
          className="flex items-center justify-center gap-3 text-sm font-bold"
        >
          {page.page > 1 && (
            <Link to="/admin/clubs" search={nettoyer({ ...filtres, page: page.page - 1 })}>
              ← Précédente
            </Link>
          )}
          <span>
            Page {page.page} sur {pages}
          </span>
          {page.page < pages && (
            <Link to="/admin/clubs" search={nettoyer({ ...filtres, page: page.page + 1 })}>
              Suivante →
            </Link>
          )}
        </nav>
      )}

      <FicheClub club={ouvert} decideur={decideur} onFermer={() => setOuvert(null)} />
    </div>
  );
}

function FicheClub({
  club,
  decideur,
  onFermer,
}: {
  club: ClubSuivi | null;
  decideur: boolean;
  onFermer: () => void;
}) {
  const [fiche, setFiche] = useState<FicheSuivi | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [terrain, setTerrain] = useState(false);
  const [note, setNote] = useState("");

  useEffect(() => {
    let actif = true;
    setFiche(null);
    setErreur(null);
    if (!club) return;
    adminFicheSuivi(club.id)
      .then((f) => actif && setFiche(f))
      .catch((e: unknown) => {
        if (actif) setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      });
    return () => {
      actif = false;
    };
  }, [club]);

  return (
    <Dialog open={club !== null} onOpenChange={(o) => !o && onFermer()}>
      <DialogContent className="max-h-[92dvh] max-w-3xl overflow-y-auto rounded-[2rem]">
        <DialogTitle className="text-2xl text-logo-blue">{club?.etablissement}</DialogTitle>
        <DialogDescription>
          {club && `${club.region} · ${club.dre} · ${club.iesg}`}
        </DialogDescription>
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        {!fiche && !erreur && <Loader2 className="mx-auto size-6 animate-spin text-logo-blue" />}
        {fiche && (
          <div className="space-y-5 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-3 py-1 font-extrabold ${STATUTS_CLUB[fiche.club.statut].classe}`}
              >
                {STATUTS_CLUB[fiche.club.statut].libelle}
              </span>
              {fiche.club.regularisation_jusquau && (
                <span className="inline-flex items-center gap-1 font-semibold text-ink">
                  <CalendarClock aria-hidden className="size-4" /> échéance le{" "}
                  {dateCourte(fiche.club.regularisation_jusquau)}
                </span>
              )}
              {fiche.club.actif_le && (
                <span className="font-medium text-muted-foreground">
                  Première activation le {dateCourte(fiche.club.actif_le)}
                </span>
              )}
            </div>

            <div className="rounded-2xl bg-mist-soft p-4">
              <p className="font-bold text-ink">
                {fiche.club.declare_terrain
                  ? "Déclaré sur le terrain"
                  : "Pas déclaré sur le terrain"}
                {fiche.declare_le && ` le ${dateCourte(fiche.declare_le)}`}
              </p>
              {fiche.declare_note && <p className="mt-1 text-ink/80">{fiche.declare_note}</p>}
              {decideur && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setNote(fiche.declare_note ?? "");
                    setTerrain(true);
                  }}
                  className="mt-2 rounded-full font-bold"
                >
                  <Flag className="size-4" />{" "}
                  {fiche.club.declare_terrain
                    ? "Retirer la déclaration"
                    : "Déclarer sur le terrain"}
                </Button>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="font-extrabold text-ink">
                  Encadreurs pris en compte ({fiche.encadreurs.length})
                </p>
                <ul className="mt-1 space-y-0.5 font-medium text-ink/80">
                  {fiche.encadreurs.map((e) => (
                    <li key={e.utilisateur_id}>
                      {e.prenom} {e.nom}
                    </li>
                  ))}
                </ul>
                {fiche.president_pseudonyme && (
                  <p className="mt-2 font-semibold text-ink">
                    Président : {fiche.president_pseudonyme}
                  </p>
                )}
              </div>
              <div>
                <p className="font-extrabold text-ink">
                  Élèves pris en compte ({fiche.eleves.length})
                </p>
                <p className="mt-1 font-medium text-ink/80">
                  {fiche.eleves.map((e) => e.pseudonyme).join(", ") || "Aucun"}
                </p>
              </div>
            </div>

            {fiche.signalements.length > 0 && (
              <div>
                <p className="font-extrabold text-ink">Désistements signalés</p>
                <ul className="mt-1 space-y-1 font-medium text-ink/80">
                  {fiche.signalements.map((s) => (
                    <li key={s.id}>
                      {dateCourte(s.signale_le)} · {s.encadreur_prenom} {s.encadreur_nom} ·{" "}
                      {s.etat === "en_attente"
                        ? "en attente"
                        : s.etat === "confirme"
                          ? "confirmé"
                          : "rejeté"}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <p className="font-extrabold text-ink">Journal des statuts</p>
              <ul className="mt-1 space-y-1 font-medium text-ink/80">
                {fiche.journal.map((l, i) => (
                  <li key={i}>
                    {dateCourte(l.cree_le)} · {l.ancien ? `${libelle(l.ancien)} → ` : ""}
                    <strong>{libelle(l.nouveau)}</strong> · {CAUSES[l.cause] ?? l.cause} ·{" "}
                    {l.nb_encadreurs} enc., {l.nb_eleves} élèves
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
        {fiche && (
          <DialogueFormulaire
            ouvert={terrain}
            onOuvert={setTerrain}
            titre={
              fiche.club.declare_terrain
                ? "Retirer la déclaration sur le terrain ?"
                : "Déclarer ce club sur le terrain ?"
            }
            description="Cette information compte le club parmi les Clubs Santé de la carte. Elle ne change ni son statut ni ses droits."
            bouton="Enregistrer"
            onEnvoie={async () => {
              const nouvelle = await adminDeclarerTerrain(
                fiche.club.id,
                !fiche.club.declare_terrain,
                note,
                fiche.version,
              );
              setFiche(nouvelle);
            }}
          >
            {!fiche.club.declare_terrain && (
              <Champ libelle="Note (facultative)">
                <input
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  maxLength={300}
                  className={CHAMP_ADMIN}
                  placeholder="Ex. : visite de la DRE du 4 novembre"
                />
              </Champ>
            )}
          </DialogueFormulaire>
        )}
      </DialogContent>
    </Dialog>
  );
}

function libelle(statut: string): string {
  return STATUTS_CLUB[statut as StatutClub]?.libelle ?? statut;
}
