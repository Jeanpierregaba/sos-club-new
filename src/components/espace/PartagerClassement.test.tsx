import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PartagerClassement } from "./PartagerClassement";
import { ErreurApi, type ClassementPersonnel } from "@/lib/api/client";

const api = vi.hoisted(() => ({
  chargerMonClassement: vi.fn(),
  chargerCarteClassement: vi.fn(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  ...api,
}));

const rang = { points: 100, rang_club: 2, rang_dre: 2, rang_national: 3, classe: true };
const classement: ClassementPersonnel = {
  categorie: "eleves",
  club: { id: "c1", nom: "Club Santé Tokoin" },
  semestre_en_cours: { libelle: "Semestre 1", debut: "2026-09-01", fin: "2027-01-31" },
  semestre: rang,
  historique: rang,
  distinctions: [],
};

globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

async function ouvrir() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <PartagerClassement />
    </QueryClientProvider>,
  );
  await act(async () =>
    fireEvent.click(screen.getByRole("button", { name: /Partager mon classement/ })),
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  URL.createObjectURL = vi.fn(() => "blob:carte");
  URL.revokeObjectURL = vi.fn();
  api.chargerCarteClassement.mockResolvedValue(new Blob(["png"], { type: "image/png" }));
});

describe("PartagerClassement", () => {
  it("propose les vues, la case du club et le téléchargement", async () => {
    api.chargerMonClassement.mockResolvedValue(classement);
    await ouvrir();

    expect(await screen.findByRole("button", { name: "Mon club" })).toBeInTheDocument();
    expect(await screen.findByAltText("Aperçu de ta carte de classement")).toHaveAttribute(
      "src",
      "blob:carte",
    );
    expect(api.chargerCarteClassement).toHaveBeenLastCalledWith({
      niveau: "national",
      periode: "semestre",
      club: false,
    });
    expect(screen.getByRole("link", { name: /Télécharger/ })).toHaveAttribute("download");

    await act(async () => fireEvent.click(screen.getByRole("button", { name: "Ma DRE" })));
    await act(async () => fireEvent.click(screen.getByLabelText("Afficher le nom de mon club")));

    expect(api.chargerCarteClassement).toHaveBeenLastCalledWith({
      niveau: "dre",
      periode: "semestre",
      club: true,
    });
  });

  it("sans club ni semestre : ni vue club, ni case, seulement l'historique", async () => {
    api.chargerMonClassement.mockResolvedValue({
      ...classement,
      club: null,
      semestre_en_cours: null,
    });
    await ouvrir();

    expect(await screen.findByRole("button", { name: "Depuis le début" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Mon club" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ce semestre" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Afficher le nom de mon club")).not.toBeInTheDocument();
    await screen.findByAltText("Aperçu de ta carte de classement");
    expect(api.chargerCarteClassement).toHaveBeenLastCalledWith({
      niveau: "national",
      periode: "historique",
      club: false,
    });
  });

  it("montre le refus de l'API, par exemple sans point", async () => {
    api.chargerMonClassement.mockResolvedValue(classement);
    api.chargerCarteClassement.mockRejectedValue(
      new ErreurApi(404, "Tu n'es pas encore classé dans cette vue."),
    );
    await ouvrir();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Tu n'es pas encore classé dans cette vue.",
    );
  });
});
