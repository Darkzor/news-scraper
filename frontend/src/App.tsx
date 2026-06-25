import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, Article, ScrapeJob, Website, WebsitePayload } from "./api";
import "./styles.css";

type View = "websites" | "articles";

const emptyForm = {
  name: "",
  base_url: "",
  enabled: true,
  discovery_selector: "a",
  title_selector: "",
  description_selector: "",
  content_selector: "",
  scrape_frequency_minutes: ""
};

function toPayload(form: typeof emptyForm): WebsitePayload {
  return {
    name: form.name,
    base_url: form.base_url,
    enabled: form.enabled,
    discovery_selector: form.discovery_selector || "a",
    title_selector: form.title_selector || null,
    description_selector: form.description_selector || null,
    content_selector: form.content_selector || null,
    scrape_frequency_minutes: form.scrape_frequency_minutes
      ? Number(form.scrape_frequency_minutes)
      : null
  };
}

function App() {
  const [view, setView] = useState<View>("websites");
  const [websites, setWebsites] = useState<Website[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [editing, setEditing] = useState<Website | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [inferringSelectors, setInferringSelectors] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const [nextWebsites, nextArticles, nextJobs] = await Promise.all([
        api.listWebsites(),
        api.listArticles(),
        api.listScrapeJobs()
      ]);
      setWebsites(Array.isArray(nextWebsites) ? nextWebsites : []);
      setArticles(Array.isArray(nextArticles) ? nextArticles : []);
      setJobs(Array.isArray(nextJobs) ? nextJobs : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const stats = useMemo(
    () => [
      { label: "Configured websites", value: websites.length },
      { label: "Scrape jobs", value: jobs.length },
      { label: "Saved articles", value: articles.length }
    ],
    [websites.length, jobs.length, articles.length]
  );

  function startCreate() {
    setEditing(null);
    setForm(emptyForm);
  }

  function startEdit(website: Website) {
    setEditing(website);
    setForm({
      name: website.name,
      base_url: website.base_url,
      enabled: website.enabled,
      discovery_selector: website.discovery_selector,
      title_selector: website.title_selector || "",
      description_selector: website.description_selector || "",
      content_selector: website.content_selector || "",
      scrape_frequency_minutes: website.scrape_frequency_minutes?.toString() || ""
    });
  }

  async function saveWebsite(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      if (editing) {
        await api.updateWebsite(editing.id, toPayload(form));
        setMessage("Website updated.");
      } else {
        await api.createWebsite(toPayload(form));
        setMessage("Website created.");
      }
      startCreate();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  async function deleteWebsite(id: number) {
    setError("");
    setMessage("");
    try {
      await api.deleteWebsite(id);
      setMessage("Website deleted.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function inferSelectors() {
    if (!form.base_url) return;
    setError("");
    setMessage("");
    setInferringSelectors(true);
    try {
      const suggestion = await api.suggestSelectors(form.base_url);
      setForm((current) => ({
        ...current,
        discovery_selector: suggestion.discovery_selector,
        title_selector: suggestion.title_selector || "",
        description_selector: suggestion.description_selector || "",
        content_selector: suggestion.content_selector || ""
      }));
      setMessage("Selectors inferred. Review and save.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Selector inference failed");
    } finally {
      setInferringSelectors(false);
    }
  }

  async function triggerScrape(id: number) {
    setError("");
    setMessage("");
    try {
      const job = await api.triggerScrape(id);
      setJobs((current) => [job, ...current]);
      setMessage(`Scrape job ${job.id} ${job.status}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scrape failed");
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">News Scraper</p>
          <h1>Admin</h1>
        </div>
        <nav aria-label="Admin navigation">
          <button className={view === "websites" ? "active" : ""} onClick={() => setView("websites")}>
            Websites
          </button>
          <button className={view === "articles" ? "active" : ""} onClick={() => setView("articles")}>
            Articles
          </button>
        </nav>
      </aside>

      <section className="workspace" aria-labelledby="dashboard-title">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Overview</p>
            <h2 id="dashboard-title">Scraping Dashboard</h2>
          </div>
          <button type="button" onClick={startCreate}>Add Website</button>
        </header>

        <div className="status-grid" aria-label="Dashboard status">
          {stats.map((card) => (
            <article className="status-card" key={card.label}>
              <p>{card.label}</p>
              <strong>{card.value}</strong>
            </article>
          ))}
        </div>

        {loading ? <p className="notice">Loading</p> : null}
        {error ? <p className="notice error">{error}</p> : null}
        {message ? <p className="notice success">{message}</p> : null}

        {view === "websites" ? (
          <div className="split">
            <section className="panel" aria-label="Website form">
              <h3>{editing ? "Edit Website" : "Create Website"}</h3>
              <form onSubmit={saveWebsite}>
                <label>
                  Name
                  <input
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                    required
                  />
                </label>
                <label>
                  Base URL
                  <input
                    value={form.base_url}
                    onChange={(event) => setForm({ ...form, base_url: event.target.value })}
                    required
                  />
                </label>
                <label>
                  Discovery selector
                  <input
                    value={form.discovery_selector}
                    onChange={(event) => setForm({ ...form, discovery_selector: event.target.value })}
                  />
                </label>
                <label>
                  Title selector
                  <input
                    value={form.title_selector}
                    onChange={(event) => setForm({ ...form, title_selector: event.target.value })}
                  />
                </label>
                <label>
                  Description selector
                  <input
                    value={form.description_selector}
                    onChange={(event) => setForm({ ...form, description_selector: event.target.value })}
                  />
                </label>
                <label>
                  Content selector
                  <input
                    value={form.content_selector}
                    onChange={(event) => setForm({ ...form, content_selector: event.target.value })}
                  />
                </label>
                <label>
                  Scrape frequency minutes
                  <input
                    min="1"
                    type="number"
                    value={form.scrape_frequency_minutes}
                    onChange={(event) => setForm({ ...form, scrape_frequency_minutes: event.target.value })}
                  />
                </label>
                <label className="toggle">
                  <input
                    checked={form.enabled}
                    type="checkbox"
                    onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
                  />
                  Enabled
                </label>
                <div className="form-actions">
                  <button
                    disabled={!form.base_url || inferringSelectors}
                    type="button"
                    onClick={inferSelectors}
                  >
                    {inferringSelectors ? "Inferring selectors" : "Infer selectors"}
                  </button>
                  <button type="submit">Save</button>
                </div>
              </form>
            </section>

            <section className="panel" aria-label="Website list">
              <h3>Websites</h3>
              {websites.length === 0 ? <p className="empty">No websites configured.</p> : null}
              {websites.map((website) => (
                <article className="row" key={website.id}>
                  <div>
                    <strong>{website.name}</strong>
                    <span>{website.base_url}</span>
                    <small>{website.enabled ? "Enabled" : "Disabled"}</small>
                  </div>
                  <div className="actions">
                    <button type="button" onClick={() => triggerScrape(website.id)}>Scrape</button>
                    <button type="button" onClick={() => startEdit(website)}>Edit</button>
                    <button type="button" onClick={() => deleteWebsite(website.id)}>Delete</button>
                  </div>
                </article>
              ))}

              <h3>Scrape Jobs</h3>
              {jobs.length === 0 ? <p className="empty">No scrape jobs yet.</p> : null}
              {jobs.map((job) => (
                <article className="row compact" key={job.id}>
                  <strong>Job {job.id}</strong>
                  <span>{job.status}</span>
                  <span>{job.saved_articles} saved</span>
                  <span>{job.failure || "No failure"}</span>
                </article>
              ))}
            </section>
          </div>
        ) : (
          <div className="split">
            <section className="panel" aria-label="Article list">
              <h3>Articles</h3>
              {articles.length === 0 ? <p className="empty">No articles extracted.</p> : null}
              {articles.map((article) => (
                <button className="article-button" key={article.id} onClick={() => setSelectedArticle(article)}>
                  <strong>{article.title}</strong>
                  <span>{article.description || article.url}</span>
                </button>
              ))}
            </section>
            <section className="panel article-detail" aria-label="Article detail">
              <h3>{selectedArticle?.title || "Article Detail"}</h3>
              {selectedArticle ? (
                <>
                  <p>{selectedArticle.description}</p>
                  <a href={selectedArticle.url}>{selectedArticle.url}</a>
                  <pre>{selectedArticle.content}</pre>
                </>
              ) : (
                <p className="empty">Select an article.</p>
              )}
            </section>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
