import { REGEXP_ONLY_DIGITS } from "input-otp";

import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";

// Les 6 chiffres de l'application d'authentification, en grandes cases. `onComplet` part au 6e chiffre.
export function ChampCode({
  id,
  valeur,
  onChange,
  onComplet,
  desactive = false,
}: {
  id: string;
  valeur: string;
  onChange: (valeur: string) => void;
  onComplet?: (valeur: string) => void;
  desactive?: boolean;
}) {
  return (
    <InputOTP
      id={id}
      maxLength={6}
      pattern={REGEXP_ONLY_DIGITS}
      inputMode="numeric"
      autoComplete="one-time-code"
      aria-label="Code à 6 chiffres de ton application d'authentification"
      value={valeur}
      onChange={onChange}
      {...(onComplet ? { onComplete: onComplet } : {})}
      disabled={desactive}
      containerClassName="justify-center"
    >
      <InputOTPGroup className="gap-2">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <InputOTPSlot
            key={i}
            index={i}
            className="h-14 w-11 rounded-xl border bg-white font-display text-2xl first:rounded-xl last:rounded-xl sm:w-12"
          />
        ))}
      </InputOTPGroup>
    </InputOTP>
  );
}
