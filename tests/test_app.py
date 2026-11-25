import os
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import requests
from PIL import Image as PILImage
from streamlit.testing.v1 import AppTest

PROJECT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_DIR / "apk_sampah_suara.py"
sys.path.insert(0, str(PROJECT_DIR))
os.environ.setdefault("ROBOFLOW_API_KEY", "test-api-key")


class FakeCapture:
    def __init__(self, *args, **kwargs):
        self.opened = True

    def isOpened(self):
        return self.opened

    def set(self, *args, **kwargs):
        return True

    def grab(self):
        return True

    def retrieve(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (30, 90, 50)
        return True, frame

    def read(self):
        return self.retrieve()

    def release(self):
        self.opened = False


def jalankan_app(predictions=None, connection_error=False):
    if connection_error:
        post_patch = patch(
            "requests.post",
            side_effect=requests.exceptions.ConnectionError("offline")
        )
    else:
        post_patch = patch("requests.post")
    with patch("cv2.VideoCapture", FakeCapture), patch("pyttsx3.init", side_effect=RuntimeError):
        with post_patch as post:
            if not connection_error:
                post.return_value.raise_for_status.return_value = None
                post.return_value.json.return_value = {
                    "predictions": predictions or {}
                }
            app = AppTest.from_file(str(APP_PATH), default_timeout=120).run()
            tombol(app, "Jalankan Pemindaian").click().run()
    return app


def tombol(app, label):
    return next(item for item in app.button if item.label == label)


def checkbox(app, label):
    return next(item for item in app.checkbox if item.label == label)


def isi_markdown(app):
    return "\n".join(element.value for element in app.markdown)


def test_klasifikasi_sampah_organik():
    app = jalankan_app({"Organic_Waste": {"confidence": 0.92}})
    teks = isi_markdown(app)
    assert "Sampah Organik" in teks
    assert "Buang ke tempat sampah organik" in teks


def test_klasifikasi_plastik():
    app = jalankan_app({"Plastics": {"confidence": 0.88}})
    assert "Plastik" in isi_markdown(app)


def test_klasifikasi_kaca_anorganik():
    app = jalankan_app({"Glass": {"confidence": 0.95}})
    teks = isi_markdown(app)
    assert "Kaca" in teks
    assert "Anorganik" in teks


def test_tampil_tiga_prediksi_teratas():
    app = jalankan_app({
        "Glass": {"confidence": 0.8},
        "Plastics": {"confidence": 0.15},
        "Carton": {"confidence": 0.05},
    })
    teks = isi_markdown(app)
    assert "3 Prediksi Teratas" in teks
    assert "Kaca" in teks
    assert "Plastik" in teks


def test_keyakinan_rendah():
    app = jalankan_app({"Glass": {"confidence": 0.2}})
    assert "Keyakinan AI hanya 20%" in isi_markdown(app)


def test_gagal_koneksi_roboflow():
    app = jalankan_app(connection_error=True)
    assert "Tidak dapat terhubung ke server AI" in isi_markdown(app)


def test_hasil_tetap_ada_setelah_rerun():
    app = jalankan_app({"Plastics": {"confidence": 0.9}})
    checkbox(app, "Aktifkan Suara").uncheck().run()
    assert "Hasil Klasifikasi" in isi_markdown(app)


def test_riwayat_tersimpan():
    app = jalankan_app({"Plastics": {"confidence": 0.9}})
    riwayat = app.session_state["riwayat"]
    assert len(riwayat) == 1
    assert riwayat[0]["Jenis"] == "Plastik"
    assert riwayat[0]["Kategori"] == "Anorganik"


def test_upload_gambar():
    buffer = BytesIO()
    PILImage.new("RGB", (640, 480), (40, 120, 60)).save(buffer, format="JPEG")
    with patch("requests.post") as post, patch("pyttsx3.init", side_effect=RuntimeError):
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {
            "predictions": {"Plastics": {"confidence": 0.9}}
        }
        app = AppTest.from_file(str(APP_PATH), default_timeout=120).run()
        app.radio[0].set_value("Upload Gambar").run()
        app.file_uploader[0].set_value(
            ("sampah.jpg", buffer.getvalue(), "image/jpeg")
        ).run()
        tombol(app, "Jalankan Pemindaian").click().run()
    assert "Plastik" in isi_markdown(app)
    assert app.session_state["riwayat"][0]["Sumber"] == "Upload Gambar"


def test_model_lokal_tanpa_model():
    with patch("cv2.VideoCapture", FakeCapture), patch("requests.post") as post:
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {"predictions": {}}
        app = AppTest.from_file(str(APP_PATH), default_timeout=120).run()
        app.radio[1].set_value("Lokal (ANN .keras)").run()
        tombol(app, "Jalankan Pemindaian").click().run()
    assert "Model lokal tidak dapat dipakai" in isi_markdown(app)


def test_kamera_tidak_tersedia():
    with patch("cv2.VideoCapture", FakeCapture):
        asli = FakeCapture.isOpened
        FakeCapture.isOpened = lambda self: False
        try:
            app = AppTest.from_file(str(APP_PATH), default_timeout=120).run()
        finally:
            FakeCapture.isOpened = asli
    assert any("Kamera sedang tidak tersedia" in w.value for w in app.warning)
