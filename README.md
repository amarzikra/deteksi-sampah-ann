# DETEKSI SAMPAH BERBASIS JARINGAN SARAF TIRUAN

Aplikasi web berbasis Streamlit yang memanfaatkan kamera, model klasifikasi Roboflow (9 kategori), dan text-to-speech untuk membantu memilah sampah secara cepat.

## Fitur

- Live preview kamera dengan kotak pemindaian hijau (menggunakan `st.fragment`, buffer frame dibersihkan agar tidak lag).
- Klasifikasi 9 kategori: `Aluminium`, `Carton`, `E-waste`, `Glass`, `Organic_Waste`, `Paper_and_Cardboard`, `Plastics`, `Textiles`, `Wood`.
- Hasil klasifikasi: label bahasa Indonesia, kategori organik/anorganik, tingkat keyakinan, 3 prediksi teratas, rekomendasi, dan informasi edukasi.
- Ambang keyakinan 60%: di bawah itu hasil tetap tampil dengan peringatan untuk mengulang pemindaian.
- Suara bisa diaktifkan/dinonaktifkan; voice Indonesia dipilih otomatis jika tersedia; kecepatan bisa diatur.
- Hasil klasifikasi tetap tersimpan walaupun pengaturan diubah (rerun).
- Retry otomatis 3 kali jika server Roboflow tidak merespons, dengan pesan error yang ramah.
- Tombol **Matikan Kamera** dan **Coba Lagi Kamera**; launcher tanpa perlu mengetik perintah di terminal.
- Tiga sumber gambar: **Kamera Lokal (live)**, **Kamera Browser** (`st.camera_input`), dan **Upload Gambar** — dua terakhir bisa dipakai di HP/cloud tanpa webcam server.
- Suara bisa dipilih: **Browser** (Web Speech API, keluar dari perangkat pengguna) atau **Server** (`pyttsx3`).
- Riwayat klasifikasi, statistik sesi, dan ekspor CSV.
- Pilihan model: **Roboflow (cloud)** atau **Model Lokal (ANN `.keras`)** sebagai fallback offline.
- Siap di-deploy lewat Docker atau Streamlit Community Cloud.

## Arsitektur

| Bagian | Teknologi |
| --- | --- |
| Antarmuka & logika | `apk_sampah_suara.py` (Streamlit) |
| Kamera | OpenCV (DirectShow di Windows), 640x480 |
| Model klasifikasi | Roboflow classify API, model `waste-classification-awlni-o55f1/3` |
| Suara | `pyttsx3` (worker thread + antrean, tidak memblokir UI) |
| Tampilan | `style.css` + `.streamlit/config.toml` (tema gelap) |
| Pelatihan lokal | `train_ann.py` + TensorFlow (model `.keras` opsional dipakai aplikasi) |

## Struktur folder

```
apk_sampah_suara.py     aplikasi utama
style.css               tema, animasi, dan CSS responsif
assets/                 ilustrasi hero lokal (SVG)
.streamlit/             secrets.toml (rahasia) dan config.toml
train/                  dataset gambar (5 kelas: 2511 gambar)
train_ann.py            skrip melatih ANN lokal
scripts/                skrip bantu (tes kamera, inferensi cloud)
tests/                  tes otomatis (pytest)
package.json            script npm (start, stop, setup, train, test)
requirements.txt        dependensi aplikasi web
requirements-train.txt  dependensi training
requirements-dev.txt    dependensi testing
caramenjalankan.txt     panduan singkat
```

## Prasyarat

- Python 3.11 dan `py` launcher (`py -3.11 --version`).
- Webcam, koneksi internet (untuk Roboflow), dan perangkat audio (opsional).
- Node.js/npm jika ingin memakai perintah `npm`.
- Browser modern.

## Instalasi

```
npm run setup
```

Atau manual:

```
py -3.11 -m pip install -r requirements.txt
```

## Konfigurasi API key

1. Salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml`.
2. Isi `api_key` dengan API key Roboflow Anda (atau set environment variable `ROBOFLOW_API_KEY`).
3. Jangan bagikan/commit file `secrets.toml` — sudah masuk `.gitignore`.

## Menjalankan

```
npm start
```

Browser terbuka otomatis di `http://localhost:8501/#deteksi` (langsung ke area kamera). Alternatif lain:

- Tanpa terminal: double-click **`Jalankan Aplikasi.vbs`**.
- Manual: `py -3.11 -m streamlit run apk_sampah_suara.py`.

Menghentikan: `npm run stop`, double-click **`Hentikan Aplikasi.bat`**, atau klik tombol **Matikan Kamera** di aplikasi.

## Pemakaian

1. Pilih **Sumber Gambar**:
   - **Kamera Lokal (live)**: centang **Izinkan Akses Kamera**, posisikan sampah di kotak hijau.
   - **Kamera Browser**: ambil foto lewat kamera perangkat (cocok untuk HP/cloud).
   - **Upload Gambar**: pilih file JPG/PNG dari perangkat.
2. Pilih **Model**: Roboflow (cloud) atau Lokal (ANN `.keras`, perlu training dulu).
3. Klik **Jalankan Pemindaian**. Hasil tampil di bawah tombol.
4. Centang **Aktifkan Suara**, pilih mesin **Browser** atau **Server**, dan atur **Kecepatan Suara**.
5. Buka **Riwayat Klasifikasi & Statistik** untuk melihat riwayat, metrik, dan mengunduh CSV.
6. Jika kamera lokal dipakai aplikasi lain, tutup aplikasi tersebut lalu klik **Coba Lagi Kamera**.

## Melatih ANN (opsional)

```
npm run setup:train
npm run train
```

Hasil training disimpan di `model/model_ann.keras` dan `model/history.json`. Default 20 epoch; untuk percobaan cepat set environment variable `ANN_EPOCHS=1`.

> Catatan: dataset folder `train/` berisi 5 kelas, sedangkan model Roboflow (default aplikasi) memiliki 9 kelas. Model lokal yang sudah dilatih bisa dipilih lewat radio **Model → Lokal (ANN .keras)**.

## Tes otomatis

```
npm run setup:test
npm test
```

Tes mencakup pemetaan label, kategori, 3 prediksi teratas, ambang keyakinan, error koneksi Roboflow, persistensi hasil, dan kondisi kamera tidak tersedia. Tes memakai kamera dan API tiruan sehingga tidak memerlukan webcam fisik.

## Deploy

### Docker

```
docker build -t deteksi-sampah-ann .
docker run -p 8501:8501 --env-file .env deteksi-sampah-ann
```

`Dockerfile` memakai Python 3.11-slim dan menjalankan Streamlit headless di port 8501. `.dockerignore` mencegah `secrets.toml`, dataset, dan model ikut ter-copy. Untuk Cloud/HP, pilih sumber gambar **Kamera Browser** atau **Upload Gambar**, dan mesin suara **Browser**.

### Streamlit Community Cloud

1. Push repository ke GitHub (pastikan `secrets.toml` tidak ikut ter-commit).
2. Buat app di https://share.streamlit.io dengan file utama `apk_sampah_suara.py` dan Python 3.11.
3. Isi **Secrets** di dashboard dengan isi `.streamlit/secrets.toml`.
4. Gunakan sumber gambar **Kamera Browser**/**Upload Gambar** dan mesin suara **Browser** agar kamera & audio berasal dari perangkat pengunjung.

## Troubleshooting

| Masalah | Solusi |
| --- | --- |
| `ModuleNotFoundError` | Jalankan `npm run setup` |
| "Is Streamlit still running?" / Connection error | Aplikasi pernah dimatikan; jalankan `npm start` lagi lalu refresh browser |
| "Kamera sedang tidak tersedia" | Tutup tab/aplikasi lain yang memakai kamera, klik **Coba Lagi Kamera** |
| Tidak ada suara | Cek checkbox **Aktifkan Suara** dan volume sistem; voice Indonesia bergantung voice yang terpasang di Windows |
| Error API key | Periksa `.streamlit/secrets.toml` (lihat `secrets.toml.example`) |
| Hasil selalu "Keyakinan rendah" | Perbaiki pencahayaan dan posisikan objek di tengah kotak hijau |

## Atribusi

- Dataset: **Waste Classification** oleh pengguna Roboflow, lisensi **CC BY 4.0** — https://universe.roboflow.com/lasriviola/waste-classification-awlni-o55f1
- Pustaka pihak ketiga: Streamlit, OpenCV, pyttsx3, Requests, Inference SDK, TensorFlow, pytest.
- Ilustrasi hero dibuat lokal dalam bentuk SVG (tanpa aset pihak ketiga).
