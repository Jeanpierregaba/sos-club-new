import { createFileRoute } from "@tanstack/react-router";

import { FormulaireParametres } from "@/components/quiz/FormulaireParametres";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerParametresQuiz } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/certification/parametres")({
  gcTime: 0,
  loader: () => chargerParametresQuiz("certification"),
  errorComponent: ServiceIndisponible,
  component: Parametres,
});

function Parametres() {
  const { admin } = Route.useRouteContext();
  return (
    <FormulaireParametres
      historique={Route.useLoaderData()}
      parcours="certification"
      admin={admin}
    />
  );
}
