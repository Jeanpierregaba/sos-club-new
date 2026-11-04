// Même règle que l'API (spec 018) : séparateurs retirés, de 8 à 15 chiffres, « + » au début si besoin.
const SEPARATEURS = /[\s().-]/g;
const FORMAT = /^\+?[0-9]{8,15}$/;

export const normaliserTelephone = (valeur: string) => valeur.replace(SEPARATEURS, "");

export const telephoneValide = (valeur: string) => {
  const propre = normaliserTelephone(valeur);
  return propre === "" || FORMAT.test(propre);
};
