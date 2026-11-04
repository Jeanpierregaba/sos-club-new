import { STATUTS_COLLABORATEUR } from "@/lib/admin";

export function BadgeStatut({ statut }: { statut: keyof typeof STATUTS_COLLABORATEUR }) {
  const { libelle, classe } = STATUTS_COLLABORATEUR[statut];
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-extrabold ${classe}`}
    >
      {libelle}
    </span>
  );
}
