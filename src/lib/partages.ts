import type { ReseauPartage } from "@/lib/api/client";

// Les réseaux des partages vérifiés (spec 044), dans l'ordre du cahier des charges élève (§ 5.3).
export const RESEAUX: { code: ReseauPartage; nom: string }[] = [
  { code: "facebook", nom: "Facebook" },
  { code: "instagram", nom: "Instagram" },
  { code: "tiktok", nom: "TikTok" },
  { code: "linkedin", nom: "LinkedIn" },
];

export const nomDuReseau = (code: ReseauPartage) =>
  RESEAUX.find((r) => r.code === code)?.nom ?? code;
