# ========================================================================
# STREAMLIT FRONTEND — HYBRID SUMMARIZATION SYSTEM
# Backend: FastAPI (IndoBERT RTE + IndoT5 Abstractive)
# ========================================================================

import streamlit as st
import requests

# ========================================================================
# CONFIG
# ========================================================================
API_URL = "http://localhost:8000/summarize"

st.set_page_config(
    page_title="Sistem Ringkasan Berita Otomatis",
    page_icon="📰",
    layout="wide",
)

# ========================================================================
# CUSTOM CSS (LIGHT THEME)
# ========================================================================
st.markdown("""
<style>
/* ---- Global ---- */
.main { background-color: #ffffff; }
h1, h2, h3, h4, p, span, label { color: #1e293b !important; }
textarea { font-size: 16px !important; background-color: #f8fafc !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }

/* ---- Tombol utama ---- */
.stButton>button {
    background: linear-gradient(135deg, #FF4B4B, #c0392b);
    color: white !important;
    border: none;
    border-radius: 10px;
    height: 3.2em;
    font-weight: 600;
    font-size: 15px;
    transition: all 0.2s;
    box-shadow: 0 4px 6px rgba(255,75,75,0.2);
}
.stButton>button:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 6px 10px rgba(255,75,75,0.3); }

/* ---- Kotak statistik ---- */
.stat-box {
    background-color: #f8fafc;
    padding: 18px 12px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.stat-title {
    font-size: 11px;
    color: #64748b !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 6px;
    font-weight: 600;
}
.stat-value {
    font-size: 26px;
    font-weight: 700;
    color: #0f172a !important;
}
.stat-sub {
    font-size: 11px;
    color: #94a3b8 !important;
    margin-top: 3px;
}

/* ---- Badge confidence ---- */
.badge-high  { color: #16a34a; font-weight: 600; }
.badge-mid   { color: #d97706; font-weight: 600; }
.badge-low   { color: #dc2626; font-weight: 600; }

/* ---- Kotak ringkasan output ---- */
.summary-box {
    background: #ffffff;
    border-left: 5px solid #FF4B4B;
    border-top: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 20px 24px;
    font-size: 17px;
    line-height: 1.75;
    color: #1e293b !important;
    margin-top: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background-color: #f1f5f9;
    border-right: 1px solid #e2e8f0;
}
/* Memperbaiki warna teks di expander */
.streamlit-expanderHeader { color: #1e293b !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ========================================================================
# HELPER: badge confidence
# ========================================================================
def confidence_badge(score: float) -> str:
    if score >= 0.75:
        return f'<span class="badge-high">● Tinggi ({score:.2f})</span>'
    elif score >= 0.50:
        return f'<span class="badge-mid">● Sedang ({score:.2f})</span>'
    else:
        return f'<span class="badge-low">● Rendah ({score:.2f})</span>'


# ========================================================================
# SIDEBAR — PENGATURAN RINGKASAN
# ========================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/news.png", width=64)
    st.title("Pengaturan Ringkasan")
    st.caption("Sesuaikan parameter hasil ringkasan teks.")
    st.divider()

    # --- Strategi Premis ---
    st.subheader("🎯 Strategi Premis")
    strategy_option = st.radio(
        "Pilih kalimat acuan utama:",
        options=["🔵 Kalimat Pertama", "🟣 Kalimat Terakhir", "🟡 Highlight Otomatis (AI)"],
        help="Menentukan kalimat mana yang menjadi fokus utama untuk seleksi relevansi."
    )
    
    strategy_map = {
        "🔵 Kalimat Pertama": "first",
        "🟣 Kalimat Terakhir": "last",
        "🟡 Highlight Otomatis (AI)": "highlight"
    }
    selected_strategy = strategy_map[strategy_option]

    st.divider()

    # --- Panjang Ringkasan ---
    st.subheader("📏 Panjang Ringkasan (Token)")
    length_range = st.slider(
        "Rentang minimum & maksimum:",
        min_value=10, 
        max_value=400, 
        value=(30, 120), 
        step=5,
        help="Geser titik kiri untuk minimal kata, dan titik kanan untuk maksimal kata."
    )
    min_len, max_len = length_range
    
    if min_len >= max_len:
        st.error("⚠️ Panjang minimum harus lebih kecil dari maksimum!")

    st.divider()

    # --- Gaya Bahasa ---
    st.subheader("🖊️ Gaya Penulisan")
    style_option = st.select_slider(
        "Pilih kreativitas AI:",
        options=["Tepat & Faktual", "Seimbang", "Lebih Bervariasi"],
        value="Seimbang"
    )

    style_map = {
        "Tepat & Faktual":  "precise",
        "Seimbang":         "balanced",
        "Lebih Bervariasi": "creative",
    }
    creativity_value = style_map[style_option]

    st.divider()

    # --- Rasio Kompresi ---
    st.subheader("🗜️ Rasio Kompresi")
    compression_ratio = st.slider(
        "Persentase kalimat relevan yang dipakai:",
        min_value=0.25, 
        max_value=1.0, 
        value=1.0, 
        step=0.25,
        help="1.0 = pakai semua kalimat yang lolos seleksi. 0.5 = pakai 50% terbaik."
    )


# ========================================================================
# HEADER
# ========================================================================
st.title("📰 Sistem Ringkasan Berita Otomatis")
st.markdown(
    "Sistem ini membaca teks berita, memilih kalimat-kalimat paling relevan berdasarkan strategi premis, "
    "lalu merangkumnya menjadi lebih padat menggunakan AI."
)

with st.expander("ℹ️ Bagaimana cara kerjanya?", expanded=False):
    st.markdown("""
    <div style="font-size:17px; line-height:1.9; color:#334155;">
    <ol>
        <li><b>Identifikasi Kalimat Utama (Premis)</b> — Sistem menentukan kalimat acuan sesuai strategi yang dipilih.</li>
        <li><b>Seleksi Kalimat Relevan</b> — Model AI (IndoBERT) menyaring kalimat lain yang maknanya memiliki keterkaitan dengan premis.</li>
        <li><b>Penggabungan</b> — Kalimat-kalimat yang lolos disusun kembali.</li>
        <li><b>Penulisan Ulang</b> — IndoT5 menulis ulang draf gabungan menjadi ringkasan bahasa alami yang mengalir.</li>
        <li><b>Pembersihan</b> — Teks di-filter dari pengulangan (hallusinasi) yang sering terjadi pada AI.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ========================================================================
# INPUT
# ========================================================================
st.markdown("<b>📝 Tempel teks berita di sini</b>", unsafe_allow_html=True)

input_text = st.text_area(
    label="",
    height=280,
    placeholder="Contoh: Jakarta, 13 April 2026 — Pemerintah Indonesia..."
)

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    run_btn = st.button("🚀 Ringkas Sekarang!", use_container_width=True)
with col_btn2:
    if st.button("🔄 Bersihkan"):
        st.rerun()

# ========================================================================
# PROSES
# ========================================================================
if run_btn:
    if not input_text.strip():
        st.warning("⚠️ Teks belum diisi. Silakan tempel berita yang ingin diringkas.")
        st.stop()

    if min_len >= max_len:
        st.error("⚠️ Periksa pengaturan di sebelah kiri: panjang minimum harus lebih kecil dari maksimum.")
        st.stop()

    with st.status("⏳ Sedang memproses berita...", expanded=True) as status:
        st.write(f"🔍 Menjalankan strategi premis: **{strategy_option.split(' ', 1)[1]}**...")
        try:
            payload = {
                "text": input_text,
                "min_length": min_len,
                "max_length": max_len,
                "creativity": creativity_value,
                "premise_strategy": selected_strategy,
                "compression_ratio": compression_ratio
            }
            response = requests.post(API_URL, json=payload, timeout=600)

            if response.status_code == 200:
                data = response.json()
                st.write("✅ Seleksi relevansi kalimat (IndoBERT) selesai.")
                st.write("✅ Penulisan ulang abstraktif (IndoT5) selesai.")
                status.update(label="✅ Ringkasan siap!", state="complete", expanded=False)
            else:
                status.update(label="❌ Gagal memproses", state="error")
                detail = response.json().get("detail", response.text)
                st.error(f"Kesalahan dari server ({response.status_code}): {detail}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error(
                "❌ Tidak dapat terhubung ke server. "
                "Pastikan backend FastAPI sudah berjalan di `localhost:8000`."
            )
            st.stop()
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")
            st.stop()

    # ====================================================================
    # OUTPUT
    # ====================================================================
    st.divider()

    # --- Ringkasan utama ---
    st.subheader("✨ Hasil Ringkasan")
    st.markdown(f'<div class="summary-box">{data["summary"]}</div>', unsafe_allow_html=True)

    st.caption(
        f"Strategi: **{strategy_option.split(' ', 1)[1]}** &nbsp;|&nbsp; "
        f"Gaya: **{style_option}** &nbsp;|&nbsp; "
        f"Jumlah kata output: **{data.get('output_word_count', 0)}**"
    )

    st.divider()

    # --- Statistik ---
    st.subheader("📊 Statistik Proses")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-title">Total Kalimat Berita</div>'
            f'<div class="stat-value">{data.get("total_sentences", 0)}</div>'
            f'<div class="stat-sub">kalimat dalam teks asli</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-title">Kalimat Digunakan</div>'
            f'<div class="stat-value">{data.get("entailed_count", 0)}</div>'
            f'<div class="stat-sub">lolos seleksi relevansi</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        total_sents = data.get("total_sentences", 1)
        ratio = round((data.get("entailed_count", 0) / (total_sents if total_sents > 0 else 1)) * 100, 1)
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-title">Tingkat Seleksi</div>'
            f'<div class="stat-value">{ratio}%</div>'
            f'<div class="stat-sub">proporsi kalimat relevan</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c4:
        avg_conf_pct = round(data.get("avg_confidence", 0) * 100, 1)
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-title">Rata-rata Keyakinan AI</div>'
            f'<div class="stat-value">{avg_conf_pct}%</div>'
            f'<div class="stat-sub">skor relevansi IndoBERT</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # --- Detail proses (collapsible) ---
    with st.expander("🔍 Lihat Detail Proses Seleksi Kalimat"):

        st.markdown("#### 1️⃣ Kalimat Utama (Premis)")
        st.info(f'_{data.get("premise", "Tidak ada data premis")}_')

        st.markdown("#### 2️⃣ Kalimat yang Dianggap Relevan")
        st.caption(
            "Kalimat-kalimat berikut dinilai memiliki makna yang sesuai dengan kalimat utama "
            "dan disusun sebagai kerangka sebelum ditulis ulang."
        )

        details = data.get("entailment_details", [])
        if details:
            for det in details:
                badge_html = confidence_badge(det["confidence"])
                st.markdown(
                    f"**Kalimat ke-{det['position']}** &nbsp; {badge_html}<br>"
                    f"<span style='color: #475569;'>{det['text']}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown("<hr style='margin: 10px 0; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
        else:
            st.warning("Tidak ada kalimat yang lolos seleksi (menggunakan fallback kalimat awal).")

    # --- Copy ringkasan ---
    st.subheader("📋 Salin Ringkasan")
    st.code(data["summary"], language=None)