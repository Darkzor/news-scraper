import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App", () => {
  it("renders the initial admin dashboard shell", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Scraping Dashboard" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Admin navigation" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Website" })).toBeEnabled();
  });

  it("shows the expected empty-state metrics", () => {
    render(<App />);

    expect(screen.getByText("Configured websites")).toBeInTheDocument();
    expect(screen.getByText("Active scrapes")).toBeInTheDocument();
    expect(screen.getByText("Saved articles")).toBeInTheDocument();
    expect(screen.getByText("Awaiting first scrape")).toBeInTheDocument();
  });
});
