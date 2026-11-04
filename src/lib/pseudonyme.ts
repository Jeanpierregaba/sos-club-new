// Les règles du pseudonyme reprises de l'API (backend/app/eleves/pseudonyme.py), pour un message immédiat.
// L'API reste seule juge : elle vérifie aussi les mots interdits et les pseudonymes déjà pris.

const LONGUEUR_MIN = 3;
const LONGUEUR_MAX = 30;
const CHIFFRES_MAX = 5;

export function erreurPseudonyme(saisie: string): string | null {
  const propre = saisie.trim().split(/\s+/).join(" ");
  if (propre.length < LONGUEUR_MIN || propre.length > LONGUEUR_MAX)
    return `Ton pseudonyme fait de ${LONGUEUR_MIN} à ${LONGUEUR_MAX} caractères.`;
  // Alphabet latin seulement, accents compris : d'autres alphabets imiteraient un pseudonyme existant.
  if (!/^[\p{Script=Latin}0-9 .-]+$/u.test(propre))
    return "Ton pseudonyme ne contient que des lettres, des chiffres, des espaces, « - » et « . ».";
  if (!/\p{Script=Latin}/u.test(propre)) return "Ton pseudonyme contient au moins une lettre.";
  if ((propre.match(/[0-9]/g) ?? []).length > CHIFFRES_MAX)
    return "Ton pseudonyme ne peut pas contenir de numéro de téléphone.";
  return null;
}
