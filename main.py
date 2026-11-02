import cv2
import numpy as np
from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class ParmakTakipApp(App):
    def build(self):
        # Kivy arayüz görüntüsünü tutacak bileşen
        self.img_bileseni = Image()
        
        # Mobil ön kamera aktivasyonu (Genellikle 0 veya 1 ön kameradır)
        self.cap = cv2.VideoCapture(0)
        
        # İşlemciyi yormamak adına çözünürlüğü mobil standartlara düşürüyoruz
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        # Saniyede 30 kare güncellenecek şekilde zamanlayıcıyı kur
        Clock.schedule_interval(self.goruntu_guncelle, 1.0 / 30.0)
        
        return self.img_bileseni

    def goruntu_guncelle(self, dt):
        success, frame = self.cap.read()
        if success:
            # Telefonlar dikey tutulduğu için görüntüyü 90 derece sağa döndür
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            
            # Doğal ön kamera deneyimi için aynalama yap
            frame = cv2.flip(frame, 1)
            
            # --- Görüntü İşleme Mantığı (Ten Rengi Filtreleme) ---
            blur = cv2.GaussianBlur(frame, (5, 5), 0)
            hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
            
            alt_ten = np.array([0, 20, 70], dtype="uint8")
            ust_ten = np.array([20, 255, 255], dtype="uint8")
            
            maske = cv2.inRange(hsv, alt_ten, ust_ten)
            maske = cv2.erode(maske, None, iterations=2)
            maske = cv2.dilate(maske, None, iterations=2)
            
            konturlar, _ = cv2.findContours(maske.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(konturlar) > 0:
                en_buyuk_kontur = max(konturlar, key=cv2.contourArea)
                
                # Mobil hassasiyet için alan sınırını 1000 piksele çektik
                if cv2.contourArea(en_buyuk_kontur) > 1000:
                    (x, y, w, h) = cv2.boundingRect(en_buyuk_kontur)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    
                    # El alanının en üst (Y koordinatı en küçük) parmak ucunu bul
                    en_tepe_nokta = tuple(en_buyuk_kontur[en_buyuk_kontur[:, :, 1].argmin()][0])
                    
                    # Hedef noktayı yeşil daire ile işaretle
                    cv2.circle(frame, en_tepe_nokta, 8, (0, 255, 0), -1)
                    
                    cv2.putText(frame, f"PARMAK UCU: {en_tepe_nokta}", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)

            # Üst Bilgi Paneli
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 30), (245, 117, 16), -1)
            cv2.putText(frame, 'PARMAK TAKIP AKTIF', (10, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            # -----------------------------------------------------

            # Matris formatındaki resmi Kivy dokusuna dönüştürüp ekrana bas
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.img_bileseni.texture = texture

    def on_stop(self):
        # Uygulama kapandığında kamerayı güvenli kapat
        self.cap.release()

if __name__ == '__main__':
    ParmakTakipApp().run()
