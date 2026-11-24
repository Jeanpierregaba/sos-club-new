import { createFileRoute } from "@tanstack/react-router";

import { MotDePasseOublie } from "@/components/comptes/MotDePasseOublie";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/mot-de-passe-oublie")({
  head: () => ({
    meta: [{ title: m.mdp_oublie_meta() }, { name: "robots", content: "noindex" }],
  }),
  component: MotDePasseOublie,
});
