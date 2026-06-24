const navigationItems = ["Websites", "Scrape Jobs", "Articles"];

const statusCards = [
  {
    label: "Configured websites",
    value: "0",
    detail: "Ready for source setup"
  },
  {
    label: "Active scrapes",
    value: "0",
    detail: "No jobs running"
  },
  {
    label: "Saved articles",
    value: "0",
    detail: "Awaiting first scrape"
  }
];

function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">News Scraper</p>
          <h1>Admin</h1>
        </div>
        <nav aria-label="Admin navigation">
          {navigationItems.map((item) => (
            <a href={`#${item.toLowerCase().replace(" ", "-")}`} key={item}>
              {item}
            </a>
          ))}
        </nav>
      </aside>

      <section className="workspace" aria-labelledby="dashboard-title">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Overview</p>
            <h2 id="dashboard-title">Scraping Dashboard</h2>
          </div>
          <button type="button">Add Website</button>
        </header>

        <div className="status-grid" aria-label="Dashboard status">
          {statusCards.map((card) => (
            <article className="status-card" key={card.label}>
              <p>{card.label}</p>
              <strong>{card.value}</strong>
              <span>{card.detail}</span>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;
