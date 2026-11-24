import { ArrowRight } from "lucide-react";
import { lien } from "@/lib/langues";
import { photos } from "@/lib/galerie";
import { m } from "@/paraglide/messages.js";

export function GalerieSection() {
  return (
    <section id="galerie" className="scroll-mt-16 bg-mist-soft py-20">
      <div className="mx-auto max-w-7xl px-5">
        <div data-reveal className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <h2 className="text-4xl md:text-5xl">
              <span className="text-logo-blue">{m.galerie_bloc_titre_1()}</span>{" "}
              <span className="text-primary">{m.galerie_bloc_titre_2()}</span>
            </h2>
            <p className="mt-4 max-w-xl text-muted-foreground">{m.galerie_bloc_texte()}</p>
          </div>
          <a
            href={lien("/galerie")}
            className="btn-fx inline-flex items-center gap-2 rounded-full bg-primary px-7 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
          >
            {m.galerie_voir_plus()} <ArrowRight className="size-4" />
          </a>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4">
          {photos.slice(0, 6).map((p) => (
            <figure
              key={p.img}
              className="group overflow-hidden rounded-2xl shadow-card md:rounded-3xl"
            >
              <img
                src={p.img}
                alt={p.alt}
                loading="lazy"
                width={p.w}
                height={p.h}
                className={`aspect-[4/3] w-full object-cover transition duration-500 group-hover:scale-105 ${p.pos}`}
              />
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
