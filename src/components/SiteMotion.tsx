import { useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";

// Décale l'apparition des éléments d'une même rangée.
export const retard = (i: number) => ({ "--delay": `${i * 80}ms` }) as CSSProperties;

// Apparitions au défilement, barre de progression et ombre du header. Seuls les éléments présents au premier rendu sont animés.
export function SiteMotion() {
  const barre = useRef<HTMLDivElement>(null);

  // Avant l'affichage : ce qui est déjà à l'écran ne doit ni clignoter ni rejouer d'animation.
  useLayoutEffect(() => {
    if (
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
      !("IntersectionObserver" in window)
    )
      return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          e.target.setAttribute("data-visible", "anim");
          observer.unobserve(e.target);
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    document.querySelectorAll("[data-reveal]").forEach((el) => {
      if (el.getBoundingClientRect().top < window.innerHeight)
        el.setAttribute("data-visible", "instant");
      else observer.observe(el);
    });
    // Les éléments montés plus tard (listes filtrées, contenu calculé au navigateur) s'affichent sans animation.
    const ajouts = new MutationObserver((mutations) => {
      for (const m of mutations)
        m.addedNodes.forEach((n) => {
          if (!(n instanceof Element)) return;
          for (const el of [n, ...n.querySelectorAll("[data-reveal]")])
            if (el.hasAttribute("data-reveal") && !el.hasAttribute("data-visible"))
              el.setAttribute("data-visible", "instant");
        });
    });
    ajouts.observe(document.body, { childList: true, subtree: true });
    document.documentElement.classList.add("reveal-ready");
    return () => {
      ajouts.disconnect();
      observer.disconnect();
      document.documentElement.classList.remove("reveal-ready");
    };
  }, []);

  useEffect(() => {
    const header = document.querySelector("header");
    let attente = 0;
    const maj = () => {
      attente = 0;
      const y = window.scrollY;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (barre.current) barre.current.style.transform = `scaleX(${max > 0 ? y / max : 0})`;
      header?.toggleAttribute("data-scrolled", y > 8);
    };
    const demande = () => {
      attente ||= requestAnimationFrame(maj);
    };
    maj();
    window.addEventListener("scroll", demande, { passive: true });
    window.addEventListener("resize", demande);
    return () => {
      cancelAnimationFrame(attente);
      window.removeEventListener("scroll", demande);
      window.removeEventListener("resize", demande);
    };
  }, []);

  return (
    <div
      ref={barre}
      aria-hidden
      className="fixed inset-x-0 top-0 z-30 h-1 origin-left scale-x-0 bg-primary"
    />
  );
}
