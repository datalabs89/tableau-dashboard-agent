# Tableau Dashboard Agent 🚀

Agent khusus untuk **membuat** dan **mendesain ulang (redesign)** dashboard Tableau secara otomatis, terstruktur, dan tervalidasi menggunakan ekosistem repositori resmi [Tableau](https://github.com/tableau).

---

## 🛠️ Integrasi Repositori Tableau & Tools

Agent ini mengintegrasikan repositori dan standar resmi dari Tableau:

1. **`tableau/document-api-python`**:
   - Membaca, menginspeksi, dan memodifikasi metadata workbook (`.twb`) dan packaged workbook (`.twbx`).
   - Manajemen koneksi database, server, nama database, kredensial, dan pemetaan field dependencies.
2. **`tableau/tableau-document-schemas`**:
   - Skema resmi XML Schema Definition (XSD) Tableau (`twb_2026.1.0.xsd`, `twb_2026.2.0.xsd`).
   - Validasi sintaksis dan integritas dokumen XML sebelum workbook dibuka di Tableau Desktop atau dipublikasikan.
3. **`tableau/Visualization-Linting`**:
   - Audit visual dan analitis: pencegahan pemotongan sumbu (zero-baseline rule untuk diagram batang), deteksi sumbu terbalik (reversed axes), pencegahan over-encoding warna, dan analisis keterbacaan.
4. **`tableau/tableau_langchain`**:
   - Pola agen otonom, integrasi prompt analitik, dan semantik VizQL Data Service.
5. **`cwtwb` & Declarative Layout Engine**:
   - Pembuatan dan restrukturisasi layout container bertingkat (`layout-basic`, `layout-flow` Horizontal & Vertical).
   - Pengaturan padding, margin, border, warna latar (card design), dan aksi interaktif (*filter on click* & *highlight*).

---

## 🎨 Design System & Tema Tersedia

Agent menyediakan sistem desain eksekutif siap pakai:
- **`executive-light`**: Tampilan modern C-level. Kanvas abu-abu lembut (`#F1F5F9`), kartu putih bersih (`#FFFFFF`), border halus (`#E2E8F0`), padding 8px, aksen biru korporat.
- **`executive-dark`**: Tampilan command center modern. Kanvas gelap (`#0B0F19`), kartu kontras tinggi (`#151D2F`), aksen cyan (`#38BDF8`).
- **`minimalist-slate`**: Desain minimalis berdensitas tinggi untuk laporan operasional dan tabel metrik padat.

---

## 📦 Instalasi & Setup

```bash
# Clone atau buka direktori
cd C:\Users\User\tableau-dashboard-agent

# Install dependensi
pip install -e .
```

---

## 💻 Panduan Penggunaan CLI

### 1. Inspeksi Workbook
Melihat daftar lembar kerja (worksheets), dashboard, sumber data, dan koneksi:
```bash
python -m tableau_dashboard_agent inspect "C:\path\to\workbook.twbx"
```

### 2. Audit Visual & Struktural (Visual Linting)
Menganalisis kesalahan desain, zona melayang (*floating zones*), dan ketiadaan interaktivitas:
```bash
python -m tableau_dashboard_agent lint "C:\path\to\workbook.twbx"
```

### 3. Mendesain Ulang Dashboard (Redesign)
Mengubah dashboard yang berantakan atau bertipe floating menjadi layout container eksekutif yang rapi dan terstruktur:
```bash
python -m tableau_dashboard_agent redesign "C:\path\to\workbook.twbx" \
    --output "C:\path\to\workbook_Redesigned.twbx" \
    --theme executive-light \
    --target "Overview"
```

### 4. Membuat Dashboard Baru (Create)
Membuat dashboard baru dari lembar kerja yang ada dengan layout hierarkis (Header banner + KPI Ribbon + Main Grid):
```bash
python -m tableau_dashboard_agent create "C:\path\to\workbook.twbx" \
    --title "Executive Leadership View" \
    --subtitle "KPIs and Performance Breakdown" \
    --kpis "Total Sales" \
    --charts "SalesbySegment" "ShippingTrend" \
    --theme executive-light \
    --output "C:\path\to\workbook_New.twbx"
```

### 5. Validasi Skema Resmi Tableau
Memvalidasi struktur XML terhadap skema resmi XSD 2026.1/2026.2:
```bash
python -m tableau_dashboard_agent validate "C:\path\to\workbook.twb"
```

### 6. Ganti Koneksi / Server Data Source
Mengubah server atau database sumber data secara aman tanpa membuka Tableau Desktop:
```bash
python -m tableau_dashboard_agent swap-conn "C:\path\to\workbook.twb" \
    --server "prod-db.corp.internal" \
    --dbname "SalesData"
```

---

## 🐍 Penggunaan via Python API

```python
from tableau_dashboard_agent import TableauDashboardAgent

agent = TableauDashboardAgent(default_theme="executive-light")

# 1. Audit
lint_report = agent.lint_workbook("my_dashboard.twbx")
print(f"Health score: {lint_report.score}/100")

# 2. Redesign
redesign_result = agent.redesign_dashboard(
    file_path="my_dashboard.twbx",
    output_path="my_dashboard_redesigned.twbx",
    theme="executive-light",
    add_filter_actions=True,
)
print(redesign_result.summary())
```
