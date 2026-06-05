"""
PV-DOC — Veri Modelleri
Tüm proje verisi bu modüllerde tutulur ve JSON ile kaydedilir.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum
import json


class UrunFormu(Enum):
    TABLET = "Tablet"
    FILM_TABLET = "Film Tablet"
    KAPSUL = "Kapsül"
    KAPSUL_FILM_TABLET = "Kapsül + Film Tablet"


class TabletYapisi(Enum):
    TEK_KATMAN = "Tek Katman"
    CIFT_KATMAN = "Çift Katman"


class LimitTipi(Enum):
    ARALIK = "Aralık (%min – %max)"
    MIN = "Minimum (NLT)"
    MAX = "Maksimum (NMT)"
    HEDEF_TOLERANS = "Hedef ± Tolerans"
    SABIT_METIN = "Sabit Metin"
    BILGI_AMACLI = "Bilgi Amaçlıdır"


# ─── İmpürite ─────────────────────────────────────────────────────────────────

@dataclass
class ImpuriteSpek:
    ad: str = ""
    limit_tipi: str = "Maks. %"
    deger: str = ""
    ipk: bool = False
    serbest_birakma: bool = True
    raf_omru: bool = True

    def to_dict(self) -> dict:
        return {
            "ad": self.ad, "limit_tipi": self.limit_tipi,
            "deger": self.deger, "ipk": self.ipk,
            "serbest_birakma": self.serbest_birakma,
            "raf_omru": self.raf_omru,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImpuriteSpek":
        return cls(
            ad=d.get("ad", ""), limit_tipi=d.get("limit_tipi", "Maks. %"),
            deger=d.get("deger", ""), ipk=d.get("ipk", False),
            serbest_birakma=d.get("serbest_birakma", True),
            raf_omru=d.get("raf_omru", True),
        )


# ─── Etken Madde Analitik Spek ────────────────────────────────────────────────

@dataclass
class EtkenMaddeAnalitikSpek:
    """
    Bir etken maddeye ait analitik spesifikasyonlar.
    Bulk, Çekirdek Tablet ve Film Tablet için ortak kullanılır.
    Her operasyon kendi checkbox'larını taşır.
    """
    ad: str = ""  # Etken madde adı (referans)

    # Miktar Tayini — tüm operasyonlarda aynı spek, bir kez girilir
    miktar_hedef: str = ""
    miktar_birim: str = "mg/ftb"
    miktar_tolerans: str = "5.0"
    miktar_ipk: bool = False
    miktar_sb: bool = True
    miktar_raf: bool = True

    # Teşhis — sabit metin, her operasyonda var
    teshis_ipk_bulk: bool = True
    teshis_ipk_cekirdek: bool = False
    teshis_ipk_film: bool = False

    # Dissolüsyon — Bulk'ta yok, Çekirdek ve Film'de var
    dis_min_q: str = "80.0"
    dis_sure_dk: str = "45"
    dis_sb: bool = True
    dis_raf: bool = True

    # İlgili Bileşikler (İmpüriteler)
    impuriteler: List[ImpuriteSpek] = field(default_factory=list)
    imp_ipk: bool = False
    imp_sb: bool = True
    imp_raf: bool = True

    def to_dict(self) -> dict:
        return {
            "ad": self.ad,
            "miktar_hedef": self.miktar_hedef,
            "miktar_birim": self.miktar_birim,
            "miktar_tolerans": self.miktar_tolerans,
            "miktar_ipk": self.miktar_ipk,
            "miktar_sb": self.miktar_sb,
            "miktar_raf": self.miktar_raf,
            "teshis_ipk_bulk": self.teshis_ipk_bulk,
            "teshis_ipk_cekirdek": self.teshis_ipk_cekirdek,
            "teshis_ipk_film": self.teshis_ipk_film,
            "dis_min_q": self.dis_min_q,
            "dis_sure_dk": self.dis_sure_dk,
            "dis_sb": self.dis_sb,
            "dis_raf": self.dis_raf,
            "impuriteler": [i.to_dict() for i in self.impuriteler],
            "imp_ipk": self.imp_ipk,
            "imp_sb": self.imp_sb,
            "imp_raf": self.imp_raf,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EtkenMaddeAnalitikSpek":
        obj = cls()
        for k, v in d.items():
            if k == "impuriteler":
                obj.impuriteler = [ImpuriteSpek.from_dict(i) for i in v]
            elif hasattr(obj, k):
                setattr(obj, k, v)
        return obj


# ─── Bulk Katman Spek ─────────────────────────────────────────────────────────

@dataclass
class BulkKatmanSpek:
    """
    Tek bir bulk katmanına ait spesifikasyonlar.
    Tek katmanda: 1 adet BulkKatmanSpek ("Bulk Karışımı")
    Çift katmanda: 2 adet BulkKatmanSpek ("Katman I Bulk", "Katman II Bulk")
    """
    katman_adi: str = "Bulk Karışımı"  # "Katman I Bulk" veya "Katman II Bulk"

    # Genel — tüm katman için tek spek
    gorunus: str = ""
    gorunus_ipk: bool = True

    elek_ipk: bool = True
    bulk_dans_ipk: bool = True
    tap_dans_ipk: bool = True

    # Mikrobiyolojik — katman başına tek spek
    mikro_ipk: bool = False
    mikro_sb: bool = False
    mikro_raf: bool = False

    # Karışım Tekdüzeliği — katmandaki her etken için
    kt_alt: str = "85.0"
    kt_ust: str = "115.0"
    kt_ipk: bool = False
    kt_sb: bool = False
    kt_raf: bool = False

    # Bu katmana ait etken madde indeksleri (ProjeVerisi.etken_maddeler listesine index)
    etken_indeksler: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "katman_adi": self.katman_adi,
            "gorunus": self.gorunus,
            "gorunus_ipk": self.gorunus_ipk,
            "elek_ipk": self.elek_ipk,
            "bulk_dans_ipk": self.bulk_dans_ipk,
            "tap_dans_ipk": self.tap_dans_ipk,
            "mikro_ipk": self.mikro_ipk,
            "mikro_sb": self.mikro_sb,
            "mikro_raf": self.mikro_raf,
            "kt_alt": self.kt_alt,
            "kt_ust": self.kt_ust,
            "kt_ipk": self.kt_ipk,
            "kt_sb": self.kt_sb,
            "kt_raf": self.kt_raf,
            "etken_indeksler": self.etken_indeksler,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BulkKatmanSpek":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj


# ─── Çekirdek Tablet Fiziksel Spek ────────────────────────────────────────────

@dataclass
class CekirdekTabletSpek:
    """Çekirdek tablet fiziksel spesifikasyonları."""
    gorunus: str = ""
    gorunus_ipk: bool = True
    gorunus_sb: bool = True
    gorunus_raf: bool = True

    ort_agirlik_hedef_mg: str = ""
    ort_agirlik_tolerans: str = "5.0"
    ort_agirlik_ipk: bool = True
    ort_agirlik_sb: bool = True
    ort_agirlik_raf: bool = True

    at_l1_alt: str = ""
    at_l1_ust: str = ""
    at_l2_alt: str = ""
    at_l2_ust: str = ""
    at_ipk: bool = True
    at_sb: bool = True
    at_raf: bool = True

    kalinlik_hedef: str = ""
    kalinlik_alt: str = ""
    kalinlik_ust: str = ""
    kalinlik_ipk: bool = True
    kalinlik_sb: bool = True
    kalinlik_raf: bool = False

    cap_hedef: str = ""
    cap_alt: str = ""
    cap_ust: str = ""
    cap_ipk: bool = True
    cap_sb: bool = True
    cap_raf: bool = False

    sertlik_min: str = ""
    sertlik_max: str = ""
    sertlik_birim: str = "kP"
    sertlik_ipk: bool = True
    sertlik_sb: bool = True
    sertlik_raf: bool = False

    asinma_max: str = "1.0"
    asinma_ipk: bool = True
    asinma_sb: bool = True
    asinma_raf: bool = False

    dagılma_ipk: bool = True
    dagılma_sb: bool = True
    dagılma_raf: bool = False

    # Mikrobiyolojik — çekirdek tablet için tek
    mikro_ipk: bool = False
    mikro_sb: bool = False
    mikro_raf: bool = False

    def ort_agirlik_alt(self) -> float:
        try:
            return round(float(self.ort_agirlik_hedef_mg) * (1 - float(self.ort_agirlik_tolerans) / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_ust(self) -> float:
        try:
            return round(float(self.ort_agirlik_hedef_mg) * (1 + float(self.ort_agirlik_tolerans) / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_spek_str(self) -> str:
        if not self.ort_agirlik_hedef_mg:
            return ""
        return f"{self.ort_agirlik_hedef_mg} mg ±%{self.ort_agirlik_tolerans} ({self.ort_agirlik_alt()} – {self.ort_agirlik_ust()} mg)"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "CekirdekTabletSpek":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj


# ─── Film Tablet Fiziksel Spek ────────────────────────────────────────────────

@dataclass
class FilmTabletSpek:
    """Film tablet fiziksel spesifikasyonları."""
    gorunus: str = ""
    gorunus_ipk: bool = True
    gorunus_sb: bool = True
    gorunus_raf: bool = True

    ort_agirlik_hedef_mg: str = ""
    ort_agirlik_tolerans: str = "5.0"
    ort_agirlik_ipk: bool = True
    ort_agirlik_sb: bool = True
    ort_agirlik_raf: bool = True

    at_l1_alt: str = ""
    at_l1_ust: str = ""
    at_l2_alt: str = ""
    at_l2_ust: str = ""
    at_ipk: bool = True
    at_sb: bool = True
    at_raf: bool = True

    dagılma_ipk: bool = True
    dagılma_sb: bool = True
    dagılma_raf: bool = False

    # Mikrobiyolojik — film tablet için tek
    mikro_ipk: bool = False
    mikro_sb: bool = False
    mikro_raf: bool = False

    def ort_agirlik_alt(self) -> float:
        try:
            return round(float(self.ort_agirlik_hedef_mg) * (1 - float(self.ort_agirlik_tolerans) / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_ust(self) -> float:
        try:
            return round(float(self.ort_agirlik_hedef_mg) * (1 + float(self.ort_agirlik_tolerans) / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_spek_str(self) -> str:
        if not self.ort_agirlik_hedef_mg:
            return ""
        return f"{self.ort_agirlik_hedef_mg} mg ±%{self.ort_agirlik_tolerans} ({self.ort_agirlik_alt()} – {self.ort_agirlik_ust()} mg)"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "FilmTabletSpek":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj


# ─── Eski EtkenMaddeSpek (geriye dönük uyumluluk) ────────────────────────────

@dataclass
class EtkenMaddeSpek:
    """
    Geriye dönük uyumluluk için korundu.
    Yeni kod EtkenMaddeAnalitikSpek kullanır.
    """
    ad: str = ""
    gorunus: str = ""
    elek_spek: str = "Bilgi amaçlıdır."
    elek_ipk: bool = True
    bulk_spek: str = "Bilgi amaçlıdır."
    bulk_ipk: bool = True
    tap_spek: str = "Bilgi amaçlıdır."
    tap_ipk: bool = True
    kt_alt: str = "85.0"
    kt_ust: str = "115.0"
    kt_ipk: bool = False
    kt_serbest_birakma: bool = False
    kt_raf_omru: bool = False
    miktar_hedef_mg: str = ""
    miktar_birim: str = "mg/ftb"
    miktar_tolerans: str = "5.0"
    miktar_serbest_birakma: bool = True
    miktar_raf_omru: bool = True
    dis_min_q: str = "80.0"
    dis_sure_dk: str = "45"
    dis_serbest_birakma: bool = True
    dis_raf_omru: bool = True
    impuriteler: List[ImpuriteSpek] = field(default_factory=list)
    mikrobiyolojik_dahil: bool = True

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "impuriteler"}
        d["impuriteler"] = [i.to_dict() for i in self.impuriteler]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "EtkenMaddeSpek":
        obj = cls()
        for k, v in d.items():
            if k == "impuriteler":
                obj.impuriteler = [ImpuriteSpek.from_dict(i) for i in v]
            elif hasattr(obj, k):
                setattr(obj, k, v)
        return obj


# ─── Ana Proje Verisi ─────────────────────────────────────────────────────────

@dataclass
class ProjeVerisi:
    """Ana proje veri modeli."""

    # Temel Bilgiler
    firma_adi: str = ""
    urun_adi: str = ""
    pvp_dokuman_no: str = ""
    pvr_dokuman_no: str = ""
    revizyon_no: str = "00"
    tarih: str = ""
    urun_formu: str = UrunFormu.FILM_TABLET.value
    tablet_yapisi: str = TabletYapisi.TEK_KATMAN.value

    # Seri Bilgileri
    seri_1_no: str = ""
    seri_2_no: str = ""
    seri_3_no: str = ""
    seri_boyutu: str = ""

    # Etken Madde Listesi (sadece ad ve katman ataması)
    etken_maddeler: List[EtkenMaddeSpek] = field(default_factory=list)

    # Spec Kartı — Yeni yapı
    cekirdek_spek: CekirdekTabletSpek = field(default_factory=CekirdekTabletSpek)
    film_spek: FilmTabletSpek = field(default_factory=FilmTabletSpek)
    bulk_katmanlar: List[BulkKatmanSpek] = field(default_factory=list)
    etken_analitik_spekler: List[EtkenMaddeAnalitikSpek] = field(default_factory=list)

    # Modül verileri
    birim_formul_satirlar: List[Dict] = field(default_factory=list)
    pvp_notlar: List[Dict] = field(default_factory=list)
    pvr_notlar: List[Dict] = field(default_factory=list)
    risk_satirlar: List[Dict] = field(default_factory=list)
    parametre_satirlar: List[Dict] = field(default_factory=list)
    ekipman_satirlar: List[Dict] = field(default_factory=list)
    numune_satirlar: List[Dict] = field(default_factory=list)
    uretim_prosesi_metni: str = ""
    proses_adimlar: List[Dict] = field(default_factory=list)
    akis_elemanlar: List[Dict] = field(default_factory=list)
    akis_oklar: List[Dict] = field(default_factory=list)
    sapmalar: List[Dict] = field(default_factory=list)
    sonuc_metni: str = ""
    yorum_metni: str = ""
    revizyon_satirlar: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "firma_adi": self.firma_adi,
            "urun_adi": self.urun_adi,
            "pvp_dokuman_no": self.pvp_dokuman_no,
            "pvr_dokuman_no": self.pvr_dokuman_no,
            "revizyon_no": self.revizyon_no,
            "tarih": self.tarih,
            "urun_formu": self.urun_formu,
            "tablet_yapisi": self.tablet_yapisi,
            "seri_1_no": self.seri_1_no,
            "seri_2_no": self.seri_2_no,
            "seri_3_no": self.seri_3_no,
            "seri_boyutu": self.seri_boyutu,
            "etken_maddeler": [e.to_dict() for e in self.etken_maddeler],
            "cekirdek_spek": self.cekirdek_spek.to_dict(),
            "film_spek": self.film_spek.to_dict(),
            "bulk_katmanlar": [b.to_dict() for b in self.bulk_katmanlar],
            "etken_analitik_spekler": [e.to_dict() for e in self.etken_analitik_spekler],
            "birim_formul_satirlar": self.birim_formul_satirlar,
            "pvp_notlar": self.pvp_notlar,
            "pvr_notlar": self.pvr_notlar,
            "risk_satirlar": self.risk_satirlar,
            "parametre_satirlar": self.parametre_satirlar,
            "ekipman_satirlar": self.ekipman_satirlar,
            "numune_satirlar": self.numune_satirlar,
            "uretim_prosesi_metni": self.uretim_prosesi_metni,
            "proses_adimlar": self.proses_adimlar,
            "akis_elemanlar": self.akis_elemanlar,
            "akis_oklar": self.akis_oklar,
            "sapmalar": self.sapmalar,
            "sonuc_metni": self.sonuc_metni,
            "yorum_metni": self.yorum_metni,
            "revizyon_satirlar": self.revizyon_satirlar,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProjeVerisi":
        obj = cls()
        obj.firma_adi = d.get("firma_adi", "")
        obj.urun_adi = d.get("urun_adi", "")
        obj.pvp_dokuman_no = d.get("pvp_dokuman_no", "")
        obj.pvr_dokuman_no = d.get("pvr_dokuman_no", "")
        obj.revizyon_no = d.get("revizyon_no", "00")
        obj.tarih = d.get("tarih", "")
        obj.urun_formu = d.get("urun_formu", UrunFormu.FILM_TABLET.value)
        obj.tablet_yapisi = d.get("tablet_yapisi", TabletYapisi.TEK_KATMAN.value)
        obj.seri_1_no = d.get("seri_1_no", "")
        obj.seri_2_no = d.get("seri_2_no", "")
        obj.seri_3_no = d.get("seri_3_no", "")
        obj.seri_boyutu = d.get("seri_boyutu", "")
        obj.etken_maddeler = [EtkenMaddeSpek.from_dict(e) for e in d.get("etken_maddeler", [])]
        if "cekirdek_spek" in d:
            obj.cekirdek_spek = CekirdekTabletSpek.from_dict(d["cekirdek_spek"])
        if "film_spek" in d:
            obj.film_spek = FilmTabletSpek.from_dict(d["film_spek"])
        obj.bulk_katmanlar = [BulkKatmanSpek.from_dict(b) for b in d.get("bulk_katmanlar", [])]
        obj.etken_analitik_spekler = [EtkenMaddeAnalitikSpek.from_dict(e) for e in d.get("etken_analitik_spekler", [])]
        obj.birim_formul_satirlar = d.get("birim_formul_satirlar", [])
        obj.pvp_notlar = d.get("pvp_notlar", [])
        obj.pvr_notlar = d.get("pvr_notlar", [])
        obj.risk_satirlar = d.get("risk_satirlar", [])
        obj.parametre_satirlar = d.get("parametre_satirlar", [])
        obj.ekipman_satirlar = d.get("ekipman_satirlar", [])
        obj.numune_satirlar = d.get("numune_satirlar", [])
        obj.uretim_prosesi_metni = d.get("uretim_prosesi_metni", "")
        obj.proses_adimlar = d.get("proses_adimlar", [])
        obj.akis_elemanlar = d.get("akis_elemanlar", [])
        obj.akis_oklar = d.get("akis_oklar", [])
        obj.sapmalar = d.get("sapmalar", [])
        obj.sonuc_metni = d.get("sonuc_metni", "")
        obj.yorum_metni = d.get("yorum_metni", "")
        obj.revizyon_satirlar = d.get("revizyon_satirlar", [])
        return obj

    def save(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "ProjeVerisi":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def bulk_katmanlari_olustur(self):
        """
        Proje bilgilerine göre bulk katmanlarını otomatik oluşturur.
        Spec kartı ilk açıldığında çağrılır.
        """
        if self.bulk_katmanlar:
            return  # Zaten oluşturulmuş

        n = len(self.etken_maddeler)
        if self.tablet_yapisi == TabletYapisi.TEK_KATMAN.value:
            katman = BulkKatmanSpek(katman_adi="Bulk Karışımı")
            katman.etken_indeksler = list(range(n))
            self.bulk_katmanlar = [katman]
        else:  # Çift katman
            k1 = BulkKatmanSpek(katman_adi="Katman I Bulk")
            k2 = BulkKatmanSpek(katman_adi="Katman II Bulk")
            # Varsayılan: etkenler eşit bölünür
            yari = max(1, n // 2)
            k1.etken_indeksler = list(range(yari))
            k2.etken_indeksler = list(range(yari, n))
            self.bulk_katmanlar = [k1, k2]

        # Analitik spekleri oluştur
        if not self.etken_analitik_spekler:
            for em in self.etken_maddeler:
                spek = EtkenMaddeAnalitikSpek(ad=em.ad)
                # Mevcut veriden taşı
                spek.miktar_hedef = em.miktar_hedef_mg
                spek.miktar_birim = em.miktar_birim
                spek.miktar_tolerans = em.miktar_tolerans
                spek.dis_min_q = em.dis_min_q
                spek.dis_sure_dk = em.dis_sure_dk
                spek.impuriteler = em.impuriteler[:]
                self.etken_analitik_spekler.append(spek)
