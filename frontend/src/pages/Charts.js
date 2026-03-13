import { useState, useEffect } from "react";
import axios from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

const API = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : "/api");
const COLORS = {
  increase: "#40916c",
  decrease: "#e63946",
  no_change: "#adb5bd",
};

export default function Charts() {
  const [treatment, setTreatment] = useState("chitosan");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/experiments/`, {
        params: { treatment, direction: "increase" },
      });
      // Aggregate: average change_vs_control per metric
      const map = {};
      for (const r of res.data) {
        if (r.change_vs_control == null || !r.metric) continue;
        if (!map[r.metric])
          map[r.metric] = { values: [], direction: r.direction };
        map[r.metric].values.push(r.change_vs_control);
      }
      const agg = Object.entries(map)
        .map(([metric, { values, direction }]) => ({
          metric: metric.length > 20 ? metric.slice(0, 18) + "…" : metric,
          avg:
            Math.round(
              (values.reduce((a, b) => a + b, 0) / values.length) * 10,
            ) / 10,
          direction,
          n: values.length,
        }))
        .sort((a, b) => b.avg - a.avg)
        .slice(0, 15);
      setData(agg);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="card">
        <h2 style={{ marginBottom: 16, fontSize: 16 }}>
          Effect Size by Metric
        </h2>
        <div className="filters">
          <input
            placeholder="Treatment"
            value={treatment}
            onChange={(e) => setTreatment(e.target.value)}
          />
          <button className="btn" onClick={load}>
            Update
          </button>
        </div>

        {loading && <div className="empty">Loading...</div>}
        {!loading && data.length === 0 && <div className="empty">No data</div>}
        {!loading && data.length > 0 && (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={data}
              margin={{ top: 10, right: 20, left: 0, bottom: 80 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="metric"
                angle={-40}
                textAnchor="end"
                tick={{ fontSize: 12 }}
                interval={0}
              />
              <YAxis
                label={{
                  value: "Avg change %",
                  angle: -90,
                  position: "insideLeft",
                  fontSize: 12,
                }}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(v, n, p) => [
                  `${v}% (n=${p.payload.n})`,
                  "Avg change",
                ]}
              />
              <Bar dataKey="avg" radius={[4, 4, 0, 0]}>
                {data.map((d, i) => (
                  <Cell
                    key={i}
                    fill={d.avg >= 0 ? COLORS.increase : COLORS.decrease}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
