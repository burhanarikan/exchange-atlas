# Yazı tipleri · lisans durumu

Bu klasördeki `.woff2` dosyaları **bu projenin telifi altında değildir.** Depo kökündeki
`LICENSE` (MIT) yalnız projenin kendi kaynak kodunu kapsar; buradaki dosyalar kendi
lisanslarıyla gelir.

| Aile | Kaynak proje | Lisans |
|---|---|---|
| Inter | rsms/inter | SIL Open Font License 1.1 |
| Manrope | sharanda/manrope | SIL Open Font License 1.1 |

## Lisans metinleri

| Dosya | Kaynağı |
|---|---|
| `OFL-Inter.txt` | `github.com/rsms/inter` → `LICENSE.txt` |
| `OFL-Manrope.txt` | `github.com/google/fonts` → `ofl/manrope/OFL.txt` |

İkisi de **birebir indirildi**, yeniden yazılmadı. Bu önemli: ezberden ya da yeniden
ifade edilerek yazılan bir lisans metni geçersizdir, hatalı bir lisans dosyası hiç
olmamasından kötüdür.

Dosyaların başındaki telif satırları (`Copyright … The Inter Project Authors`,
`Copyright 2018 The Manrope Project Authors`) **olduğu gibi kalmalı**, OFL 1.1 bunu
şart koşuyor.

### Neden ayrı dosya gerekiyordu

Alt küme (subset) üretimi sırasında `.woff2` dosyalarının içindeki telif kayıtları
düşmüş; dosyalar kendi başlarına lisansı taşımıyor. `fonts.css` içinde "OFL lisansı"
diye bir cümle vardı ama o bir **beyan**, lisans belgesi değil.

Bu eksik `tests/test_yayina_hazirlik.py` ile denetleniyor: lisans dosyaları yoksa,
boşsa ya da OFL metni gibi görünmüyorsa test kırılır.

### Manrope'un kaynağı neden Google Fonts deposu

Yazı tipinin kendi deposunda (`sharanda/manrope`) lisans dosyası bulunabilir bir yolda
değil (denenen yolların hepsi 404 verdi). Google Fonts deposu Manrope'u OFL altında
dağıtıyor ve lisans metnini `ofl/manrope/OFL.txt` yolunda tutuyor; telif satırı yine
özgün projeyi (`sharanda/manrope`) gösteriyor.

## Alt küme üretimi

Dosyalar latin ve latin-ext alt kümelerine bölünmüş (`unicode-range` ile `fonts.css`
içinde eşleniyor). Bu, ziyaretçinin yalnız ihtiyaç duyduğu aralığı indirmesini
sağlıyor. Üretim komutu kayıtlı değil. Yeniden üretmek gerekirse yordam da buraya
yazılmalı.
