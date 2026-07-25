
Usage
Start CS2 (in windowed mode for best results)

Run the application

The ESP overlay and radar will appear automatically

Use the configuration file to adjust settings

Project Structure
text
FPS_Mechanics_Lab/
├── src/           # Source code
├── config/        # Configuration files
├── logs/          # Log files
└── README.md      # Documentation
Modules
core/: Memory reading, entity management, offsets

math/: World to screen, aimbot mathematics

esp/: Overlay rendering with PyQt5

radar/: 2D minimap with map data

aimbot/: Aimbot, triggerbot, rapidfire

security/: Anti-cheat analysis

utils/: Configuration, logging, performance

Contributing
This is an educational project. Contributions are welcome for:

Documentation improvements

Bug fixes

Feature additions (within educational scope)

Code optimizations

License
This project is licensed under the MIT License - see the LICENSE file for details.

🇹🇷 Türkçe
Genel Bakış
FPS Mechanics Lab, Counter-Strike 2 gibi Source 2 tabanlı FPS oyunlarının temel mekaniklerini analiz etmek ve görselleştirmek için tasarlanmış eğitim amaçlı akademik bir projedir.

⚠️ Önemli Uyarı
BU PROJE SADECE EĞİTİM AMAÇLIDIR

Bu yazılımı çevrimiçi oyunlarda KULLANMAYIN

Bu bir teknik analiz aracıdır, HİLE DEĞİLDİR

Yazarlar herhangi bir kötüye kullanımdan sorumlu değildir

Özellikler
🧠 Bellek Analizi: Dinamik offset'lerle external bellek okuma

🎯 World to Screen: Matematiksel 3D'den 2D'ye projeksiyon

👁️ ESP Overlay: Kutu, iskelet, sağlık barı, isim, mesafe render'ı

🗺️ 2D Radar: Gerçek zamanlı oyuncu takibi ile minimap

📐 Aimbot Matematik: Eğitim amaçlı açı hesaplama ve yumuşatma

🔫 Recoil Control: RCS analizi ve görselleştirme

⚡ Performans: Multithreading ve Numba optimizasyonu

🔒 Güvenlik Analizi: Anti-cheat tespit yöntemleri ve güvenli uygulamalar
