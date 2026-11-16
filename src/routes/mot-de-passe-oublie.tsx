import { createFileRoute } from "@tanstack/react-router";

import { MotDePasseOublie } from "@/components/comptes/MotDePasseOublie";

export const Route = createFileRoute("/mot-de-passe-oublie")({
  head: () => ({
    meta: [
      { title: "Mot de passe oublié — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: MotDePasseOublie,
});
