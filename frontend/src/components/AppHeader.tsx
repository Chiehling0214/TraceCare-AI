import { Link } from "../router";

export function AppHeader() {
  return (
    <header className="app-header">
      <div>
        <h1>TraceCare AI</h1>
        <p>可追溯臨床證據與實體警示決策支援系統</p>
      </div>
      <nav>
        <span className="tag">Synthetic Data</span>
        <span className="tag tag-outline">Competition Prototype</span>
        <Link href="/" className="nav-link">
          病人總覽
        </Link>
        <Link href="/demo-data" className="nav-link">
          Demo Data
        </Link>
      </nav>
    </header>
  );
}
