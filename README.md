# Magang Berdampak API

> API untuk mengakses data lowongan magang dari Simbelmawa dengan sistem scraper terpisah

## 🏗️ Arsitektur Sistem

```
+------------------------+      (4. API Call)      +--------------------+
|       Pengguna API     | ----------------------> |    FastAPI Server  |
| (Frontend, Aplikasi)   |                         |   (api_server.py)  |
+------------------------+      <------------------ +---------+----------+
                                 (5. Respons JSON)          | (3. Baca Data)
                                                            v
+------------------------+      (1. Trigger)      +--------------------+
| Scheduler (cron)       | ----------------------> | Database (SQLite)  |
| (misal: setiap 6 jam)  |                         |  (magang_data.db)  |
+------------------------+                         +---------+----------+
                                                            ^
                                                            | (2. Tulis Data)
                                                  +---------+----------+
                                                  |   Scraper/Worker   |
                                                  |   (scraper.py)     |
                                                  +--------------------+
```

## 📁 Struktur Proyek

```
magang-berdampak-api/
├── scraper_new/
│   └── scraper.py          # Worker untuk scraping data
├── api_new/
│   └── api_server.py       # FastAPI server
├── database/
│   ├── magang_data.db      # SQLite database (auto-generated)
│   └── detail_cache.json   # Cache untuk optimasi (auto-generated)
├── config/
│   └── config.py           # Konfigurasi aplikasi
├── deployment/
│   ├── deploy.sh           # Script deployment otomatis
│   ├── gunicorn.conf.py    # Konfigurasi Gunicorn
│   ├── magang-api.service  # Systemd service file
│   └── crontab             # Cron job untuk scheduled scraping
├── docs/
├── requirements.txt        # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Development

1. **Clone dan setup environment:**
```bash
cd magang-berdampak-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Jalankan scraper sekali untuk populate database:**
```bash
cd scraper_new
python scraper.py
```

3. **Jalankan API server:**
```bash
cd api_new
python api_server.py
```

4. **Akses API:**
- API: http://localhost:8000
- Dokumentasi: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Production Deployment

```bash
# Di server VPS (Ubuntu/Debian)
sudo ./deployment/deploy.sh
```

Script ini akan:
- Install dependencies sistem
- Setup virtual environment
- Konfigurasi systemd service
- Setup Nginx reverse proxy (opsional)
- Konfigurasi cron job untuk scraping otomatis
- Menjalankan initial scrape

## 📚 API Endpoints

### 🔍 GET `/api/v1/lowongan`
Mendapatkan daftar lowongan dengan filtering dan pagination.

**Parameters:**
- `q` (optional): Search query untuk posisi, mitra, atau kategori
- `lokasi` (optional): Filter berdasarkan lokasi
- `mitra` (optional): Filter berdasarkan mitra spesifik
- `kategori` (optional): Filter berdasarkan kategori spesifik
- `limit` (default: 20, max: 100): Jumlah hasil per halaman
- `offset` (default: 0): Jumlah hasil yang dilewati

**Response:**
```json
{
  "query": {
    "q": "developer",
    "lokasi": null,
    "mitra": null,
    "kategori": null,
    "limit": 20,
    "offset": 0
  },
  "count": 15,
  "total_in_db": 241,
  "data": [
    {
      "id_lowongan": 12345,
      "posisi": "Software Developer",
      "mitra": "PT. Tech Company",
      "kategori": "Teknologi Informasi",
      "jumlah_dibutuhkan": 2,
      "lokasi_penempatan": "Jakarta",
      "deskripsi_singkat": "Lowongan untuk software developer...",
      "url_detail": "https://simbelmawa.kemdikbud.go.id/magang/lowongan/software-developer-123",
      "last_updated": "2024-01-15T10:30:00"
    }
  ]
}
```

### 🔍 GET `/api/v1/lowongan/{id_lowongan}`
Mendapatkan detail lengkap untuk lowongan spesifik.

**Response:**
```json
{
  "id_lowongan": 12345,
  "posisi": "Software Developer",
  "mitra": "PT. Tech Company",
  "kategori": "Teknologi Informasi",
  "jumlah_dibutuhkan": 2,
  "lokasi_penempatan": "Jakarta",
  "deskripsi_singkat": "Lowongan untuk software developer...",
  "url_detail": "https://simbelmawa.kemdikbud.go.id/magang/lowongan/software-developer-123",
  "deskripsi_detail": "Detail lengkap dari lowongan...",
  "tugas_tanggung_jawab": "Mengembangkan aplikasi | Testing | Code review",
  "kualifikasi": "[Pendidikan] S1 Informatika | [Keahlian] Python, JavaScript",
  "kompetensi_dikembangkan": "Programming | Problem solving | Teamwork",
  "last_updated": "2024-01-15T10:30:00",
  "created_at": "2024-01-15T08:00:00"
}
```

### 📊 GET `/api/v1/stats`
Mendapatkan statistik dan metadata API.

**Response:**
```json
{
  "total_lowongan": 241,
  "last_scrape_timestamp": "2024-01-15T10:30:00",
  "successful_details": 235,
  "failed_details": 6,
  "database_file_exists": true,
  "api_version": "1.0.0"
}
```

### 📝 GET `/api/v1/categories`
Mendapatkan semua kategori yang tersedia.

### 🏢 GET `/api/v1/mitras`
Mendapatkan semua mitra yang tersedia.

### ⚡ POST `/api/v1/trigger-scrape` (Protected)
Memicu proses scraping manual.

**Headers required:**
```
X-API-Key: your-secret-api-key-here
```

### 🩺 GET `/health`
Health check endpoint.

## 🔧 Konfigurasi

### Environment Variables
Buat file `.env` di root directory:

```env
ENVIRONMENT=production
MAGANG_API_KEY=your-super-secret-api-key-here
```

### Database
- SQLite database: `database/magang_data.db`
- Cache file: `database/detail_cache.json`
- Auto-cleanup data lama yang sudah tidak ada di website

### Scheduling
Scraper berjalan otomatis setiap 6 jam via cron job:
```bash
0 */6 * * * cd /opt/magang-berdampak-api/scraper_new && /opt/magang-berdampak-api/venv/bin/python scraper.py
```

## 🔐 Security

1. **API Key Protection**: Endpoint `trigger-scrape` dilindungi dengan API key
2. **CORS**: Konfigurasi CORS untuk production
3. **Rate Limiting**: Implementasi rate limiting untuk scraper
4. **Data Sanitization**: Pembersihan data input dan output

## 📊 Monitoring & Logging

### Logs Location
- API logs: `/var/log/magang-api/`
- Scraper cron logs: `/var/log/magang-api/scraper-cron.log`
- Systemd logs: `journalctl -u magang-api -f`

### Health Monitoring
- Health endpoint: `/health`
- Stats endpoint: `/api/v1/stats`
- Database status monitoring

## 🛠️ Development

### Local Development
```bash
# Start API in development mode
cd api_new
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

# Run scraper manually
cd scraper_new
python scraper.py
```

### Testing
```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/stats
curl "http://localhost:8000/api/v1/lowongan?q=developer&limit=5"
```

## 🚀 Deployment

### Requirements
- Ubuntu/Debian server
- Python 3.8+
- Nginx (optional, for reverse proxy)
- Minimum 512MB RAM, 1GB storage

### Auto Deployment
```bash
sudo ./deployment/deploy.sh
```

### Manual Deployment
1. Copy files to `/opt/magang-berdampak-api/`
2. Install dependencies: `pip install -r requirements.txt`
3. Setup systemd service: `cp deployment/magang-api.service /etc/systemd/system/`
4. Enable service: `systemctl enable magang-api && systemctl start magang-api`
5. Setup cron: `crontab -e` dan tambahkan line dari `deployment/crontab`

## 🔄 Data Flow

1. **Scheduler (Cron)** → Menjalankan scraper setiap 6 jam
2. **Scraper** → Mengambil data dari Simbelmawa, simpan ke SQLite
3. **Database** → Menyimpan data lowongan dan metadata
4. **API Server** → Membaca dari database, serve via HTTP
5. **Client** → Mengakses data via REST API

## 📈 Performance

- **Database**: SQLite dengan indexing optimal
- **Caching**: JSON cache untuk detail lowongan
- **Async**: Full async implementation untuk I/O operations
- **Connection Pooling**: Optimasi koneksi database
- **Pagination**: Built-in pagination untuk response besar

## 🆘 Troubleshooting

### Common Issues

1. **Database tidak ditemukan**
   ```bash
   cd scraper_new && python scraper.py
   ```

2. **API tidak bisa diakses**
   ```bash
   systemctl status magang-api
   journalctl -u magang-api -f
   ```

3. **Scraper gagal**
   ```bash
   tail -f /var/log/magang-api/scraper-cron.log
   ```

4. **Permission errors**
   ```bash
   sudo chown -R www-data:www-data /opt/magang-berdampak-api
   ```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

## 📄 License

MIT License - lihat file LICENSE untuk detail lengkap.

## 📞 Support

- Issues: Gunakan GitHub Issues
- Email: your-email@domain.com
- Dokumentasi: `/docs` endpoint di API

---

**Catatan**: Ganti `your-secret-api-key-here` dengan API key yang aman untuk production! 