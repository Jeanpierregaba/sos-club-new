import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConfirmationEmail } from "./ConfirmationEmail";

const confirmerEmail = vi.hoisted(() => vi.fn());
const renvoyerCode = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/client", async () => {
  class ErreurApi extends Error {
    constructor(
      readonly statut: number,
      message: string,
    ) {
      super(message);
    }
  }
  return {
    confirmerEmail,
    renvoyerCode,
    ErreurApi,
    MESSAGE_INDISPONIBLE: "Service indisponible.",
  };
});

// Le vrai champ (input-otp) a besoin de ResizeObserver, absent de jsdom : un champ simple le remplace.
vi.mock("@/components/admin/ChampCode", () => ({
  ChampCode: ({
    id,
    valeur,
    onChange,
  }: {
    id: string;
    valeur: string;
    onChange: (valeur: string) => void;
  }) => <input id={id} value={valeur} onChange={(e) => onChange(e.target.value)} />,
}));

const { ErreurApi } = await import("@/lib/api/client");
const moi = { id: "1", identifiant: "v.1", prenom: "Koffi", nom: "A", role: "visiteur" };

describe("ConfirmationEmail", () => {
  beforeEach(() => {
    confirmerEmail.mockReset();
    renvoyerCode.mockReset();
  });

  it("confirme avec le code saisi", async () => {
    confirmerEmail.mockResolvedValue(moi);
    const onConfirme = vi.fn();
    render(<ConfirmationEmail email="koffi@gmail.com" onConfirme={onConfirme} />);

    expect(screen.getByText("koffi@gmail.com")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Code de confirmation"), {
      target: { value: "042917" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmer mon adresse" }));

    await waitFor(() => expect(onConfirme).toHaveBeenCalledWith(moi));
    expect(confirmerEmail).toHaveBeenCalledWith("koffi@gmail.com", "042917");
  });

  it("affiche le refus de l'API", async () => {
    confirmerEmail.mockRejectedValue(new ErreurApi(400, "Ce code est incorrect ou expiré."));
    render(<ConfirmationEmail email="koffi@gmail.com" onConfirme={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Code de confirmation"), {
      target: { value: "000000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmer mon adresse" }));

    expect(await screen.findByText("Ce code est incorrect ou expiré.")).toBeInTheDocument();
  });

  it("ne permet pas de renvoyer un code avant une minute", () => {
    render(<ConfirmationEmail email="koffi@gmail.com" onConfirme={vi.fn()} />);

    const renvoi = screen.getByRole("button", { name: /Renvoyer un code \(60 s\)/ });
    expect(renvoi).toBeDisabled();
  });

  it("montre le code de test hors production", () => {
    render(<ConfirmationEmail email="koffi@gmail.com" codeDeTest="123456" onConfirme={vi.fn()} />);

    expect(screen.getByText("123456")).toBeInTheDocument();
    expect(screen.getByText(/Contenu de test/)).toBeInTheDocument();
  });
});
