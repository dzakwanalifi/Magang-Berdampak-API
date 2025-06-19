# Magang Berdampak API - Panduan Penggunaan

## 🚀 Quick Start Guide

### 1. Setup Development Environment

```bash
# Clone atau ekstrak proyek
cd magang-berdampak-api

# Install dependencies
pip install -r requirements.txt

# Jalankan development server (otomatis setup)
python run_dev.py
```

### 2. Akses API Documentation

Setelah server berjalan, akses:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints Reference

### Base URL: `http://localhost:8000` (development)

### 1. Health & Status

#### `GET /health`
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "database": "ok",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/stats`
```bash
curl http://localhost:8000/api/v1/stats
```

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

### 2. Lowongan Endpoints

#### `GET /api/v1/lowongan` - List Lowongan

**Basic Usage:**
```bash
curl "http://localhost:8000/api/v1/lowongan?limit=5"
```

**With Search:**
```bash
curl "http://localhost:8000/api/v1/lowongan?q=developer&limit=10"
```

**With Filters:**
```bash
curl "http://localhost:8000/api/v1/lowongan?lokasi=Jakarta&kategori=IT&limit=10"
```

**With Pagination:**
```bash
curl "http://localhost:8000/api/v1/lowongan?limit=20&offset=40"
```

**Parameters:**
- `q` (string): Search dalam posisi, mitra, kategori
- `lokasi` (string): Filter berdasarkan lokasi
- `mitra` (string): Filter berdasarkan nama mitra
- `kategori` (string): Filter berdasarkan kategori
- `limit` (int): Jumlah hasil (1-100, default: 20)
- `offset` (int): Skip hasil (default: 0)

**Response:**
```json
{
  "query": {
    "q": "developer",
    "lokasi": null,
    "mitra": null,
    "kategori": null,
    "limit": 10,
    "offset": 0
  },
  "count": 5,
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

#### `GET /api/v1/lowongan/{id_lowongan}` - Detail Lowongan

```bash
curl "http://localhost:8000/api/v1/lowongan/12345"
```

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
  "deskripsi_detail": "Detail lengkap dari lowongan magang ini...",
  "tugas_tanggung_jawab": "Mengembangkan aplikasi web | Testing dan debugging | Code review",
  "kualifikasi": "[Pendidikan] S1 Informatika/Sistem Informasi | [Keahlian] Python, JavaScript, SQL",
  "kompetensi_dikembangkan": "Programming skills | Problem solving | Teamwork | Project management",
  "last_updated": "2024-01-15T10:30:00",
  "created_at": "2024-01-15T08:00:00"
}
```

### 3. Filter Helpers

#### `GET /api/v1/categories` - List Kategori
```bash
curl "http://localhost:8000/api/v1/categories"
```

**Response:**
```json
{
  "categories": [
    "Teknologi Informasi",
    "Administrasi",
    "Marketing",
    "Keuangan"
  ],
  "count": 4
}
```

#### `GET /api/v1/mitras` - List Mitra
```bash
curl "http://localhost:8000/api/v1/mitras"
```

**Response:**
```json
{
  "mitras": [
    "PT. Tech Company",
    "CV. Digital Solutions",
    "Bank ABC"
  ],
  "count": 3
}
```

### 4. Admin Endpoints

#### `POST /api/v1/trigger-scrape` - Trigger Manual Scrape (Protected)

```bash
curl -X POST "http://localhost:8000/api/v1/trigger-scrape" \
     -H "X-API-Key: your-secret-api-key-here"
```

**Response:**
```json
{
  "message": "Scraping process has been triggered. Check /api/v1/stats after a few minutes for updated data.",
  "status": "triggered"
}
```

## 🔧 Programming Examples

### Python

```python
import requests

# Setup
BASE_URL = "http://localhost:8000"

# Get stats
response = requests.get(f"{BASE_URL}/api/v1/stats")
stats = response.json()
print(f"Total lowongan: {stats['total_lowongan']}")

# Search for developer positions
response = requests.get(f"{BASE_URL}/api/v1/lowongan", params={
    'q': 'developer',
    'limit': 10
})
lowongan_list = response.json()

for lowongan in lowongan_list['data']:
    print(f"- {lowongan['posisi']} di {lowongan['mitra']}")

# Get detail
if lowongan_list['data']:
    id_lowongan = lowongan_list['data'][0]['id_lowongan']
    detail_response = requests.get(f"{BASE_URL}/api/v1/lowongan/{id_lowongan}")
    detail = detail_response.json()
    print(f"Detail: {detail['deskripsi_detail']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function getAllLowongan() {
    try {
        const response = await axios.get(`${BASE_URL}/api/v1/lowongan`, {
            params: {
                limit: 20,
                q: 'developer'
            }
        });
        
        console.log(`Found ${response.data.count} lowongan`);
        return response.data.data;
    } catch (error) {
        console.error('Error:', error.response.data);
    }
}

async function getLowonganDetail(id) {
    try {
        const response = await axios.get(`${BASE_URL}/api/v1/lowongan/${id}`);
        return response.data;
    } catch (error) {
        console.error('Error:', error.response.data);
    }
}

// Usage
getAllLowongan().then(lowongan => {
    if (lowongan && lowongan.length > 0) {
        getLowonganDetail(lowongan[0].id_lowongan).then(detail => {
            console.log('Detail:', detail);
        });
    }
});
```

### JavaScript (Browser/Fetch)

```javascript
// Fetch lowongan list
async function fetchLowongan(query = '', limit = 20) {
    const params = new URLSearchParams({
        q: query,
        limit: limit
    });
    
    const response = await fetch(`http://localhost:8000/api/v1/lowongan?${params}`);
    const data = await response.json();
    
    return data;
}

// Usage in frontend
fetchLowongan('developer', 10)
    .then(result => {
        console.log(`Found ${result.count} lowongan`);
        result.data.forEach(lowongan => {
            console.log(`- ${lowongan.posisi} at ${lowongan.mitra}`);
        });
    });
```

## 📊 Response Status Codes

- `200` - OK: Request berhasil
- `404` - Not Found: Resource tidak ditemukan
- `401` - Unauthorized: API key tidak valid (untuk endpoint protected)
- `422` - Validation Error: Parameter tidak valid
- `500` - Internal Server Error: Error server
- `503` - Service Unavailable: Database tidak tersedia

## 🔍 Search Tips

### Text Search (`q` parameter):
- Mencari di kolom: `posisi`, `mitra`, `kategori`
- Case-insensitive
- Partial matching
- Contoh: `q=developer` akan menemukan "Software Developer", "Frontend Developer", dll.

### Location Filter (`lokasi` parameter):
- Mencari di kolom: `lokasi_penempatan`
- Contoh: `lokasi=Jakarta` akan menemukan "Jakarta Pusat", "Jakarta Selatan", dll.

### Mitra Filter (`mitra` parameter):
- Exact atau partial matching pada nama mitra
- Contoh: `mitra=Bank` akan menemukan "Bank ABC", "Bank XYZ", dll.

### Pagination:
- Gunakan `limit` dan `offset` untuk pagination
- Maksimum `limit` adalah 100
- `total_in_db` memberikan informasi total records

## 🚨 Error Handling

### Common Errors:

1. **Database not found (503)**:
   ```bash
   # Jalankan scraper untuk populate database
   cd scraper_new && python scraper.py
   ```

2. **Validation Error (422)**:
   ```json
   {
     "detail": [
       {
         "loc": ["query", "limit"],
         "msg": "ensure this value is less than or equal to 100",
         "type": "value_error.number.not_le"
       }
     ]
   }
   ```

3. **Resource Not Found (404)**:
   ```json
   {
     "detail": "Lowongan with ID 999999 not found"
   }
   ```

## 🔄 Data Freshness

- Data di-update otomatis setiap 6 jam via cron job
- Cek `last_scrape_timestamp` di endpoint `/api/v1/stats`
- Trigger manual scrape via `/api/v1/trigger-scrape` (memerlukan API key)

## 📈 Performance Tips

1. **Pagination**: Gunakan `limit` yang wajar (20-50) untuk response cepat
2. **Caching**: Response dapat di-cache di sisi client
3. **Specific Queries**: Gunakan filter spesifik daripada mengambil semua data
4. **Detail on Demand**: Ambil detail hanya saat dibutuhkan

## 🔐 Authentication

Hanya endpoint `/api/v1/trigger-scrape` yang memerlukan authentication:
```bash
curl -X POST "http://localhost:8000/api/v1/trigger-scrape" \
     -H "X-API-Key: your-secret-api-key-here"
```

API key dapat diatur di file `.env` atau environment variable `MAGANG_API_KEY`.

## 📞 Support

- Dokumentasi: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Test Script: `python test_api.py` 