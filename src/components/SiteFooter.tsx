import { useState, type FormEvent } from "react";
import { Facebook, Instagram, Linkedin, MapPin, Phone, Send, Tv, Youtube } from "lucide-react";
import { retard } from "@/components/SiteMotion";
import { TikTokIcon } from "@/components/TikTokIcon";
import { m } from "@/paraglide/messages.js";

const SITE = "https://www.sos-docteur.tv";
const IBDA = "https://ibdastudio.com/";

// Facebook et LinkedIn : adresses reprises du site de référence. YouTube : adresse de la chaîne à renseigner, elle pointe vers « # » en attendant.
const medias = [
  {
    i: TikTokIcon,
    t: "TikTok",
    d: "@clubsantesosdocte",
    href: "https://www.tiktok.com/@clubsantesosdocte",
    c: "text-night",
  },
  {
    i: Instagram,
    t: "Instagram",
    d: "@clubsantesosdocteurtv",
    href: "https://www.instagram.com/clubsantesosdocteurtv",
    c: "text-rose",
  },
  {
    i: Facebook,
    t: "Facebook",
    d: "Clubs Santé SOS DOCTEUR TV",
    href: "https://web.facebook.com/profile.php?id=61591819257886",
    c: "text-sky",
  },
  { i: Youtube, t: "YouTube TV", d: "@ClubSantéSOSDocteurTV", href: "#", c: "text-logo-red" },
  {
    i: Linkedin,
    t: "LinkedIn",
    d: "Club Santé Docteur SOS TV",
    href: "https://www.linkedin.com/company/club-sant%C3%A9-docteur-sos-tv/about/",
    c: "text-logo-blue",
  },
  { i: Tv, t: "SOS Docteur TV", d: "www.sos-docteur.tv", href: SITE, c: "text-logo-red" },
];

const externe = (href: string) =>
  href === "#" ? {} : { target: "_blank", rel: "noopener noreferrer" };

export function SiteFooter() {
  const [envoye, setEnvoye] = useState(false);
  // Aucun service d'envoi n'est branché : l'adresse saisie n'est ni transmise ni conservée.
  const sAbonner = (e: FormEvent) => {
    e.preventDefault();
    setEnvoye(true);
  };

  return (
    <footer className="bg-night pt-16 text-primary-foreground">
      <div className="mx-auto max-w-7xl px-5">
        <div>
          <div data-reveal className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl uppercase text-primary md:text-4xl">{m.pied_medias_titre()}</h2>
            <p className="mt-2 text-white/70">{m.pied_medias_texte()}</p>
          </div>
          <ul className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {medias.map((media, n) => (
              <li key={media.t} data-reveal="zoom" style={retard(n)}>
                <a
                  href={media.href}
                  {...externe(media.href)}
                  className="card-fx group flex h-full flex-col items-center rounded-2xl border border-white/10 bg-white/5 p-4 text-center hover:border-white/30 hover:bg-white/10"
                >
                  <span
                    className={`${media.c} flex h-12 w-12 items-center justify-center rounded-full bg-white transition duration-300 group-hover:-rotate-6 group-hover:scale-110`}
                  >
                    <media.i className="h-6 w-6" />
                  </span>
                  <span className="mt-3 font-extrabold leading-tight">{media.t}</span>
                  <span className="mt-1 max-w-full break-words text-[11px] text-white/70 sm:text-xs">
                    {media.d}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div
          data-reveal
          className="mt-14 grid items-center gap-6 rounded-[2rem] border border-white/15 bg-white/5 p-6 md:p-10 lg:grid-cols-2 lg:gap-12"
        >
          <div>
            <h2 className="text-3xl uppercase text-primary md:text-4xl">
              {m.pied_newsletter_titre()}
            </h2>
            <p className="mt-2 text-white/70">{m.pied_newsletter_texte()}</p>
          </div>
          <div>
            <form onSubmit={sAbonner} className="flex flex-col gap-2 sm:flex-row">
              <label htmlFor="newsletter-email" className="sr-only">
                {m.pied_newsletter_adresse()}
              </label>
              <input
                id="newsletter-email"
                type="email"
                required
                placeholder={m.pied_newsletter_exemple()}
                autoComplete="email"
                className="h-12 w-full min-w-0 rounded-full border border-white/20 bg-white/5 px-5 text-sm outline-none transition placeholder:text-white/50 focus:border-primary focus:bg-white/10"
              />
              <button
                type="submit"
                className="btn-fx group flex h-12 items-center justify-center gap-2 rounded-full bg-primary px-6 text-[15px] font-bold"
              >
                {m.pied_newsletter_abonner()}{" "}
                <Send className="h-4 w-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </button>
            </form>
            {envoye && (
              <p role="status" className="mt-3 text-sm font-semibold text-sun animate-in fade-in">
                {m.pied_newsletter_bientot()}
              </p>
            )}
          </div>
        </div>

        {/* Une seule ligne sur grand écran (xl) : AIMES-AFRIQUE à gauche, le copyright au milieu, IBDA STUDIO à droite. */}
        <div className="mt-14 grid gap-4 border-t border-white/10 py-6 text-center text-sm text-white/70 xl:grid-cols-[auto_minmax(0,1fr)_auto] xl:items-center xl:gap-6">
          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 xl:justify-start">
            <span className="font-display uppercase tracking-wide text-primary">AIMES-AFRIQUE</span>
            <span className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4 shrink-0 text-primary" /> {m.pied_adresse()}
            </span>
            <a
              href="tel:+22822224545"
              className="flex items-center gap-1.5 transition hover:text-white"
            >
              <Phone className="h-4 w-4 shrink-0 text-primary" /> +228 22 22 45 45
            </a>
          </div>
          <p>{m.pied_droits({ annee: "2026" })}</p>
          <p className="xl:text-right">
            {m.pied_propulse()}{" "}
            <a
              href={IBDA}
              {...externe(IBDA)}
              className="font-bold text-white underline-offset-4 transition hover:underline"
            >
              IBDA STUDIO
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
