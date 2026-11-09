import { Link } from "@tanstack/react-router";
import { Award, Download, ShieldCheck } from "lucide-react";

import { URL_CERTIFICAT_PDF, type MaCertification } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

// Le certificat du joueur (spec 029) : à télécharger s'il est valide, avec le lien de sa page de vérification.
export function CarteCertificat({
  certificat,
}: {
  certificat: NonNullable<MaCertification["certificat"]>;
}) {
  if (certificat.etat === "revoque") {
    return (
      <section className="rounded-3xl bg-logo-red/10 p-6 ring-1 ring-logo-red/30">
        <h2 className="font-sans text-lg font-extrabold text-logo-red">
          Ton certificat est révoqué
        </h2>
        <p className="mt-1 text-sm text-ink">
          Le certificat n° {certificat.numero} n'est plus valide. Tu as reçu le motif par
          notification ; écris à l'équipe nationale si tu penses qu'il s'agit d'une erreur.
        </p>
      </section>
    );
  }
  return (
    <section className="flex flex-col gap-5 rounded-3xl bg-gradient-to-br from-sun/40 via-white to-primary/10 p-6 shadow-card ring-1 ring-sun sm:flex-row sm:items-center">
      <span className="grid size-16 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground shadow-card">
        <Award aria-hidden className="size-8" />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="font-sans text-xl font-extrabold text-logo-blue">
          Certification Génie Imhotep obtenue !
        </h2>
        <p className="mt-1 text-sm text-ink">
          Certificat n° <span className="font-mono font-bold">{certificat.numero}</span>, délivré le{" "}
          {dateCourte(certificat.delivre_le)}.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <a
          href={URL_CERTIFICAT_PDF}
          download
          className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-sm font-bold text-primary-foreground"
        >
          <Download aria-hidden className="size-4" /> Télécharger mon certificat
        </a>
        <Link
          to="/certificats/$numero"
          params={{ numero: certificat.numero }}
          className="inline-flex h-11 items-center gap-2 rounded-full px-5 text-sm font-bold text-logo-blue ring-1 ring-border hover:bg-mist"
        >
          <ShieldCheck aria-hidden className="size-4" /> Page de vérification
        </Link>
      </div>
    </section>
  );
}
