import { useState, type FormEvent } from "react";
import {
  Facebook,
  Globe,
  Instagram,
  Linkedin,
  MapPin,
  Phone,
  Send,
  Tv,
  Youtube,
} from "lucide-react";
import { retard } from "@/components/SiteMotion";
import { TikTokIcon } from "@/components/TikTokIcon";
import logo from "@/assets/logo.webp";

const SITE = "https://www.sos-docteur.tv";

// Facebook, YouTube et LinkedIn : adresses à renseigner, elles pointent vers « # » en attendant.
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
  { i: Facebook, t: "Facebook", d: "Clubs Santé SOS DOCTEUR TV", href: "#", c: "text-sky" },
  { i: Youtube, t: "YouTube TV", d: "SOS DOCTEUR TV", href: "#", c: "text-logo-red" },
  { i: Linkedin, t: "LinkedIn", d: "Club Santé Docteur SOS TV", href: "#", c: "text-logo-blue" },
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
        <div
          data-reveal
          className="grid items-center gap-6 rounded-[2rem] border border-white/15 bg-white/5 p-6 md:p-10 lg:grid-cols-2 lg:gap-12"
        >
          <div>
            <h2 className="text-3xl uppercase text-primary md:text-4xl">Newsletter</h2>
            <p className="mt-2 text-white/70">
              Suis l’impact des clubs en recevant notre synthèse mensuelle.
            </p>
          </div>
          <div>
            <form onSubmit={sAbonner} className="flex flex-col gap-2 sm:flex-row">
              <label htmlFor="newsletter-email" className="sr-only">
                Ton adresse e-mail
              </label>
              <input
                id="newsletter-email"
                type="email"
                required
                placeholder="ton-email@adresse.tg"
                autoComplete="email"
                className="h-12 w-full min-w-0 rounded-full border border-white/20 bg-white/5 px-5 text-sm outline-none transition placeholder:text-white/50 focus:border-primary focus:bg-white/10"
              />
              <button
                type="submit"
                className="btn-fx group flex h-12 items-center justify-center gap-2 rounded-full bg-primary px-6 text-[15px] font-bold"
              >
                M’abonner{" "}
                <Send className="h-4 w-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </button>
            </form>
            {envoye && (
              <p role="status" className="mt-3 text-sm font-semibold text-sun animate-in fade-in">
                L’inscription à la newsletter ouvrira bientôt. Merci de ta patience !
              </p>
            )}
          </div>
        </div>

        <div className="mt-14">
          <div data-reveal className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl uppercase text-primary md:text-4xl">Nos médias officiels</h2>
            <p className="mt-2 text-white/70">
              Suis les reportages, émissions télévisées et activités des Clubs Santé et de SOS
              DOCTEUR TV.
            </p>
          </div>
          <ul className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {medias.map((m, n) => (
              <li key={m.t} data-reveal="zoom" style={retard(n)}>
                <a
                  href={m.href}
                  {...externe(m.href)}
                  className="card-fx group flex h-full flex-col items-center rounded-2xl border border-white/10 bg-white/5 p-4 text-center hover:border-white/30 hover:bg-white/10"
                >
                  <span
                    className={`${m.c} flex h-12 w-12 items-center justify-center rounded-full bg-white transition duration-300 group-hover:-rotate-6 group-hover:scale-110`}
                  >
                    <m.i className="h-6 w-6" />
                  </span>
                  <span className="mt-3 font-extrabold leading-tight">{m.t}</span>
                  <span className="mt-1 max-w-full break-words text-[11px] text-white/70 sm:text-xs">
                    {m.d}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-14 flex flex-wrap items-center justify-between gap-6 border-t border-white/10 py-8">
          {/* Le logo bleu foncé disparaîtrait sur le fond nuit : il garde sa plaque blanche. */}
          <a href="/" className="btn-fx rounded-xl bg-white px-3 py-2">
            <img
              src={logo}
              alt="Club Santé SOS Docteur TV"
              width={1014}
              height={195}
              loading="lazy"
              className="h-8 w-auto"
            />
          </a>
          <div className="min-w-0">
            <h2 className="text-lg uppercase tracking-wide text-primary">AIMES-AFRIQUE</h2>
            <ul className="mt-2 flex flex-wrap gap-x-6 gap-y-2 text-sm text-white/70">
              <li className="flex items-center gap-2">
                <MapPin className="h-4 w-4 shrink-0 text-primary" /> Lomé, Quartier Adidoadin, Togo
              </li>
              <li>
                <a
                  href="tel:+22822224545"
                  className="flex items-center gap-2 transition hover:text-white"
                >
                  <Phone className="h-4 w-4 shrink-0 text-primary" /> +228 22 22 45 45
                </a>
              </li>
              <li>
                <a
                  href={SITE}
                  {...externe(SITE)}
                  className="flex items-center gap-2 underline underline-offset-4 transition hover:text-white"
                >
                  <Globe className="h-4 w-4 shrink-0 text-primary" /> www.sos-docteur.tv
                </a>
              </li>
            </ul>
          </div>
        </div>
        <p className="border-t border-white/10 py-5 text-center text-sm text-white/70">
          © 2026 Club Santé SOS Docteur TV. Tous droits réservés.
        </p>
      </div>
    </footer>
  );
}
