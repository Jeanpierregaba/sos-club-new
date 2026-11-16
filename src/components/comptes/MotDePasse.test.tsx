import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReinitialiserMembre } from "@/components/clubs/ReinitialiserMembre";
import { BandeauMotDePasse } from "@/components/espace/BandeauMotDePasse";

const api = vi.hoisted(() => ({ reinitialiserMembre: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

beforeEach(() => vi.clearAllMocks());

describe("ReinitialiserMembre (spec 039)", () => {
  it("demande un motif puis montre le mot de passe provisoire une seule fois", async () => {
    api.reinitialiserMembre.mockResolvedValue({ mot_de_passe: "abcd2345efgh" });
    render(<ReinitialiserMembre affiliationId="a-1" pseudonyme="Yao" />);

    fireEvent.click(screen.getByRole("button", { name: "Réinitialiser le mot de passe de Yao" }));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Mot de passe oublié en classe." },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
    });

    expect(api.reinitialiserMembre).toHaveBeenCalledWith("a-1", "Mot de passe oublié en classe.");
    expect(screen.getByLabelText("Mot de passe à donner à l’élève")).toHaveTextContent(
      "abcd2345efgh",
    );
    expect(screen.getByText(/en main propre/)).toBeInTheDocument();
  });

  it("affiche le refus de l'API, par exemple le plafond du jour", async () => {
    const { ErreurApi } = await import("@/lib/api/client");
    api.reinitialiserMembre.mockRejectedValue(
      new ErreurApi(429, "Tu as déjà fait 10 réinitialisations en 24 heures."),
    );
    render(<ReinitialiserMembre affiliationId="a-1" pseudonyme="Yao" />);

    fireEvent.click(screen.getByRole("button", { name: /Réinitialiser le mot de passe/ }));
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "Mot de passe oublié en classe." },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
    });

    expect(screen.getByText(/10 réinitialisations en 24 heures/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Mot de passe à donner à l’élève")).toBeNull();
  });
});

describe("BandeauMotDePasse (spec 039)", () => {
  it("conseille de choisir son mot de passe sans rien bloquer", () => {
    const onChanger = vi.fn();
    render(<BandeauMotDePasse onChanger={onChanger} />);

    fireEvent.click(screen.getByRole("button", { name: "Choisir mon mot de passe" }));

    expect(screen.getByRole("status")).toHaveTextContent("réinitialisé");
    expect(onChanger).toHaveBeenCalled();
  });
});
