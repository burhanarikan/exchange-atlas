# Güvenlik Politikası

## Desteklenen sürüm

Yalnızca `main` dalındaki güncel sürüm desteklenir. Exchange Atlas sunucu tarafı uygulama, veritabanı, kullanıcı hesabı veya çalışma anında dış istek içermeyen statik bir sitedir. Bu nedenle güvenlik değerlendirmesi; yayın paketi, JavaScript, veri üretim betikleri, GitHub Actions ve barındırma response header'larını kapsar.

## Güvenlik bildirimi

Bir güvenlik açığı bulduysanız ayrıntıları kamuya açık issue olarak paylaşmadan önce proje sahibine doğrudan yazın: `burhanarikan@yaani.com`. Bildiriminize etkilenen URL veya dosyayı, yeniden üretme adımlarını, beklenen ve gerçekleşen davranışı ve mümkünse etki değerlendirmesini ekleyin.

Kimlik bilgisi, token, parola veya kişisel veri içeren kanıtları e-posta gövdesine ya da issue'ya koymayın. Gerekirse yalnızca güvenli ve sınırlı bir kanıt paylaşın. Proje sahibi bildirimi aldıktan sonra erişim ve etkiyi doğrular; düzeltme yayımlandığında bildirimi yapan kişiye geri dönüş yapılır. Belirli bir yanıt süresi garanti edilmez, ancak güvenlik bildirimleri normal özellik taleplerinden öncelikli değerlendirilir.

## Kapsam

Kapsama; `site/` içindeki HTML, CSS, JavaScript ve üretilmiş veri paketleri; `scripts/` altındaki veri üretim kodu; GitHub Actions workflow'ları; yayın yapılandırması; CSP ve gerçek HTTP response header'ları girer. Üniversitelerin kendi web sitelerindeki güvenlik sorunları bu projenin kapsamı değildir; bu tür bulgular ilgili kurumun resmî kanalına bildirilmelidir.

## Mevcut güvenlik sınırları

Exchange Atlas kullanıcıdan veri almaz, sunucuya veri göndermez, kullanıcı hesabı oluşturmaz ve analitik/izleme servisi çalıştırmaz. Üretilen üniversite verileri kamuya açık kaynaklardan derlenir; veri sahipliği ve resmî başvuru otoritesi ilgili kurumdadır. Bu politika, veri doğruluğu taleplerinin yerine geçmez; veri hataları için issue şablonlarını veya `KAYNAK.md` belgesindeki kurumsal kanalı kullanın.
