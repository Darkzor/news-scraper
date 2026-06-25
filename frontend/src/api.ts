export type Website = {
  id: number;
  name: string;
  base_url: string;
  enabled: boolean;
  discovery_selector: string;
  title_selector: string | null;
  description_selector: string | null;
  content_selector: string | null;
  target_topics: string | null;
  scrape_frequency_minutes: number | null;
};

export type Article = {
  id: number;
  website_id: number;
  url: string;
  title: string;
  description: string;
  content: string;
};

export type ScrapeJob = {
  id: number;
  website_id: number;
  status: string;
  saved_articles: number;
  skipped_articles: number;
  failure: string | null;
};

export type WebsitePayload = Omit<Website, "id">;
export type SelectorSuggestion = Pick<
  Website,
  "discovery_selector" | "title_selector" | "description_selector" | "content_selector"
>;

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (response.status === 204) {
    return null as T;
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export const api = {
  listWebsites: () => request<Website[]>("/websites"),
  createWebsite: (payload: WebsitePayload) =>
    request<Website>("/websites", { method: "POST", body: JSON.stringify(payload) }),
  updateWebsite: (id: number, payload: Partial<WebsitePayload>) =>
    request<Website>(`/websites/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteWebsite: (id: number) => request<void>(`/websites/${id}`, { method: "DELETE" }),
  suggestSelectors: (base_url: string) =>
    request<SelectorSuggestion>("/selector-suggestions", {
      method: "POST",
      body: JSON.stringify({ base_url })
    }),
  triggerScrape: (id: number) => request<ScrapeJob>(`/websites/${id}/scrape`, { method: "POST" }),
  listScrapeJobs: () => request<ScrapeJob[]>("/scrape-jobs"),
  listArticles: () => request<Article[]>("/articles")
};
