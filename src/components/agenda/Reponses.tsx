import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ErreurApi, pointerPresences } from "@/lib/api/client";
import type { ReponsesEvenement } from "@/lib/api/client";
import { REPONSES } from "@/lib/agenda";

// Les réponses des membres et, après le début de l'événement, le pointage des présents. Réservé aux encadreurs du
// club et à son président : ces noms ne sont jamais publics.
export function Reponses({
  evenementId,
  initiales,
}: {
  evenementId: string;
  initiales: ReponsesEvenement;
}) {
  const [reponses, setReponses] = useState(initiales);
  const [presences, setPresences] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(initiales.membres.map((m) => [m.eleve_id, m.present === true])),
  );
  const [message, setMessage] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  async function enregistrer() {
    setEnCours(true);
    setMessage(null);
    try {
      const vue = await pointerPresences(evenementId, presences);
      setReponses(vue);
      setMessage("Présences enregistrées.");
    } catch (e) {
      setMessage(
        e instanceof ErreurApi ? e.message : "Les présences n'ont pas pu être enregistrées.",
      );
    } finally {
      setEnCours(false);
    }
  }

  return (
    <section className="mt-8 rounded-[1.75rem] bg-white p-5 shadow-card md:p-7">
      <h2 className="text-2xl text-logo-blue">Réponses des membres</h2>
      <p className="mt-2 text-sm font-semibold text-muted-foreground">
        {reponses.participe} participe{reponses.participe > 1 ? "nt" : ""} · {reponses.peut_etre}{" "}
        peut-être · {reponses.non} non · {reponses.sans_reponse} sans réponse
        {reponses.pointage_ouvert || reponses.presents > 0
          ? ` · ${reponses.presents} présent(s)`
          : ""}
      </p>
      {reponses.membres.length === 0 ? (
        <p className="mt-4 font-medium text-muted-foreground">
          Le club n'a pas encore de membre confirmé.
        </p>
      ) : (
        <ul className="mt-4 divide-y">
          {reponses.membres.map((m) => (
            <li key={m.eleve_id} className="flex flex-wrap items-center gap-3 py-3">
              <span className="min-w-0 flex-1">
                <span className="block font-bold">{m.nom}</span>
                <span className="block text-sm font-medium text-muted-foreground">
                  {m.pseudonyme}
                </span>
              </span>
              <span className="text-sm font-semibold">
                {m.reponse ? REPONSES[m.reponse] : "Pas de réponse"}
              </span>
              {reponses.pointage_ouvert && (
                <label className="flex items-center gap-2 text-sm font-bold">
                  <input
                    type="checkbox"
                    className="size-5"
                    checked={presences[m.eleve_id] ?? false}
                    onChange={(e) =>
                      setPresences((avant) => ({ ...avant, [m.eleve_id]: e.target.checked }))
                    }
                  />
                  Présent
                </label>
              )}
            </li>
          ))}
        </ul>
      )}
      {reponses.pointage_ouvert && reponses.membres.length > 0 && (
        <Button
          className="mt-4 h-11 rounded-full px-6 font-bold"
          disabled={enCours}
          onClick={() => void enregistrer()}
        >
          Enregistrer les présences
        </Button>
      )}
      {message && (
        <p role="status" className="mt-3 text-sm font-semibold">
          {message}
        </p>
      )}
    </section>
  );
}
