# Maç Skor Overlay Botu

Bu bot, gönderdiğin maç videosunu izler, videonun üstündeki skor kutusunu
okur ve yeşil ekranlı (kroma yeşili), iki takım logosunun yan yana durduğu,
skorun gol oldukça güncellendiği bir video üretir. Bunu kendi videonun
üzerine CapCut gibi bir programda bindirebilirsin.

## Botu nasıl kurarsın (adım adım)

### 1. Bu dosyaları GitHub'a yükle
- github.com'da yeni bir repo (proje) oluştur.
- Bu klasördeki **TÜM dosya ve klasörleri** oraya yükle - özellikle
  şunların gerçekten yüklendiğinden emin ol (bunlar gözden kaçmaya
  müsait, daha önce sorun yaşadık):
  - `Dockerfile` (büyük harfle başlıyor, uzantısı yok)
  - `fonts` klasörü (içindeki .ttf dosyalarıyla birlikte)
- En garantili yöntem: GitHub'ın web sitesinde reponu aç, "Add file" →
  "Upload files" de, bilgisayarındaki `mac-skor-botu` klasörünün
  İÇİNDEKİ her şeyi (klasörler dahil) oraya sürükleyip bırak.

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
- Railway, repodaki `Dockerfile`'ı görüp ona göre kuracak (ffmpeg ve
  tesseract dahil her şeyi kendisi kuruyor, birkaç dakika sürebilir).
- **Kurulumu doğrulamak için:** Railway'de projene tıkla, üstteki
  **"Build Logs"** sekmesine bak. Orada `ffmpeg` ve `tesseract-ocr`
  kelimelerinin geçtiği satırlar görmelisin - bu, kurulumun doğru
  gittiğinin kanıtı.

### 4. Botu test et
- Telegram'da botunu bul, direkt bir video linki gönder (artık `/start`
  yazmana bile gerek yok, link atman yeterli).
- Sırasıyla: (bot linkten indiremezse videoyu doğrudan yüklemeni
  ister), birinci takım logosu, ikinci takım logosu gönder.
- Bot "video hazırlanıyor, bekleyin" diyecek, birkaç dakika içinde
  yeşil ekranlı skor videosunu gönderecek.
- Herhangi bir adımda yeni bir link gönderirsen, bot otomatik olarak
  o linkle baştan başlar.

## Önemli: neden önce link isteniyor?

Telegram'ın kendi kuralı gereği bir bot, Telegram'a yüklenen dosyaları
**sadece 20 MB'a kadar** indirebiliyor. Maç videoları çoğu zaman bundan
büyük olduğu için, bot videoyu Telegram üzerinden değil, **doğrudan
linkten (YouTube'dan)** indiriyor - bu sınıra hiç takılmıyor. Link bir
sebeple çalışmazsa (özel video vb.), bot sana videoyu direkt yüklemeni
ister; o durumda video 20 MB'dan küçük olmalı.


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
- **"ffmpeg bulunamadı" ya da "tesseract bulunamadı" hatası:** Bu, 1.
  adımdaki `Dockerfile`'ın GitHub'a gerçekten yüklenmediği anlamına
  gelir. Reponu kontrol et, `Dockerfile` yoksa tekrar yükle.

## Link "indirilemedi" diyorsa - cookies eklemen gerekiyor (önemli)

YouTube artık pek çok videoda "bu bir bot mu, insan mı?" diye
sorguluyor ve Railway gibi sunucu adreslerinden gelen istekleri
reddedebiliyor ("Sign in to confirm you're not a bot" hatası). Bot
bunu aşmak için birkaç farklı yöntemi otomatik dener, ama bazı
videolarda bu yeterli olmuyor - o zaman **cookies eklemek gerekiyor**
(YouTube'a, senin kendi hesabınla giriş yapmış gibi görünmesini sağlar):

1. Chrome'da şu eklentiyi kur: **"Get cookies.txt LOCALLY"**
   (Chrome Web Mağazası'ndan aratabilirsin).
2. youtube.com'a git, kendi hesabınla oturum aç.
3. Eklentiye tıkla, "Export" veya "Download" de - bir `cookies.txt`
   dosyası inecek.
4. O dosyayı bir metin düzenleyiciyle (Not Defteri vb.) aç, İÇİNDEKİ
   her şeyi kopyala.
5. Railway'de projenin **Variables** kısmına git, yeni bir değişken ekle:
   - İsim: `YTDLP_COOKIES`
   - Değer: az önce kopyaladığın metnin tamamı
6. Kaydet, Railway yeniden deploy edecek.

Bunu yaptıktan sonra bot, YouTube'a senin oturumunla giriyormuş gibi
davranacağı için "sign in to confirm you're not a bot" hatası
büyük ölçüde ortadan kalkacak.

**Dikkat:** Bu cookies dosyası senin YouTube hesabınla ilişkili özel bir
bilgi - kimseyle paylaşma, sadece Railway'in Variables kısmına (ki bu
sadece senin görebileceğin bir yer) ekle.

## Şu an bu bot ne yapmıyor (ileride eklenebilir)

- Videodaki spikerin ne söylediğini dinleyip anlamıyor (şu an sadece
  ekrandaki skor kutusunu okuyor). İstersen bunu ileride ekleyebiliriz,
  skoru bulmakta daha da güvenilir olur.
- Ofsayt/iptal golü ayrı ayrı anlamıyor - ama zaten orijinal videonun
  skor kutusu da iptal gollerde değişmediği için, bot da bunu otomatik
  olarak "saymamış" oluyor.
