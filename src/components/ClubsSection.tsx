import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { dres, grandLome } from "@/lib/togo-dre";

const totalClubs = dres.reduce((n, r) => n + r.clubs, 0);
const teinte = (couleur: string) => `color-mix(in oklch, ${couleur} 12%, white)`;
// Assombrie pour que le texte blanc reste lisible, y compris sur les régions orange.
const fond = (couleur: string) =>
  `linear-gradient(135deg, color-mix(in oklch, ${couleur} 92%, black), color-mix(in oklch, ${couleur} 72%, black))`;

export function ClubsSection() {
  const [dre, setDre] = useState(grandLome);
  const c = dre.couleur;
  const stats = [
    { n: dre.clubs, t: "Total clubs" },
    { n: dre.nbIesg, t: "IESG rattachées" },
    {
      n: `${((dre.clubs / totalClubs) * 100).toFixed(1).replace(".", ",")} %`,
      t: "des clubs du Togo",
    },
  ];

  return (
    <section
      id="clubs"
      className="scroll-mt-16 bg-card bg-linear-to-b from-mist/50 to-primary/5 py-20"
    >
      <div className="mx-auto max-w-7xl px-5">
        <div data-reveal className="mx-auto max-w-3xl text-center">
          <h2 className="text-4xl md:text-5xl">
            <span className="text-logo-blue">Trouve toi aussi</span>{" "}
            <span className="text-primary">ton club santé</span>
          </h2>
          <p className="mt-4 text-muted-foreground">
            Découvre les clubs santé partout au Togo, de ta Direction Régionale de l’Éducation (DRE)
            jusqu’à ton Inspection (IESG). Clique sur ta région sur la carte pour voir ses IESG.
          </p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[2fr_3fr]">
          <div data-reveal="left" className="rounded-3xl border bg-card p-5 shadow-card">
            <div className="flex items-center justify-between gap-2">
              <p className="flex items-center gap-2 font-extrabold uppercase">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: c }} />
                DRE {dre.nom}
              </p>
              <span
                className="whitespace-nowrap rounded-full px-3 py-1 text-xs font-bold text-primary-foreground"
                style={{ backgroundColor: c }}
              >
                {dre.nbIesg} IESG
              </span>
            </div>
            <div className="mt-4 rounded-2xl border p-4">
              <div className="relative mx-auto aspect-[250/640] w-full max-w-[250px]">
                {/* Les régions se cliquent à la souris ; au clavier et au lecteur d'écran, ce sont les étiquettes qui sélectionnent. */}
                <svg
                  viewBox="0 0 250 640"
                  aria-hidden="true"
                  className="absolute inset-0 h-full w-full overflow-visible"
                >
                  {/* La région sélectionnée passe en dernier pour que son contour ne soit pas recouvert par ses voisines. */}
                  {[...dres.filter((r) => r.id !== dre.id), dre].map((r) => (
                    <path
                      key={r.id}
                      d={r.d}
                      fill={r.couleur}
                      onClick={() => setDre(r)}
                      strokeLinejoin="round"
                      className={`cursor-pointer transition-[filter,stroke-width] duration-200 hover:brightness-110 ${r.id === dre.id ? "stroke-ink stroke-2" : "stroke-white stroke-[1.5]"}`}
                    />
                  ))}
                </svg>
                {dres.map((r) => {
                  const on = r.id === dre.id;
                  return (
                    <button
                      key={r.id}
                      type="button"
                      aria-pressed={on}
                      onClick={() => setDre(r)}
                      style={{
                        left: `${r.label.x}%`,
                        top: `${r.label.y}%`,
                        borderColor: r.couleur,
                        backgroundColor: on ? r.couleur : undefined,
                      }}
                      className={`absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[10px] font-extrabold uppercase shadow-sm transition duration-200 hover:scale-110 active:scale-95 ${on ? "z-10 text-primary-foreground" : "bg-white/90 text-ink"}`}
                    >
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: on ? "white" : r.couleur }}
                      />
                      {r.nom}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div
            data-reveal="right"
            className="flex flex-col overflow-hidden rounded-3xl border bg-card shadow-card"
          >
            <div key={dre.id} className="flex flex-1 flex-col animate-in fade-in duration-300">
              <div className="p-6 text-primary-foreground md:p-8" style={{ background: fond(c) }}>
                <span className="rounded-full border border-white/40 bg-white/15 px-3 py-1 text-[11px] font-extrabold uppercase">
                  Zone scolaire officielle
                </span>
                <h3 className="mt-4 text-4xl uppercase md:text-5xl">DRE {dre.nom}</h3>
                <p className="mt-1 font-medium">{dre.complet}</p>
                <div className="mt-6 grid grid-cols-3 gap-2 md:gap-3">
                  {stats.map((s) => (
                    <div
                      key={s.t}
                      className="rounded-2xl border border-white/30 bg-white/15 p-3 text-center backdrop-blur-md"
                    >
                      <p className="whitespace-nowrap font-display text-2xl leading-none md:text-4xl">
                        {s.n}
                      </p>
                      <p className="mt-2 text-[11px] font-bold md:text-xs">{s.t}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex flex-1 flex-col p-6 md:p-8">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-extrabold uppercase">
                    Inspections de l’Éducation Secondaire Générale
                  </p>
                  {dre.iesg.length > 0 && (
                    <p className="text-xs font-semibold text-muted-foreground">
                      Sélectionne une IESG
                    </p>
                  )}
                </div>
                {dre.iesg.length > 0 ? (
                  <div className="mt-4 grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(10rem,1fr))]">
                    {dre.iesg.map((i) => {
                      const part = Math.round((i.clubs / dre.clubs) * 100);
                      return (
                        <a
                          key={i.nom}
                          href="#"
                          className="card-fx group flex flex-col rounded-2xl p-5"
                          style={{ backgroundColor: teinte(c) }}
                        >
                          <span className="flex items-start justify-between gap-2">
                            <span className="min-w-0">
                              <span className="block font-extrabold">{i.nom}</span>
                              <span className="block text-xs font-medium text-ink/70">
                                {i.zone}
                              </span>
                            </span>
                            <span
                              className="shrink-0 rounded-full bg-card p-2 shadow-sm"
                              style={{ color: c }}
                            >
                              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                            </span>
                          </span>
                          <span className="mt-6 flex flex-wrap items-baseline gap-x-2">
                            <span className="font-display text-5xl leading-none">{i.clubs}</span>
                            <span className="text-sm font-bold">clubs actifs</span>
                          </span>
                          <span className="mt-4 block h-1.5 overflow-hidden rounded-full bg-card">
                            <span
                              className="block h-full origin-left rounded-full animate-in slide-in-from-left-full duration-700"
                              style={{ width: `${part}%`, backgroundColor: c }}
                            />
                          </span>
                          <span className="mt-2 block text-xs font-semibold text-ink/70">
                            {part} % des clubs de la région
                          </span>
                        </a>
                      );
                    })}
                  </div>
                ) : (
                  <p className="mt-4 flex flex-1 items-center justify-center rounded-2xl border border-dashed p-6 text-center text-sm font-semibold text-muted-foreground">
                    Le détail des {dre.nbIesg} IESG de cette région sera bientôt disponible.
                  </p>
                )}
                <a
                  href="/carte-des-clubs"
                  className="btn-fx mt-6 self-start rounded-full bg-primary px-6 py-3 text-center text-[15px] font-bold text-primary-foreground shadow-card"
                >
                  Découvrir les établissements
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
