import asyncio
import httpx
import json
import sqlite3
import time
import os
import random
from datetime import datetime
from typing import List, Dict, Optional, Set
import logging

# --- Konfigurasi ---
BASE_URL = "https://simbelmawa.kemdikbud.go.id/magang/lowongan"

# Get paths relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, 'database', 'detail_cache.json')
DB_FILE = os.path.join(BASE_DIR, 'database', 'magang_data.db')

# Pengaturan scraping
MAX_CONCURRENT_REQUESTS = 25 
RETRY_COUNT = 3
RETRY_DELAY = 2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Fungsi Helper Cache ---
def load_cache() -> Dict:
    """Load cache from JSON file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                logger.info(f"Cache ditemukan. Memuat {CACHE_FILE}...")
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Cache rusak. Memulai dari awal.")
            return {}
    return {}

def save_to_cache(cache: Dict) -> None:
    """Save cache to JSON file"""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# --- Fungsi Database ---
def init_db() -> None:
    """Initialize SQLite database with optimized schema"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create main table with proper indexing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lowongan (
            id_lowongan INTEGER PRIMARY KEY,
            posisi TEXT NOT NULL,
            mitra TEXT,
            kategori TEXT,
            jumlah_dibutuhkan INTEGER,
            lokasi_penempatan TEXT,
            deskripsi_singkat TEXT,
            url_detail TEXT UNIQUE,
            deskripsi_detail TEXT,
            tugas_tanggung_jawab TEXT,
            kualifikasi TEXT,
            kompetensi_dikembangkan TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create metadata table for tracking scrape info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_metadata (
            id INTEGER PRIMARY KEY,
            last_scrape_timestamp TEXT NOT NULL,
            total_lowongan INTEGER NOT NULL,
            successful_details INTEGER NOT NULL,
            failed_details INTEGER NOT NULL
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posisi ON lowongan(posisi)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mitra ON lowongan(mitra)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kategori ON lowongan(kategori)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lokasi ON lowongan(lokasi_penempatan)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_updated ON lowongan(last_updated)')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_to_db(all_full_data: List[Dict], valid_ids: Set[int]) -> None:
    """Save data to database and cleanup old entries"""
    if not all_full_data:
        logger.warning("No data to save to database")
        return
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    rows_to_insert = []
    skipped_count = 0
    success_count = 0
    
    for item in all_full_data:
        detail_lowongan = item.get('detail', {}).get('lowongan', {})
        
        # Process even if detail is missing (save summary data)
        if detail_lowongan:
            # Full data with details
            kriteria_list = detail_lowongan.get('lowongan_kriteria', [])
            kualifikasi_str = " | ".join([
                f"[{k.get('kategori', '').replace('_', ' ').title()}] {k.get('deskripsi', '').replace(chr(10), ' ')}" 
                for k in kriteria_list if k.get('deskripsi')
            ])
            
            tugas_list = detail_lowongan.get('lowongan_tanggung_jawab', [])
            tugas_str = " | ".join([
                t.get('deskripsi', '').replace(chr(10), ' ') 
                for t in tugas_list if t.get('deskripsi')
            ])
            
            capaian_list = detail_lowongan.get('lowongan_capaian', [])
            kompetensi_str = " | ".join([
                c.get('deskripsi', '').replace(chr(10), ' ') 
                for c in capaian_list if c.get('deskripsi')
            ])
            
            deskripsi_detail = str(detail_lowongan.get('deskripsi', '')).replace('\n', ' ')
        else:
            # Summary data only
            skipped_count += 1
            kualifikasi_str = ""
            tugas_str = ""
            kompetensi_str = ""
            deskripsi_detail = ""
        
        # Common data processing
        row_tuple = (
            item.get('id_lowongan'),
            item.get('posisi_magang', ''),
            item.get('mitra', ''),
            item.get('kategori_posisi', ''),
            item.get('jumlah', 0),
            str(item.get('lokasi_penempatan', '')).replace('\n', ' | '),
            str(item.get('deskripsi', '')).replace('\n', ' '),
            f"{BASE_URL}/{item.get('slug', '')}" if item.get('slug') else '',
            deskripsi_detail,
            tugas_str,
            kualifikasi_str,
            kompetensi_str,
            datetime.now().isoformat()
        )
        rows_to_insert.append(row_tuple)
        success_count += 1
    
    # Insert/Update data
    sql_query = '''
        INSERT OR REPLACE INTO lowongan (
            id_lowongan, posisi, mitra, kategori, jumlah_dibutuhkan, 
            lokasi_penempatan, deskripsi_singkat, url_detail, 
            deskripsi_detail, tugas_tanggung_jawab, kualifikasi, 
            kompetensi_dikembangkan, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    cursor.executemany(sql_query, rows_to_insert)
    
    # Cleanup: Delete entries that are no longer on the website
    if valid_ids:
        placeholders = ','.join('?' for _ in valid_ids)
        delete_query = f'DELETE FROM lowongan WHERE id_lowongan NOT IN ({placeholders})'
        cursor.execute(delete_query, list(valid_ids))
        deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} outdated entries from database")
    
    # Update metadata
    cursor.execute('DELETE FROM scrape_metadata')  # Keep only latest
    cursor.execute('''
        INSERT INTO scrape_metadata (last_scrape_timestamp, total_lowongan, successful_details, failed_details)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now().isoformat(), len(rows_to_insert), success_count - skipped_count, skipped_count))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database updated: {success_count} total, {success_count - skipped_count} with details, {skipped_count} summary only")

# --- Fungsi Fetch Inti ---
async def fetch_with_retry(client: httpx.AsyncClient, url: str, headers: Dict) -> Optional[httpx.Response]:
    """Fetch URL with retry mechanism"""
    for attempt in range(RETRY_COUNT):
        try:
            response = await client.get(url, headers=headers, timeout=45.0)
            response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Attempt {attempt + 1}/{RETRY_COUNT} failed for {url}. Error: {type(e).__name__}")
            if attempt + 1 == RETRY_COUNT:
                return None
            await asyncio.sleep(RETRY_DELAY + random.uniform(0, 1))
    return None

async def get_initial_data_and_version(client: httpx.AsyncClient) -> tuple[Optional[str], Optional[int], List[Dict]]:
    """Get initial data and version from the website"""
    try:
        response = await client.get(BASE_URL)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        app_div = soup.find('div', id='app')
        
        if not app_div:
            raise Exception("Could not find app div")
            
        page_data = json.loads(app_div.get('data-page'))
        version = page_data.get('version')
        pagination_info = page_data['props']['data']
        total_pages = pagination_info['last_page']
        first_page_lowongan = pagination_info['data']
        
        logger.info(f"Version: {version} | Total Pages: {total_pages}")
        return version, total_pages, first_page_lowongan
        
    except Exception as e:
        logger.error(f"Failed to get initial data: {e}")
        return None, None, []

async def fetch_list_page(client: httpx.AsyncClient, page_num: int, semaphore: asyncio.Semaphore, inertia_version: str) -> List[Dict]:
    """Fetch lowongan list from specific page"""
    async with semaphore:
        url_halaman = f"{BASE_URL}?page={page_num}"
        headers = {'X-Inertia': 'true', 'X-Inertia-Version': inertia_version}
        response = await fetch_with_retry(client, url_halaman, headers)
        if response:
            return response.json()['props']['data']['data']
        return []

async def fetch_detail_page(client: httpx.AsyncClient, lowongan_summary: Dict, semaphore: asyncio.Semaphore, inertia_version: str) -> Optional[Dict]:
    """Fetch detail page for a specific lowongan"""
    async with semaphore:
        slug = lowongan_summary.get('slug')
        if not slug:
            return None
            
        detail_url = f"{BASE_URL}/{slug}"
        headers = {'X-Inertia': 'true', 'X-Inertia-Version': inertia_version}
        response = await fetch_with_retry(client, detail_url, headers)
        
        if response:
            detail_data_json = response.json()
            full_data = {**lowongan_summary, "detail": detail_data_json.get('props', {})}
            logger.info(f"Successfully fetched detail: {slug}")
            return full_data
            
        logger.warning(f"Failed to fetch detail: {slug}")
        return None

async def main() -> None:
    """Main scraping function"""
    start_time = time.time()
    logger.info("=== Starting Magang Berdampak Scraper ===")
    
    try:
        # Initialize database
        init_db()
        
        # Load cache
        cache = load_cache()
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        async with httpx.AsyncClient(
            timeout=30.0, 
            follow_redirects=True, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        ) as client:
            
            # Stage 1: Get all lowongan summaries
            logger.info("--- STAGE 1: Fetching all lowongan summaries ---")
            version, total_pages, first_page_data = await get_initial_data_and_version(client)
            if not version:
                logger.error("Failed to get initial data. Exiting.")
                return

            all_lowongan_summary = first_page_data
            
            # Fetch remaining pages
            if total_pages > 1:
                list_tasks = [
                    fetch_list_page(client, page, semaphore, version) 
                    for page in range(2, total_pages + 1)
                ]
                list_results = await asyncio.gather(*list_tasks)
                for page_data in list_results:
                    all_lowongan_summary.extend(page_data)
            
            logger.info(f"Total {len(all_lowongan_summary)} lowongan summaries fetched")
            
            # Deduplication based on id_lowongan
            seen_ids = set()
            unique_lowongan = []
            duplicate_count = 0
            
            for item in all_lowongan_summary:
                item_id = item.get('id_lowongan')
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_lowongan.append(item)
                else:
                    duplicate_count += 1
            
            if duplicate_count > 0:
                logger.info(f"Removed {duplicate_count} duplicates")
            
            all_lowongan_summary = unique_lowongan
            valid_ids = {item.get('id_lowongan') for item in all_lowongan_summary if item.get('id_lowongan')}
            logger.info(f"After dedup: {len(all_lowongan_summary)} unique lowongan")

            # Cache management
            cached_slugs = set(cache.keys())
            all_slugs_from_summary = {low.get('slug') for low in all_lowongan_summary if low.get('slug')}
            needed_lowongan = [low for low in all_lowongan_summary if low.get('slug') not in cached_slugs]
            
            logger.info(f"Found {len(cache)} items in cache")
            logger.info(f"Need to fetch: {len(needed_lowongan)} new details")
            
            # Clean old cache entries
            cached_but_not_in_summary = cached_slugs - all_slugs_from_summary
            if cached_but_not_in_summary:
                logger.info(f"Cleaning {len(cached_but_not_in_summary)} outdated cache entries")
                for old_slug in cached_but_not_in_summary:
                    del cache[old_slug]

            # Stage 2: Fetch new details
            if needed_lowongan:
                logger.info(f"--- STAGE 2: Fetching {len(needed_lowongan)} new details ---")
                detail_tasks = [
                    fetch_detail_page(client, summary, semaphore, version) 
                    for summary in needed_lowongan
                ]
                new_details_results = await asyncio.gather(*detail_tasks)
                
                success_count = 0
                failed_count = 0
                
                for i, res in enumerate(new_details_results):
                    original_summary = needed_lowongan[i]
                    if res and res.get('slug'):
                        cache[res.get('slug')] = res
                        success_count += 1
                    else:
                        # Save summary even if detail failed
                        if original_summary.get('slug'):
                            cache[original_summary.get('slug')] = {**original_summary, "detail": {}}
                        failed_count += 1
                
                save_to_cache(cache)
                logger.info(f"New details: {success_count} successful, {failed_count} failed")
            else:
                logger.info("--- STAGE 2: No new details needed ---")
                
            # Stage 2.5: Retry failed details
            items_without_detail = [
                item for item in cache.values() 
                if not item.get('detail', {}).get('lowongan')
            ]
            
            if items_without_detail:
                logger.info(f"--- STAGE 2.5: Retrying {len(items_without_detail)} failed details ---")
                retry_tasks = [
                    fetch_detail_page(client, item, semaphore, version) 
                    for item in items_without_detail[:50]  # Limit retries
                ]
                retry_results = await asyncio.gather(*retry_tasks)
                
                retry_success = 0
                for res in retry_results:
                    if res and res.get('slug') and res.get('detail', {}).get('lowongan'):
                        cache[res.get('slug')] = res
                        retry_success += 1
                
                if retry_success > 0:
                    save_to_cache(cache)
                    logger.info(f"Retry successful: {retry_success} items")

        # Stage 3: Save to database
        logger.info("--- STAGE 3: Saving to database ---")
        all_full_data = list(cache.values())
        save_to_db(all_full_data, valid_ids)
        
        # Final summary
        data_with_complete_detail = [
            item for item in all_full_data 
            if item.get('detail', {}).get('lowongan')
        ]
        data_summary_only = [
            item for item in all_full_data 
            if not item.get('detail', {}).get('lowongan')
        ]
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("=== SCRAPING SUMMARY ===")
        logger.info(f"Total lowongan from website: {len(all_lowongan_summary)}")
        logger.info(f"Total in cache: {len(all_full_data)}")
        logger.info(f"Complete data (with details): {len(data_with_complete_detail)}")
        logger.info(f"Summary only: {len(data_summary_only)}")
        logger.info(f"Total duration: {duration:.2f} seconds")
        logger.info("=== Scraping completed successfully ===")
        
    except Exception as e:
        logger.error(f"Scraping failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 