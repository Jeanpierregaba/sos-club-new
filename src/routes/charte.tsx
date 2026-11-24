import { createFileRoute } from "@tanstack/react-router";
import { EyeOff, HeartHandshake, MessageSquareWarning, ShieldCheck, UserRound } from "lucide-react";

import { EnTete } from "@/components/EnTete";
import { FilAriane } from "@/components/FilAriane";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { LANGUE_DE_BASE, langueCourante } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/charte")({
  head: () => ({
    meta: [
      { title: m.charte_meta_titre() },
      { name: "description", content: m.charte_meta_description() },
    ],
  }),
  component: Charte,
});

// Texte provisoire (spec 017), tiré de docs/RULES.md : à valider par le porteur du projet et par un juriste.
// Le changer impose de changer aussi `version_charte` dans la configuration de l'API. Spec 052 : la version française
// fait foi, l'anglais et l'allemand le disent.
const regles = () => [
  {
    i: HeartHandshake,
    t: m.charte_1_titre(),
    d: m.charte_1_texte(),
  },
  {
    i: UserRound,
    t: m.charte_2_titre(),
    d: m.charte_2_texte(),
  },
  {
    i: EyeOff,
    t: m.charte_3_titre(),
    d: m.charte_3_texte(),
  },
  {
    i: ShieldCheck,
    t: m.charte_4_titre(),
    d: m.charte_4_texte(),
  },
  {
    i: MessageSquareWarning,
    t: m.charte_5_titre(),
    d: m.charte_5_texte(),
  },
];

function Charte() {
  return (
    <>
      <SiteHeader />
      <main className="bg-carnet">
        <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 md:py-16">
          <FilAriane rubrique={m.charte_rubrique()} page={m.charte_page()} />
          <div className="mt-6">
            <EnTete sur={m.charte_page()} bleu={m.charte_bleu()} vert={m.charte_vert()}>
              {m.charte_texte()}
            </EnTete>
          </div>
          <p className="mt-6 rounded-2xl bg-sun/20 px-4 py-3 text-sm font-semibold text-ink/80">
            {m.charte_provisoire()}
            {langueCourante() !== LANGUE_DE_BASE && <> {m.charte_reference()}</>}
          </p>
          <ol className="mt-10 grid gap-4">
            {regles().map(({ i: Icone, t, d }, rang) => (
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
