"""Üniversite ayrıştırıcıları paketi."""
from .bilecik import BILECIK_HEADERS, parse_bilecik
from .common import (
    EPOSTA,
    ERASMUS_ULKE,
    FOLD_EXCEPTIONS,
    ISCED_FAMILY,
    _bosluk_sadelestir,
    aile_tahminle_bulundu,
    clean,
    eposta_ayikla,
    fam_fields,
    fold,
    isced_family,
    isced_kodu,
    make_search,
    parse_validity,
    tr_upper,
    ulke_onekten,
    unify_department_spelling,
)
from .esogu import ESOGU_SEVIYE, parse_esogu
from .kku import KKU_HEADERS, KKU_SEVIYE, parse_kku
from .maku import MAKU_BASLIK_ONEK, MAKU_BASLIKLAR, maku_sutunlari, parse_maku
from .marmara import (
    MARMARA_LEJANT_BASI,
    MARMARA_PARCA,
    MARMARA_SEVIYE,
    marmara_dil_sozlugu,
    marmara_kontenjan_bol,
    marmara_seviyeler,
    parse_marmara,
)

PARSERS = {
    p.__name__: p
    for p in (parse_maku, parse_marmara, parse_esogu, parse_bilecik, parse_kku)
}

__all__ = [
    "BILECIK_HEADERS",
    "EPOSTA",
    "ERASMUS_ULKE",
    "ESOGU_SEVIYE",
    "FOLD_EXCEPTIONS",
    "ISCED_FAMILY",
    "KKU_HEADERS",
    "KKU_SEVIYE",
    "MAKU_BASLIKLAR",
    "MAKU_BASLIK_ONEK",
    "MARMARA_LEJANT_BASI",
    "MARMARA_PARCA",
    "MARMARA_SEVIYE",
    "PARSERS",
    "_bosluk_sadelestir",
    "aile_tahminle_bulundu",
    "clean",
    "eposta_ayikla",
    "fam_fields",
    "fold",
    "isced_family",
    "isced_kodu",
    "make_search",
    "maku_sutunlari",
    "marmara_dil_sozlugu",
    "marmara_kontenjan_bol",
    "marmara_seviyeler",
    "parse_bilecik",
    "parse_esogu",
    "parse_kku",
    "parse_maku",
    "parse_marmara",
    "parse_validity",
    "tr_upper",
    "ulke_onekten",
    "unify_department_spelling",
]
