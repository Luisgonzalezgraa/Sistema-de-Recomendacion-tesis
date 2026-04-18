"""
API Routes and Endpoints
Defines all REST endpoints for the irrigation recommendation system
"""
from flask import request, jsonify
from flask_restful import Resource, reqparse
import logging
from app.models.data_models import GeoPoint, WaterComposition, APIResponse
from app.modules.geospatial_analyzer import GeospatialAnalyzer
from app.modules.hydraulic_calculator import HydraulicCalculator
from app.modules.recommendation_engine import RecommendationEngine
from app.services.elevation_service import create_elevation_service
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class HealthCheck(Resource):
    """Health check endpoint"""
    
    def get(self):
        """Check API health status"""
        return APIResponse(
            success=True,
            message="API is running",
            data={'version': config.API_VERSION}
        ).to_dict(), 200


class ElevationAnalysis(Resource):
    """Elevation and topographic analysis endpoint"""
    
    def __init__(self):
        self.geospatial = GeospatialAnalyzer()
        self.elevation_service = create_elevation_service(config.GOOGLE_ELEVATION_API_KEY)
    
    def post(self):
        """
        Perform elevation analysis for given points
        
        Expected JSON:
        {
            "points": [
                {"latitude": float, "longitude": float},
                ...
            ]
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'points' not in data:
                return APIResponse(
                    success=False,
                    message="Missing 'points' field in request",
                    errors=["points field is required"]
                ).to_dict(), 400
            
            # Parse geo points
            geo_points = []
            for point_data in data['points']:
                try:
                    point = GeoPoint(
                        latitude=point_data['latitude'],
                        longitude=point_data['longitude'],
                        elevation=point_data.get('elevation')
                    )
                    geo_points.append(point)
                except KeyError as e:
                    return APIResponse(
                        success=False,
                        message=f"Invalid point data: missing field {str(e)}",
                        errors=[f"Each point must have latitude and longitude"]
                    ).to_dict(), 400
            
            if len(geo_points) < 2:
                return APIResponse(
                    success=False,
                    message="At least 2 points are required",
                    errors=["Need minimum 2 points for analysis"]
                ).to_dict(), 400
            
            # Fetch missing elevation data
            geo_points_with_elevation = self.elevation_service.get_geo_points_with_elevation(
                geo_points
            )
            
            # Perform topographic analysis between first and last point
            topo_analysis = self.geospatial.calculate_slope(
                geo_points_with_elevation[0],
                geo_points_with_elevation[-1]
            )
            
            return APIResponse(
                success=True,
                message="Topographic analysis completed",
                data=topo_analysis.to_dict()
            ).to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error in elevation analysis: {str(e)}")
            return APIResponse(
                success=False,
                message="Error performing elevation analysis",
                errors=[str(e)]
            ).to_dict(), 500


class HydraulicAnalysisEndpoint(Resource):
    """Hydraulic analysis endpoint"""
    
    def __init__(self):
        self.hydraulic = HydraulicCalculator(config.__dict__)
        self.geospatial = GeospatialAnalyzer()
        self.elevation_service = create_elevation_service(config.GOOGLE_ELEVATION_API_KEY)
    
    def post(self):
        """
        Perform hydraulic analysis for irrigation system
        
        Expected JSON:
        {
            "topographic_analysis": {...},
            "water_composition": {
                "density": float,
                "temperature": float,
                "ph": float,
                "salinity": float,
                "hardness": float
            },
            "pipe_length": float,
            "pipe_diameter": float,
            "flow_rate": float
        }
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = [
                'topographic_analysis',
                'water_composition',
                'pipe_length',
                'pipe_diameter',
                'flow_rate'
            ]
            
            missing = [f for f in required_fields if f not in data]
            if missing:
                return APIResponse(
                    success=False,
                    message=f"Missing required fields: {', '.join(missing)}",
                    errors=missing
                ).to_dict(), 400
            
            # Parse water composition
            water_data = data['water_composition']
            water_comp = WaterComposition(
                density=water_data.get('density', 1000),
                temperature=water_data.get('temperature', 20),
                ph=water_data.get('ph', 7.0),
                salinity=water_data.get('salinity', 0),
                hardness=water_data.get('hardness', 0),
                fertilizer_content=water_data.get('fertilizer_content'),
                pesticide_content=water_data.get('pesticide_content')
            )
            
            # Reconstruct topographic analysis from data
            topo_data = data['topographic_analysis']
            start_point = GeoPoint(**topo_data['point_start'])
            end_point = GeoPoint(**topo_data['point_end'])
            
            from app.models.data_models import TopographicAnalysis
            topo = TopographicAnalysis(
                point_start=start_point,
                point_end=end_point,
                elevation_difference=topo_data['elevation_difference'],
                slope_percentage=topo_data['slope_percentage'],
                slope_radians=topo_data['slope_radians'],
                slope_degrees=topo_data['slope_degrees'],
                distance=topo_data['distance']
            )
            
            # Perform hydraulic analysis
            hydraulic_result = self.hydraulic.perform_hydraulic_analysis(
                topographic_analysis=topo,
                water_composition=water_comp,
                pipe_length=data['pipe_length'],
                pipe_diameter=data['pipe_diameter'],
                flow_rate=data['flow_rate'],
                emitter_coefficient=data.get('emitter_coefficient', 0.95),
                emitter_exponent=data.get('emitter_exponent', 0.55)
            )
            
            return APIResponse(
                success=True,
                message="Hydraulic analysis completed",
                data=hydraulic_result.to_dict()
            ).to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error in hydraulic analysis: {str(e)}")
            return APIResponse(
                success=False,
                message="Error performing hydraulic analysis",
                errors=[str(e)]
            ).to_dict(), 500


class RecommendationEndpoint(Resource):
    """Complete recommendation endpoint"""
    
    def __init__(self):
        self.geospatial = GeospatialAnalyzer()
        self.hydraulic = HydraulicCalculator(config.__dict__)
        self.recommendation_engine = RecommendationEngine()
        self.elevation_service = create_elevation_service(config.GOOGLE_ELEVATION_API_KEY)
    
    def post(self):
        """
        Generate complete recommendations for irrigation system
        
        Expected JSON:
        {
            "location": {
                "latitude": float,
                "longitude": float
            },
            "endpoint": {
                "latitude": float,
                "longitude": float
            },
            "water_composition": {
                "density": float,
                "temperature": float,
                "ph": float,
                "salinity": float,
                "hardness": float,
                "fertilizer_content": string (optional),
                "pesticide_content": string (optional)
            },
            "pipe_length": float,
            "pipe_diameter": float,
            "flow_rate": float
        }
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = [
                'location', 'endpoint', 'water_composition',
                'pipe_length', 'pipe_diameter', 'flow_rate'
            ]
            
            missing = [f for f in required_fields if f not in data]
            if missing:
                return APIResponse(
                    success=False,
                    message=f"Missing required fields: {', '.join(missing)}",
                    errors=missing
                ).to_dict(), 400
            
            # Parse geographic points
            start_point = GeoPoint(
                latitude=data['location']['latitude'],
                longitude=data['location']['longitude']
            )
            end_point = GeoPoint(
                latitude=data['endpoint']['latitude'],
                longitude=data['endpoint']['longitude']
            )
            
            # Fetch elevation data
            points_with_elevation = self.elevation_service.get_geo_points_with_elevation(
                [start_point, end_point]
            )
            
            # Perform topographic analysis
            topo_analysis = self.geospatial.calculate_slope(
                points_with_elevation[0],
                points_with_elevation[1]
            )
            
            # Parse water composition
            water_data = data['water_composition']
            water_comp = WaterComposition(
                density=water_data.get('density', 1000),
                temperature=water_data.get('temperature', 20),
                ph=water_data.get('ph', 7.0),
                salinity=water_data.get('salinity', 0),
                hardness=water_data.get('hardness', 0),
                fertilizer_content=water_data.get('fertilizer_content'),
                pesticide_content=water_data.get('pesticide_content')
            )
            
            # Perform hydraulic analysis
            hydraulic_result = self.hydraulic.perform_hydraulic_analysis(
                topographic_analysis=topo_analysis,
                water_composition=water_comp,
                pipe_length=data['pipe_length'],
                pipe_diameter=data['pipe_diameter'],
                flow_rate=data['flow_rate'],
                emitter_coefficient=data.get('emitter_coefficient', 0.95),
                emitter_exponent=data.get('emitter_exponent', 0.55)
            )
            
            # Generate recommendations
            recommendation = self.recommendation_engine.generate_recommendations(
                topographic_analysis=topo_analysis,
                water_composition=water_comp,
                hydraulic_analysis=hydraulic_result
            )
            
            return APIResponse(
                success=True,
                message="Recommendations generated successfully",
                data=recommendation.to_dict()
            ).to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return APIResponse(
                success=False,
                message="Error generating recommendations",
                errors=[str(e)]
            ).to_dict(), 500


def register_routes(app, api):
    """
    Register all routes with the Flask app
    
    Args:
        app: Flask application instance
        api: Flask-RESTful Api instance
    """
    # Health check
    api.add_resource(HealthCheck, '/api/v1/health')
    
    # Elevation analysis
    api.add_resource(ElevationAnalysis, '/api/v1/analysis/elevation')
    
    # Hydraulic analysis
    api.add_resource(HydraulicAnalysisEndpoint, '/api/v1/analysis/hydraulic')
    
    # Recommendations
    api.add_resource(RecommendationEndpoint, '/api/v1/recommendations')
    
    # API documentation
    @app.route('/api/v1/docs')
    def documentation():
        return {
            'title': config.API_TITLE,
            'version': config.API_VERSION,
            'endpoints': {
                'health': {
                    'url': '/api/v1/health',
                    'method': 'GET',
                    'description': 'Check API health status'
                },
                'elevation_analysis': {
                    'url': '/api/v1/analysis/elevation',
                    'method': 'POST',
                    'description': 'Perform elevation analysis for geographic points'
                },
                'hydraulic_analysis': {
                    'url': '/api/v1/analysis/hydraulic',
                    'method': 'POST',
                    'description': 'Perform hydraulic analysis for irrigation system'
                },
                'recommendations': {
                    'url': '/api/v1/recommendations',
                    'method': 'POST',
                    'description': 'Generate complete design recommendations'
                }
            }
        }, 200
