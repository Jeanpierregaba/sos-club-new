import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EditeurQuestion } from "./EditeurQuestion";

describe("EditeurQuestion", () => {
  it("envoie l'énoncé, les choix et la bonne réponse cochée", async () => {
    const enregistre = vi.fn().mockResolvedValue(undefined);
    render(<EditeurQuestion onEnregistre={enregistre} />);
    const bouton = screen.getByRole("button", { name: /Ajouter la question/ });
    expect(bouton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Énoncé"), { target: { value: " Combien ? " } });
    fireEvent.click(screen.getByRole("button", { name: /Ajouter un choix/ }));
    fireEvent.change(screen.getByLabelText("Choix 1"), { target: { value: "Un" } });
    fireEvent.change(screen.getByLabelText("Choix 2"), { target: { value: "Deux" } });
    fireEvent.change(screen.getByLabelText("Choix 3"), { target: { value: "Trois" } });
    fireEvent.click(screen.getByLabelText("Choix 3 : bonne réponse"));
    await act(async () => fireEvent.click(bouton));

    expect(enregistre).toHaveBeenCalledWith({
      enonce: "Combien ?",
      choix: ["Un", "Deux", "Trois"],
      bonne_reponse: 2,
      explication: null,
    });
  });

  it("garde la bonne réponse alignée quand on retire un choix", async () => {
    const enregistre = vi.fn().mockResolvedValue(undefined);
    render(
      <EditeurQuestion
        question={{
          id: "q",
          enonce: "Laquelle ?",
          choix: ["A", "B", "C"],
          bonne_reponse: 2,
          explication: null,
          ordre: 1,
          active: true,
        }}
        onEnregistre={enregistre}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retirer le choix 1" }));
    await act(async () =>
      fireEvent.click(screen.getByRole("button", { name: /Enregistrer la question/ })),
    );

    expect(enregistre).toHaveBeenCalledWith(
      expect.objectContaining({ choix: ["B", "C"], bonne_reponse: 1 }),
    );
  });
});
