// Emplacements à remplacer par les vrais logos. Le défilement n'est continu que si une liste dépasse la largeur de l'écran : répéter les logos s'il y en a peu.
const partenaires = Array.from({ length: 8 }, (_, i) => `Logo partenaire ${i + 1}`);

function Logos({ masque = false }: { masque?: boolean }) {
  return (
    <ul aria-hidden={masque || undefined} className="flex shrink-0 gap-6 pr-6">
      {partenaires.map((p) => (
        <li
          key={p}
          className="flex h-24 w-48 items-center justify-center rounded-2xl border bg-card px-4 text-center text-sm font-bold text-muted-foreground shadow-sm transition duration-300 hover:scale-105 hover:border-primary hover:text-logo-blue"
        >
          {p}
        </li>
      ))}
    </ul>
  );
}

export function PartenairesSection() {
  return (
    <section id="partenaires" className="scroll-mt-16 py-20">
      <div data-reveal className="mx-auto max-w-3xl px-5 text-center">
        <h2 className="text-4xl md:text-5xl">
          <span className="text-logo-blue">Nos Soutiens</span>{" "}
          <span className="text-primary">& Partenaires</span>
        </h2>
        <p className="mt-4 text-muted-foreground">
          Nous remercions chaleureusement les ministères, organisations non-gouvernementales et
          réseaux de médias qui soutiennent l’excellence sanitaire chez les jeunes du Togo.
        </p>
      </div>
      {/* La seconde liste, identique, prend le relais quand la première sort de l'écran. Sans animation, le visiteur fait défiler à la main. */}
      <div
        data-reveal
        className="mt-10 overflow-hidden py-2 [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)] motion-reduce:overflow-x-auto"
      >
        <div className="flex w-max animate-marquee hover:[animation-play-state:paused] motion-reduce:animate-none">
          <Logos />
          <div className="contents motion-reduce:hidden">
            <Logos masque />
          </div>
        </div>
      </div>
    </section>
  );
}
