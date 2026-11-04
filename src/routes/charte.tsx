import { createFileRoute } from "@tanstack/react-router";
import { EyeOff, HeartHandshake, MessageSquareWarning, ShieldCheck, UserRound } from "lucide-react";

import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/charte")({
  head: () => ({
    meta: [
      { title: "Charte des Clubs Santé — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content: "Les règles que chaque membre des Clubs Santé accepte en créant son compte.",
      },
    ],
  }),
  component: Charte,
});

// Texte provisoire (spec 017), tiré de docs/RULES.md : à valider par le porteur du projet et par un juriste.
// Le changer impose de changer aussi `version_charte` dans la configuration de l'API.
const regles = [
  {
    i: HeartHandshake,
    t: "Je respecte les autres",
    d: "Pas d'insulte, de moquerie, de harcèlement ni de propos discriminant, en ligne comme dans mon club.",
  },
  {
    i: UserRound,
    t: "J'utilise un pseudonyme",
    d: "Mon pseudonyme est mon seul nom public. Il ne contient ni mon nom complet, ni mon numéro, ni mon adresse email. L'équipe nationale peut me demander d'en changer.",
  },
  {
    i: EyeOff,
    t: "Je protège mes informations",
    d: "Je ne publie jamais mes coordonnées ni celles d'un autre élève. Mon identifiant et mon mot de passe restent secrets.",
  },
  {
    i: ShieldCheck,
    t: "Je publie des contenus fiables",
    d: "Tout ce que je publie est relu par l'équipe nationale avant d'être visible. Je partage des informations de santé vérifiées, sans photo d'une personne qui n'a pas donné son accord.",
  },
  {
    i: MessageSquareWarning,
    t: "Je joue franc-jeu",
    d: "Un seul compte par élève. Les points obtenus par la triche (comptes multiples, réponses copiées) sont retirés, et le compte peut être suspendu.",
  },
];

function Charte() {
  return (
    <>
      <SiteHeader />
      <main className="bg-carnet">
        <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 md:py-16">
          <FilAriane rubrique="Compte élève" page="Charte" />
          <div className="mt-6">
            <EnTete sur="Charte" bleu="Les règles des" vert="Clubs Santé">
              En créant ton compte, tu acceptes ces règles. Elles protègent chaque membre de la
              communauté.
            </EnTete>
          </div>
          <p className="mt-6 rounded-2xl bg-sun/20 px-4 py-3 text-sm font-semibold text-ink/80">
            Version provisoire, en cours de validation par l'équipe du programme.
          </p>
          <ol className="mt-10 grid gap-4">
            {regles.map(({ i: Icone, t, d }, rang) => (
              <li
                key={t}
                className="flex gap-4 rounded-3xl bg-white p-5 shadow-card ring-1 ring-border sm:p-6"
              >
                <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Icone aria-hidden className="size-6" />
                </span>
                <div>
                  <h2 className="text-xl text-logo-blue">
                    {rang + 1}. {t}
                  </h2>
                  <p className="mt-1 font-medium text-muted-foreground">{d}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
