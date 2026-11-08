import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PropositionFiche } from "./PropositionFiche";
import type { AxePublic, PropositionFiche as Proposition } from "@/lib/api/client";

const api = vi.hoisted(() => ({ proposerFiche: vi.fn(), retirerProposition: vi.fn() }));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const axes: AxePublic[] = [
  { code: "sante-environnement", libelle: "Santé & environnement", description: "" },
  { code: "sport-secourisme", libelle: "Sport & secourisme", description: "" },
];
const enAttente: Proposition = {
  id: "p1",
  etat: "en_attente",
  description: "Des ateliers chaque jeudi.",
  axes: ["sport-secourisme"],
  motif: null,
  soumis_le: "2026-11-08T10:00:00Z",
  version: 2,
};

beforeEach(() => vi.clearAllMocks());

describe("PropositionFiche", () => {
  it("n'envoie rien tant que la fiche n'a pas changé, puis envoie la proposition", async () => {
    const rafraichir = vi.fn().mockResolvedValue(undefined);
    api.proposerFiche.mockResolvedValue({ ...enAttente });
    render(
      <PropositionFiche
        description="Le club du lycée."
        axes={["sante-environnement"]}
        tousLesAxes={axes}
        propositions={[]}
        onRafraichir={rafraichir}
      />,
    );
    const bouton = screen.getByRole("button", { name: /Proposer ces changements/ });
    expect(bouton).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Sport & secourisme" }));
    await act(async () => fireEvent.click(bouton));

    expect(api.proposerFiche).toHaveBeenCalledWith({
      description: "Le club du lycée.",
      axes: ["sante-environnement", "sport-secourisme"],
    });
    expect(rafraichir).toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent(/Proposition envoyée/);
  });

  it("montre la proposition en attente et permet de la retirer", async () => {
    api.retirerProposition.mockResolvedValue(undefined);
    render(
      <PropositionFiche
        description={null}
        axes={[]}
        tousLesAxes={axes}
        propositions={[enAttente]}
        onRafraichir={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText(/en attente de validation/)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Proposer ces changements/ }),
    ).not.toBeInTheDocument();
    await act(async () =>
      fireEvent.click(screen.getByRole("button", { name: /Retirer la proposition/ })),
    );
    expect(api.retirerProposition).toHaveBeenCalledWith("p1");
  });
});
