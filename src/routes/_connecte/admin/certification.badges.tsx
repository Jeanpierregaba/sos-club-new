import { createFileRoute, useRouter } from "@tanstack/react-router";
import { Save } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { peut } from "@/lib/admin";
import {
  changerReglesBadges,
  chargerBadgesDelivres,
  chargerReglesBadges,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/admin/certification/badges")({
  gcTime: 0,
  loader: async () => {
    const [regles, delivres] = await Promise.all([chargerReglesBadges(), chargerBadgesDelivres()]);
    return { regles, delivres };
  },
  errorComponent: ServiceIndisponible,
  component: Badges,
});

function Badges() {
  const { regles, delivres } = Route.useLoaderData();
  const { admin } = Route.useRouteContext();
  const router = useRouter();
  // Les règles de tous les joueurs : réservé à qui publie (l'API exige aussi la double authentification).
  const modifiable = peut(admin, "quiz", "approuver");
  const [noms, setNoms] = useState(regles.en_cours.noms);
  const [paliers, setPaliers] = useState(regles.en_cours.paliers.map(String));
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  async function enregistrer() {
    setErreur(null);
    setInfo(null);
    setEnCours(true);
    try {
      const v = await changerReglesBadges({ noms, paliers: paliers.map(Number) });
      setInfo(`Version ${v.version} en vigueur pour les badges à venir.`);
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form
        className="grid gap-4 rounded-3xl bg-white p-5 shadow-card sm:p-7"
        onSubmit={(e) => {
          e.preventDefault();
          void enregistrer();
        }}
      >
        <h2 className="font-display text-xl text-ink">
          Règles des badges, version {regles.en_cours.version}
        </h2>
        <p className="text-sm text-muted-foreground">
          Chaque badge se délivre à la fin de sa thématique : après 4, 8, 12, 16 et 20 quiz réussis
          (spec 034). Seuls les noms se règlent. Un badge déjà obtenu garde son nom et son palier.
        </p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted-foreground">
              <th className="pb-2 font-semibold">Badge</th>
              <th className="pb-2 font-semibold">Après (quiz réussis)</th>
            </tr>
          </thead>
          <tbody>
            {noms.map((nom, i) => (
              <tr key={i}>
                <td className="py-1 pr-2">
                  <input
                    aria-label={`Nom du badge ${i + 1}`}
                    className={CHAMP_ADMIN}
                    value={nom}
                    maxLength={40}
                    disabled={!modifiable}
                    onChange={(e) =>
                      setNoms((n) => n.map((x, j) => (j === i ? e.target.value : x)))
                    }
                  />
                </td>
                <td className="w-28 py-1">
                  <input
                    aria-label={`Palier du badge ${i + 1}`}
                    className={CHAMP_ADMIN}
                    inputMode="numeric"
                    value={paliers[i]}
                    disabled
                    onChange={(e) =>
                      setPaliers((p) => p.map((x, j) => (j === i ? e.target.value : x)))
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        {info && (
          <p role="status" className="text-sm font-semibold text-primary">
            {info}
          </p>
        )}
        {modifiable && (
          <Button type="submit" className="w-fit rounded-full font-bold" disabled={enCours}>
            <Save className="size-4" /> Enregistrer une nouvelle version
          </Button>
        )}
        <details className="text-sm">
          <summary className="cursor-pointer font-semibold">Historique des règles</summary>
          <ul className="mt-2 grid gap-2">
            {regles.versions.map((v) => (
              <li key={v.version} className="rounded-2xl bg-mist/60 p-3">
                <strong>Version {v.version}</strong> · {dateCourte(v.cree_le)} —{" "}
                {v.noms.map((n, i) => `${n} ${v.paliers[i]}`).join(", ")}
              </li>
            ))}
          </ul>
        </details>
      </form>

      <section className="rounded-3xl bg-white p-5 shadow-card sm:p-7">
        <h2 className="font-display text-xl text-ink">Derniers badges délivrés</h2>
        {delivres.badges.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">Aucun badge délivré pour l'instant.</p>
        ) : (
          <ul className="mt-3 grid gap-2 text-sm">
            {delivres.badges.map((b, i) => (
              <li
                key={i}
                className="flex flex-wrap justify-between gap-2 rounded-2xl bg-mist/60 p-3"
              >
                <span>
                  <strong>{b.nom}</strong> · {b.titulaire} (
                  {b.role === "eleve" ? "élève" : "encadreur"})
                </span>
                <span className="text-muted-foreground">{dateCourte(b.obtenu_le)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
