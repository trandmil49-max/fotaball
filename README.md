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
- Sırasıyla: video linki, (bot linkten indiremezse videoyu doğrudan
  yüklemeni ister), birinci takım logosu, ikinci takım logosu gönder.
- Bot "video hazırlanıyor, bekleyin" diyecek, birkaç dakika içinde
  yeşil ekranlı skor videosunu gönderecek.

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

## Link bazen "indirilemedi" diyorsa (YouTube'un kendi engeli)

YouTube, sunucu/veri merkezi adreslerinden (Railway de bu kategoride)
gelen indirme isteklerini bazen "bot" sanıp engelliyor. Bot bunu aşmak
için otomatik olarak birkaç farklı yöntemi sırayla dener (telefon
uygulamasıymış gibi görünme gibi) - çoğu zaman bu yeterli olur.

Eğer bazı videolarda hâlâ "indirilemedi" derse, en kesin çözüm
**cookies** eklemektir (YouTube'a senin hesabınla girmiş gibi görünmesini
sağlar):

1. Bilgisayarında Chrome'a "Get cookies.txt LOCALLY" adlı eklentiyi kur.
2. youtube.com'da oturum açıkken bu eklentiyle cookies.txt dosyasını
   indir.
3. O dosyanın İÇERİĞİNİ (metnini) kopyala.
4. Railway'de **Variables** kısmına yeni bir değişken ekle:
   - İsim: `YTDLP_COOKIES`
   - Değer: kopyaladığın metin
5. Deploy'a bas.

Bu adım **zorunlu değil** - önce cookies olmadan dene, çoğu video zaten
çalışacaktır. Sadece belirli videolar inatla indirilemezse bu son çare.

## Şu an bu bot ne yapmıyor (ileride eklenebilir)

- Videodaki spikerin ne söylediğini dinleyip anlamıyor (şu an sadece
  ekrandaki skor kutusunu okuyor). İstersen bunu ileride ekleyebiliriz,
  skoru bulmakta daha da güvenilir olur.
- Ofsayt/iptal golü ayrı ayrı anlamıyor - ama zaten orijinal videonun
  skor kutusu da iptal gollerde değişmediği için, bot da bunu otomatik
  olarak "saymamış" oluyor.
