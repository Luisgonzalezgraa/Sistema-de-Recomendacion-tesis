"""
API Routes and Endpoints
Defines all REST endpoints for the irrigation recommendation system
"""
from flask import request, jsonify, send_file, send_from_directory
from flask_restful import Resource, reqparse
import logging
import os
import time
from werkzeug.utils import secure_filename
from app.models.data_models import GeoPoint, WaterComposition, APIResponse
from app.modules.geospatial_analyzer import GeospatialAnalyzer
from app.modules.hydraulic_calculator import HydraulicCalculator
from app.modules.recommendation_engine import RecommendationEngine
from app.services.elevation_service import create_elevation_service
from app.database import add_material, add_pump, delete_material, delete_pump, list_materials, list_pumps
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

CATALOG_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def save_catalog_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    file_ext = os.path.splitext(file_storage.filename)[1].lower()
    if file_ext not in CATALOG_IMAGE_EXTENSIONS:
        raise ValueError("La foto del material debe ser JPG, PNG o WEBP.")

    api_root = os.path.dirname(os.path.dirname(__file__))
    catalog_dir = os.path.join(api_root, "uploads", "catalog")
    os.makedirs(catalog_dir, exist_ok=True)
    safe_name = secure_filename(file_storage.filename)
    filename = f"{int(time.time() * 1000)}_{safe_name}"
    file_path = os.path.join(catalog_dir, filename)
    file_storage.save(file_path)
    return f"/uploads/catalog/{filename}"


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


class PumpCatalogEndpoint(Resource):
    """Pump catalog endpoint backed by SQLite"""

    def get(self):
        return APIResponse(
            success=True,
            message="Pump catalog loaded",
            data=list_pumps()
        ).to_dict(), 200

    def post(self):
        try:
            data = request.get_json() or {}
            required = ["model", "engine_power_hp", "max_flow_l_min", "max_head_m"]
            missing = [field for field in required if data.get(field) in (None, "")]
            if missing:
                return APIResponse(
                    success=False,
                    message=f"Missing required fields: {', '.join(missing)}",
                    errors=missing
                ).to_dict(), 400

            pump = add_pump(data)
            return APIResponse(
                success=True,
                message="Pump added to catalog",
                data=pump
            ).to_dict(), 201
        except Exception as e:
            logger.error(f"Error adding pump: {str(e)}")
            return APIResponse(
                success=False,
                message="Error adding pump to catalog",
                errors=[str(e)]
            ).to_dict(), 500

    def delete(self, pump_id=None):
        if pump_id is None:
            return APIResponse(
                success=False,
                message="Pump id is required",
                errors=["pump_id"]
            ).to_dict(), 400
        try:
            deleted = delete_pump(pump_id)
            return APIResponse(
                success=True,
                message="Pump deleted from catalog",
                data=deleted
            ).to_dict(), 200
        except ValueError as e:
            return APIResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            ).to_dict(), 404
        except Exception as e:
            logger.error(f"Error deleting pump: {str(e)}")
            return APIResponse(
                success=False,
                message="Error deleting pump from catalog",
                errors=[str(e)]
            ).to_dict(), 500


class MaterialCatalogEndpoint(Resource):
    """Irrigation material catalog endpoint backed by SQLite"""

    def get(self):
        material_type = request.args.get("type")
        return APIResponse(
            success=True,
            message="Material catalog loaded",
            data=list_materials(material_type)
        ).to_dict(), 200

    def post(self):
        try:
            if request.mimetype in ("multipart/form-data", "application/x-www-form-urlencoded"):
                data = request.form.to_dict()
                image_url = save_catalog_image(request.files.get("photo")) if request.mimetype == "multipart/form-data" else None
                if image_url:
                    data["image_url"] = image_url
            elif request.is_json:
                data = request.get_json(silent=True) or {}
            else:
                data = {}

            required = ["material_type", "name", "component"]
            missing = [field for field in required if data.get(field) in (None, "")]
            if missing:
                return APIResponse(
                    success=False,
                    message=f"Missing required fields: {', '.join(missing)}",
                    errors=missing
                ).to_dict(), 400

            material = add_material(data)
            return APIResponse(
                success=True,
                message="Material added to catalog",
                data=material
            ).to_dict(), 201
        except ValueError as e:
            logger.warning(f"Invalid material input: {str(e)}")
            return APIResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            ).to_dict(), 400
        except Exception as e:
            logger.error(f"Error adding material: {str(e)}")
            return APIResponse(
                success=False,
                message="Error adding material to catalog",
                errors=[str(e)]
            ).to_dict(), 500

    def delete(self, material_id=None):
        if material_id is None:
            return APIResponse(
                success=False,
                message="Material id is required",
                errors=["material_id"]
            ).to_dict(), 400
        try:
            deleted = delete_material(material_id)
            return APIResponse(
                success=True,
                message="Material deleted from catalog",
                data=deleted
            ).to_dict(), 200
        except ValueError as e:
            return APIResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            ).to_dict(), 404
        except Exception as e:
            logger.error(f"Error deleting material: {str(e)}")
            return APIResponse(
                success=False,
                message="Error deleting material from catalog",
                errors=[str(e)]
            ).to_dict(), 500


class ImageAnalysisEndpoint(Resource):
    """Image analysis endpoint - processes geospatial images (TIFF, GeoTIFF, etc.)"""

    PUMP_CATALOG = [
        {
            'model': 'Honda WB20',
            'type': 'Centrifuga 2 pulg.',
            'engine': 'GX160',
            'engine_power_hp': 4.8,
            'max_flow_l_min': 670,
            'max_head_m': 32.0,
            'max_pressure_kpa': 313.92,
            'source': 'Honda Fuerza Chile',
            'source_url': 'https://fuerza.honda.cl/motobomba/motobomba-honda-wb20/'
        },
        {
            'model': 'Honda WB30',
            'type': 'Centrifuga 3 pulg.',
            'engine': 'GX160',
            'engine_power_hp': 4.8,
            'max_flow_l_min': 1100,
            'max_head_m': 23.0,
            'max_pressure_kpa': 225.63,
            'source': 'Honda Fuerza Chile',
            'source_url': 'https://fuerza.honda.cl/motobomba/motobomba-honda-wb30/'
        },
        {
            'model': 'Honda WH20',
            'type': 'Alta presion 2 pulg.',
            'engine': 'GX160',
            'engine_power_hp': 4.8,
            'max_flow_l_min': 450,
            'max_head_m': 45.0,
            'max_pressure_kpa': 441.45,
            'source': 'Honda Fuerza Chile',
            'source_url': 'https://fuerza.honda.cl/motobomba/motobomba-honda-wh20/'
        },
        {
            'model': 'Honda WT30',
            'type': 'Aguas turbias 3 pulg.',
            'engine': 'GX270',
            'engine_power_hp': 8.3,
            'max_flow_l_min': 1210,
            'max_head_m': 27.0,
            'max_pressure_kpa': 264.87,
            'source': 'Honda Fuerza Chile',
            'source_url': 'https://fuerza.honda.cl/motobomba/motobomba-honda-wt30/'
        },
        {
            'model': 'Koshin SEV-50X',
            'type': 'Centrifuga agua limpia 2 pulg.',
            'engine': 'Koshin K180',
            'engine_power_hp': 4.8,
            'max_flow_l_min': 620,
            'max_head_m': 27.0,
            'max_pressure_kpa': 264.87,
            'source': 'Koshin Pump',
            'source_url': 'https://koshin-pump.com/en/product/sev-50x/'
        },
        {
            'model': 'Koshin KTZ-50X',
            'type': 'Aguas sucias 2 pulg.',
            'engine': 'Koshin K180',
            'engine_power_hp': 4.7,
            'max_flow_l_min': 680,
            'max_head_m': 22.0,
            'max_pressure_kpa': 215.82,
            'source': 'Koshin LTD',
            'source_url': 'https://www.koshin-ltd.jp/en/products/60.html'
        },
        {
            'model': 'Koshin KTH-50X',
            'type': 'Aguas sucias 2 pulg.',
            'engine': 'Honda GX160',
            'engine_power_hp': 4.8,
            'max_flow_l_min': 700,
            'max_head_m': 30.0,
            'max_pressure_kpa': 294.30,
            'source': 'Koshin Espana',
            'source_url': 'https://koshin.es/producto/kth-80x/'
        },
        {
            'model': 'Daishin-Honda SCH-5050HX',
            'type': 'Alta presion 2 pulg.',
            'engine': 'Honda GX160',
            'engine_power_hp': 5.5,
            'max_flow_l_min': 400,
            'max_head_m': 50.0,
            'max_pressure_kpa': 490.50,
            'source': 'Procimspa Chile',
            'source_url': 'https://www.procimspa.cl/m/?Id=1383&L=S1'
        },
        {
            'model': 'Evans 7IME1000',
            'type': 'Industrial electrica 3 pulg.',
            'engine': 'Electrico trifasico',
            'engine_power_hp': 10.0,
            'max_flow_l_min': 1500,
            'max_head_m': 40.0,
            'max_pressure_kpa': 392.40,
            'source': 'Evans Mexico',
            'source_url': 'https://evans.com.mx/bomba-industrial-electrica-10-hp-7ime1000.html'
        }
    ]
    
    def __init__(self):
        self.geospatial = GeospatialAnalyzer()
        self.hydraulic = HydraulicCalculator(config.__dict__)
        self.recommendation_engine = RecommendationEngine()
        self.elevation_service = create_elevation_service(config.GOOGLE_ELEVATION_API_KEY)
    
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
            
            assumptions = self._parse_hydraulic_assumptions(request.form)

            # Procesar la imagen y extraer parametros
            analysis_results = self._analyze_image(temp_path, file.filename, assumptions)
            
            # Return success with analysis results
            return APIResponse(
                success=True,
                message="Image analyzed successfully",
                data=analysis_results
            ).to_dict(), 200
            
        except ValueError as e:
            logger.warning(f"Invalid image analysis input: {str(e)}")
            return APIResponse(
                success=False,
                message=str(e),
                errors=[str(e)]
            ).to_dict(), 400
        except Exception as e:
            logger.error(f"Error in image analysis: {str(e)}")
            return APIResponse(
                success=False,
                message="Error processing image",
                errors=[str(e)]
            ).to_dict(), 500
    
    def _parse_hydraulic_assumptions(self, form_data):
        defaults = {
            'flow_per_hectare_l_min': 35.0,
            'emitter_operating_pressure_kpa': 100.0,
            'pressure_safety_factor': 1.2,
            'pump_efficiency': 0.60,
            'max_sector_area_ha': 3.0,
            'minimum_flow_l_min': 20.0,
            'hazen_williams_c': 150.0,
            'pipe_diameter_large_m': 0.04,
            'pipe_diameter_small_m': 0.032,
            'minimum_pipe_length_m': 80.0,
            'pipe_length_factor': 1.25
        }
        ranges = {
            'flow_per_hectare_l_min': (1.0, 500.0),
            'emitter_operating_pressure_kpa': (10.0, 500.0),
            'pressure_safety_factor': (1.0, 2.5),
            'pump_efficiency': (0.1, 0.95),
            'max_sector_area_ha': (0.1, 100.0),
            'minimum_flow_l_min': (0.0, 500.0),
            'hazen_williams_c': (60.0, 180.0),
            'pipe_diameter_large_m': (0.005, 0.5),
            'pipe_diameter_small_m': (0.005, 0.5),
            'minimum_pipe_length_m': (1.0, 5000.0),
            'pipe_length_factor': (0.1, 10.0)
        }

        assumptions = {}
        for key, default in defaults.items():
            raw_value = form_data.get(key, default)
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                value = default

            lower, upper = ranges[key]
            assumptions[key] = min(max(value, lower), upper)

        return assumptions

    def _analyze_image(self, file_path, filename, hydraulic_assumptions=None):
        """
        Analyze either a DEM GeoTIFF or a georeferenced drone GeoTIFF.
        RGB imagery is used only for its coordinates; elevation comes from
        Google Elevation API so the system does not invent values from pixels.
        """
        import numpy as np

        dem_data = self._read_dem(file_path)
        source_width = dem_data.get('source_width', dem_data['width'])
        source_height = dem_data.get('source_height', dem_data['height'])
        source_pixel_size_x, source_pixel_size_y = self._pixel_size_meters(dem_data)
        source_area = self._area_hectares(
            source_width,
            source_height,
            source_pixel_size_x,
            source_pixel_size_y
        )
        terrain_limits = self._build_terrain_limits(
            dem_data,
            source_width,
            source_height,
            source_pixel_size_x,
            source_pixel_size_y,
            source_area
        )

        if dem_data.get('array') is None:
            dem_data = self._build_dem_from_google(dem_data)

        elevation = dem_data['array'].astype('float64')
        width = dem_data['width']
        height = dem_data['height']

        valid = np.isfinite(elevation)
        if not valid.any():
            raise ValueError("El DEM no contiene valores de elevacion validos.")

        values = elevation[valid]
        min_elev = float(np.min(values))
        max_elev = float(np.max(values))
        median_elev = float(np.median(values))
        elevation_diff = max_elev - min_elev

        pixel_size_x, pixel_size_y = self._pixel_size_meters(dem_data)
        slope_percentage = None
        slope_degrees = None
        slope_ratio = None
        critical_zones_percentage = None
        slope_values = np.array([])

        if pixel_size_x and pixel_size_y:
            elevation_for_gradient = elevation.copy()
            if not np.isfinite(elevation_for_gradient).all():
                elevation_for_gradient[~np.isfinite(elevation_for_gradient)] = median_elev
            gradient_y, gradient_x = np.gradient(elevation_for_gradient, pixel_size_y, pixel_size_x)
            slope_ratio_values = np.sqrt(gradient_x ** 2 + gradient_y ** 2)
            slope = slope_ratio_values * 100
            slope_degrees_values = np.degrees(np.arctan(slope_ratio_values))
            slope_values = slope[np.isfinite(slope)]
            valid_degree_values = slope_degrees_values[np.isfinite(slope_degrees_values)]
            valid_ratio_values = slope_ratio_values[np.isfinite(slope_ratio_values)]
            if slope_values.size:
                slope_percentage = float(np.mean(slope_values))
                slope_degrees = float(np.mean(valid_degree_values))
                slope_ratio = float(np.mean(valid_ratio_values))
                p75 = float(np.percentile(slope_values, 75))
                critical_zones_percentage = float(np.mean(slope_values >= p75) * 100)

        terrain_analysis = {
            'slope_percentage': round(slope_percentage, 2) if slope_percentage is not None else None,
            'slope_degrees': round(slope_degrees, 2) if slope_degrees is not None else None,
            'slope_ratio': round(slope_ratio, 4) if slope_ratio is not None else None,
            'slope_mean_definition': 'Media aritmetica del angulo de pendiente por celda DEM: atan(sqrt((dz/dx)^2 + (dz/dy)^2)).',
            'max_elevation': round(max_elev, 2),
            'min_elevation': round(min_elev, 2),
            'median_elevation': round(median_elev, 2),
            'elevation_difference': round(elevation_diff, 2),
            'critical_zones_percentage': round(critical_zones_percentage, 2) if critical_zones_percentage is not None else None,
            'source': dem_data.get('source_label', 'GeoTIFF DEM'),
            'sample_points': dem_data.get('sample_points'),
            'pixel_size_x_m': round(pixel_size_x, 3) if pixel_size_x else None,
            'pixel_size_y_m': round(pixel_size_y, 3) if pixel_size_y else None,
            'elevation_profile': self._build_elevation_profile(elevation, pixel_size_x),
            'slope_distribution': self._build_slope_distribution(slope_values),
            'terrain_limits': terrain_limits,
            'crs': dem_data.get('crs'),
            'transform': dem_data.get('transform')
        }

        hydraulic_analysis = self._build_preliminary_hydraulic_analysis(
            slope_percentage=slope_percentage,
            elevation_diff=elevation_diff,
            area_hectares=source_area,
            assumptions=hydraulic_assumptions
        )

        if slope_percentage is None:
            recommendations = [{
                'priority': 'Informacion',
                'type': 'DEM',
                'message': 'Se calcularon elevaciones, pero no pendiente: falta georreferenciacion o tamano de pixel confiable.',
                'action': 'Usar un GeoTIFF con CRS y transformacion espacial, o configurar Google Elevation API para imagenes de dron.'
            }]
        elif slope_percentage > 20:
            recommendations = [{
                'priority': 'Medio',
                'type': 'Pendiente',
                'message': f'Pendiente media: {slope_degrees:.2f} grados. El informe recomienda separar zonas y controlar presion en terrenos con desnivel relevante.',
                'action': 'Validar sectores de riego, reguladores de presion y diferencia de carga por elevacion.'
            }]
        else:
            recommendations = [{
                'priority': 'Bajo',
                'type': 'Pendiente',
                'message': f'Pendiente media: {slope_degrees:.2f} grados. El terreno no muestra una restriccion topografica severa para el diseno preliminar.',
                'action': 'Continuar con calculo hidraulico usando caudal, diametro, longitud y presion disponible.'
            }]

        estimated_drip_length = self._estimate_drip_length(source_area)
        materials_analysis = self._build_materials_analysis(
            hydraulic_analysis=hydraulic_analysis,
            area_hectares=source_area,
            estimated_drip_length=estimated_drip_length
        )
        recommendations.extend([
            self._hydraulic_recommendation(hydraulic_analysis),
            self._materials_recommendation(materials_analysis)
        ])

        design_analysis = {
            'recommendations': recommendations,
            'estimated_area': source_area,
            'estimated_drip_length': estimated_drip_length,
            'complexity_level': self._classify_design_complexity(
                slope_percentage,
                source_area,
                hydraulic_analysis.get('hydraulic_risk')
            ),
            'estimated_cost_level': self._classify_cost_level(
                slope_percentage,
                source_area,
                hydraulic_analysis.get('hydraulic_risk')
            )
        }

        return {
            'file_name': filename,
            'file_size': os.path.getsize(file_path),
            'image_dimensions': {
                'width': int(source_width),
                'height': int(source_height),
                'pixels': int(source_width * source_height)
            },
            'terrain_analysis': terrain_analysis,
            'hydraulic_analysis': hydraulic_analysis,
            'materials_analysis': materials_analysis,
            'design_recommendations': design_analysis,
            'status': 'completed',
            'message': 'Analisis completado desde DEM GeoTIFF o Google Elevation API'
        }

    def _read_dem(self, file_path):
        try:
            import rasterio
            import numpy as np

            with rasterio.open(file_path) as src:
                transform = src.transform
                has_spatial_reference = bool(src.crs)
                dem_data = {
                    'array': None,
                    'width': src.width,
                    'height': src.height,
                    'source_width': src.width,
                    'source_height': src.height,
                    'band_count': src.count,
                    'crs': str(src.crs) if src.crs else None,
                    'transform': tuple(transform)[:6] if has_spatial_reference else None,
                    'pixel_size_x': abs(transform.a) if has_spatial_reference and transform else None,
                    'pixel_size_y': abs(transform.e) if has_spatial_reference and transform else None,
                    'bounds': tuple(src.bounds) if has_spatial_reference and src.bounds else None,
                    'source_label': 'GeoTIFF georreferenciado + Google Elevation API'
                }

                if src.count == 1:
                    band = src.read(1, masked=True).astype('float64')
                    dem_data['array'] = band.filled(np.nan)
                    dem_data['source_label'] = 'GeoTIFF DEM de una banda'
                elif not has_spatial_reference:
                    raise ValueError(
                        "La imagen tiene varias bandas y no trae georreferenciacion. "
                        "Para una fotografia de dron usa GeoTIFF/ortomosaico con CRS y bounds."
                    )

                return dem_data
        except ImportError:
            pass

        try:
            from PIL import Image
            import numpy as np

            img = Image.open(file_path)
            if len(img.getbands()) != 1:
                raise ValueError(
                    "La imagen tiene varias bandas pero no pude leer georreferenciacion. "
                    "Exportala como GeoTIFF con CRS para poder consultar Google Elevation API."
                )
            return {
                'array': np.array(img, dtype='float64'),
                'width': img.size[0],
                'height': img.size[1],
                'source_width': img.size[0],
                'source_height': img.size[1],
                'band_count': 1,
                'crs': None,
                'transform': None,
                'pixel_size_x': None,
                'pixel_size_y': None,
                'bounds': None,
                'source_label': 'Imagen de una banda sin georreferenciacion'
            }
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                "No pude leer el archivo como GeoTIFF. Para la tesis sube un DEM de una banda "
                "o una ortofoto GeoTIFF georreferenciada para consultar Google Elevation API."
            ) from e

    def _build_elevation_profile(self, elevation, pixel_size_x):
        import numpy as np

        if elevation.size == 0:
            return []

        center_row = elevation[elevation.shape[0] // 2, :]
        valid_indexes = np.where(np.isfinite(center_row))[0]
        if valid_indexes.size == 0:
            return []

        max_points = 18
        selected = valid_indexes
        if valid_indexes.size > max_points:
            selected = valid_indexes[np.linspace(0, valid_indexes.size - 1, max_points).astype(int)]

        spacing = pixel_size_x if pixel_size_x else 1
        return [
            {
                'distance_m': round(float(index * spacing), 2),
                'elevation_m': round(float(center_row[index]), 2)
            }
            for index in selected
        ]

    def _build_slope_distribution(self, slope_values):
        import numpy as np

        if slope_values is None or slope_values.size == 0:
            return []

        bins = [
            ('0-2', 0, 2),
            ('2-5', 2, 5),
            ('5-10', 5, 10),
            ('10-15', 10, 15),
            ('15-25', 15, 25),
            ('>25', 25, np.inf)
        ]
        total = slope_values.size
        distribution = []
        for label, lower, upper in bins:
            if np.isinf(upper):
                mask = slope_values >= lower
            else:
                mask = (slope_values >= lower) & (slope_values < upper)
            count = int(np.sum(mask))
            distribution.append({
                'range': label,
                'count': count,
                'percentage': round(float((count / total) * 100), 2)
            })
        return distribution

    def _build_preliminary_hydraulic_analysis(self, slope_percentage, elevation_diff, area_hectares, assumptions=None):
        assumptions = assumptions or self._parse_hydraulic_assumptions({})
        area = area_hectares if area_hectares and area_hectares > 0 else 1.0
        design_sector_ha = min(area, assumptions['max_sector_area_ha'])
        flow_per_hectare_l_min = assumptions['flow_per_hectare_l_min']
        available_flow_l_min = max(
            assumptions['minimum_flow_l_min'],
            design_sector_ha * flow_per_hectare_l_min
        )
        flow_m3_s = available_flow_l_min / 60000
        pipe_length_m = max(
            assumptions['minimum_pipe_length_m'],
            (design_sector_ha * 10000) ** 0.5 * assumptions['pipe_length_factor']
        )
        pipe_diameter_m = (
            assumptions['pipe_diameter_large_m']
            if design_sector_ha >= 1 else
            assumptions['pipe_diameter_small_m']
        )

        friction_loss_bar = self.hydraulic.calculate_hazen_williams_loss(
            length=pipe_length_m,
            flow_rate=flow_m3_s,
            diameter=pipe_diameter_m,
            c_coefficient=assumptions['hazen_williams_c']
        )
        elevation_pressure_kpa = elevation_diff * 9.81
        friction_loss_kpa = friction_loss_bar * 100
        total_pressure_loss_kpa = friction_loss_kpa + elevation_pressure_kpa
        emitter_operating_pressure_kpa = assumptions['emitter_operating_pressure_kpa']
        safety_factor = assumptions['pressure_safety_factor']
        pressure_before_safety_kpa = emitter_operating_pressure_kpa + total_pressure_loss_kpa
        initial_pressure_kpa = pressure_before_safety_kpa * safety_factor
        final_pressure_kpa = initial_pressure_kpa - total_pressure_loss_kpa
        required_total_pressure_kpa = initial_pressure_kpa
        required_total_head_m = required_total_pressure_kpa / 9.81
        required_pump_power_hp = self._required_pump_power_hp(
            flow_l_min=available_flow_l_min,
            total_head_m=required_total_head_m,
            efficiency=assumptions['pump_efficiency']
        )
        pump_catalog = self._evaluate_pump_catalog(
            required_total_head_m=required_total_head_m,
            required_total_pressure_kpa=required_total_pressure_kpa,
            required_flow_l_min=available_flow_l_min
        )
        recommended_pump = next(
            (pump for pump in pump_catalog if pump['meets_requirements']),
            pump_catalog[-1] if pump_catalog else None
        )

        if final_pressure_kpa < 70 or total_pressure_loss_kpa > 80 or (slope_percentage or 0) > 20:
            risk = 'Alto'
        elif final_pressure_kpa < 100 or total_pressure_loss_kpa > 45 or (slope_percentage or 0) > 8:
            risk = 'Medio'
        else:
            risk = 'Bajo'

        return {
            'source_pressure': round(initial_pressure_kpa, 2),
            'emitter_operating_pressure': round(emitter_operating_pressure_kpa, 2),
            'pressure_safety_factor': safety_factor,
            'pressure_before_safety': round(pressure_before_safety_kpa, 2),
            'available_flow': round(available_flow_l_min, 2),
            'flow_per_hectare': round(flow_per_hectare_l_min, 2),
            'pressure_loss': round(total_pressure_loss_kpa, 2),
            'final_pressure': round(final_pressure_kpa, 2),
            'required_total_pressure': round(required_total_pressure_kpa, 2),
            'required_total_head': round(required_total_head_m, 2),
            'required_pump_power': round(required_pump_power_hp, 2),
            'hydraulic_risk': risk,
            'pipe_diameter': round(pipe_diameter_m * 1000, 0),
            'pipe_length': round(pipe_length_m, 2),
            'design_sector_area': round(design_sector_ha, 2),
            'elevation_pressure_change': round(elevation_pressure_kpa, 2),
            'friction_loss': round(friction_loss_kpa, 2),
            'pump_catalog': pump_catalog,
            'recommended_pump': recommended_pump,
            'required_pump_spec': {
                'minimum_power_hp': round(required_pump_power_hp, 2),
                'required_flow_l_min': round(available_flow_l_min, 2),
                'required_head_m': round(required_total_head_m, 2),
                'required_pressure_kpa': round(required_total_pressure_kpa, 2),
                'terrain_context': (
                    f"Sector estimado de {round(design_sector_ha, 2)} ha, "
                    f"desnivel {round(elevation_diff, 2)} m, "
                    f"perdida total {round(total_pressure_loss_kpa, 2)} kPa."
                )
            },
            'assumptions': {
                key: round(value, 4)
                for key, value in assumptions.items()
            },
            'calculation_basis': 'Presion minima requerida en fuente = presion operacion goteros + desnivel DEM/Google + friccion Hazen-Williams, con margen configurable; bomba evaluada con caudal maximo y altura total de catalogo.'
        }

    def _required_pump_power_hp(self, flow_l_min, total_head_m, efficiency=0.60):
        flow_m3_s = flow_l_min / 60000
        watts = 1000 * 9.81 * flow_m3_s * total_head_m / efficiency
        return watts / 745.7

    def _evaluate_pump_catalog(self, required_total_head_m, required_total_pressure_kpa, required_flow_l_min):
        evaluated = []
        for pump in list_pumps():
            meets_flow = pump['max_flow_l_min'] >= required_flow_l_min
            meets_head = (
                pump['max_head_m'] >= required_total_head_m and
                pump['max_pressure_kpa'] >= required_total_pressure_kpa
            )
            meets_requirements = meets_flow and meets_head
            item = dict(pump)
            item.update({
                'meets_flow': meets_flow,
                'meets_head': meets_head,
                'meets_requirements': meets_requirements,
                'flow_margin_l_min': round(pump['max_flow_l_min'] - required_flow_l_min, 2),
                'head_margin_m': round(pump['max_head_m'] - required_total_head_m, 2),
                'selection_note': (
                    'Cumple caudal y altura/presion requeridos para el terreno analizado.'
                    if meets_requirements else
                    'No cumple completamente el caudal y/o la altura requerida; revisar alternativa de mayor capacidad.'
                )
            })
            evaluated.append(item)
        return sorted(
            evaluated,
            key=lambda pump: (
                not pump['meets_requirements'],
                not pump['meets_head'],
                not pump['meets_flow'],
                pump['engine_power_hp'],
                pump['max_flow_l_min']
            )
        )

    def _build_materials_analysis(self, hydraulic_analysis, area_hectares, estimated_drip_length):
        pipe_diameter_mm = hydraulic_analysis.get('pipe_diameter') or 32
        pressure_kpa = hydraulic_analysis.get('source_pressure') or 0
        flow_l_min = hydraulic_analysis.get('available_flow') or 0
        sector_area = hydraulic_analysis.get('design_sector_area') or (area_hectares or 1)
        drip_length_m = estimated_drip_length or self._estimate_drip_length(sector_area) or 0
        lateral_spacing_m = 2.0
        emitter_spacing_m = 0.3
        emitter_flow_l_h = 2.0
        estimated_emitters = int(round(drip_length_m / emitter_spacing_m)) if drip_length_m else None

        if pressure_kpa > 300:
            pipe_pressure_class = 'PN 10'
        elif pressure_kpa > 180:
            pipe_pressure_class = 'PN 6'
        else:
            pipe_pressure_class = 'PN 4'

        main_pipe_type = 'HDPE'
        lateral_pipe_type = 'Cinta o tuberia de goteo PE'
        valve_size = f"{int(pipe_diameter_mm)} mm"
        filter_mesh = '120 mesh' if flow_l_min <= 100 else '120-150 mesh'

        items = [
            {
                'category': 'Tuberia principal',
                'component': f'{main_pipe_type} {int(pipe_diameter_mm)} mm {pipe_pressure_class}',
                'quantity': f"{hydraulic_analysis.get('pipe_length', 0)} m",
                'purpose': 'Conducir el caudal desde la fuente hasta el sector de riego.'
            },
            {
                'category': 'Laterales de goteo',
                'component': f'{lateral_pipe_type} 16 mm',
                'quantity': f"{round(drip_length_m, 0)} m" if drip_length_m else 'Definir con plano de cultivo',
                'purpose': 'Distribuir agua en las lineas de cultivo.'
            },
            {
                'category': 'Goteros',
                'component': f'Goteros {emitter_flow_l_h} L/h cada {emitter_spacing_m} m',
                'quantity': f"{estimated_emitters} unidades aprox." if estimated_emitters else 'Definir con separacion real',
                'purpose': 'Aplicar el agua de forma localizada.'
            },
            {
                'category': 'Llave de paso',
                'component': f'Valvula bola PVC/HDPE {valve_size}',
                'quantity': '1 por sector + 1 general',
                'purpose': 'Aislar sectores para operacion y mantenimiento.'
            },
            {
                'category': 'Filtro',
                'component': f'Filtro de malla o disco {filter_mesh}',
                'quantity': '1 unidad en cabezal',
                'purpose': 'Proteger goteros frente a obstrucciones.'
            },
            {
                'category': 'Regulacion',
                'component': 'Regulador de presion para goteo',
                'quantity': '1 por sector',
                'purpose': 'Mantener presion estable en las lineas laterales.'
            },
            {
                'category': 'Control',
                'component': 'Manometro 0-6 bar',
                'quantity': '2 unidades',
                'purpose': 'Verificar presion de entrada y salida del sector.'
            },
            {
                'category': 'Conexiones',
                'component': 'Tee, codos, reducciones, abrazaderas y terminales',
                'quantity': 'Segun trazado final',
                'purpose': 'Unir tuberias y cerrar laterales.'
            }
        ]

        return {
            'main_pipe_type': main_pipe_type,
            'main_pipe_diameter_mm': int(pipe_diameter_mm),
            'pipe_pressure_class': pipe_pressure_class,
            'lateral_pipe_type': lateral_pipe_type,
            'lateral_diameter_mm': 16,
            'valve_type': 'Valvula bola PVC/HDPE',
            'valve_diameter_mm': int(pipe_diameter_mm),
            'filter_type': f'Filtro de malla o disco {filter_mesh}',
            'emitter_type': f'Gotero {emitter_flow_l_h} L/h',
            'emitter_spacing_m': emitter_spacing_m,
            'lateral_spacing_m': lateral_spacing_m,
            'estimated_emitters': estimated_emitters,
            'estimated_lateral_length_m': round(drip_length_m, 0) if drip_length_m else None,
            'items': items,
            'catalog_options': {
                'main_pipe': list_materials('main_pipe'),
                'laterals': list_materials('laterals'),
                'valves': list_materials('valves'),
                'emitters': list_materials('emitters')
            },
            'message': 'Listado preliminar de materiales para riego por goteo; ajustar cantidades con plano final, cultivo y marco de plantacion.'
        }

    def _hydraulic_recommendation(self, hydraulic_analysis):
        risk = hydraulic_analysis.get('hydraulic_risk')
        priority = 'Alto' if risk == 'Alto' else 'Medio' if risk == 'Medio' else 'Bajo'
        return {
            'priority': priority,
            'type': 'Hidraulica',
            'message': (
                f"Riesgo hidraulico {risk}. Perdida estimada "
                f"{hydraulic_analysis.get('pressure_loss')} kPa considerando desnivel y friccion."
            ),
            'action': 'Validar caudal, diametro y longitud real; recalcular Hazen-Williams antes de comprar componentes.'
        }

    def _materials_recommendation(self, materials_analysis):
        return {
            'priority': 'Medio',
            'type': 'Materiales',
            'message': (
                f"Tuberia principal {materials_analysis['main_pipe_type']} "
                f"{materials_analysis['main_pipe_diameter_mm']} mm "
                f"{materials_analysis['pipe_pressure_class']} y laterales de goteo "
                f"{materials_analysis['lateral_diameter_mm']} mm."
            ),
            'action': 'Revisar listado de materiales y ajustar cantidades con el plano definitivo de riego.'
        }

    def _build_terrain_limits(self, dem_data, width, height, pixel_size_x, pixel_size_y, area_hectares):
        limits = {
            'width_px': int(width),
            'height_px': int(height),
            'pixel_size_x_m': round(pixel_size_x, 3) if pixel_size_x else None,
            'pixel_size_y_m': round(pixel_size_y, 3) if pixel_size_y else None,
            'area_hectares': area_hectares,
            'projected_bounds': dem_data.get('bounds'),
            'geographic_bounds': None,
            'center': None
        }

        try:
            west, south, east, north = self._bounds_wgs84(dem_data)
            limits['geographic_bounds'] = {
                'west': round(float(west), 6),
                'south': round(float(south), 6),
                'east': round(float(east), 6),
                'north': round(float(north), 6)
            }
            limits['center'] = {
                'latitude': round(float((north + south) / 2), 6),
                'longitude': round(float((east + west) / 2), 6)
            }
        except ValueError:
            pass

        return limits

    def _estimate_drip_length(self, area_hectares, row_spacing_m=2.0):
        if not area_hectares:
            return None
        return round((area_hectares * 10000) / row_spacing_m, 0)

    def _classify_design_complexity(self, slope_percentage, area_hectares, hydraulic_risk):
        slope = slope_percentage or 0
        area = area_hectares or 0
        if hydraulic_risk == 'Alto' or slope > 20 or area > 20:
            return 'Alta'
        if hydraulic_risk == 'Medio' or slope > 8 or area > 5:
            return 'Media'
        return 'Baja'

    def _classify_cost_level(self, slope_percentage, area_hectares, hydraulic_risk):
        slope = slope_percentage or 0
        area = area_hectares or 0
        if hydraulic_risk == 'Alto' or area > 20 or slope > 20:
            return 'Alto'
        if hydraulic_risk == 'Medio' or area > 5 or slope > 8:
            return 'Medio'
        return 'Bajo'

    def _build_dem_from_google(self, image_data, grid_size=15):
        import numpy as np

        if self.elevation_service.__class__.__name__ == 'MockElevationService':
            raise ValueError(
                "Para analizar una fotografia/ortofoto GeoTIFF se requiere GOOGLE_ELEVATION_API_KEY. "
                "Sin esa clave el sistema no debe generar elevaciones simuladas."
            )

        west, south, east, north = self._bounds_wgs84(image_data)
        if west == east or south == north:
            raise ValueError("El GeoTIFF no tiene una extension geografica valida.")

        lons = np.linspace(west, east, grid_size)
        lats = np.linspace(north, south, grid_size)
        points = [(float(lat), float(lon)) for lat in lats for lon in lons]
        elevations = self.elevation_service.get_elevations_batch(points)
        elevation_grid = np.array(
            [np.nan if value is None else float(value) for value in elevations],
            dtype='float64'
        ).reshape((grid_size, grid_size))

        if not np.isfinite(elevation_grid).any():
            raise ValueError("Google Elevation API no devolvio elevaciones validas para esta imagen.")

        mid_lat = float((north + south) / 2)
        mid_lon = float((west + east) / 2)
        pixel_size_x_m = self.geospatial._haversine_distance(mid_lat, west, mid_lat, east) / (grid_size - 1)
        pixel_size_y_m = self.geospatial._haversine_distance(north, mid_lon, south, mid_lon) / (grid_size - 1)

        result = dict(image_data)
        result.update({
            'array': elevation_grid,
            'width': grid_size,
            'height': grid_size,
            'pixel_size_x_m': pixel_size_x_m,
            'pixel_size_y_m': pixel_size_y_m,
            'bounds': (west, south, east, north),
            'crs': 'EPSG:4326',
            'sample_points': len(points),
            'source_label': 'Google Elevation API sobre grilla GeoTIFF'
        })
        return result

    def _bounds_wgs84(self, image_data):
        bounds = image_data.get('bounds')
        crs = image_data.get('crs')
        if not bounds or not crs:
            raise ValueError("El GeoTIFF necesita CRS y bounds para obtener latitud/longitud.")

        if '4326' in crs:
            return bounds

        try:
            from rasterio.warp import transform_bounds
            return transform_bounds(crs, 'EPSG:4326', *bounds, densify_pts=21)
        except Exception as e:
            raise ValueError("No pude convertir los bounds del GeoTIFF a WGS84.") from e

    def _pixel_size_meters(self, dem_data):
        if dem_data.get('pixel_size_x_m') and dem_data.get('pixel_size_y_m'):
            return dem_data['pixel_size_x_m'], dem_data['pixel_size_y_m']

        pixel_size_x = dem_data.get('pixel_size_x')
        pixel_size_y = dem_data.get('pixel_size_y')
        crs = dem_data.get('crs') or ''
        bounds = dem_data.get('bounds')

        if not pixel_size_x or not pixel_size_y:
            return None, None

        if '4326' in crs and bounds:
            import math
            west, south, east, north = bounds
            lat = (south + north) / 2
            meters_per_degree_lat = 111_320
            meters_per_degree_lon = 111_320 * math.cos(math.radians(lat))
            return pixel_size_x * meters_per_degree_lon, pixel_size_y * meters_per_degree_lat

        return pixel_size_x, pixel_size_y

    def _area_hectares(self, width, height, pixel_size_x, pixel_size_y):
        if not pixel_size_x or not pixel_size_y:
            return None
        return round((width * pixel_size_x * height * pixel_size_y) / 10_000, 2)


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

    # Catalogs
    api.add_resource(PumpCatalogEndpoint, '/api/v1/catalog/pumps', '/api/v1/catalog/pumps/<int:pump_id>')
    api.add_resource(MaterialCatalogEndpoint, '/api/v1/catalog/materials', '/api/v1/catalog/materials/<int:material_id>')
    
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
                'pump_catalog': {
                    'url': '/api/v1/catalog/pumps',
                    'method': 'GET, POST',
                    'description': 'List or add pump catalog entries'
                },
                'material_catalog': {
                    'url': '/api/v1/catalog/materials',
                    'method': 'GET, POST',
                    'description': 'List or add irrigation material catalog entries'
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
                    'message': 'Los archivos de la interfaz no estÃ¡n disponibles. Compruebe la instalaciÃ³n.',
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

            image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
            if filename.lower().endswith(image_extensions):
                return send_file(file_path)
            
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

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Serve uploaded catalog images."""
        uploads_path = os.path.join(api_root, 'uploads')
        return send_from_directory(uploads_path, filename)
