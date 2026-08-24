# Bu dosya boş ve olması bir karar.
#
# Olmadığında `python3 -m unittest discover` depo kökünden çalıştırıldığında
# "NO TESTS RAN" diyor · yani SESSİZCE hiçbir şey denetlemiyor ve çıkış kodu
# başarılı oluyor. Yöntemin bekçilediği hata sınıfının ta kendisi: yeşil yanan
# boşluk.
#
# Aynı eksik önce yöntem deposunda bulunup düzeltildi, buraya DÖNÜLMEDİ ·
# bir sınıfın tek örneğini düzeltip ötekini bırakmanın bedeli. Dışarıdan bir
# okuyucu yakaladı.
