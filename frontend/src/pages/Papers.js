import { useState, useEffect } from "react";
import axios from "axios";

const API = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : "/api");

export default function Papers() {
  const [papers, setPapers] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [experiments, setExperiments] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/papers/`).then((r) => {
      setPapers(r.data);
      setLoading(false);
    });
  }, []);

  const toggle = async (paperId) => {
    if (expanded === paperId) {
      setExpanded(null);
      return;
    }
    setExpanded(paperId);
    if (!experiments[paperId]) {
      const res = await axios.get(`${API}/experiments/`, {
        params: { paper_id: paperId },
      });
      setExperiments((e) => ({ ...e, [paperId]: res.data }));
    }
  };

  if (loading) return <div className="empty">Loading...</div>;

  return (
    <div>
      <div className="card">
        <h2 style={{ fontSize: 16, marginBottom: 4 }}>All Papers</h2>
        <p style={{ fontSize: 13, color: "#888", marginBottom: 16 }}>
          {papers.length} papers in database
        </p>

        {papers.map((p) => (
          <div
            key={p.id}
            style={{
              borderBottom: "1px solid #f0f0f0",
              paddingBottom: 16,
              marginBottom: 16,
            }}
          >
            <div
              style={{
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
              onClick={() => toggle(p.id)}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                  {p.title}
                </div>
                <div style={{ fontSize: 12, color: "#888" }}>
                  {p.experiment_count} experiment groups
                  {p.journal && ` · ${p.journal}`}
                  {p.year && ` · ${p.year}`}
                </div>
              </div>
              <span style={{ fontSize: 18, color: "#aaa", marginLeft: 16 }}>
                {expanded === p.id ? "▲" : "▼"}
              </span>
            </div>

            {expanded === p.id && (
              <div style={{ marginTop: 16 }}>
                {!experiments[p.id] ? (
                  <div style={{ color: "#aaa", fontSize: 13 }}>Loading...</div>
                ) : experiments[p.id].length === 0 ? (
                  <div style={{ color: "#aaa", fontSize: 13 }}>
                    No results found
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Treatment</th>
                          <th>Mode</th>
                          <th>Conc.</th>
                          <th>Metric</th>
                          <th>Direction</th>
                          <th>Change %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {experiments[p.id].map((r, i) => (
                          <tr key={i}>
                            <td>{r.treatment}</td>
                            <td>{r.application_mode || "—"}</td>
                            <td>
                              {r.concentration
                                ? `${r.concentration} ${r.concentration_unit}`
                                : "—"}
                            </td>
                            <td>{r.metric || "—"}</td>
                            <td>
                              {r.direction && (
                                <span className={`badge ${r.direction}`}>
                                  {r.direction}
                                </span>
                              )}
                            </td>
                            <td>
                              {r.change_vs_control != null
                                ? `${r.change_vs_control > 0 ? "+" : ""}${r.change_vs_control}%`
                                : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
