import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://localhost:8000/summarize";

const strategies = [
  { id: "first", index: "01", title: "Opening signal", copy: "Mulai dari kalimat pembuka berita." },
  { id: "highlight", index: "02", title: "AI highlight", copy: "Deteksi otomatis pusat perhatian teks." },
  { id: "last", index: "03", title: "Closing signal", copy: "Gunakan kalimat penutup sebagai premis." },
];

const styles = [
  { id: "precise", title: "Presisi", copy: "Faktual, rapat, minim interpretasi." },
  { id: "balanced", title: "Seimbang", copy: "Alami dengan kontrol yang stabil." },
  { id: "creative", title: "Ekspresif", copy: "Lebih lentur dalam penyusunan ulang." },
];

function Stat({ label, value, note }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>;
}

function App() {
  const [text, setText] = useState("");
  const [strategy, setStrategy] = useState("first");
  const [creativity, setCreativity] = useState("balanced");
  const [minLength, setMinLength] = useState(30);
  const [maxLength, setMaxLength] = useState(120);
  const [compression, setCompression] = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const summarize = async () => {
    if (!text.trim()) {
      setError("Masukkan teks berita sebelum menjalankan analisis.");
      return;
    }
    if (minLength >= maxLength) {
      setError("Panjang minimum harus lebih kecil dari maksimum.");
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, min_length: minLength, max_length: maxLength, creativity, premise_strategy: strategy, compression_ratio: compression }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Server gagal memproses teks.");
      setResult(data);
    } catch (requestError) {
      setError(requestError.message.includes("fetch") ? "Backend belum terhubung. Jalankan FastAPI di localhost:8000." : requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setText(""); setResult(null); setError(""); setCopied(false); };
  const copySummary = async () => {
    if (!result?.summary) return;
    await navigator.clipboard.writeText(result.summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" /><div className="ambient ambient-two" />
      <header className="topbar">
        <a className="brand" href="/" aria-label="Signal home"><span className="brand-mark">//</span><span>SIGNAL<span className="brand-muted">.LAB</span></span></a>
        <div className="top-meta"><span className="status-dot" /> MODEL ONLINE <span className="meta-separator">/</span> HYBRID R3.1</div>
      </header>

      <main>
        <section className="hero reveal">
          <div className="eyebrow"><span className="eyebrow-line" /> INTELLIGENCE WORKBENCH / 01</div>
          <h1>Find the <em>signal</em><br />inside the noise.</h1>
          <p className="hero-copy">Mesin ringkas berita hibrida untuk menemukan inti, menguji relevansi, lalu menulis ulang dengan alur yang tetap manusiawi.</p>
        </section>

        <section className="workspace reveal delay-one">
          <div className="workspace-head"><div><span className="section-kicker">INPUT / 01</span><h2>Source material</h2></div><span className="char-count">{text.length.toLocaleString("id-ID")} chars</span></div>
          <textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Tempel teks berita di sini..." aria-label="Teks berita" />
          <div className="input-footer"><span>Indonesian language model</span><span>Up to 800 sentences</span></div>
        </section>

        <section className="control-grid reveal delay-two">
          <div className="control-main">
            <div className="section-heading"><span className="section-kicker">METHOD / 02</span><h2>Choose your lens</h2><p>Premis menentukan dari mana sistem membaca cerita.</p></div>
            <div className="strategy-list">{strategies.map((item) => <button key={item.id} className={`strategy ${strategy === item.id ? "selected" : ""}`} onClick={() => setStrategy(item.id)}><span className="strategy-index">{item.index}</span><span><strong>{item.title}</strong><small>{item.copy}</small></span><span className="radio-mark" /></button>)}</div>
          </div>
          <aside className="settings-panel">
            <div className="section-heading"><span className="section-kicker">TUNING / 03</span><h2>Fine controls</h2></div>
            <label className="range-label"><span>Compression ratio</span><strong>{Math.round(compression * 100)}%</strong></label>
            <input type="range" min="0.25" max="1" step="0.25" value={compression} onChange={(event) => setCompression(Number(event.target.value))} />
            <label className="range-label"><span>Output window</span><strong>{minLength}—{maxLength}</strong></label>
            <div className="dual-range"><input type="range" min="10" max="180" step="5" value={minLength} onChange={(event) => setMinLength(Number(event.target.value))} /><input type="range" min="40" max="400" step="5" value={maxLength} onChange={(event) => setMaxLength(Number(event.target.value))} /></div>
            <div className="style-switch"><span>Writing mode</span><div>{styles.map((item) => <button key={item.id} className={creativity === item.id ? "active" : ""} onClick={() => setCreativity(item.id)}>{item.title}</button>)}</div></div>
          </aside>
        </section>

        <div className="action-row reveal delay-three"><button className="primary-action" onClick={summarize} disabled={loading}><span>{loading ? "ANALYZING..." : "RUN ANALYSIS"}</span><b>{loading ? "..." : "↗"}</b></button><button className="ghost-action" onClick={reset}>CLEAR</button>{error && <p className="error-message">{error}</p>}</div>

        {loading && <div className="processing"><span className="loader" /><span>IndoBERT is tracing relevance<span className="blink">...</span></span><small>Entailment filter / abstractive rewrite</small></div>}

        {result && <section className="result-section reveal">
          <div className="result-heading"><div><span className="section-kicker">OUTPUT / 04</span><h2>Signal extracted.</h2></div><button className="copy-button" onClick={copySummary}>{copied ? "COPIED" : "COPY SUMMARY"} <span>↗</span></button></div>
          <article className="summary-card"><span className="quote-mark">“</span><p>{result.summary}</p><footer><span>ABSTRACTIVE REWRITE / {result.output_word_count} WORDS</span><span className="confidence">CONFIDENCE {Math.round(result.avg_confidence * 100)}%</span></footer></article>
          <div className="stats-grid"><Stat label="Source sentences" value={result.total_sentences} note="in original text" /><Stat label="Selected signals" value={result.entailed_count} note="passed IndoBERT" /><Stat label="Selection rate" value={`${Math.round((result.entailed_count / Math.max(result.total_sentences, 1)) * 100)}%`} note="of source" /><Stat label="Avg confidence" value={`${Math.round(result.avg_confidence * 100)}%`} note="relevance score" /></div>
          <details className="evidence"><summary>View evidence trail <span>+</span></summary><div className="evidence-content"><div className="premise"><span className="section-kicker">PRIMARY PREMISE</span><p>{result.premise}</p></div>{result.entailment_details.map((detail) => <div className="evidence-row" key={`${detail.position}-${detail.text}`}><span>#{String(detail.position).padStart(2, "0")}</span><p>{detail.text}</p><strong>{Math.round(detail.confidence * 100)}%</strong></div>)}</div></details>
        </section>}
      </main>
      <footer className="page-footer"><span>SIGNAL.LAB / HYBRID SUMMARIZATION SYSTEM</span><span>BUILT FOR CLARITY, NOT NOISE</span></footer>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);