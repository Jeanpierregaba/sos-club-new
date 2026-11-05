import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CompteARebours } from "./CompteARebours";

afterEach(() => vi.useRealTimers());

describe("CompteARebours", () => {
  it("découpe le temps restant en jours, heures, minutes et secondes", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2027-01-30T06:58:55Z"));
    render(<CompteARebours cible="2027-02-01T08:00:00Z" />);
    act(() => vi.advanceTimersByTime(0));

    // 2 jours, 1 heure, 1 minute et 5 secondes.
    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual([
      "02Jours",
      "01Heures",
      "01Minutes",
      "05Secondes",
    ]);
  });

  it("annonce le départ une fois la date passée", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2027-03-01T00:00:00Z"));
    render(<CompteARebours cible="2027-02-01T08:00:00Z" />);
    act(() => vi.advanceTimersByTime(0));

    expect(screen.getByText("C’est parti !")).toBeInTheDocument();
  });
});
