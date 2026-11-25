import os
import csv
import html
import io
import json
import time
import queue
import threading
import base64
import numpy as np
import requests
import cv2
import pyttsx3
import streamlit as st
from PIL import Image
from streamlit.components.v1 import html as components_html

#konfigurasi global api
def get_roboflow_config():
    api_key = os.environ.get("ROBOFLOW_API_KEY", "")
    model_id = "waste-classification-awlni-o55f1/3"
    try:
        api_key = st.secrets["roboflow"]["api_key"]
    except Exception:
        pass
    try:
        model_id = st.secrets["roboflow"]["model_id"]
    except Exception:
        pass
    return api_key, model_id

ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID = get_roboflow_config()
ROBOFLOW_API_URL = f"https://classify.roboflow.com/{ROBOFLOW_MODEL_ID}?api_key={ROBOFLOW_API_KEY}"

# tampilan awal masuk/halaman
st.set_page_config(
    page_title="DETEKSI SAMPAH BERBASIS JARINGAN SARAF TIRUAN",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if not ROBOFLOW_API_KEY:
    st.error("API key Roboflow belum diatur. Salin .streamlit/secrets.toml.example menjadi .streamlit/secrets.toml lalu isi api_key.")
    st.stop()

#load custom css
try:
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# memuat Icons menggunakan phosphor icons
st.markdown('<link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" />', unsafe_allow_html=True)


ORGANIK = {"Organic_Waste", "Organic Waste", "Wood"}


def get_hero_src():
    try:
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "hero-ilustrasi.svg"
        )
        with open(path, "r", encoding="utf-8") as file:
            svg = file.read()
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    except (OSError, UnicodeError):
        return ""


HERO_SRC = get_hero_src()
HERO_IMG = (
    f'<img src="{HERO_SRC}" alt="Ilustrasi deteksi sampah berbasis Jaringan Saraf Tiruan" '
    'style="max-width: 100%; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">'
    if HERO_SRC else ""
)


def get_label_indonesia(label_inggris):
    mapping = {
        "Plastics": "Plastik",
        "Plastic": "Plastik",
        "Organic_Waste": "Sampah Organik",
        "Organic Waste": "Sampah Organik",
        "Aluminium": "Aluminium",
        "Paper_and_Cardboard": "Kertas dan Kardus",
        "Paper and Cardboard": "Kertas dan Kardus",
        "Carton": "Karton",
        "Glass": "Kaca",
        "E-waste": "Sampah Elektronik",
        "Textiles": "Tekstil",
        "Wood": "Kayu"
    }
    return mapping.get(label_inggris, label_inggris)

def get_kategori_info(label_inggris):
    return "Organik" if label_inggris in ORGANIK else "Anorganik"

def get_rekomendasi(label_inggris):
    rekomendasi = {
        "Organic_Waste": "Buang ke tempat sampah organik.",
        "Organic Waste": "Buang ke tempat sampah organik.",
        "Wood": "Buang ke tempat sampah organik atau olah menjadi kompos.",
        "Plastics": "Buang ke tempat sampah anorganik agar dapat didaur ulang.",
        "Plastic": "Buang ke tempat sampah anorganik agar dapat didaur ulang.",
        "Glass": "Buang ke tempat sampah anorganik; bungkus pecahan kaca agar aman.",
        "E-waste": "Buang ke tempat sampah elektronik/B3, jangan dicampur sampah rumah tangga.",
        "Textiles": "Buang ke tempat sampah anorganik atau donasikan jika masih layak pakai.",
        "Aluminium": "Buang ke tempat sampah anorganik agar dapat didaur ulang.",
        "Paper_and_Cardboard": "Buang ke tempat sampah anorganik agar dapat didaur ulang.",
        "Paper and Cardboard": "Buang ke tempat sampah anorganik agar dapat didaur ulang.",
        "Carton": "Buang ke tempat sampah anorganik agar dapat didaur ulang."
    }
    return rekomendasi.get(label_inggris, "Buang ke tempat sampah anorganik agar dapat didaur ulang.")

def get_edukasi_info(label_inggris):
    edukasi = {
        "Plastics": "Plastik membutuhkan waktu sangat lama untuk terurai. Memilah plastik sejak awal membantu proses daur ulang dan mengurangi pencemaran lingkungan.",
        "Plastic": "Plastik membutuhkan waktu sangat lama untuk terurai. Memilah plastik sejak awal membantu proses daur ulang dan mengurangi pencemaran lingkungan.",
        "Organic_Waste": "Sampah organik dapat diolah menjadi kompos sehingga mengurangi volume sampah yang dibuang ke TPA.",
        "Organic Waste": "Sampah organik dapat diolah menjadi kompos sehingga mengurangi volume sampah yang dibuang ke TPA.",
        "Aluminium": "Aluminium dapat didaur ulang berkali-kali tanpa kehilangan kualitas materialnya.",
        "Paper_and_Cardboard": "Kertas dan kardus yang dipilah dengan baik dapat diproses kembali menjadi produk baru.",
        "Paper and Cardboard": "Kertas dan kardus yang dipilah dengan baik dapat diproses kembali menjadi produk baru.",
        "Carton": "Karton yang bersih lebih mudah diproses dalam sistem daur ulang.",
        "Glass": "Kaca dapat didaur ulang tanpa kehilangan kualitas, tetapi pecahan kaca berbahaya jika tercampur sampah lain.",
        "E-waste": "Sampah elektronik mengandung logam dan bahan berbahaya yang harus diolah di tempat khusus.",
        "Textiles": "Tekstil yang masih layak dapat didonasikan; limbah kain bisa diolah menjadi produk kerajinan.",
        "Wood": "Kayu termasuk sampah organik yang dapat dijadikan kompos, arang, atau bahan bakar biomassa."
    }
    return edukasi.get(label_inggris, "Mengenali jenis sampah sebelum membuangnya membantu proses daur ulang menjadi lebih efektif.<br>Mari bersama menjaga lingkungan dengan memilah sampah dengan benar")

def get_pesan_suara(label_indo, kategori, dikenali=True):
    if not dikenali:
        return "Objek tidak dapat dikenali. Pastikan sampah berada di dalam area pemindaian dan pencahayaan cukup."
    
    if kategori == "Organik":
        return f"Objek berhasil dikenali. Jenis sampah {label_indo}. Sampah ini dapat diolah menjadi kompos."
    else:
        return f"Objek berhasil dikenali. Jenis sampah {label_indo}. Termasuk kategori anorganik. Silakan buang ke tempat sampah anorganik."

#bagiann nan UI 

# Navbar
st.markdown("""
<div class="glass-nav" id="home">
    <div class="nav-logo">
        <i class="ph ph-leaf" style="color: var(--accent);"></i> Deteksi Sampah
    </div>
    <div class="nav-links">
        <a href="#home">Home</a>
        <a href="#tentang">Teknologi</a>
        <a href="#deteksi">Area Deteksi</a>
    </div>
    <a href="#deteksi" class="nav-btn"><i class="ph ph-scan"></i> Mulai Deteksi</a>
</div>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="ai-shape"></div>
    <div class="hero-badge"><i class="ph ph-sparkle"></i> AI Powered Waste Classification</div>
    <h1>DETEKSI SAMPAH<br><span class="text-gradient-green">BERBASIS JARINGAN SARAF TIRUAN</span></h1>
    <p class="subtitle" style="margin-bottom: 40px; font-size: 1.15rem;">Aplikasi web yang mengintegrasikan Computer Vision dan Jaringan Saraf Tiruan (ANN) untuk mendeteksi serta mengklasifikasikan jenis sampah secara instan melalui citra digital. Masa depan Green Technology dimulai dari genggaman Anda.</p>
    <div class="hero-buttons" style="display: flex; gap: 16px; justify-content: center;">
        <a href="#deteksi" class="btn-primary-custom"><i class="ph ph-camera"></i> Mulai Klasifikasi</a>
        <a href="#tentang" class="btn-secondary-custom"><i class="ph ph-brain"></i> Cara Kerja</a>
    </div>
</div>
""", unsafe_allow_html=True)

# tentang Section samo dampa
st.markdown(f"""
<div id="tentang" style="max-width: 1100px; margin: 120px auto 80px auto; display: flex; flex-wrap: wrap; gap: 60px; align-items: center; padding: 20px;">
    <div style="flex: 1; min-width: 300px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; color: var(--accent); font-weight: 500; margin-bottom: 16px; font-size: 0.85rem; letter-spacing: 0.05em;"><i class="ph ph-cpu"></i> CORE TECHNOLOGY</div>
        <h2 style="font-size: 2.25rem; line-height: 1.2;">Membangun Masa Depan<br><span class="text-gradient-green">Green Technology</span></h2>
        <p style="font-size: 1.05rem;">Pencampuran sampah merupakan hambatan utama daur ulang global. Deteksi Sampah memanfaatkan <strong style="color: var(--text-main); font-weight: 600;">Jaringan Saraf Tiruan</strong> untuk memberikan solusi visual instan.</p>
        <ul style="color: var(--text-muted); line-height: 2; list-style-type: none; padding-left: 0; margin-top: 32px;">
            <li style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;"><i class="ph ph-check-circle" style="color: var(--accent); font-size: 1.25rem;"></i><span style="font-size: 0.95rem;">Klasifikasi 9 kategori sampah dengan model AI terlatih.</span></li>
            <li style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;"><i class="ph ph-check-circle" style="color: var(--accent); font-size: 1.25rem;"></i><span style="font-size: 0.95rem;">Analisis citra cepat melalui model AI di cloud.</span></li>
            <li style="display: flex; align-items: center; gap: 16px;"><i class="ph ph-check-circle" style="color: var(--accent); font-size: 1.25rem;"></i><span style="font-size: 0.95rem;">Dampak langsung terhadap ekosistem berkelanjutan.</span></li>
        </ul>
    </div>
    <div style="flex: 1; min-width: 300px; position: relative;">
        <!-- Background elements removed for cleaner look -->
        
<div style="text-align: center; width: 100%;">
{HERO_IMG}
</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ko area deteksi
st.markdown('''
<div id="deteksi" style="padding-top: 80px;">
    <div style="text-align: center;"><div class="hero-badge"><i class="ph ph-scan"></i> Terminal Klasifikasi</div></div>
    <h2 style="text-align: center; margin-bottom: 16px;">Inisialisasi <span class="text-gradient-green">Kamera</span></h2>
    <p style="text-align: center; max-width: 600px; margin: 0 auto 64px auto;">Posisikan objek di dalam kotak pemindai hijau. AI Engine kami akan menguraikan citra, menganalisis struktur, dan memberikan hasil klasifikasi secara komprehensif.</p>
</div>
''', unsafe_allow_html=True)

#logic

def buka_kamera():
    if os.name == "nt":
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(0)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
    return cap

def get_kamera():
    cap = st.session_state.get("kamera")
    if cap is None or not cap.isOpened():
        cap = buka_kamera()
        st.session_state.kamera = cap
    return cap

def tutup_kamera():
    cap = st.session_state.pop("kamera", None)
    if cap is not None:
        cap.release()

def baca_frame_terbaru(cap):
    if cap is None or not cap.isOpened():
        return None
    for _ in range(2):
        cap.grab()
    ok, frame = cap.retrieve()
    if not ok or frame is None:
        return None
    return cv2.flip(frame, 1)

BATAS_KEYAKINAN = 60


def normalisasi_conf(confidence):
    return confidence * 100 if confidence <= 1 else confidence


def parse_prediksi(hasil_json):
    data = hasil_json.get("predictions", [])
    daftar = []
    if isinstance(data, dict):
        for nama, detail in data.items():
            try:
                conf = float(detail.get("confidence", 0))
            except (AttributeError, TypeError, ValueError):
                continue
            daftar.append((str(nama), normalisasi_conf(conf)))
    elif isinstance(data, list):
        for item in data:
            try:
                nama = str(item.get("class", ""))
                conf = float(item.get("confidence", 0))
            except (AttributeError, TypeError, ValueError):
                continue
            daftar.append((nama, normalisasi_conf(conf)))
    elif isinstance(data, str):
        daftar.append((data, 100.0))
    if not daftar and "top" in hasil_json:
        daftar.append((str(hasil_json["top"]), 100.0))
    daftar.sort(key=lambda item: item[1], reverse=True)
    return daftar


def kirim_ke_roboflow(img_base64):
    for percobaan in range(3):
        try:
            response = requests.post(
                ROBOFLOW_API_URL,
                data=img_base64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            return response.json(), None
        except ValueError:
            return None, "Respons server AI tidak valid. Coba lagi beberapa saat."
        except requests.exceptions.RequestException:
            if percobaan < 2:
                time.sleep(1)
    return None, "Tidak dapat terhubung ke server AI. Periksa koneksi internet, lalu coba lagi."


def render_hasil(hasil):
    if not hasil:
        return ""
    status = hasil.get("status")
    if status in ("error", "tidak_dikenali"):
        icon = "ph-warning" if status == "error" else "ph-question"
        pesan = html.escape(str(hasil.get("pesan", "")))
        return f'<div class="error-card fade-in"><i class="ph {icon}"></i> {pesan}</div>'

    label = html.escape(str(hasil.get("label", "")))
    kategori = html.escape(str(hasil.get("kategori", "")))
    conf = int(hasil.get("confidence", 0))
    rekomendasi = html.escape(str(hasil.get("rekomendasi", "")))
    edukasi = html.escape(str(hasil.get("edukasi", ""))).replace("&lt;br&gt;", "<br>")
    top3 = "".join(
        '<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:0.9rem;">'
        '<span style="color:var(--text-muted);">{}</span>'
        '<span style="font-weight:700;color:var(--text-main);">{}%</span>'
        '</div>'.format(html.escape(str(nama)), int(nilai))
        for nama, nilai in hasil.get("top3", [])
    )
    peringatan = ""
    if status == "rendah":
        pesan = html.escape(str(hasil.get("pesan", "")))
        peringatan = (
            '<div class="error-card" style="margin-top:16px;background:rgba(255,215,0,0.1);'
            'border-color:rgba(255,215,0,0.3);color:#FFD700;">'
            f'<i class="ph ph-warning"></i> {pesan}</div>'
        )
    return (
        '<div class="result-card fade-in">'
        '<div class="result-header"><i class="ph ph-check-circle" style="color:var(--accent);font-size:1.5rem;"></i>'
        '<h4>Hasil Klasifikasi</h4></div>'
        '<div class="result-body">'
        '<div class="result-row"><span class="label">Jenis Sampah</span>'
        f'<span class="value text-gradient-green" style="font-size:1.25rem;">{label}</span></div>'
        '<div class="result-row"><span class="label">Kategori</span>'
        f'<span class="badge modern-badge">{kategori}</span></div>'
        '<div class="result-row confidence-section">'
        '<div class="conf-header"><span class="label">Keyakinan AI</span>'
        f'<span class="value">{conf}%</span></div>'
        '<div class="progress-bar-container">'
        f'<div class="progress-bar-fill" style="width:{conf}%;"></div>'
        '</div></div>'
        '<div class="result-row" style="flex-direction:column;align-items:stretch;gap:4px;">'
        '<span class="label">3 Prediksi Teratas</span>'
        f'{top3}</div>'
        '<div class="rekomendasi-box"><h5 class="rekomendasi-title">Rekomendasi</h5>'
        f'<p class="rekomendasi-text">{rekomendasi}</p></div>'
        '<div class="education-card" style="margin-top:8px;box-shadow:none;background:rgba(0,0,0,0.15);border-color:rgba(255,255,255,0.05);">'
        '<div class="edu-header"><h5> Tahukah Kamu?</h5></div>'
        f'<p class="edu-text">{edukasi}</p></div>'
        f'{peringatan}'
        '</div></div>'
    )

def _worker_suara(antrean):
    try:
        engine = pyttsx3.init()
        for voice in engine.getProperty("voices"):
            nama = str(getattr(voice, "name", "")).lower()
            bahasa = " ".join(
                str(item).lower() for item in (getattr(voice, "languages", []) or [])
            )
            if "indonesia" in nama or "indonesian" in nama or "id_id" in bahasa or "id-id" in bahasa:
                engine.setProperty("voice", voice.id)
                break
    except Exception:
        engine = None
    while True:
        item = antrean.get()
        if item is None:
            break
        teks, kecepatan = item
        if engine is not None and teks:
            try:
                engine.setProperty("rate", int(kecepatan))
                engine.say(teks)
                engine.runAndWait()
            except Exception:
                pass
        antrean.task_done()

@st.cache_resource
def get_antrean_suara():
    antrean = queue.Queue()
    threading.Thread(target=_worker_suara, args=(antrean,), daemon=True).start()
    return antrean

def ucapkan_teks(teks, aktif, kecepatan=150):
    if not aktif or not teks:
        return
    antrean = get_antrean_suara()
    while not antrean.empty():
        try:
            antrean.get_nowait()
            antrean.task_done()
        except queue.Empty:
            break
    antrean.put((teks, kecepatan))


KELAS_LOKAL = ["Organic_Waste", "Plastics", "Carton", "Paper_and_Cardboard", "Aluminium"]


@st.cache_resource
def get_model_lokal():
    import tensorflow as tf
    model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "model", "model_ann.keras"
    )
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model lokal belum ada. Jalankan: npm run train")
    return tf.keras.models.load_model(model_path)


def prediksi_model_lokal(gambar_bgr):
    try:
        model = get_model_lokal()
        gambar_rgb = cv2.cvtColor(gambar_bgr, cv2.COLOR_BGR2RGB)
        gambar_rgb = cv2.resize(gambar_rgb, (128, 128))
        data = np.expand_dims(gambar_rgb / 255.0, axis=0).astype("float32")
        hasil = model.predict(data, verbose=0)[0]
        prediksi = {
            KELAS_LOKAL[i]: {"confidence": float(hasil[i])}
            for i in range(len(KELAS_LOKAL))
        }
        return {"predictions": prediksi}, None
    except Exception as error:
        return None, f"Model lokal tidak dapat dipakai: {error}"


def dapatkan_prediksi(gambar_bgr, mode_model):
    _, img_encoded = cv2.imencode(".jpg", gambar_bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode("utf-8")
    if mode_model == "Lokal (ANN .keras)":
        return prediksi_model_lokal(gambar_bgr)
    return kirim_ke_roboflow(img_base64)


def ucapkan_di_browser(teks, kecepatan):
    payload = json.dumps({"teks": teks, "kecepatan": kecepatan})
    skrip = """
    <script>
    const data = %s;
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(data.teks);
        u.lang = 'id-ID';
        u.rate = Math.max(0.5, Math.min(2, data.kecepatan / 150));
        const voices = window.speechSynthesis.getVoices();
        const v = voices.find(x => x.lang && x.lang.toLowerCase().replace('_','-').startsWith('id'));
        if (v) u.voice = v;
        window.speechSynthesis.speak(u);
    }
    </script>
    """ % payload
    components_html(skrip, height=0)


def catat_riwayat(hasil, sumber, model):
    if "riwayat" not in st.session_state:
        st.session_state.riwayat = []
    st.session_state.riwayat.append({
        "Waktu": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Sumber": sumber,
        "Model": model,
        "Jenis": hasil.get("label", "-"),
        "Kategori": hasil.get("kategori", "-"),
        "Keyakinan (%)": hasil.get("confidence", 0),
        "Status": hasil.get("status", "")
    })


def hapus_riwayat():
    st.session_state.riwayat = []


def render_riwayat():
    riwayat = st.session_state.get("riwayat", [])
    with st.expander("Riwayat Klasifikasi & Statistik", expanded=False):
        if not riwayat:
            st.info("Belum ada klasifikasi.")
            return
        total = len(riwayat)
        rata = sum(int(item["Keyakinan (%)"]) for item in riwayat) / total
        organik = sum(1 for item in riwayat if item["Kategori"] == "Organik")
        kol1, kol2, kol3 = st.columns(3)
        kol1.metric("Total Pemindaian", total)
        kol2.metric("Rata-rata Keyakinan", f"{rata:.1f}%")
        kol3.metric("Sampah Organik", organik)
        st.dataframe(riwayat, hide_index=True, use_container_width=True)
        keluar = io.StringIO()
        penulis = csv.DictWriter(keluar, fieldnames=list(riwayat[0].keys()))
        penulis.writeheader()
        penulis.writerows(riwayat)
        st.download_button(
            "Unduh Riwayat (CSV)",
            data=keluar.getvalue().encode("utf-8"),
            file_name="riwayat_klasifikasi.csv",
            mime="text/csv"
        )
        st.button("Hapus Riwayat", on_click=hapus_riwayat, type="secondary")


@st.fragment(run_every="0.15s")
def tampilkan_pratinjau_kamera(kamera_aktif):
    if not kamera_aktif:
        return
    cap = get_kamera()
    frame = baca_frame_terbaru(cap)
    if frame is None:
        st.session_state.kamera_gagal = True
        st.caption("Status kamera: gagal dibuka.")
        st.warning("Kamera sedang tidak tersedia atau dipakai aplikasi lain.")
        if st.button("Coba Lagi Kamera", key="coba_lagi_kamera"):
            cap = st.session_state.pop("kamera", None)
            if cap is not None:
                cap.release()
            st.session_state.kamera_gagal = False
            st.rerun()
        return
    st.session_state.kamera_gagal = False
    st.caption("Status kamera: aktif — preview langsung tampil di bawah ini.")
    tinggi, lebar, _ = frame.shape
    x1, y1 = int(lebar/4), int(tinggi/4)
    x2, y2 = int(lebar*3/4), int(tinggi*3/4)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (118, 230, 0), 3)
    cv2.putText(frame, "Posisikan Sampah di Kotak Hijau", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (118, 230, 0), 2)
    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", output_format="JPEG", width="stretch")

if "tombol_diklik" not in st.session_state:
    st.session_state.tombol_diklik = False

def pemicu_klasifikasi():
    st.session_state.tombol_diklik = True

def matikan_aplikasi_total():
    st.session_state.kamera_dimatikan = True

_, col2, _ = st.columns([1, 8, 1])

with col2:
    st.markdown('<div class="streamlit-camera-container">', unsafe_allow_html=True)
    sumber_gambar = st.radio(
        "Sumber Gambar",
        ["Kamera Lokal (live)", "Kamera Browser", "Upload Gambar"],
        horizontal=True
    )
    kamera_aktif = False
    gambar_sumber = None
    if sumber_gambar == "Kamera Lokal (live)":
        kamera_dimatikan = st.session_state.get("kamera_dimatikan", False)
        kamera_aktif = st.checkbox("Izinkan Akses Kamera", value=not kamera_dimatikan)
        tampilkan_pratinjau_kamera(kamera_aktif)
    elif sumber_gambar == "Kamera Browser":
        gambar_sumber = st.camera_input("Ambil foto sampah")
    else:
        gambar_sumber = st.file_uploader(
            "Pilih gambar sampah", type=["jpg", "jpeg", "png"]
        )

    mode_model = st.radio(
        "Model", ["Roboflow (cloud)", "Lokal (ANN .keras)"], horizontal=True
    )
    suara_aktif = st.checkbox("Aktifkan Suara", value=True)
    if suara_aktif:
        kecepatan_suara = st.slider(
            "Kecepatan Suara", min_value=100, max_value=220, value=150, step=10
        )
        mesin_suara = st.radio(
            "Mesin Suara", ["Browser", "Server (pyttsx3)"], horizontal=True
        )
    else:
        kecepatan_suara = 150
        mesin_suara = "Browser"

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        st.button("Jalankan Pemindaian", use_container_width=True, on_click=pemicu_klasifikasi)
    with col_btn2:
        st.button("Matikan Kamera", use_container_width=True, on_click=matikan_aplikasi_total, type="secondary")

    status_placeholder = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

if sumber_gambar == "Kamera Lokal (live)" and not kamera_aktif:
    st.warning("Pemindai kamera lokal dinonaktifkan. Izinkan akses kamera atau pilih sumber gambar lain.")

# Footer
st.markdown("""
<div class="modern-footer">
    <div style="display: flex; justify-content: center; gap: 32px; margin-bottom: 40px; font-size: 28px; color: var(--text-muted);">
        <a href="https://github.com/amarzikra/deteksi-sampah-ann" target="_blank" style="color: inherit; transition: all 0.3s ease;" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--text-muted)'"><i class="ph ph-github-logo"></i></a>
        <a href="http://linkedin.com/in/lasriviolaa" target="_blank" style="color: inherit; transition: all 0.3s ease;" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--text-muted)'"><i class="ph ph-linkedin-logo"></i></a>
        <a href="mailto:lasriviola2@gmail.com" style="color: inherit; transition: all 0.3s ease;" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--text-muted)'"><i class="ph ph-envelope-simple"></i></a>
    </div>
    <div style="width: 60px; height: 4px; background: var(--accent); margin: 0 auto 32px auto; border-radius: 4px;"></div>
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px;">
        <i class="ph ph-leaf" style="color: var(--accent); font-size: 1.5rem;"></i>
        <h3 style="margin: 0; font-weight: 800; font-size: 1.5rem;">Deteksi Sampah</h3>
    </div>
    <p style="font-weight: 500; color: var(--text-muted); font-size: 0.95rem;">&copy; 2026. Designed &amp; Developed by amarzikra.</p>
    <p style="color: rgba(255,255,255,0.3); font-size: 0.85rem; margin-top: 8px;">Pioneering Green Technology with Artificial Intelligence.</p>
</div>
""", unsafe_allow_html=True)


# 2. Logika klasifikasi
if sumber_gambar == "Kamera Lokal (live)" and kamera_aktif:
    cap = get_kamera()
else:
    tutup_kamera()
    cap = None

if st.session_state.tombol_diklik:
    st.session_state.tombol_diklik = False
    frame = None
    if sumber_gambar == "Kamera Lokal (live)":
        frame = baca_frame_terbaru(cap)
    elif gambar_sumber is not None:
        try:
            gambar_pil = Image.open(gambar_sumber).convert("RGB")
            frame = cv2.cvtColor(np.array(gambar_pil), cv2.COLOR_RGB2BGR)
        except Exception:
            frame = None

    if frame is None:
        pesan = (
            "Belum ada gambar untuk dipindai. Ambil foto atau unggah gambar terlebih dahulu."
            if sumber_gambar != "Kamera Lokal (live)"
            else "Kamera gagal diakses. Tutup aplikasi lain yang memakai kamera, lalu coba lagi."
        )
        st.session_state.hasil_klasifikasi = {"status": "error", "pesan": pesan}
    else:
        tinggi, lebar, _ = frame.shape
        x1, y1 = int(lebar/4), int(tinggi/4)
        x2, y2 = int(lebar*3/4), int(tinggi*3/4)
        gambar_potong = frame[y1:y2, x1:x2]

        status_placeholder.markdown('<div class="loading-state"><i class="ph ph-robot spin-icon"></i>  AI sedang menganalisis objek...</div>', unsafe_allow_html=True)

        hasil_json, error = dapatkan_prediksi(gambar_potong, mode_model)

        if error:
            st.session_state.hasil_klasifikasi = {"status": "error", "pesan": error}
        elif "error" in hasil_json:
            st.session_state.hasil_klasifikasi = {
                "status": "error",
                "pesan": f"Gagal memproses: {hasil_json['error']}"
            }
        else:
            prediksi = parse_prediksi(hasil_json)
            if not prediksi:
                st.session_state.hasil_klasifikasi = {
                    "status": "tidak_dikenali",
                    "pesan": get_pesan_suara("", "", False)
                }
            else:
                kelas, confidence = prediksi[0]
                conf_pct = int(round(confidence))
                top3 = [
                    (get_label_indonesia(nama), int(round(nilai)))
                    for nama, nilai in prediksi[:3]
                ]
                label_indo = get_label_indonesia(kelas)
                kategori = get_kategori_info(kelas)
                rekomendasi = get_rekomendasi(kelas)
                edukasi = get_edukasi_info(kelas)
                if conf_pct < BATAS_KEYAKINAN:
                    status = "rendah"
                    pesan = (
                        f"Keyakinan AI hanya {conf_pct}%. Ulangi pemindaian dengan pencahayaan "
                        "cukup dan objek di tengah kotak hijau."
                    )
                else:
                    status = "sukses"
                    pesan = get_pesan_suara(label_indo, kategori, True)
                st.session_state.hasil_klasifikasi = {
                    "status": status,
                    "label": label_indo,
                    "kategori": kategori,
                    "confidence": conf_pct,
                    "top3": top3,
                    "rekomendasi": rekomendasi,
                    "edukasi": edukasi,
                    "pesan": pesan
                }

    catat_riwayat(st.session_state.hasil_klasifikasi, sumber_gambar, mode_model)
    pesan_suara = st.session_state.hasil_klasifikasi.get("pesan", "")
    if suara_aktif:
        if mesin_suara == "Browser":
            ucapkan_di_browser(pesan_suara, kecepatan_suara)
        else:
            ucapkan_teks(pesan_suara, True, kecepatan_suara)

status_placeholder.markdown(
    render_hasil(st.session_state.get("hasil_klasifikasi")),
    unsafe_allow_html=True
)
render_riwayat()