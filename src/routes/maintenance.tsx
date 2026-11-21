import { createFileRoute } from "@tanstack/react-router";

import { PageMaintenance } from "@/components/PageMaintenance";

// La page reste accessible pendant la maintenance : c'est elle que le garde de la racine affiche.
export const Route = createFileRoute("/maintenance")({
  head: () => ({
    meta: [
      { title: "Maintenance — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: PageMaintenance,
});
