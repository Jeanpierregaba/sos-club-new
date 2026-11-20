import { Link } from "@tanstack/react-router";
import { Award, Lock, Medal } from "lucide-react";
import { useEffect, useState } from "react";

import { Choix, ListeClassement, Pagination } from "@/components/classements/TableauClassement";
import { PartagerClassement } from "@/components/espace/PartagerClassement";
import { Button } from "@/components/ui/button";
import {
  chargerClassementMonClub,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type ClassementClubInterne,
  type ClassementPersonnel,
  type PeriodeClassement,
  type RangPersonnel,
} from "@/lib/api/client";
import { formaterPoints, PERIODES, rangOuNonClasse } from "@/lib/classements";

// Les rangs d'un élève ou d'un encadreur (spec 036) : son club, sa DRE et le pays, pour le semestre en cours et
// depuis le début. L'API calcule les rangs ; le site les affiche.
export function RangsPersonnels({ classement }: { classement: ClassementPersonnel }) {
  return (
    <section
      aria-labelledby="titre-mes-rangs"
      className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
    >
      <p className="text-xs font-extrabold uppercase tracking-widest text-logo-red">
        Classements du réseau
      </p>
      <h2 id="titre-mes-rangs" className="mt-1 flex items-center gap-2 text-2xl">
        <Medal aria-hidden className="size-6 text-primary" />
        <span className="text-logo-blue">Mes</span> <span className="text-primary">rangs</span>
      </h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {classement.semestre_en_cours ? (
          <Rangs
            titre={`Semestre en cours · ${classement.semestre_en_cours.libelle}`}
            rangs={classement.semestre}
            club={classement.club !== null}
          />
        ) : (
          <div className="rounded-2xl bg-mist-soft p-4">
            <p className="text-sm font-extrabold text-logo-blue">Semestre en cours</p>
            <p className="mt-3 font-bold text-ink">Aucun semestre en cours</p>
          </div>
        )}
        <Rangs
          titre="Total historique"
          rangs={classement.historique}
          club={classement.club !== null}
        />
      </div>
      {classement.distinctions.length > 0 && (
        <div className="mt-5 rounded-2xl bg-sun/25 p-4 ring-1 ring-sun">
          <p className="flex items-center gap-2 text-sm font-extrabold text-logo-blue">
            <Award aria-hidden className="size-5 text-primary" /> Mes distinctions
          </p>
          <ul className="mt-2 space-y-1">
            {classement.distinctions.map((d) => (
              <li key={`${d.semestre}-${d.place}`} className="font-bold text-ink">
                {d.distinction} du semestre {d.semestre}
                <span className="ml-2 text-sm font-semibold text-muted-foreground">
                  {formaterPoints(d.points)} points
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-4">
        {(classement.semestre.classe || classement.historique.classe) && (
          <PartagerClassement encadreur={classement.categorie === "encadreurs"} />
        )}
        <Link
          to="/hall-of-fame"
          className="inline-flex text-sm font-bold text-primary underline-offset-4 hover:underline"
        >
          Voir les classements complets
        </Link>
      </div>
    </section>
  );
}

function Rangs({ titre, rangs, club }: { titre: string; rangs: RangPersonnel; club: boolean }) {
  return (
    <div className="rounded-2xl bg-mist-soft p-4">
      <p className="text-sm font-extrabold text-logo-blue">{titre}</p>
      <p className="mt-1 text-sm font-semibold text-muted-foreground">
        {formaterPoints(rangs.points)} points
      </p>
      {rangs.classe ? (
        <dl className="mt-3 grid grid-cols-3 gap-2 text-center">
          <Case titre="Club" valeur={club ? rangOuNonClasse(rangs.rang_club) : "Sans club"} />
          <Case titre="DRE" valeur={rangOuNonClasse(rangs.rang_dre)} />
          <Case titre="National" valeur={rangOuNonClasse(rangs.rang_national)} />
        </dl>
      ) : (
        <p className="mt-3 font-bold text-ink">Pas encore classé</p>
      )}
    </div>
  );
}

function Case({ titre, valeur }: { titre: string; valeur: string }) {
  return (
    <div className="flex flex-col-reverse rounded-xl bg-white p-2">
      <dt className="text-xs font-bold text-muted-foreground">{titre}</dt>
      <dd className="font-display text-lg leading-tight text-ink">{valeur}</dd>
    </div>
  );
}

const PAR_PAGE = 50;

type Categorie = "eleves" | "encadreurs";
const CATEGORIES_CLUB: { valeur: Categorie; libelle: string }[] = [
  { valeur: "eleves", libelle: "Élèves" },
  { valeur: "encadreurs", libelle: "Encadreurs" },
];

// Le classement interne du club (spec 036) : privé, visible de ses membres, de ses encadreurs et de son président.
// Il se charge dans le navigateur, filtre par filtre ; l'API vérifie l'appartenance au club à chaque requête.
export function ClassementDuClub() {
  const [categorie, setCategorie] = useState<Categorie>("eleves");
  const [periode, setPeriode] = useState<PeriodeClassement>("semestre");
  const [page, setPage] = useState(1);
  const [essai, setEssai] = useState(0);
  const [etat, setEtat] = useState<
    | { type: "chargement" }
    | { type: "pret"; classement: ClassementClubInterne }
    | { type: "hors-club" }
    | { type: "erreur"; message: string }
  >({ type: "chargement" });

  useEffect(() => {
    let actif = true;
    setEtat({ type: "chargement" });
    chargerClassementMonClub({ categorie, periode, page, par_page: PAR_PAGE })
      .then((classement) => actif && setEtat({ type: "pret", classement }))
      .catch((erreur: unknown) => {
        if (!actif) return;
        if (erreur instanceof ErreurApi && (erreur.statut === 404 || erreur.statut === 403))
          setEtat({ type: "hors-club" });
        else
          setEtat({
            type: "erreur",
            message: erreur instanceof ErreurApi ? erreur.message : MESSAGE_INDISPONIBLE,
          });
      });
    return () => {
      actif = false;
    };
  }, [categorie, periode, page, essai]);

  if (etat.type === "hors-club") return null;

  return (
    <section
      aria-labelledby="titre-classement-club"
      className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
    >
      <p className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-widest text-logo-red">
        <Lock aria-hidden className="size-3.5" /> Visible des seuls membres du club
      </p>
      <h2 id="titre-classement-club" className="mt-1 text-2xl">
        <span className="text-logo-blue">Classement de</span>{" "}
        <span className="text-primary">mon club</span>
      </h2>
      {etat.type === "pret" && (
        <p className="mt-1 text-sm font-semibold text-muted-foreground">
          {etat.classement.club.nom}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-3">
        <Choix
          libelle="Membres classés"
          options={CATEGORIES_CLUB}
          valeur={categorie}
          choisir={(valeur) => {
            setCategorie(valeur);
            setPage(1);
          }}
        />
        <Choix
          libelle="Période"
          options={PERIODES}
          valeur={periode}
          choisir={(valeur) => {
            setPeriode(valeur);
            setPage(1);
          }}
        />
      </div>
      <div className="mt-4">
        {etat.type === "chargement" && (
          <p className="font-semibold text-muted-foreground">Chargement du classement…</p>
        )}
        {etat.type === "erreur" && (
          <div className="flex flex-wrap items-center gap-3">
            <p className="font-semibold text-logo-red">{etat.message}</p>
            <Button
              variant="outline"
              className="rounded-full font-bold"
              onClick={() => setEssai((n) => n + 1)}
            >
              Réessayer
            </Button>
          </div>
        )}
        {etat.type === "pret" &&
          (periode === "semestre" && !etat.classement.semestre ? (
            <p className="font-semibold text-muted-foreground">Aucun semestre en cours.</p>
          ) : etat.classement.lignes.length === 0 ? (
            <p className="font-semibold text-muted-foreground">
              Personne n'a encore de points sur cette période.
            </p>
          ) : (
            <>
              <ListeClassement
                libelle="Classement interne du club"
                lignes={etat.classement.lignes.map((ligne, index) => ({
                  cle: String(index),
                  rang: ligne.rang,
                  nom: ligne.nom,
                  sousTitre: "",
                  points: ligne.points,
                  estMoi: ligne.est_moi,
                }))}
              />
              <Pagination
                page={page}
                total={etat.classement.total}
                parPage={PAR_PAGE}
                allerA={setPage}
              />
            </>
          ))}
      </div>
    </section>
  );
}
