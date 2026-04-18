"""
Flask application factory
"""
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
import logging
from config import get_config


def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format=app.config.get('LOG_FORMAT')
    )
    
    # Initialize extensions
    CORS(app)
    api = Api(app)
    
    # Register blueprints and routes
    from app.routes import register_routes
    register_routes(app, api)
    
    # Error handlers
    register_error_handlers(app)
    
    return app


def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad Request', 'message': str(error)}, 400
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not Found', 'message': 'The requested resource was not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal Server Error', 'message': 'An internal server error occurred'}, 500
