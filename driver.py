#!/usr/bin/env python3
"""
Driver script to automatically run fellowship data retrieval every 2 hours.
This script continuously runs data_retrieval.py to find new fellowships.
"""

import subprocess
import time
import schedule
import logging
import sys
import os
from datetime import datetime
import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('driver.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class FellowshipDriver:
    def __init__(self, interval_hours=2):
        self.interval_hours = interval_hours
        self.running = True
        self.script_path = os.path.join(os.path.dirname(__file__), 'data_retrieval.py')
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def run_data_retrieval(self):
        """Run the data retrieval script"""
        try:
            logger.info("Starting fellowship data retrieval...")
            
            # Run the data_retrieval.py script
            result = subprocess.run(
                [sys.executable, self.script_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                logger.info("Fellowship data retrieval completed successfully")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.strip()}")
            else:
                logger.error(f"Fellowship data retrieval failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr.strip()}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.strip()}")
                    
        except Exception as e:
            logger.error(f"Exception occurred while running data retrieval: {e}")
    
    def schedule_jobs(self):
        """Schedule the data retrieval job"""
        # Schedule to run every 2 hours
        schedule.every(self.interval_hours).hours.do(self.run_data_retrieval)
        
        # Also run immediately on startup
        logger.info("Running initial data retrieval...")
        self.run_data_retrieval()
        
        logger.info(f"Driver started. Will run data retrieval every {self.interval_hours} hours.")
        logger.info("Press Ctrl+C to stop the driver.")
    
    def run(self):
        """Main run loop"""
        self.schedule_jobs()
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for pending jobs
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(60)  # Wait before retrying
        
        logger.info("Driver stopped.")

def main():
    """Main function to start the driver"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Driver script for automatic fellowship data retrieval")
    parser.add_argument(
        '--interval', 
        type=int, 
        default=2, 
        help='Interval in hours between data retrieval runs (default: 2)'
    )
    parser.add_argument(
        '--run-once', 
        action='store_true', 
        help='Run data retrieval once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    driver = FellowshipDriver(interval_hours=args.interval)
    
    if args.run_once:
        logger.info("Running data retrieval once...")
        driver.run_data_retrieval()
        logger.info("Single run completed.")
    else:
        driver.run()

if __name__ == "__main__":
    main()
