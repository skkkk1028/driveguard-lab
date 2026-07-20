import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the project foundation and safety notice", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: "DriveGuard Lab" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Foundation initialized")).toBeInTheDocument();
    expect(
      screen.getByText(/Do not use this software to control a real vehicle/i),
    ).toBeInTheDocument();
  });
});
