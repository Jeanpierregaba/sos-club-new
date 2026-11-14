import { Award, Gamepad2, MessageSquareText, Trophy, Users } from "lucide-react";

import type { PointsDuClub, TableauGamification } from "@/lib/api/client";
import { REGIONS_SCOLAIRES } from "@/lib/clubs";

const nombre = (n: number) => n.toLocaleString("fr-FR");
const rang = (n: number) => (n === 1 ? "1er" : `${n}e`);
const region = (code: string | null) =>
  code ? (REGIONS_SCOLAIRES.find((r) => r.code === code)?.nom ?? code) : "";

// Le tableau de bord de l'élève (spec 034, lot 4) : la vue de l'année en cours, puis un décompte par parcours
// (certification, jeux, vie du site), et les archives des années passées.
export function TableauAnnuel({ tableau }: { tableau: TableauGamification }) {
  const { certification: c, jeux: j, vie: v } = tableau;
  return (
    <section
      aria-labelledby="titre-annee"
      className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
    >
      <p className="text-xs font-extrabold uppercase tracking-widest text-logo-red">
        {tableau.annee ? `Année ${tableau.annee.libelle}` : "Hors année scolaire"}
      </p>
      <h2 id="titre-annee" className="mt-1 text-2xl">
        <span className="text-logo-blue">Mon année</span>{" "}
        <span className="text-primary">en points</span>
      </h2>
      {tableau.ancien_eleve && (
        <p className="mt-3 rounded-2xl bg-mist-soft p-3 text-sm font-semibold">
          Tu es ancien élève : tes archives restent consultables, sans nouvelle récompense.
        </p>
      )}
      <dl className="mt-5 grid gap-3 sm:grid-cols-4">
        <Chiffre titre="Total de l'année" valeur={nombre(tableau.total_annuel)} />
        <Chiffre titre="Apporté à ton club" valeur={nombre(tableau.apport_club)} />
        <Chiffre
          titre={tableau.region ? `Rang · ${region(tableau.region)}` : "Rang régional"}
          valeur={tableau.rang_regional ? rang(tableau.rang_regional) : "pas encore classé"}
        />
        <Chiffre
          titre="Place dans ton club"
          valeur={tableau.place_club ? rang(tableau.place_club) : "pas encore classé"}
        />
      </dl>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Parcours
          icone={Award}
          titre="Certification"
          points={tableau.parcours["certification"] ?? 0}
        >
          <li>{c.quiz_valides} / 20 quiz validés</li>
          <li>{c.badges} / 5 badges</li>
          <li>{c.certificat ? "Certificat obtenu" : "Certificat à obtenir"}</li>
          <li>
            Cette année : quiz {nombre(c.points_quiz)} · badges {nombre(c.points_badges)} ·
            certificat {nombre(c.points_certificat)}
          </li>
        </Parcours>
        <Parcours icone={Gamepad2} titre="Jeux" points={tableau.parcours["jeux"] ?? 0}>
          <li>{j.quiz_reussis} / 100 quiz réussis</li>
          <li>{j.niveaux.filter((n) => n.etoile).length} / 4 étoiles</li>
          <li>
            Cette année : quiz {nombre(j.points_quiz)} · étoiles {nombre(j.points_etoiles)}
          </li>
          <li>{j.gold ? "Carte Gold" : "Carte membre"}</li>
        </Parcours>
        <Parcours
          icone={MessageSquareText}
          titre="Vie du site"
          points={tableau.parcours["vie"] ?? 0}
        >
          <li>{v.approuvees} contribution(s) publiée(s) depuis ton inscription</li>
          <li>{v.en_attente} en attente de modération</li>
        </Parcours>
      </div>

      <p className="mt-4 text-xs font-semibold text-muted-foreground">
        Depuis ton inscription : {nombre(tableau.total_historique)} points.
      </p>

      {tableau.archives.length > 0 && (
        <div className="mt-6">
          <h3 className="font-sans text-base font-extrabold text-ink">Mes années passées</h3>
          <ul className="mt-2 divide-y rounded-2xl ring-1 ring-border">
            {tableau.archives.map((a) => (
              <li
                key={a.libelle}
                className="flex flex-wrap justify-between gap-2 px-4 py-3 text-sm"
              >
                <span className="font-bold">{a.libelle}</span>
                <span>
                  {nombre(a.points)} points
                  {a.rang ? ` · ${rang(a.rang)} ${region(a.region)}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function Chiffre({ titre, valeur }: { titre: string; valeur: string }) {
  return (
    <div className="rounded-2xl bg-mist-soft p-4">
      <dt className="text-xs font-bold text-muted-foreground">{titre}</dt>
      <dd className="font-display text-2xl tabular-nums text-logo-blue">{valeur}</dd>
    </div>
  );
}

function Parcours({
  icone: Icone,
  titre,
  points,
  children,
}: {
  icone: typeof Trophy;
  titre: string;
  points: number;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl p-4 ring-1 ring-border">
      <p className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-extrabold">
          <Icone aria-hidden className="size-5 text-primary" /> {titre}
        </span>
        <span className="font-display text-xl tabular-nums">{nombre(points)}</span>
      </p>
      <ul className="mt-3 space-y-1 text-sm font-medium text-ink/80">{children}</ul>
    </div>
  );
}

// Le total annuel du club, par parcours (spec 034) : la moitié des gains de ses élèves affiliés.
export function PointsClub({ points }: { points: PointsDuClub }) {
  return (
    <section
      aria-labelledby="titre-points-club"
      className="mt-6 rounded-3xl bg-white p-6 shadow-card ring-1 ring-border sm:p-8"
    >
      <h2 id="titre-points-club" className="flex items-center gap-2 text-2xl">
        <Users aria-hidden className="size-6 text-primary" />
        <span className="text-logo-blue">Les points</span>{" "}
        <span className="text-primary">du club</span>
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        La moitié de chaque gain de ses élèves affiliés
        {points.annee ? `, année ${points.annee.libelle}` : ""}.
      </p>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Chiffre titre="Total de l'année" valeur={nombre(points.total_annuel)} />
        <Chiffre titre="Certification" valeur={nombre(points.parcours["certification"] ?? 0)} />
        <Chiffre titre="Jeux · quiz" valeur={nombre(points.jeux_quiz)} />
        <Chiffre titre="Jeux · étoiles" valeur={nombre(points.jeux_etoiles)} />
        <Chiffre titre="Vie du site" valeur={nombre(points.parcours["vie"] ?? 0)} />
        <Chiffre titre="Depuis le début" valeur={nombre(points.total_historique)} />
      </dl>
    </section>
  );
}
