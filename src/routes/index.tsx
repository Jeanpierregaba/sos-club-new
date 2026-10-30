import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, Search, Users, Play, BookOpen, ClipboardCheck, Gamepad2, Award, Trophy, ChevronLeft, ChevronRight } from "lucide-react";
import hero from "@/assets/hero.jpg";
import mascot from "@/assets/mascot.png";
import story1 from "@/assets/story1.jpg";
import story2 from "@/assets/story2.jpg";
import quiz from "@/assets/quiz.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Club Santé SOS Docteur TV — Ton club, tes talents, tes défis" },
      { name: "description", content: "Apprends, joue et fais bouger ton établissement avec les Clubs Santé du Togo." },
      { property: "og:title", content: "Club Santé SOS Docteur TV" },
      { property: "og:description", content: "Apprends, joue et fais bouger ton établissement avec les Clubs Santé du Togo." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const univers = [
  { t: "Académie Génie Imhotep", d: "Apprendre, se former, réussir", c: "bg-sky" },
  { t: "Santé sexuelle & valeurs", d: "S'informer, se respecter", c: "bg-rose" },
  { t: "TV & Médias", d: "Créer, informer, partager", c: "bg-primary" },
  { t: "Sports & Secourisme", d: "Bouger, sauver des vies", c: "bg-tangerine" },
  { t: "Jeux & Bourses", d: "Jouer, gagner, saisir sa chance", c: "bg-sun" },
  { t: "Leadership", d: "S'engager, impacter", c: "bg-tangerine" },
  { t: "Bien-être & Environnement", d: "Vivre mieux, protéger la planète", c: "bg-leaf" },
];

const stars = [
  { img: story2, tag: "TV & Médias", tc: "bg-primary", t: "Les lycéens en action !", d: "Reportage du Club Santé du Lycée de Lomé sur la prévention du paludisme." },
  { img: story1, tag: "Sports & Secourisme", tc: "bg-tangerine", t: "Apprendre aujourd'hui, sauver des vies demain !", d: "Initiation aux premiers secours avec les clubs santé." },
  { img: hero, tag: "Vie des clubs", tc: "bg-leaf", t: "Une journée verte pour un meilleur cadre de vie", d: "Les clubs se mobilisent pour l'environnement." },
];

const heroSlides = [
  {
    img: hero,
    alt: "Lycéens souriants",
    lines: [
      { t: "TON CLUB.", c: "text-primary" },
      { t: "TES TALENTS.", c: "text-tangerine" },
      { t: "TES DÉFIS.", c: "text-leaf" },
    ],
    sub: "Apprends, joue et fais bouger ton établissement !",
  },
  {
    img: quiz,
    alt: "Lycéens réunis autour du quiz santé",
    lines: [
      { t: "APPRENDS.", c: "text-sky" },
      { t: "RÉVISE.", c: "text-tangerine" },
      { t: "GAGNE DES POINTS.", c: "text-leaf" },
    ],
    sub: "Le défi du jour t'attend : teste tes connaissances !",
  },
  {
    img: story1,
    alt: "Initiation aux premiers secours",
    lines: [
      { t: "BOUGE.", c: "text-sky" },
      { t: "APPRENDS.", c: "text-tangerine" },
      { t: "SAUVE DES VIES.", c: "text-leaf" },
    ],
    sub: "Initiation aux premiers secours avec les clubs santé.",
  },
  {
    img: story2,
    alt: "Reportage du Club Santé du Lycée de Lomé",
    lines: [
      { t: "CRÉE.", c: "text-sky" },
      { t: "INFORME.", c: "text-tangerine" },
      { t: "PASSE À LA TV.", c: "text-leaf" },
    ],
    sub: "Reportages et talents des jeunes des Clubs Santé.",
  },
];

const steps = [
  { i: BookOpen, t: "Apprends", d: "Des contenus simples et interactifs sur la santé.", c: "text-sky" },
  { i: ClipboardCheck, t: "Révise", d: "Teste tes connaissances avec quiz et jeux.", c: "text-leaf" },
  { i: Gamepad2, t: "Relève les défis", d: "Gagne des points à ton rythme.", c: "text-tangerine" },
  { i: Award, t: "Certifie-toi", d: "Obtiens la certification officielle du Club Santé.", c: "text-primary" },
];

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <img src={mascot} alt="" width={44} height={44} className="h-11 w-11" />
      <div className="leading-none">
        <div className="font-display text-xl text-primary">CLUB SANTÉ</div>
        <div className="font-display text-xs text-tangerine">SOS DOCTEUR TV</div>
      </div>
    </div>
  );
}

function Index() {
  const [active, setActive] = useState(0);
  const count = heroSlides.length;
  const next = () => setActive((a) => (a + 1) % count);
  const prev = () => setActive((a) => (a - 1 + count) % count);

  useEffect(() => {
    const t = setInterval(() => setActive((a) => (a + 1) % count), 6000);
    return () => clearInterval(t);
  }, [active, count]);

  return (
    <div className="min-h-screen text-ink">
      <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3">
          <Logo />
          <nav className="hidden gap-7 text-sm font-bold md:flex">
            {["Accueil", "Les 7 univers", "Jeux", "Certification", "Vie des clubs"].map((n, i) => (
              <a key={n} href="#" className={i === 0 ? "border-b-2 border-primary pb-1 text-primary" : "hover:text-primary"}>{n}</a>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <button className="rounded-full bg-lilac p-2.5"><Search className="h-4 w-4" /></button>
            <button className="flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground">Rejoindre le club <Users className="h-4 w-4" /></button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden bg-lilac">
        <div className="absolute inset-y-0 right-0 h-full w-full md:w-3/4">
          {heroSlides.map((s, i) => (
            <img key={i} src={s.img} alt={s.alt} width={1600} height={912} aria-hidden={i !== active}
              className={`absolute inset-0 h-full w-full object-cover object-right transition-opacity duration-700 ${i === active ? "opacity-100" : "opacity-0"}`} />
          ))}
        </div>
        <div className="absolute inset-0 bg-hero" />
        <div className="relative mx-auto grid max-w-7xl items-center px-5 py-16 md:grid-cols-2 md:py-24">
          <div>
            <h1 className="text-5xl leading-[0.95] md:text-7xl">
              {heroSlides[active].lines.map((l) => (
                <span key={l.t}><span className={l.c}>{l.t}</span><br /></span>
              ))}
            </h1>
            <p className="mt-5 text-xl font-bold">{heroSlides[active].sub}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#" className="flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-bold text-primary-foreground shadow-card"><Trophy className="h-5 w-5" /> Je relève un défi <ArrowRight className="h-4 w-4" /></a>
              <a href="#univers" className="flex items-center gap-2 rounded-full bg-card px-6 py-3 font-bold shadow-card">Découvrir les univers <ArrowRight className="h-4 w-4" /></a>
            </div>
            <div className="mt-8 flex items-center gap-4">
              <div className="flex gap-2">
                <button aria-label="Diapositive précédente" onClick={prev} className="flex h-10 w-10 items-center justify-center rounded-full bg-card text-ink shadow-card transition hover:bg-lilac"><ChevronLeft className="h-5 w-5" /></button>
                <button aria-label="Diapositive suivante" onClick={next} className="flex h-10 w-10 items-center justify-center rounded-full bg-card text-ink shadow-card transition hover:bg-lilac"><ChevronRight className="h-5 w-5" /></button>
              </div>
              <div className="flex gap-2">
                {heroSlides.map((_, i) => (
                  <button key={i} aria-label={`Aller à la diapositive ${i + 1}`} onClick={() => setActive(i)}
                    className={`h-2.5 rounded-full transition-all ${i === active ? "w-8 bg-primary" : "w-2.5 bg-primary/30 hover:bg-primary/50"}`} />
                ))}
              </div>
            </div>
          </div>
          <div className="relative hidden h-full md:block">
            <img src={mascot} alt="Mascotte caméléon" width={1024} height={1024} className="absolute -bottom-24 left-0 w-80 drop-shadow-2xl" />
            <div className="absolute right-0 top-0 rotate-6 rounded-[2rem] bg-sun px-6 py-4 font-hand text-2xl leading-tight">Des jeunes en bonne<br />santé pour un<br />meilleur Togo !</div>
          </div>
        </div>
      </section>

      {/* Défi du jour */}
      <section className="mx-auto -mt-6 max-w-7xl px-5">
        <div className="relative grid items-center gap-6 rounded-3xl bg-sun p-6 shadow-card md:grid-cols-[1fr_2fr]">
          <div>
            <h2 className="text-4xl">LE DÉFI DU JOUR</h2>
            <p className="font-bold">Teste tes connaissances et gagne des points !</p>
          </div>
          <div className="rounded-2xl bg-card p-5">
            <p className="text-xs font-extrabold uppercase text-rose">Santé & bien-être</p>
            <p className="mt-1 font-extrabold">Quelle est la meilleure façon de se protéger contre le paludisme ?</p>
            <div className="mt-4 flex flex-wrap gap-3">
              {["Dormir sous une moustiquaire", "Boire beaucoup d'eau", "Éviter les fruits la nuit"].map((o, i) => (
                <button key={o} className={`rounded-xl border-2 px-4 py-2 text-sm font-bold ${i === 0 ? "border-leaf bg-leaf text-primary-foreground" : "border-border"}`}>
                  {"ABC"[i]} · {o}
                </button>
              ))}
              <button className="ml-auto rounded-full bg-primary px-6 py-2 font-bold text-primary-foreground">Valider</button>
            </div>
          </div>
        </div>
      </section>

      {/* Univers */}
      <section id="univers" className="mx-auto max-w-7xl px-5 py-20">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-4xl md:text-5xl"><span className="text-primary">7 UNIVERS,</span> 1000 POSSIBILITÉS</h2>
            <p className="mt-2 text-muted-foreground">Explore les sept axes du Club Santé et trouve celui qui te fait vibrer !</p>
          </div>
          <a href="#" className="font-bold text-primary underline">Découvrir les 7 univers →</a>
        </div>
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-7">
          {univers.map((u) => (
            <a key={u.t} href="#" className={`${u.c} group flex flex-col items-center rounded-3xl p-4 text-center text-primary-foreground shadow-card transition hover:-translate-y-2`}>
              <img src={mascot} alt="" loading="lazy" width={1024} height={1024} className="h-24 w-24 transition group-hover:scale-110" />
              <h3 className="mt-2 text-lg leading-tight">{u.t.toUpperCase()}</h3>
              <p className="mt-2 flex-1 text-xs font-semibold">{u.d}</p>
              <span className="mt-3 rounded-full bg-card p-1.5 text-ink"><ArrowRight className="h-4 w-4" /></span>
            </a>
          ))}
        </div>
      </section>

      {/* Stars */}
      <section className="mx-auto max-w-7xl px-5 pb-20">
        <h2 className="text-4xl md:text-5xl"><span className="text-primary">C'EST VOUS</span> LES STARS !</h2>
        <p className="mt-2 text-muted-foreground">Les réalisations et talents des jeunes des Clubs Santé.</p>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {stars.map((s) => (
            <article key={s.t} className="overflow-hidden rounded-3xl bg-card shadow-card">
              <div className="relative">
                <img src={s.img} alt={s.t} loading="lazy" className="aspect-[3/2] w-full object-cover object-right" />
                <span className="absolute -bottom-5 right-5 rounded-full bg-primary p-3 text-primary-foreground"><Play className="h-5 w-5 fill-current" /></span>
              </div>
              <div className="p-5">
                <span className={`${s.tc} rounded-full px-3 py-1 text-xs font-extrabold uppercase text-primary-foreground`}>{s.tag}</span>
                <h3 className="mt-3 font-sans text-lg font-extrabold">{s.t}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Parcours */}
      <section className="mx-auto max-w-7xl px-5 pb-20">
        <div className="relative rounded-[2rem] bg-lilac p-8 md:p-12">
          <h2 className="text-4xl text-primary md:text-5xl">PASSE AU NIVEAU SUPÉRIEUR</h2>
          <p className="mt-2">Un parcours simple et amusant pour obtenir ta certification !</p>
          <div className="mt-8 grid gap-5 md:grid-cols-4">
            {steps.map((s, i) => (
              <div key={s.t} className="rounded-2xl bg-card p-5 text-center shadow-card">
                <span className="mx-auto flex h-8 w-8 items-center justify-center rounded-full bg-primary font-display text-primary-foreground">{i + 1}</span>
                <s.i className={`mx-auto mt-3 h-10 w-10 ${s.c}`} />
                <h3 className="mt-2 text-xl">{s.t}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 text-center">
            <a href="#" className="inline-flex items-center gap-2 rounded-full bg-primary px-8 py-3 font-bold text-primary-foreground">Commencer mon parcours <ArrowRight className="h-4 w-4" /></a>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-cta text-primary-foreground">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-6 px-5 py-14">
          <div>
            <h2 className="text-4xl md:text-5xl">PRÊT À FAIRE PARTIE <span className="text-sun">DE L'AVENTURE ?</span></h2>
            <p className="mt-2">Rejoins des milliers de jeunes engagés pour une meilleure santé.</p>
          </div>
          <div className="text-center">
            <a href="#" className="inline-flex items-center gap-2 rounded-full bg-sun px-8 py-4 font-extrabold text-ink"><Users className="h-5 w-5" /> Rejoindre le club <ArrowRight className="h-4 w-4" /></a>
            <p className="mt-2 text-sm">C'est gratuit et ouvert à tous les lycéens !</p>
          </div>
        </div>
      </section>

      <footer className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-8 text-sm">
        <Logo />
        <p className="text-muted-foreground">© 2026 Club Santé SOS Docteur TV. Tous droits réservés.</p>
      </footer>
    </div>
  );
}
