import logging, asyncio
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def reindex_job():
    log.info("── Scheduled re-index started ──")
    try:
        from src.scraper  import scrape_all
        from src.loader   import prepare_all_chunks
        from src.embedder import upload_to_pinecone
        asyncio.run(scrape_all())
        chunks = prepare_all_chunks()
        upload_to_pinecone(chunks, namespace="rbs")
        log.info("✅ Re-index complete")
    except Exception as e:
        log.error(f"Re-index failed: {e}", exc_info=True)

def start_scheduler(weeks=1):
    s = BackgroundScheduler()
    s.add_job(reindex_job, "interval", weeks=weeks, id="reindex",
              max_instances=1, coalesce=True)
    s.start()
    log.info(f"Scheduler running — every {weeks} week(s)")
    return s
