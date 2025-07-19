"""
Main application entry point for Amber-Home data collection service.
"""

import logging
import signal
import sys
import time
from typing import Optional
from .config import Config
from .database import DatabaseService
from .services import AmberService, CollectionService

# Configure logging
def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)


class Application:
    """Main application class."""
    
    def __init__(self):
        self.running = True
        self.db_service: Optional[DatabaseService] = None
        self.amber_service: Optional[AmberService] = None
        self.collection_service: Optional[CollectionService] = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, stopping gracefully...")
        self.running = False
    
    def initialize_services(self) -> None:
        """Initialize all application services."""
        logger.info("Initializing application services...")
        
        # Validate configuration
        Config.validate()
        
        # Initialize database service
        self.db_service = DatabaseService()
        self.db_service.connect()
        self.db_service.ensure_schema()
        
        # Initialize Amber API service
        self.amber_service = AmberService()
        self.amber_service.initialize()
        
        # Initialize collection service
        self.collection_service = CollectionService(self.db_service, self.amber_service)
        
        logger.info("All services initialized successfully")
    
    def cleanup_services(self) -> None:
        """Cleanup application services."""
        logger.info("Cleaning up application services...")
        
        if self.db_service:
            self.db_service.disconnect()
        
        logger.info("Cleanup completed")
    
    def should_initialize_data(self) -> bool:
        """Determine if database needs initialization."""
        if Config.FORCE_REINIT:
            logger.info("FORCE_REINIT=true, forcing full data collection")
            return True
        
        if not self.db_service.is_initialized():
            logger.info("Database not fully initialized")
            return True
        
        logger.info("Database already initialized")
        return False
    
    def run_data_collection_cycle(self) -> None:
        """Run a single data collection cycle."""
        try:
            # Collect sites first (required for data collection)
            self.collection_service.collect_sites()
            
            # Check if we need to initialize with historical data
            if self.should_initialize_data():
                logger.info("Running historical data collection...")
                self.collection_service.collect_historical_data()
            else:
                logger.info("Running incremental data update...")
                self.collection_service.update_latest_data()
                
        except Exception as e:
            logger.error(f"Error during data collection cycle: {e}")
            raise
    
    def run_update_loop(self) -> None:
        """Run the main update loop - collect new data every 5 minutes."""
        logger.info(f"Starting continuous update loop (every {Config.COLLECTION_INTERVAL_MINUTES} minutes)...")
        
        while self.running:
            try:
                # Update with latest data (no future data will be collected)
                logger.info("Running scheduled data update...")
                self.collection_service.update_latest_data()
                
                # Wait for configured interval before next update
                interval_seconds = Config.COLLECTION_INTERVAL_MINUTES * 60
                logger.info(f"Next update in {Config.COLLECTION_INTERVAL_MINUTES} minutes...")
                
                for _ in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error during update cycle: {e}")
                # Wait 1 minute before retrying on error
                logger.info("Waiting 1 minute before retrying...")
                time.sleep(60)
    
    def run(self) -> None:
        """Main application entry point."""
        logger.info("Starting Amber-Home Data Collection Service...")
        
        try:
            # Initialize all services
            self.initialize_services()
            
            # Run initial data collection
            self.run_data_collection_cycle()
            
            # Start continuous update loop (5-minute intervals)
            self.run_update_loop()
            
        except Exception as e:
            logger.error(f"Fatal error in application: {e}")
            raise
        
        finally:
            self.cleanup_services()
            
        logger.info("Application stopped")


def main():
    """Application entry point."""
    setup_logging()
    
    app = Application()
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()