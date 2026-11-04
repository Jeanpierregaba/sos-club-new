import { useEffect, useRef, useState } from "react";

// Le rendu serveur affiche le vrai chiffre (sans JavaScript, ou si l'utilisateur limite les animations) ; le compte part de 0 quand le chiffre devient visible.
export function Compteur({ value }: { value: number }) {
  const [current, setCurrent] = useState(value);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setCurrent(0);
    let frame = 0;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const tick = (now: number) => {
          const p = Math.min(Math.max(now - start, 0) / 1800, 1);
          setCurrent(Math.round(value * (1 - (1 - p) ** 3)));
          if (p < 1) frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
      },
      { threshold: 0.5 },
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value]);

  return <span ref={ref}>{String(current).replace(/\B(?=(\d{3})+$)/g, " ")}</span>;
}
