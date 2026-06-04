# PV-DOC — Proses Validasyon Doküman Sistemi

Pharmaceutical solid dosage form (Tablet, Film Tablet, Kapsül) için
otomatik proses validasyon protokolü (PVP) ve raporu (PVR) üreten
masaüstü uygulama.

## İndirme

**[⬇️ Son Sürümü İndir](../../releases/latest)** — `PV-DOC.exe`

Kurulum gerekmez, doğrudan çalıştırın.

## Özellikler

- Spec kartı ile tek seferlik spesifikasyon girişi
- PVP ve PVR otomatik oluşturma
- Sonuç tablolarını otomatik doldurma (spec sınırlarında)
- Word (.docx) ve PDF çıktı
- Proje kaydet/yükle sistemi
- Spec şablonu kaydet/yükle

## Gereksinimler

- Windows 10/11 (64-bit)
- İnternet bağlantısı gerekmez

## Geliştirici Notları

```bash
pip install -r requirements.txt
python main.py
```

## Build

Her `.py` dosyası değiştiğinde GitHub Actions otomatik olarak
`PV-DOC.exe` oluşturur. Actions sekmesinden indirebilirsiniz.
