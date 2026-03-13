import { useState } from "react";
import axios from "axios";

const API = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : "/api");

export default function Search() {
  const [filters, setFilters] = useState({
    species: "",
    treatment: "",
    metric: "",
    direction: "",
  });
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v),
      );
      const res = await axios.get(`${API}/experiments/`, { params });
      setRows(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const set = (k, v) => setFilters((f) => ({ ...f, [k]: v }));

  return (
    <div>
      <div className="card">
        <h2 style={{ marginBottom: 16, fontSize: 16 }}>Search Experiments</h2>
        <div className="filters">
          <input
            placeholder="Species (e.g. tomato)"
            value={filters.species}
            onChange={(e) => set("species", e.target.value)}
          />
          <input
            placeholder="Treatment (e.g. chitosan)"
            value={filters.treatment}
            onChange={(e) => set("treatment", e.target.value)}
          />
          <input
            placeholder="Metric (e.g. SPAD)"
            value={filters.metric}
            onChange={(e) => set("metric", e.target.value)}
          />
          <select
            value={filters.direction}
            onChange={(e) => set("direction", e.target.value)}
          >
            <option value="">All directions</option>
            <option value="increase">Increase</option>
            <option value="decrease">Decrease</option>
            <option value="no_change">No change</option>
          </select>
          <button className="btn" onClick={search}>
            Search
          </button>
          <button
            className="btn secondary"
            onClick={() => {
              setFilters({
                species: "",
                treatment: "",
                metric: "",
                direction: "",
              });
              setRows([]);
            }}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="card">
        {loading && <div className="empty">Loading...</div>}
        {!loading && rows.length === 0 && (
          <div className="empty">Enter filters and click Search</div>
        )}
        {!loading && rows.length > 0 && (
          <>
            <p style={{ marginBottom: 12, fontSize: 13, color: "#666" }}>
              {rows.length} results
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Species</th>
                    <th>Treatment</th>
                    <th>Mode</th>
                    <th>Conc.</th>
                    <th>Metric</th>
                    <th>Direction</th>
                    <th>Change %</th>
                    <th>Paper</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      <td>
                        <i>{r.species}</i>
                      </td>
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
                      <td
                        style={{
                          maxWidth: 200,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                        title={r.paper_title}
                      >
                        {r.paper_title?.slice(0, 40)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
