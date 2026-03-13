import { useState, useRef, useEffect } from "react";
import axios from "axios";

const API = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === "development" ? "http://localhost:8000/api" : "/api");

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [queueStatus, setQueueStatus] = useState(null);
  const [lastError, setLastError] = useState(null);
  const inputRef = useRef();

  const onFile = (e) => setFiles(Array.from(e.target.files || []));

  useEffect(() => {
    const check = async () => {
      try {
        const res = await axios.get(`${API}/upload/status`);
        setQueueStatus(res.data);
        setLastError(res.data?.last_error ?? null);
      } catch {
        setQueueStatus(null);
      }
    };
    check();
    const id = setInterval(check, 2000);
    return () => clearInterval(id);
  }, []);

  const upload = async () => {
    if (!files.length) return;
    setLoading(true);
    setStatus(null);
    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      const res = await axios.post(`${API}/upload/`, form);
      setStatus({ type: "success", msg: `✅ ${res.data.message}` });
      setFiles([]);
      if (inputRef.current) inputRef.current.value = "";
    } catch (e) {
      setStatus({
        type: "error",
        msg: `❌ ${e.response?.data?.detail || e.message}`,
      });
    }
    setLoading(false);
  };

  const busy = (queueStatus?.processing_count ?? 0) > 0 || (queueStatus?.queue_length ?? 0) > 0;

  return (
    <div>
      <div className="card">
        <h2 style={{ marginBottom: 16, fontSize: 16 }}>Upload Research Papers</h2>
        <div
          className="upload-zone"
          onClick={() => !loading && inputRef.current?.click()}
          style={{
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          <div style={{ fontSize: 48 }}>📄</div>
          <p>
            {files.length > 0
              ? `${files.length} file(s) selected`
              : "Click to select PDF files (multiple allowed)"}
          </p>
          <p>The pipeline will extract experimental data (max 2 processed at a time)</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            multiple
            style={{ display: "none" }}
            onChange={onFile}
            disabled={loading}
          />
        </div>

        {files.length > 0 && (
          <div style={{ marginTop: 16, display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, flex: 1 }}>
              {files.map((f, i) => (
                <span key={i} style={{ fontSize: 13, padding: "4px 8px", background: "#f0f4f8", borderRadius: 4 }}>
                  📎 {f.name}
                </span>
              ))}
            </div>
            <button className="btn" onClick={upload} disabled={loading}>
              {loading ? "Uploading..." : `Upload ${files.length} file(s)`}
            </button>
          </div>
        )}

        {queueStatus && (queueStatus.queue_length > 0 || queueStatus.processing_count > 0) && (
          <div className="status info" style={{ marginTop: 16 }}>
            <strong>Queue:</strong> {queueStatus.queue_length} waiting · {queueStatus.processing_count} processing
            {queueStatus.processing?.length > 0 && (
              <span style={{ marginLeft: 8 }}>({queueStatus.processing.join(", ")})</span>
            )}
          </div>
        )}

        {queueStatus?.completed?.length > 0 && (
          <div style={{ marginTop: 12, fontSize: 13 }}>
            <strong>Recent:</strong>
            <ul style={{ margin: "4px 0 0 0", paddingLeft: 20, maxHeight: 120, overflow: "auto" }}>
              {queueStatus.completed.slice(-10).reverse().map((c, i) => (
                <li key={i} style={{ color: c.status === "ok" ? "#40916c" : "#e63946" }}>
                  {c.filename} — {c.status === "ok" ? "✓" : `✗ ${c.error || ""}`}
                </li>
              ))}
            </ul>
          </div>
        )}

        {status && <div className={`status ${status.type}`} style={{ marginTop: 12 }}>{status.msg}</div>}
        {lastError && status?.type !== "success" && (
          <div className="status error" style={{ marginTop: 8 }}>
            ⚠️ Last error: {lastError}
          </div>
        )}

        {status?.type === "success" && (
          <div className="status info" style={{ marginTop: 8 }}>
            ℹ️ Files are queued. View results in the Search tab as they complete.
          </div>
        )}
      </div>
    </div>
  );
}
