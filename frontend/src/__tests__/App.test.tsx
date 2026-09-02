import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../App";

describe("App", () => {
  it("renders the home page", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /prepare smarter/i })).toBeInTheDocument();
  });

  it("has accessible navigation", () => {
    render(<App />);
    const nav = screen.getByRole("navigation");
    expect(nav).toBeInTheDocument();
  });
});