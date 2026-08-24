# Değişiklik Günlüğü

Bu dosya, Exchange Atlas'taki kullanıcıya veya katkı sürecine anlamlı değişiklikleri kısa biçimde kaydeder. Veri yenilemelerinin ayrıntılı künyesi [`site/kaynak-kunyesi.json`](site/kaynak-kunyesi.json) içinde tutulur.

Biçim [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), sürümleme ise mümkün olduğunda [Semantic Versioning](https://semver.org/) ilkelerini izler.

## [Unreleased]

Henüz yayımlanmamış değişiklikler burada tutulur.

## [1.0.0] - 2026-08-24

### Added

- MAKÜ, Marmara Üniversitesi ve ESOGÜ için aranabilir ve filtrelenebilir Erasmus+ ikili anlaşma listeleri.
- Üniversite seçimi, bölüm/partner/ülke araması, ülke/alan/derece/kontenjan filtreleri ve iki dilli arayüz.
- MAKÜ için başvuru rehberi ve kurumların resmî kaynaklarına doğrudan bağlantılar.
- Kaynak okuma kararlarını, farkları ve kurumların düzeltme/kaldırma kanalını açıklayan belgeler.
- Statik yayın paketi, yerel fontlar, sıkı CSP ve Cloudflare Pages response header yapılandırması.
- Veri, içerik, erişilebilirlik, güvenlik ve yayın önkoşullarını denetleyen otomatik test paketi.
- Üniversite personeli, öğrenci ve geliştiriciler için issue/katkı akışları.

### Changed

- Marmara Üniversitesi kısa adı kullanıcı arayüzü ve proje belgelerinde `MÜ` olarak tutarlı hâle getirildi.
- Resmî başvuru yönlendirmeleri Erasmus+ koordinatörlüğü, uluslararası ilişkiler birimi veya diğer ilgili birimi kapsayacak şekilde netleştirildi.
- Alan okuma rehberi ön lisans, lisans, yüksek lisans ve doktora kontenjan gösterimlerini daha açık anlatacak şekilde güncellendi.
- Alt sayfaların kanonik sosyal metadata’sı, Twitter başlıkları ve açıklamaları tamamlandı; footer farklı dil ve ekran genişliklerinde sıkılaştırıldı.
- Sosyal önizleme kartı, güncel canlı arayüzü ve Marmara Üniversitesi’nin `MÜ` kısa adını yansıtacak şekilde yenilendi.
- LinkedIn’in eski kart cache’ini aşmak için normal route’ları etkilemeyen noindex paylaşım alias’ı eklendi.

[Unreleased]: https://github.com/burhanarikan/exchange-atlas/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/burhanarikan/exchange-atlas/releases/tag/v1.0.0
