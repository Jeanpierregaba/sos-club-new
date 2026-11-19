import type { ReseauPartage } from "@/lib/api/client";
import { nomDuReseau } from "@/lib/partages";

// L'aperçu d'un partage déclaré (spec 044) : le réseau et le lien, ouvert par le modérateur dans un nouvel onglet,
// sans transmettre l'adresse de l'admin. L'API ne visite jamais ce lien.
export function ApercuPartage({ champs }: { champs: Record<string, string> }) {
  const lien = champs["lien"] ?? "";
  return (
    <div className="space-y-3 rounded-2xl bg-carnet p-5 text-ink">
      <p>
        <strong>
          {champs["nature"] === "partage"
            ? "Partage de son propre article"
            : "Republication d'un article du site"}
        </strong>{" "}
        sur {nomDuReseau((champs["reseau"] ?? "facebook") as ReseauPartage)}
      </p>
      {lien.startsWith("https://") ? (
        <a
          href={lien}
          target="_blank"
          rel="noopener noreferrer nofollow"
          className="block break-all font-bold text-logo-blue underline-offset-4 hover:underline"
        >
          {lien}
        </a>
      ) : (
        <p className="break-all">{lien}</p>
      )}
      <p className="text-sm text-muted-foreground">
        Ouvre la publication et vérifie qu'elle existe, qu'elle est visible et qu'elle relaie bien
        cet article. Sinon, refuse avec un motif : la personne pourra déclarer un autre lien.
      </p>
    </div>
  );
}
