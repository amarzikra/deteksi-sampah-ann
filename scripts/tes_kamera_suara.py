import cv2
import pyttsx3

# 1. Inisialisasi mesin Suara (pyttsx3)
engine = pyttsx3.init()

# kecepatan bicara
engine.setProperty('rate', 150)

print("Mencoba membunyikan suara perkenalan...")
engine.say("halo gess kamera sudah aktif ya, mari kita deteksi sampah menggunakan metode ann!")
engine.runAndWait()

# 2.mengaktifkan kamera 
# ingat ngka 0 artinya memanggil kamera bawaan laptop 
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Waduh, kamera kamu gak bisa dibuka!")
    exit()

print("\nKamera berhasil aktif! Tekan tombol 'q' di keyboard untuk tutupkamera.")

# perulangan untuk memunculkan video live 
while True:
    # tangkap frame demi frame dari kamera
    ret, frame = cap.read()
    if not ret:
        print("Gagal mengambil gambar dari kamera.")
        break

    # tampilan live
    cv2.imshow("Kamera Deteksi Sampah", frame)

    # codingan  keluar q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 3. ni code mersihin memori klau kamera ditutup
cap.release()
cv2.destroyAllWindows()
print("Kamera berhasil dimatikan yayaaa!")