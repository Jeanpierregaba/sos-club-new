import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";

// Bouton « Retour en haut », sur tout le site : il apparaît une fois qu'on a descendu d'un écran.
export function RetourEnHaut() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const suivre = () => setVisible(window.scrollY > window.innerHeight * 0.8);
    suivre();
    window.addEventListener("scroll", suivre, { passive: true });
    return () => window.removeEventListener("scroll", suivre);
  }, []);

  const remonter = () => {
    const reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduit ? "auto" : "smooth" });
  };

  return (
    <button
      type="button"
      onClick={remonter}
      aria-label="Retour en haut de la page"
      title="Retour en haut"
      tabIndex={visible ? 0 : -1}
      aria-hidden={!visible}
      className={`btn-fx fixed bottom-5 right-5 z-40 inline-flex size-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-card ring-2 ring-white transition-[opacity,translate] duration-300 print:hidden md:bottom-8 md:right-8 ${
        visible ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-4 opacity-0"
      }`}
    >
      <ArrowUp className="size-5" />
    </button>
  );
}
