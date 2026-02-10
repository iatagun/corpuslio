# Redis Setup for Windows

## Seçenek 1: WSL2 ile Redis (Önerilen)

### 1. WSL2 Kur (Eğer yoksa)

```powershell
wsl --install
```

Bilgisayarı restart edin.

### 2. WSL2'de Redis Kur

```bash
# WSL terminalini açın
wsl

# Redis kur
sudo apt update
sudo apt install redis-server -y

# Redis'i başlat
sudo service redis-server start

# Test et
redis-cli ping
# PONG döner
```

### 3. Windows'tan Erişim

Redis WSL2'de `localhost:6379` üzerinden erişilebilir. Django ayarlarında değişiklik gerekmez!

---

## Seçenek 2: Memurai (Kolay ama Ücretli)

1. [Memurai](https://www.memurai.com/get-memurai) indir
2. Kur (otomatik başlar)
3. `localhost:6379` hazır!

---

## Seçenek 3: Docker

```bash
docker run -d -p 6379:6379 redis:alpine
```

---

## Django'yu Çalıştırma

### Terminal 1: Redis (WSL2)
```bash
wsl
sudo service redis-server start
```

### Terminal 2: Celery Worker
```bash
cd ocrchestra_django
celery -A ocrchestra_django worker -l info --pool=solo
```

**⚠️ Windows için `--pool=solo` gerekli!**

### Terminal 3: Django
```bash
cd ocrchestra_django
python manage.py runserver
```

---

## Test

1. http://localhost:8000/upload/ 
2. Dosya yükle
3. "İşlem başlatıldı" mesajı görmelisiniz
4. Celery worker loglarında işlemi görebilirsiniz

---

## Hata Ayıklama

**Redis bağlanmazsa:**
```bash
# WSL2'de Redis çalışıyor mu?
wsl redis-cli ping

# Redis logları
wsl sudo tail -f /var/log/redis/redis-server.log
```

**Celery hatası:**
```bash
# Windows'ta mutlaka --pool=solo kullanın
celery -A ocrchestra_django worker -l info --pool=solo
```
