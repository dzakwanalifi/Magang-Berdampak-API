from fastapi import FastAPI, HTTPException, Depends, Query, Security, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sqlite3
import os
import subprocess
import json
from datetime import datetime
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
# Get paths relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, 'database', 'magang_data.db')
API_KEY = os.getenv('MAGANG_API_KEY', 'your-secret-api-key-here')  # Change this in production!
SCRAPER_SCRIPT = os.path.join(BASE_DIR, 'scraper_new', 'scraper.py')

# Initialize FastAPI app
app = FastAPI(
    title="Magang Berdampak API",
    description="API untuk mengakses data lowongan magang dari Simbelmawa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LowonganSummary(BaseModel):
    id_lowongan: int
    posisi: str
    mitra: str
    kategori: str
    jumlah_dibutuhkan: int
    lokasi_penempatan: str
    deskripsi_singkat: str
    url_detail: str
    last_updated: str

class LowonganDetail(LowonganSummary):
    deskripsi_detail: str
    tugas_tanggung_jawab: str
    kualifikasi: str
    kompetensi_dikembangkan: str
    created_at: str

class LowonganListResponse(BaseModel):
    query: Dict[str, Any]
    count: int
    total_in_db: int
    data: List[LowonganSummary]

class StatsResponse(BaseModel):
    total_lowongan: int
    last_scrape_timestamp: Optional[str]
    successful_details: int
    failed_details: int
    database_file_exists: bool
    api_version: str

class TriggerScrapeResponse(BaseModel):
    message: str
    status: str

# Database helper functions
def get_db_connection():
    """Get database connection with error handling"""
    if not os.path.exists(DB_FILE):
        raise HTTPException(status_code=503, detail="Database not found. Please run scraper first.")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")

def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for protected endpoints"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# API Endpoints

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Magang Berdampak API",
        "version": "1.0.0",
        "endpoints": {
            "lowongan_list": "/api/v1/lowongan",
            "lowongan_detail": "/api/v1/lowongan/{id_lowongan}",
            "stats": "/api/v1/stats",
            "docs": "/docs"
        }
    }

@app.get("/api/v1/lowongan", response_model=LowonganListResponse)
async def get_lowongan_list(
    q: Optional[str] = Query(None, description="Search query for posisi, mitra, or kategori"),
    lokasi: Optional[str] = Query(None, description="Filter by location"),
    mitra: Optional[str] = Query(None, description="Filter by mitra"),
    kategori: Optional[str] = Query(None, description="Filter by kategori"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get list of lowongan with filtering and pagination
    
    - **q**: Free text search across posisi, mitra, and kategori
    - **lokasi**: Filter by location text
    - **mitra**: Filter by specific mitra
    - **kategori**: Filter by specific kategori
    - **limit**: Maximum results per page (1-100)
    - **offset**: Number of results to skip for pagination
    """
    conn = get_db_connection()
    
    try:
        # Build dynamic query
        where_conditions = []
        params = []
        
        if q:
            where_conditions.append("(posisi LIKE ? OR mitra LIKE ? OR kategori LIKE ?)")
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term])
        
        if lokasi:
            where_conditions.append("lokasi_penempatan LIKE ?")
            params.append(f"%{lokasi}%")
            
        if mitra:
            where_conditions.append("mitra LIKE ?")
            params.append(f"%{mitra}%")
            
        if kategori:
            where_conditions.append("kategori LIKE ?")
            params.append(f"%{kategori}%")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM lowongan {where_clause}"
        total_result = conn.execute(count_query, params).fetchone()
        total_in_db = total_result['total'] if total_result else 0
        
        # Get paginated results
        main_query = f"""
            SELECT id_lowongan, posisi, mitra, kategori, jumlah_dibutuhkan, 
                   lokasi_penempatan, deskripsi_singkat, url_detail, last_updated
            FROM lowongan 
            {where_clause}
            ORDER BY last_updated DESC, id_lowongan DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        cursor = conn.execute(main_query, params)
        results = cursor.fetchall()
        
        # Convert to response format
        lowongan_list = []
        for row in results:
            lowongan_list.append(LowonganSummary(
                id_lowongan=row['id_lowongan'],
                posisi=row['posisi'],
                mitra=row['mitra'],
                kategori=row['kategori'],
                jumlah_dibutuhkan=row['jumlah_dibutuhkan'],
                lokasi_penempatan=row['lokasi_penempatan'],
                deskripsi_singkat=row['deskripsi_singkat'],
                url_detail=row['url_detail'],
                last_updated=row['last_updated']
            ))
        
        return LowonganListResponse(
            query={
                "q": q,
                "lokasi": lokasi,
                "mitra": mitra,
                "kategori": kategori,
                "limit": limit,
                "offset": offset
            },
            count=len(lowongan_list),
            total_in_db=total_in_db,
            data=lowongan_list
        )
        
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        conn.close()

@app.get("/api/v1/lowongan/{id_lowongan}", response_model=LowonganDetail)
async def get_lowongan_detail(id_lowongan: int):
    """
    Get detailed information for a specific lowongan
    
    - **id_lowongan**: The ID of the lowongan to retrieve
    """
    conn = get_db_connection()
    
    try:
        query = """
            SELECT id_lowongan, posisi, mitra, kategori, jumlah_dibutuhkan, 
                   lokasi_penempatan, deskripsi_singkat, url_detail, 
                   deskripsi_detail, tugas_tanggung_jawab, kualifikasi, 
                   kompetensi_dikembangkan, last_updated, created_at
            FROM lowongan 
            WHERE id_lowongan = ?
        """
        
        cursor = conn.execute(query, (id_lowongan,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Lowongan with ID {id_lowongan} not found")
        
        return LowonganDetail(
            id_lowongan=result['id_lowongan'],
            posisi=result['posisi'],
            mitra=result['mitra'],
            kategori=result['kategori'],
            jumlah_dibutuhkan=result['jumlah_dibutuhkan'],
            lokasi_penempatan=result['lokasi_penempatan'],
            deskripsi_singkat=result['deskripsi_singkat'],
            url_detail=result['url_detail'],
            deskripsi_detail=result['deskripsi_detail'],
            tugas_tanggung_jawab=result['tugas_tanggung_jawab'],
            kualifikasi=result['kualifikasi'],
            kompetensi_dikembangkan=result['kompetensi_dikembangkan'],
            last_updated=result['last_updated'],
            created_at=result['created_at']
        )
        
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        conn.close()

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get API statistics and metadata
    """
    database_exists = os.path.exists(DB_FILE)
    
    if not database_exists:
        return StatsResponse(
            total_lowongan=0,
            last_scrape_timestamp=None,
            successful_details=0,
            failed_details=0,
            database_file_exists=False,
            api_version="1.0.0"
        )
    
    conn = get_db_connection()
    
    try:
        # Get total lowongan count
        total_query = "SELECT COUNT(*) as total FROM lowongan"
        total_result = conn.execute(total_query).fetchone()
        total_lowongan = total_result['total'] if total_result else 0
        
        # Get latest scrape metadata
        metadata_query = """
            SELECT last_scrape_timestamp, successful_details, failed_details 
            FROM scrape_metadata 
            ORDER BY id DESC 
            LIMIT 1
        """
        metadata_result = conn.execute(metadata_query).fetchone()
        
        if metadata_result:
            last_scrape = metadata_result['last_scrape_timestamp']
            successful_details = metadata_result['successful_details']
            failed_details = metadata_result['failed_details']
        else:
            last_scrape = None
            successful_details = 0
            failed_details = 0
        
        return StatsResponse(
            total_lowongan=total_lowongan,
            last_scrape_timestamp=last_scrape,
            successful_details=successful_details,
            failed_details=failed_details,
            database_file_exists=True,
            api_version="1.0.0"
        )
        
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        conn.close()

@app.get("/api/v1/categories")
async def get_categories():
    """Get all available categories"""
    conn = get_db_connection()
    
    try:
        query = "SELECT DISTINCT kategori FROM lowongan WHERE kategori IS NOT NULL ORDER BY kategori"
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        categories = [row['kategori'] for row in results]
        
        return {
            "categories": categories,
            "count": len(categories)
        }
        
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        conn.close()

@app.get("/api/v1/mitras")
async def get_mitras():
    """Get all available mitras"""
    conn = get_db_connection()
    
    try:
        query = "SELECT DISTINCT mitra FROM lowongan WHERE mitra IS NOT NULL ORDER BY mitra"
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        mitras = [row['mitra'] for row in results]
        
        return {
            "mitras": mitras,
            "count": len(mitras)
        }
        
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        conn.close()

# Background task for scraping
async def run_scraper():
    """Run scraper as background task"""
    try:
        logger.info("Starting background scraper task")
        
        # Get absolute path to scraper
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        scraper_dir = os.path.join(project_root, 'scraper_new')
        scraper_path = os.path.join(scraper_dir, 'scraper.py')
        
        # Check if scraper exists
        if not os.path.exists(scraper_path):
            logger.error(f"Scraper script not found at: {scraper_path}")
            return
        
        # Run scraper in thread to avoid Windows subprocess issues
        import threading
        import subprocess
        import sys
        
        def run_scraper_sync():
            try:
                python_exe = sys.executable
                cmd = [python_exe, scraper_path]
                
                logger.info(f"Running command: {' '.join(cmd)}")
                logger.info(f"Working directory: {scraper_dir}")
                
                result = subprocess.run(
                    cmd,
                    cwd=scraper_dir,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )
                
                if result.returncode == 0:
                    logger.info("Scraper completed successfully")
                    if result.stdout:
                        logger.info(f"Scraper output: {result.stdout}")
                else:
                    logger.error(f"Scraper failed with return code {result.returncode}")
                    if result.stderr:
                        logger.error(f"Scraper error: {result.stderr}")
                        
            except subprocess.TimeoutExpired:
                logger.error("Scraper timed out after 30 minutes")
            except Exception as e:
                logger.error(f"Error in scraper thread: {e}", exc_info=True)
        
        # Run in background thread
        thread = threading.Thread(target=run_scraper_sync, daemon=True)
        thread.start()
        logger.info("Scraper started in background thread")
            
    except Exception as e:
        logger.error(f"Error running scraper: {e}", exc_info=True)

@app.post("/api/v1/trigger-scrape", response_model=TriggerScrapeResponse)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key)
):
    """
    Trigger manual scraping process (Protected endpoint)
    
    Requires X-API-Key header with valid API key.
    """
    if not os.path.exists(SCRAPER_SCRIPT):
        raise HTTPException(status_code=503, detail="Scraper script not found")
    
    # Add background task
    background_tasks.add_task(run_scraper)
    
    return TriggerScrapeResponse(
        message="Scraping process has been triggered. Check /api/v1/stats after a few minutes for updated data.",
        status="triggered"
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    database_status = "ok" if os.path.exists(DB_FILE) else "database_missing"
    
    return {
        "status": "ok",
        "database": database_status,
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(sqlite3.Error)
async def sqlite_exception_handler(request, exc):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 