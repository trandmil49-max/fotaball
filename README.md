# Maç Skor Overlay Botu

Bu bot, gönderdiğin maç videosunu izler, videonun üstündeki skor kutusunu
okur ve yeşil ekranlı (kroma yeşili), iki takım logosunun yan yana durduğu,
skorun gol oldukça güncellendiği bir video üretir. Bunu kendi videonun
üzerine CapCut gibi bir programda bindirebilirsin.

## Botu nasıl kurarsın (adım adım)

### 1. Bu dosyaları GitHub'a yükle
- github.com'da yeni bir repo (proje) oluştur.
- Bu klasördeki tüm dosyaları oraya yükle.

### 2. Telegram'dan bot token'ı al
- Telegram'da **@BotFather** ile konuş.
- `/newbot` yaz, botuna bir isim ver.
- Sana uzun bir kod (token) verecek, onu kopyala. Örnek görünüş:
  `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3. Railway'de projeyi oluştur
- railway.app adresine git, GitHub hesabınla giriş yap.
- "New Project" -> "Deploy from GitHub repo" seçeneğiyle yüklediğin
  repoyu seç.
- Proje ayarlarında **Variables** (Değişkenler) kısmına git ve şunu ekle:
  - İsim: `BOT_TOKEN`
  - Değer: BotFather'ın sana verdiği kod
- Railway otomatik olarak dosyaları okuyup botu kuracak (birkaç dakika
  sürebilir, "tesseract" ve "ffmpeg" gibi ek programları kendisi kuruyor).

### 4. Botu test et
- Telegram'da botunu bul, `/start` yaz.
- Sırasıyla: maç videosu, video linki (yoksa "geç" yaz), birinci takım
  logosu, ikinci takım logosu gönder.
- Bot sana birkaç dakika içinde yeşil ekranlı skor videosunu gönderecek.

## Bir şey yanlış giderse

- **Bot skoru hiç bulamıyor / yanlış buluyor:** `config.py` dosyasındaki
  `TOP_CROP_RATIO` sayısını değiştir. Bu sayı, botun videonun "üstten ne
  kadarına" baktığını belirliyor (0.28 = üstten %28). Skor kutusu daha
  aşağıdaysa bu sayıyı büyüt (örnek: 0.35), daha yukarıdaysa küçült
  (örnek: 0.20). Değiştirip GitHub'a tekrar yükle, Railway kendiliğinden
  güncelleyecek.
- **"FINAL" / "SEMIFINAL" yazısı çıkmıyor:** Bu, videonun üst kutusunda ya
  da verdiğin linkin başlığında bu kelime geçmiyorsa normaldir - bot
  uydurmuyor, sadece gördüğünü/okuduğunu yazıyor.
- **Video çok büyükse bot gönderemeyebilir:** Telegram'ın bot üzerinden
  gönderilebilecek dosyalarda boyut sınırı var. Çok uzun videolarla
  sorun yaşarsan haber ver, videoyu küçük parçalara bölecek bir ek
  adım ekleyebiliriz.

## Şu an bu bot ne yapmıyor (ileride eklenebilir)

- Videodaki spikerin ne söylediğini dinleyip anlamıyor (şu an sadece
  ekrandaki skor kutusunu okuyor). İstersen bunu ileride ekleyebiliriz,
  skoru bulmakta daha da güvenilir olur.
- Ofsayt/iptal golü ayrı ayrı anlamıyor - ama zaten orijinal videonun
  skor kutusu da iptal gollerde değişmediği için, bot da bunu otomatik
  olarak "saymamış" oluyor.
