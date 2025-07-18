import logging
import sys
from app.core.config import settings

def setup_logging():
    """Setup application logging"""
    # level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # logging.basicConfig(
    #     level=level,
    #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #     handlers=[
    #         logging.StreamHandler(sys.stdout),
    #         logging.FileHandler('app.log')
    #     ]
    # )
    
    # Suppress Firebase SDK logs
    logging.getLogger('firebase_admin').setLevel(logging.WARNING)
    logging.getLogger('google.cloud').setLevel(logging.WARNING)