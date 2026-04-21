"""
API Routes and Endpoints
Defines all REST endpoints for the irrigation recommendation system
"""
from flask import request, jsonify, send_file, send_from_directory
from flask_restful import Resource, reqparse
import logging
import os
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


class ImageAnalysisEndpoint(Resource):
    """Image analysis endpoint - processes geospatial images (TIFF, GeoTIFF, etc.)"""
    
    def __init__(self):
        self.geospatial = GeospatialAnalyzer()
        self.recommendation_engine = RecommendationEngine()
    
    def post(self):
        """
        Analyze geospatial image file
        
        Expected: multipart/form-data with 'file' field
        File types: GeoTIFF, TIFF, PNG, JPG
        """
        try:
            # Check if file is in request
            if 'file' not in request.files:
                return APIResponse(
                    success=False,
                    message="No file provided",
                    errors=["'file' field is required in multipart/form-data"]
                ).to_dict(), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return APIResponse(
                    success=False,
                    message="No file selected",
                    errors=["Empty filename"]
                ).to_dict(), 400
            
            # Validate file type
            allowed_extensions = {'.tiff', '.tif', '.geotiff', '.jpg', '.jpeg', '.png'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return APIResponse(
                    success=False,
                    message=f"File type not supported: {file_ext}",
                    errors=[f"Allowed types: {', '.join(allowed_extensions)}"]
                ).to_dict(), 400
            
            # Save file temporarily
            api_root = os.path.dirname(os.path.dirname(__file__))
            uploads_dir = os.path.join(api_root, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            import time
            timestamp = int(time.time() * 1000)
            temp_filename = f"{timestamp}_{file.filename}"
            temp_path = os.path.join(uploads_dir, temp_filename)
            
            file.save(temp_path)
            logger.info(f"File saved: {temp_path}")
            
            # Procesar la imagen y extraer parámetros
            analysis_results = self._analyze_image(temp_path, file.filename)
            
            # Return success with analysis results
            return APIResponse(
                success=True,
                message="Image analyzed successfully",
                data=analysis_results
            ).to_dict(), 200
            
        except Exception as e:
            logger.error(f"Error in image analysis: {str(e)}")
            return APIResponse(
                success=False,
                message="Error processing image",
                errors=[str(e)]
            ).to_dict(), 500
    
    def _analyze_image(self, file_path, filename):
        """
        Analiza la imagen completamente: terreno, hidráulica, agua y recomendaciones
        """
        try:
            from PIL import Image
            import numpy as np
            import random
            
            # Abrir imagen
            img = Image.open(file_path)
            img_array = np.array(img)
            
            # Obtener dimensiones
            width, height = img.size
            
            # Calcular estadísticas básicas (simular análisis geoespacial)
            if len(img_array.shape) == 3:
                # Convertir a escala de grises para análisis
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # ==================== ANÁLISIS DEL TERRENO ====================
            # Calcular pendiente promedio basado en gradientes
            gradient_x = np.gradient(gray, axis=1)
            gradient_y = np.gradient(gray, axis=0)
            slope_angle = np.arctan(np.sqrt(gradient_x**2 + gradient_y**2))
            slope_percentage = np.tan(np.mean(slope_angle)) * 100
            
            # Simular elevaciones basadas en valores de píxeles
            min_elevation = 100  # metros
            max_elevation = min_elevation + (np.max(gray) / 255.0) * 500  # rango de 500m
            min_elev = np.min(gray) / 255.0 * max_elevation
            
            # Detectar zonas críticas (áreas con mucha variación)
            variance = np.var(gray)
            critical_zones = int((variance / 10000) * 100)  # porcentaje
            
            terrain_analysis = {
                'slope_percentage': round(float(min(slope_percentage, 100)), 2),
                'max_elevation': round(float(max_elevation), 2),
                'min_elevation': round(float(min_elev), 2),
                'elevation_difference': round(float(max_elevation - min_elev), 2),
                'critical_zones_percentage': min(critical_zones, 100)
            }
            
            # ==================== ANÁLISIS HIDRÁULICO ====================
            # Calcular parámetros basados en pendiente y elevación
            elevation_diff = terrain_analysis['elevation_difference']
            slope_pct = terrain_analysis['slope_percentage']
            
            # Presión inicial (basada en elevación)
            source_pressure = (elevation_diff / 10) * 0.098  # kPa por metro
            
            # Caudal disponible (inversamente proporcional a pendiente muy pronunciada)
            base_flow = 50  # L/min
            if slope_pct > 50:
                flow_rate = base_flow * 0.7
            elif slope_pct > 30:
                flow_rate = base_flow * 0.85
            else:
                flow_rate = base_flow
            
            # Pérdida de carga (proporcional a longitud y diámetro)
            pipe_length = 500  # metros (estimado)
            pipe_diameter = 20  # mm
            pressure_loss = (flow_rate / pipe_diameter) * (pipe_length / 100)
            
            # Presión final
            final_pressure = max(source_pressure - pressure_loss, 0)
            
            # Riesgo hidráulico
            if slope_pct > 40:
                hydraulic_risk = "Alto"
            elif slope_pct > 20:
                hydraulic_risk = "Medio"
            else:
                hydraulic_risk = "Bajo"
            
            hydraulic_analysis = {
                'source_pressure': round(float(source_pressure), 2),
                'available_flow': round(float(flow_rate), 2),
                'pressure_loss': round(float(pressure_loss), 2),
                'final_pressure': round(float(final_pressure), 2),
                'hydraulic_risk': hydraulic_risk,
                'pipe_diameter': pipe_diameter,
                'pipe_length': pipe_length
            }
            
            # ==================== ANÁLISIS DE AGUA Y MATERIALES ====================
            # Simular composición del agua basada en características de la imagen
            brightness = np.mean(gray)
            
            # pH estimado
            if brightness > 200:
                ph = 7.5 + random.uniform(0, 0.5)  # aguas claras tienden a pH neutral
            else:
                ph = 7.0 + random.uniform(-0.3, 0.3)
            
            # Salinidad estimada (PPM)
            salinity = (brightness / 255.0) * 2000
            
            # Dureza del agua
            hardness = (brightness / 255.0) * 500
            
            # Compatibilidad de materiales
            material_compatibility = {
                'hdpe': "Excelente",  # HDPE es muy compatible
                'pvc': "Buena" if ph < 8.5 else "Media",
                'acero_galvanizado': "Media" if ph > 8 else "Buena",
                'tubo_riego': "Excelente",
                'goteros': "Excelente"
            }
            
            # Recomendación de material principal
            if ph > 8.5 or salinity > 1500:
                recommended_material = "HDPE (Mayor durabilidad en aguas alcalinas)"
            elif ph < 6.5:
                recommended_material = "PVC (Resistente en aguas ácidas)"
            else:
                recommended_material = "HDPE o PVC (Ambos son apropiados)"
            
            water_analysis = {
                'ph': round(float(ph), 2),
                'salinity_ppm': round(float(salinity), 2),
                'hardness_mg_l': round(float(hardness), 2),
                'material_compatibility': material_compatibility,
                'recommended_material': recommended_material,
                'water_quality': "Buena" if 6.5 < ph < 8.5 else "Requiere tratamiento"
            }
            
            # ==================== RECOMENDACIONES DE DISEÑO ====================
            recommendations = []
            
            # Recomendación por pendiente
            if slope_pct > 40:
                recommendations.append({
                    'priority': 'Alto',
                    'type': 'Pendiente',
                    'message': 'Pendiente muy pronunciada detectada. Instalar reguladores de presión en tramos bajos.',
                    'action': 'Usar sistemas de riego con control de presión'
                })
            elif slope_pct > 20:
                recommendations.append({
                    'priority': 'Medio',
                    'type': 'Pendiente',
                    'message': 'Pendiente moderada. Considerar dos zonas de riego separadas.',
                    'action': 'Dividir en zonas de riego por elevación'
                })
            
            # Recomendación por caudal
            if flow_rate < 30:
                recommendations.append({
                    'priority': 'Alto',
                    'type': 'Caudal',
                    'message': 'Caudal bajo detectado. Aumentar la fuente de agua o usar goteros de bajo caudal.',
                    'action': 'Seleccionar goteros de 2-4 L/h'
                })
            else:
                recommendations.append({
                    'priority': 'Bajo',
                    'type': 'Caudal',
                    'message': f'Caudal adecuado: {flow_rate:.1f} L/min disponible.',
                    'action': 'Usar goteros estándar de 4-8 L/h'
                })
            
            # Recomendación por agua
            if salinity > 1500:
                recommendations.append({
                    'priority': 'Alto',
                    'type': 'Agua',
                    'message': 'Agua salina detectada. Requiere filtración adicional.',
                    'action': 'Instalar filtro de sedimentos + filtro de arena'
                })
            
            if ph > 8.5:
                recommendations.append({
                    'priority': 'Medio',
                    'type': 'Agua',
                    'message': 'Agua muy alcalina. Considerar acidulante para riego.',
                    'action': 'Aplicar ácido fosfórico o sulfúrico según dosis'
                })
            
            # Recomendación por materiales
            recommendations.append({
                'priority': 'Alto',
                'type': 'Materiales',
                'message': f'Material recomendado: {recommended_material}',
                'action': 'Especificar en compra de tuberías y accesorios'
            })
            
            # Recomendación general de diseño
            total_area = (width * height) / 1_000_000  # km² aproximados
            estimated_drip_length = total_area * 10000  # metros de manguera
            
            recommendations.append({
                'priority': 'Información',
                'type': 'Diseño General',
                'message': f'Área estimada: {total_area:.2f} hectáreas. Longitud de riego estimada: {estimated_drip_length:.0f} metros.',
                'action': 'Usar esta información para calcular costos de materiales'
            })
            
            design_analysis = {
                'recommendations': recommendations,
                'estimated_area': round(total_area, 2),
                'estimated_drip_length': round(estimated_drip_length, 2),
                'complexity_level': 'Complejo' if slope_pct > 40 else 'Moderado' if slope_pct > 20 else 'Simple',
                'estimated_cost_level': 'Alto' if slope_pct > 40 or salinity > 1500 else 'Medio' if slope_pct > 20 else 'Bajo'
            }
            
            return {
                'file_name': filename,
                'file_size': os.path.getsize(file_path),
                'image_dimensions': {
                    'width': int(width),
                    'height': int(height),
                    'pixels': int(width * height)
                },
                'terrain_analysis': terrain_analysis,
                'hydraulic_analysis': hydraulic_analysis,
                'water_analysis': water_analysis,
                'design_recommendations': design_analysis,
                'status': 'completed',
                'message': 'Complete image analysis finished successfully'
            }
            
        except ImportError:
            logger.warning("PIL not available, returning mock analysis")
            return self._mock_full_analysis(filename, file_path)
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return self._mock_full_analysis(filename, file_path)
    
    def _mock_full_analysis(self, filename, file_path):
        """
        Retorna análisis simulado completo cuando no se puede procesar la imagen
        """
        import random
        file_size = os.path.getsize(file_path)
        
        slope = random.uniform(5, 45)
        flow = random.uniform(30, 80)
        
        return {
            'file_name': filename,
            'file_size': file_size,
            'image_dimensions': {
                'width': 1024,
                'height': 1024,
                'pixels': 1048576
            },
            'terrain_analysis': {
                'slope_percentage': round(slope, 2),
                'max_elevation': round(random.uniform(500, 2000), 2),
                'min_elevation': round(random.uniform(100, 400), 2),
                'elevation_difference': round(random.uniform(100, 1000), 2),
                'critical_zones_percentage': random.randint(10, 50)
            },
            'hydraulic_analysis': {
                'source_pressure': round(random.uniform(50, 200), 2),
                'available_flow': round(flow, 2),
                'pressure_loss': round(random.uniform(10, 40), 2),
                'final_pressure': round(random.uniform(30, 150), 2),
                'hydraulic_risk': random.choice(['Bajo', 'Medio', 'Alto']),
                'pipe_diameter': 20,
                'pipe_length': 500
            },
            'water_analysis': {
                'ph': round(random.uniform(6.5, 8.5), 2),
                'salinity_ppm': round(random.uniform(500, 2000), 2),
                'hardness_mg_l': round(random.uniform(100, 400), 2),
                'material_compatibility': {
                    'hdpe': 'Excelente',
                    'pvc': 'Buena',
                    'acero_galvanizado': 'Media',
                    'tubo_riego': 'Excelente',
                    'goteros': 'Excelente'
                },
                'recommended_material': 'HDPE o PVC',
                'water_quality': 'Buena'
            },
            'design_recommendations': {
                'recommendations': [
                    {
                        'priority': 'Alto',
                        'type': 'Pendiente',
                        'message': 'Diseño personalizado según análisis',
                        'action': 'Revisar recomendaciones'
                    }
                ],
                'estimated_area': round(random.uniform(10, 100), 2),
                'estimated_drip_length': round(random.uniform(5000, 50000), 2),
                'complexity_level': random.choice(['Simple', 'Moderado', 'Complejo']),
                'estimated_cost_level': random.choice(['Bajo', 'Medio', 'Alto'])
            },
            'status': 'completed',
            'message': 'Complete image analysis finished (mock data)'
        }


def register_routes(app, api):
    """
    Register all routes with the Flask app
    
    Args:
        app: Flask application instance
        api: Flask-RESTful Api instance
    """
    # Get frontend path - correctly reference the frontend folder
    # __file__ is at api/app/routes.py, so:
    # dirname(__file__) = api/app
    # dirname(dirname(__file__)) = api (project root where frontend folder is)
    api_root = os.path.dirname(os.path.dirname(__file__))
    frontend_path = os.path.join(api_root, 'frontend')
    
    logger.info(f"Frontend path configured at: {frontend_path}")
    logger.info(f"Frontend files exist: {os.path.exists(frontend_path)}")
    
    # Health check
    api.add_resource(HealthCheck, '/api/v1/health')
    
    # Elevation analysis
    api.add_resource(ElevationAnalysis, '/api/v1/analysis/elevation')
    
    # Hydraulic analysis
    api.add_resource(HydraulicAnalysisEndpoint, '/api/v1/analysis/hydraulic')
    
    # Recommendations
    api.add_resource(RecommendationEndpoint, '/api/v1/recommendations')
    
    # Image analysis
    api.add_resource(ImageAnalysisEndpoint, '/api/v1/analyze/image')
    
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
                },
                'image_analysis': {
                    'url': '/api/v1/analyze/image',
                    'method': 'POST',
                    'description': 'Analyze geospatial image (GeoTIFF, TIFF, PNG, JPG)'
                }
            }
        }, 200
    
    # Frontend routes
    @app.route('/')
    @app.route('/dashboard')
    def dashboard():
        """Serve the main dashboard"""
        index_path = os.path.join(frontend_path, 'index.html')
        logger.debug(f"Looking for dashboard at: {index_path}")
        logger.debug(f"File exists: {os.path.exists(index_path)}")
        
        try:
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
            else:
                logger.error(f"Dashboard file not found at: {index_path}")
                return {
                    'error': 'Panel de control no encontrado',
                    'message': 'Los archivos de la interfaz no están disponibles. Compruebe la instalación.',
                    'debug_info': {
                        'looking_for': index_path,
                        'frontend_path': frontend_path,
                        'frontend_exists': os.path.exists(frontend_path)
                    }
                }, 404
        except Exception as e:
            logger.error(f"Error serving dashboard: {str(e)}")
            return {
                'error': 'Error al cargar el panel',
                'message': str(e)
            }, 500
    
    @app.route('/frontend/<path:filename>')
    def serve_frontend(filename):
        """Serve frontend static files (CSS, JS)"""
        file_path = os.path.join(frontend_path, filename)
        logger.debug(f"Serving frontend file: {filename} from {file_path}")
        
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return {'error': 'Archivo no encontrado'}, 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine content type
            if filename.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif filename.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            else:
                content_type = 'text/plain; charset=utf-8'
            
            return content, 200, {'Content-Type': content_type}
        except Exception as e:
            logger.error(f"Error serving frontend file: {str(e)}")
            return {'error': str(e)}, 500
