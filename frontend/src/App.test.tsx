import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const website = {
  id: 1,
  name: "Example News",
  base_url: "https://example.test/",
  enabled: true,
  discovery_selector: "a",
  title_selector: null,
  description_selector: null,
  content_selector: null,
  scrape_frequency_minutes: 60
};

beforeEach(() => {
  globalThis.fetch = vi.fn(async (input, init = {}) => {
    const url = input.toString();
    if (url === "/api/websites" && !init.method) return Response.json([website]);
    if (url === "/api/websites" && init.method === "POST") {
      return Response.json({ ...website, id: 2, name: "Added News" }, { status: 201 });
    }
    if (url === "/api/websites/1" && init.method === "PATCH") return Response.json(website);
    if (url === "/api/websites/1" && init.method === "DELETE") return new Response(null, { status: 204 });
    if (url === "/api/selector-suggestions" && init.method === "POST") {
      return Response.json({
        discovery_selector: "main a.article-link",
        title_selector: "h1",
        description_selector: "meta[name='description']",
        content_selector: "article"
      });
    }
    if (url === "/api/websites/1/scrape" && init.method === "POST") {
      return Response.json({ id: 7, website_id: 1, status: "succeeded", saved_articles: 1, failure: null });
    }
    if (url === "/api/scrape-jobs" && !init.method) {
      return Response.json([{ id: 5, website_id: 1, status: "failed", saved_articles: 0, failure: "Timeout" }]);
    }
    if (url === "/api/articles" && !init.method) {
      return Response.json([
        {
          id: 10,
          website_id: 1,
          title: "Article title",
          description: "Article summary",
          content: "Article content",
          url: "https://example.test/news/alpha"
        }
      ]);
    }
    return Response.json({ detail: "Not found" }, { status: 404 });
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("lists websites and triggers a scrape", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByText("Example News")).toBeInTheDocument();
    expect(await screen.findByText("Timeout")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Scrape" }));

    expect(await screen.findByText("Scrape job 7 succeeded.")).toBeInTheDocument();
  });

  it("creates a website through the form", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.clear(await screen.findByLabelText("Name"));
    await user.type(screen.getByLabelText("Name"), "Added News");
    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "https://added.test");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/websites",
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  it("infers selectors and fills the website form", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText("Base URL"), "https://example.test");
    await user.click(screen.getByRole("button", { name: "Infer selectors" }));

    expect(await screen.findByText("Selectors inferred. Review and save.")).toBeInTheDocument();
    expect(screen.getByLabelText("Discovery selector")).toHaveValue("main a.article-link");
    expect(screen.getByLabelText("Title selector")).toHaveValue("h1");
    expect(screen.getByLabelText("Description selector")).toHaveValue("meta[name='description']");
    expect(screen.getByLabelText("Content selector")).toHaveValue("article");
  });

  it("shows selector inference errors without clearing form values", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByLabelText("Base URL"), "https://example.test");
    await user.type(screen.getByLabelText("Title selector"), "h1.current");
    vi.mocked(globalThis.fetch).mockImplementationOnce(async () =>
      Response.json({ detail: "content selector did not extract text" }, { status: 422 })
    );

    await user.click(screen.getByRole("button", { name: "Infer selectors" }));

    expect(await screen.findByText("content selector did not extract text")).toBeInTheDocument();
    expect(screen.getByLabelText("Title selector")).toHaveValue("h1.current");
  });

  it("shows article detail content", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(await screen.findByRole("button", { name: "Articles" }));
    await user.click(await screen.findByText("Article title"));

    expect(screen.getByText("Article content")).toBeInTheDocument();
  });
});
