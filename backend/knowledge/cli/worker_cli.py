import os
import sys
import time
import argparse

# Ensure the project root (backend/knowledge) is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from business_logic.ingestion_worker_service import IngestionWorkerService
from infrastructure.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Knowledge Ingestion Worker CLI (MinIO -> ES)")
    parser.add_argument("--loop", action="store_true", help="Run in a loop (daemon mode)")
    parser.add_argument("--interval", type=int, default=5, help="Loop interval in seconds (default: 5)")
    parser.add_argument("--retry", action="store_true", help="Retry failed documents after processing pending ones")
    
    args = parser.parse_args()

    # Initialize the worker service
    # This will connect to MinIO and ES (via ESIngestionProcessor)
    worker = IngestionWorkerService()
    logger.info("Ingestion Worker started.")

    try:
        if args.loop:
            logger.info(f"Running in loop mode (Interval: {args.interval}s)")
            while True:
                # 1. Process pending documents (Status: NEW)
                result = worker.process_pending_documents()
                
                # 2. Retry failed documents (if enabled)
                if args.retry and result['processed'] == 0:
                    # Only retry if no new docs were processed to avoid starvation of new tasks
                    worker.retry_failed_documents()
                
                # Sleep if idle to avoid busy loop
                if result['processed'] == 0:
                    time.sleep(args.interval)
        else:
            logger.info("Running in single-shot mode")
            # 1. Process pending
            worker.process_pending_documents()
            
            # 2. Retry failed
            if args.retry:
                worker.retry_failed_documents()
                
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        # In a real deployment, we might want to exit with non-zero status
        sys.exit(1)

if __name__ == "__main__":
    main()
