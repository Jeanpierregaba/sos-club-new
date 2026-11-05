import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/api/client")>();
  return { ...original, demanderClub: vi.fn() };
});

import { demanderClub, type AxePublic, type EtablissementRattache } from "@/lib/api/client";
import { DialogueDemandeClub } from "./DialogueDemandeClub";

const etablissement: EtablissementRattache = {
  id: "etab-1",
  nom: "Lycée de Tokoin I",
  statut: "actif",
  iesg: "IESG Golfe",
  dre_code: "grand-lome",
  dre: "Grand Lomé",
};

const axes: AxePublic[] = [
  {
    code: "sante-environnement",
    libelle: "Santé et environnement",
    description: "Protéger son cadre de vie.",
  },
  { code: "sport", libelle: "Sport et bien-être", description: "Bouger ensemble." },
  { code: "nutrition", libelle: "Nutrition", description: "Mieux manger." },
  { code: "secourisme", libelle: "Secourisme", description: "Apprendre les gestes qui sauvent." },
];

function afficher(onCree = vi.fn().mockResolvedValue(undefined)) {
  render(
    <DialogueDemandeClub
      ouvert
      onOuvert={() => {}}
      etablissement={etablissement}
      axes={axes}
      onCree={onCree}
    />,
  );
  return onCree;
}

describe("DialogueDemandeClub", () => {
  beforeEach(() => {
    vi.mocked(demanderClub)
      .mockReset()
      .mockResolvedValue({} as never);
  });

  it("n'envoie rien sans la confirmation de présidence", async () => {
    afficher();

    fireEvent.change(screen.getByLabelText("Nom officiel du club"), {
      target: { value: "Club Santé de Tokoin" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Envoyer ma demande" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Coche la case pour confirmer que tu es désigné président",
    );
    expect(demanderClub).not.toHaveBeenCalled();
  });

  it("envoie le nom, les axes choisis et les encadreurs déclaratifs", async () => {
    const onCree = afficher();

    fireEvent.change(screen.getByLabelText("Nom officiel du club"), {
      target: { value: "  Club Santé de Tokoin  " },
    });
    fireEvent.click(screen.getByLabelText("Santé et environnement"));
    fireEvent.click(screen.getByRole("button", { name: "Ajouter un encadreur" }));
    fireEvent.change(screen.getByLabelText("Nom de l'encadreur 1"), {
      target: { value: "Mme Adjo" },
    });
    fireEvent.change(screen.getByLabelText("E-mail de l'encadreur 1"), {
      target: { value: "adjo@ecole.tg" },
    });
    fireEvent.click(screen.getByRole("checkbox", { name: /Je confirme être désigné/ }));
    fireEvent.click(screen.getByRole("button", { name: "Envoyer ma demande" }));

    await waitFor(() =>
      expect(demanderClub).toHaveBeenCalledWith({
        nom: "Club Santé de Tokoin",
        description: null,
        axes: ["sante-environnement"],
        encadreurs_associes: [{ nom: "Mme Adjo", email: "adjo@ecole.tg", telephone: null }],
        confirmation: true,
      }),
    );
    expect(onCree).toHaveBeenCalled();
  });

  it("limite le choix à trois axes", () => {
    afficher();

    fireEvent.click(screen.getByLabelText("Santé et environnement"));
    fireEvent.click(screen.getByLabelText("Sport et bien-être"));
    fireEvent.click(screen.getByLabelText("Nutrition"));
    fireEvent.click(screen.getByLabelText("Secourisme"));

    expect(screen.getByText("3/3 choisis.")).toBeInTheDocument();
    expect(screen.getByLabelText("Secourisme")).not.toBeChecked();
  });
});
