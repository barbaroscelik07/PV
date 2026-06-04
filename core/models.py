"""
PV-DOC — Veri Modelleri
Tüm proje verisi bu modüllerde tutulur ve JSON/SQLite ile kaydedilir.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import os


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
            "ad": self.ad,
            "limit_tipi": self.limit_tipi,
            "deger": self.deger,
            "ipk": self.ipk,
            "serbest_birakma": self.serbest_birakma,
            "raf_omru": self.raf_omru,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImpuriteSpek":
        return cls(
            ad=d.get("ad", ""),
            limit_tipi=d.get("limit_tipi", "Maks. %"),
            deger=d.get("deger", ""),
            ipk=d.get("ipk", False),
            serbest_birakma=d.get("serbest_birakma", True),
            raf_omru=d.get("raf_omru", True),
        )


@dataclass
class EtkenMaddeSpek:
    """Bir etken maddeye ait tüm analitik spesifikasyonlar."""
    ad: str = ""
    gorunus: str = ""

    # Elek Testi
    elek_spek: str = "Bilgi amaçlıdır."
    elek_ipk: bool = True

    # Bulk Dansite
    bulk_spek: str = "Bilgi amaçlıdır."
    bulk_ipk: bool = True

    # Tap Dansite
    tap_spek: str = "Bilgi amaçlıdır."
    tap_ipk: bool = True

    # Karışım Tekdüzeliği
    kt_alt: str = "85.0"
    kt_ust: str = "115.0"
    kt_ipk: bool = False
    kt_serbest_birakma: bool = False
    kt_raf_omru: bool = False

    # Miktar Tayini (Serbest Bırakma ±5%, Raf Ömrü ±10% otomatik)
    miktar_hedef_mg: str = ""
    miktar_birim: str = "mg/ftb"
    miktar_tolerans: str = "5.0"
    miktar_serbest_birakma: bool = True
    miktar_raf_omru: bool = True

    # Dissolüsyon
    dis_min_q: str = "80.0"
    dis_sure_dk: str = "45"
    dis_serbest_birakma: bool = True
    dis_raf_omru: bool = True

    # İmpüriteler
    impuriteler: List[ImpuriteSpek] = field(default_factory=list)

    # Mikrobiyolojik (sabit değerler)
    mikrobiyolojik_dahil: bool = True

    def to_dict(self) -> dict:
        return {
            "ad": self.ad,
            "gorunus": self.gorunus,
            "elek_spek": self.elek_spek,
            "elek_ipk": self.elek_ipk,
            "bulk_spek": self.bulk_spek,
            "bulk_ipk": self.bulk_ipk,
            "tap_spek": self.tap_spek,
            "tap_ipk": self.tap_ipk,
            "kt_alt": self.kt_alt,
            "kt_ust": self.kt_ust,
            "kt_ipk": self.kt_ipk,
            "kt_serbest_birakma": self.kt_serbest_birakma,
            "kt_raf_omru": self.kt_raf_omru,
            "miktar_hedef_mg": self.miktar_hedef_mg,
            "miktar_birim": self.miktar_birim,
            "miktar_tolerans": self.miktar_tolerans,
            "miktar_serbest_birakma": self.miktar_serbest_birakma,
            "miktar_raf_omru": self.miktar_raf_omru,
            "dis_min_q": self.dis_min_q,
            "dis_sure_dk": self.dis_sure_dk,
            "dis_serbest_birakma": self.dis_serbest_birakma,
            "dis_raf_omru": self.dis_raf_omru,
            "impuriteler": [i.to_dict() for i in self.impuriteler],
            "mikrobiyolojik_dahil": self.mikrobiyolojik_dahil,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EtkenMaddeSpek":
        obj = cls()
        for k, v in d.items():
            if k == "impuriteler":
                obj.impuriteler = [ImpuriteSpek.from_dict(i) for i in v]
            elif hasattr(obj, k):
                setattr(obj, k, v)
        return obj


@dataclass
class CekirdekTabletSpek:
    """Çekirdek tablet fiziksel spesifikasyonları."""
    # Ortalama Ağırlık
    ort_agirlik_hedef_mg: str = ""
    ort_agirlik_tolerans: str = "5.0"
    ort_agirlik_ipk: bool = True
    ort_agirlik_sb: bool = True
    ort_agirlik_raf: bool = True

    # Ağırlık Tekdüzeliği (hedef ağırlıktan otomatik hesaplanır)
    at_ipk: bool = True
    at_sb: bool = True
    at_raf: bool = True

    # Kalınlık
    kalinlik_hedef: str = ""
    kalinlik_alt: str = ""
    kalinlik_ust: str = ""
    kalinlik_ipk: bool = True
    kalinlik_sb: bool = True
    kalinlik_raf: bool = False

    # Çap
    cap_hedef: str = ""
    cap_alt: str = ""
    cap_ust: str = ""
    cap_ipk: bool = True
    cap_sb: bool = True
    cap_raf: bool = False

    # Sertlik
    sertlik_min: str = ""
    sertlik_birim: str = "kP"
    sertlik_ipk: bool = True
    sertlik_sb: bool = True
    sertlik_raf: bool = False

    # Aşınma (Friabilite)
    asinma_max: str = "1.0"
    asinma_ipk: bool = True
    asinma_sb: bool = True
    asinma_raf: bool = False

    # Dağılma — tablet baskı: 15 dk sabit
    dagılma_ipk: bool = True
    dagılma_sb: bool = True
    dagılma_raf: bool = False

    def ort_agirlik_alt(self) -> float:
        try:
            hedef = float(self.ort_agirlik_hedef_mg)
            tol = float(self.ort_agirlik_tolerans)
            return round(hedef * (1 - tol / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_ust(self) -> float:
        try:
            hedef = float(self.ort_agirlik_hedef_mg)
            tol = float(self.ort_agirlik_tolerans)
            return round(hedef * (1 + tol / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_spek_str(self) -> str:
        if not self.ort_agirlik_hedef_mg:
            return ""
        return (
            f"{self.ort_agirlik_hedef_mg} mg ±%{self.ort_agirlik_tolerans} "
            f"({self.ort_agirlik_alt()} – {self.ort_agirlik_ust()} mg)"
        )

    def at_limit1_alt(self) -> float:
        return self.ort_agirlik_alt()

    def at_limit1_ust(self) -> float:
        return self.ort_agirlik_ust()

    def at_limit2_alt(self) -> float:
        try:
            hedef = float(self.ort_agirlik_hedef_mg)
            return round(hedef * 0.90, 2)
        except ValueError:
            return 0.0

    def at_limit2_ust(self) -> float:
        try:
            hedef = float(self.ort_agirlik_hedef_mg)
            return round(hedef * 1.10, 2)
        except ValueError:
            return 0.0

    def at_spek_str(self) -> str:
        if not self.ort_agirlik_hedef_mg:
            return ""
        return (
            f"≤{self.at_limit1_alt()} veya ≥{self.at_limit1_ust()} mg (maks. 2/20); "
            f"Hiçbiri: ≤{self.at_limit2_alt()} veya ≥{self.at_limit2_ust()} mg"
        )

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            d[k] = v
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CekirdekTabletSpek":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj


@dataclass
class FilmTabletSpek:
    """Film tablet fiziksel spesifikasyonları."""
    gorunus: str = ""

    # Ortalama Ağırlık
    ort_agirlik_hedef_mg: str = ""
    ort_agirlik_tolerans: str = "5.0"
    ort_agirlik_ipk: bool = True
    ort_agirlik_sb: bool = True
    ort_agirlik_raf: bool = True

    # Ağırlık Tekdüzeliği
    at_ipk: bool = True
    at_sb: bool = True
    at_raf: bool = True

    # Dağılma — film kaplama: 30 dk sabit
    dagılma_ipk: bool = True
    dagılma_sb: bool = True
    dagılma_raf: bool = False

    def ort_agirlik_alt(self) -> float:
        try:
            hedef = float(self.ort_agirlik_hedef_mg)
            tol = float(self.ort_agirlik_tolerans)
            return round(hedef * (1 - tol / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_ust(self) -> float:
        try:
            hedef = float(self.ort_agirlik_hedef_mg)
            tol = float(self.ort_agirlik_tolerans)
            return round(hedef * (1 + tol / 100), 2)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def ort_agirlik_spek_str(self) -> str:
        if not self.ort_agirlik_hedef_mg:
            return ""
        return (
            f"{self.ort_agirlik_hedef_mg} mg ±%{self.ort_agirlik_tolerans} "
            f"({self.ort_agirlik_alt()} – {self.ort_agirlik_ust()} mg)"
        )

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "FilmTabletSpek":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj


@dataclass
class ProjeVerisi:
    """Ana proje veri modeli — tüm modüllerin verisi burada."""

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

    # Etken Maddeler
    etken_maddeler: List[EtkenMaddeSpek] = field(default_factory=list)

    # Spec Kartı
    cekirdek_spek: CekirdekTabletSpek = field(default_factory=CekirdekTabletSpek)
    film_spek: FilmTabletSpek = field(default_factory=FilmTabletSpek)

    # Modül verileri (ileri aşamalarda doldurulacak)
    birim_formul_satirlar: List[Dict] = field(default_factory=list)
    pvp_notlar: List[Dict] = field(default_factory=list)
    pvr_notlar: List[Dict] = field(default_factory=list)
    risk_satirlar: List[Dict] = field(default_factory=list)
    parametre_satirlar: List[Dict] = field(default_factory=list)
    ekipman_satirlar: List[Dict] = field(default_factory=list)
    numune_satirlar: List[Dict] = field(default_factory=list)
    uretim_prosesi_metni: str = ""
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
            "birim_formul_satirlar": self.birim_formul_satirlar,
            "pvp_notlar": self.pvp_notlar,
            "pvr_notlar": self.pvr_notlar,
            "risk_satirlar": self.risk_satirlar,
            "parametre_satirlar": self.parametre_satirlar,
            "ekipman_satirlar": self.ekipman_satirlar,
            "numune_satirlar": self.numune_satirlar,
            "uretim_prosesi_metni": self.uretim_prosesi_metni,
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
        obj.etken_maddeler = [
            EtkenMaddeSpek.from_dict(e) for e in d.get("etken_maddeler", [])
        ]
        if "cekirdek_spek" in d:
            obj.cekirdek_spek = CekirdekTabletSpek.from_dict(d["cekirdek_spek"])
        if "film_spek" in d:
            obj.film_spek = FilmTabletSpek.from_dict(d["film_spek"])
        obj.birim_formul_satirlar = d.get("birim_formul_satirlar", [])
        obj.pvp_notlar = d.get("pvp_notlar", [])
        obj.pvr_notlar = d.get("pvr_notlar", [])
        obj.risk_satirlar = d.get("risk_satirlar", [])
        obj.parametre_satirlar = d.get("parametre_satirlar", [])
        obj.ekipman_satirlar = d.get("ekipman_satirlar", [])
        obj.numune_satirlar = d.get("numune_satirlar", [])
        obj.uretim_prosesi_metni = d.get("uretim_prosesi_metni", "")
        obj.sapmalar = d.get("sapmalar", [])
        obj.sonuc_metni = d.get("sonuc_metni", "")
        obj.yorum_metni = d.get("yorum_metni", "")
        obj.revizyon_satirlar = d.get("revizyon_satirlar", [])
        return obj

    def save(self, filepath: str) -> None:
        """Projeyi JSON dosyasına kaydeder."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "ProjeVerisi":
        """JSON dosyasından proje yükler."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
