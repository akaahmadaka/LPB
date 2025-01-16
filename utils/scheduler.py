from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
from database import get_db_session, get_all_links, delete_link
from typing import List
from pytz import utc  # Import UTC timezone

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkCleanupScheduler:
    def __init__(self):
        # Configure scheduler to use UTC explicitly
        self.scheduler = BackgroundScheduler(timezone=utc)
        self.cleanup_days = 3  # Default: remove links older than 3 days
        self.runs_per_day = 4  # Default: run 4 times per day
        self.is_running = False

    def calculate_intervals(self) -> List[int]:
        """Calculate the hours when the job should run based on runs_per_day"""
        interval = 24 // self.runs_per_day
        return [i * interval for i in range(self.runs_per_day)]

    def cleanup_old_links(self):
        """Remove links that are older than the specified number of days"""
        try:
            current_time = datetime.utcnow()  # Explicitly use UTC
            cutoff_time = current_time - timedelta(days=self.cleanup_days)
            
            with get_db_session() as session:
                links = get_all_links(session)
                removed_count = 0
                
                for link in links:
                    if link.submit_date < cutoff_time:
                        logger.info(f"Removing old link: {link.title} (ID: {link.id})")
                        delete_link(link.id)
                        removed_count += 1
                
                logger.info(f"Cleanup completed at {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}. "
                          f"Removed {removed_count} old links.")
                
        except Exception as e:
            logger.error(f"Error during link cleanup: {str(e)}")

    def setup_schedule(self, runs_per_day: int, cleanup_days: int):
        """Setup the cleanup schedule"""
        try:
            # Update configuration
            self.runs_per_day = max(1, min(24, runs_per_day))  # Ensure between 1 and 24
            self.cleanup_days = max(1, cleanup_days)  # Ensure at least 1 day
            
            # Calculate run hours
            run_hours = self.calculate_intervals()
            
            # Remove existing jobs
            self.scheduler.remove_all_jobs()
            
            # Add new jobs for each hour with explicit UTC timezone
            for hour in run_hours:
                self.scheduler.add_job(
                    self.cleanup_old_links,
                    CronTrigger(hour=hour, timezone=utc),
                    name=f'cleanup_at_{hour}'
                )
            
            logger.info(f"Scheduled cleanup to run at hours (UTC): {run_hours}")
            logger.info(f"Links older than {self.cleanup_days} days will be removed")
            
        except Exception as e:
            logger.error(f"Error setting up schedule: {str(e)}")

    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Link cleanup scheduler started (UTC timezone)")

    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Link cleanup scheduler stopped")

    def get_next_run_times(self) -> List[str]:
        """Get the next scheduled run times for all jobs"""
        try:
            next_runs = []
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time
                if next_run:
                    next_runs.append(next_run.strftime("%Y-%m-%d %H:%M:%S UTC"))
            return next_runs
        except Exception as e:
            logger.error(f"Error getting next run times: {str(e)}")
            return []

# Create global scheduler instance
link_scheduler = LinkCleanupScheduler()