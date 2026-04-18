"""
Main entry point for the API application
"""
import os
import logging
from app import create_app
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Initialize and run the Flask application
    """
    # Determine environment
    env = os.getenv('FLASK_ENV', 'development')
    logger.info(f"Starting API in {env} mode")
    
    # Create Flask application
    app = create_app(env)
    
    # Get configuration
    config = get_config(env)
    
    # Run server
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = env == 'development'
    
    logger.info(f"API starting on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
