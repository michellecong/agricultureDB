import { useState } from "react";
import Search from "./pages/Search";
import Upload from "./pages/Upload";
import Charts from "./pages/Charts";
import Papers from "./pages/Papers";
import "./App.css";

const TABS = [
  { id: "papers", label: "📚 Papers" },
  { id: "search", label: "🔍 Search" },
  { id: "upload", label: "📄 Upload PDF" },
  { id: "charts", label: "📊 Charts" },
];

export default function App() {
  const [tab, setTab] = useState("search");

  return (
    <div className="app">
      <header className="header">
        <h1>🌱 Agriculture Research DB</h1>
        <nav>
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "active" : ""}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {tab === "papers" && <Papers />}
        {tab === "search" && <Search />}
        {tab === "upload" && <Upload />}
        {tab === "charts" && <Charts />}
      </main>
    </div>
  );
}
