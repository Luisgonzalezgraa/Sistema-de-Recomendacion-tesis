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
            
            # Procesar la imagen y extraer parametros
            analysis_results = self._analyze_image(temp_path, file.filename)
            
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
    
    def _analyze_image(self, file_path, filename):
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
        critical_zones_percentage = None

        if pixel_size_x and pixel_size_y:
            elevation_for_gradient = elevation.copy()
            if not np.isfinite(elevation_for_gradient).all():
                elevation_for_gradient[~np.isfinite(elevation_for_gradient)] = median_elev
            gradient_y, gradient_x = np.gradient(elevation_for_gradient, pixel_size_y, pixel_size_x)
            slope = np.sqrt(gradient_x ** 2 + gradient_y ** 2) * 100
            slope_values = slope[np.isfinite(slope)]
            if slope_values.size:
                slope_percentage = float(np.mean(slope_values))
                p75 = float(np.percentile(slope_values, 75))
                critical_zones_percentage = float(np.mean(slope_values >= p75) * 100)

        terrain_analysis = {
            'slope_percentage': round(slope_percentage, 2) if slope_percentage is not None else None,
            'max_elevation': round(max_elev, 2),
            'min_elevation': round(min_elev, 2),
            'median_elevation': round(median_elev, 2),
            'elevation_difference': round(elevation_diff, 2),
            'critical_zones_percentage': round(critical_zones_percentage, 2) if critical_zones_percentage is not None else None,
            'source': dem_data.get('source_label', 'GeoTIFF DEM'),
            'sample_points': dem_data.get('sample_points'),
            'pixel_size_x_m': round(pixel_size_x, 3) if pixel_size_x else None,
            'pixel_size_y_m': round(pixel_size_y, 3) if pixel_size_y else None,
            'crs': dem_data.get('crs'),
            'transform': dem_data.get('transform')
        }

        hydraulic_analysis = self._build_preliminary_hydraulic_analysis(
            slope_percentage=slope_percentage,
            elevation_diff=elevation_diff,
            area_hectares=source_area
        )
        water_analysis = self._build_reference_water_analysis()

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
                'message': f'Pendiente media: {slope_percentage:.2f}%. El informe recomienda separar zonas y controlar presion en terrenos con desnivel relevante.',
                'action': 'Validar sectores de riego, reguladores de presion y diferencia de carga por elevacion.'
            }]
        else:
            recommendations = [{
                'priority': 'Bajo',
                'type': 'Pendiente',
                'message': f'Pendiente media: {slope_percentage:.2f}%. El terreno no muestra una restriccion topografica severa para el diseno preliminar.',
                'action': 'Continuar con calculo hidraulico usando caudal, diametro, longitud y presion disponible.'
            }]

        recommendations.extend([
            self._hydraulic_recommendation(hydraulic_analysis),
            self._water_material_recommendation(water_analysis)
        ])

        estimated_drip_length = self._estimate_drip_length(source_area)
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
            'water_analysis': water_analysis,
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

    def _build_preliminary_hydraulic_analysis(self, slope_percentage, elevation_diff, area_hectares):
        initial_pressure_kpa = 150.0
        area = area_hectares if area_hectares and area_hectares > 0 else 1.0
        design_sector_ha = min(area, 3.0)
        available_flow_l_min = max(20.0, design_sector_ha * 35.0)
        flow_m3_s = available_flow_l_min / 60000
        pipe_length_m = max(80.0, (design_sector_ha * 10000) ** 0.5 * 1.25)
        pipe_diameter_m = 0.04 if design_sector_ha >= 1 else 0.032

        friction_loss_bar = self.hydraulic.calculate_hazen_williams_loss(
            length=pipe_length_m,
            flow_rate=flow_m3_s,
            diameter=pipe_diameter_m,
            c_coefficient=150
        )
        elevation_pressure_kpa = elevation_diff * 9.81
        friction_loss_kpa = friction_loss_bar * 100
        total_pressure_loss_kpa = friction_loss_kpa + elevation_pressure_kpa
        final_pressure_kpa = initial_pressure_kpa - total_pressure_loss_kpa

        if final_pressure_kpa < 70 or total_pressure_loss_kpa > 80 or (slope_percentage or 0) > 20:
            risk = 'Alto'
        elif final_pressure_kpa < 100 or total_pressure_loss_kpa > 45 or (slope_percentage or 0) > 8:
            risk = 'Medio'
        else:
            risk = 'Bajo'

        return {
            'source_pressure': round(initial_pressure_kpa, 2),
            'available_flow': round(available_flow_l_min, 2),
            'pressure_loss': round(total_pressure_loss_kpa, 2),
            'final_pressure': round(final_pressure_kpa, 2),
            'hydraulic_risk': risk,
            'pipe_diameter': round(pipe_diameter_m * 1000, 0),
            'pipe_length': round(pipe_length_m, 2),
            'design_sector_area': round(design_sector_ha, 2),
            'elevation_pressure_change': round(elevation_pressure_kpa, 2),
            'friction_loss': round(friction_loss_kpa, 2),
            'calculation_basis': 'Preliminar por sector: desnivel DEM/Google + Hazen-Williams con supuestos de diseno.'
        }

    def _build_reference_water_analysis(self):
        return {
            'ph': 7.2,
            'salinity_ppm': 450,
            'hardness_mg_l': 180,
            'material_compatibility': {
                'hdpe': 'Excelente',
                'pvc': 'Buena',
                'acero_galvanizado': 'Media',
                'goteros': 'Buena'
            },
            'recommended_material': 'HDPE 16-20 mm con filtrado de malla/disco',
            'water_quality': 'Buena referencial',
            'message': 'Perfil referencial usado cuando no hay analisis de laboratorio; debe validarse con pH, salinidad y dureza reales.'
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
            'action': 'Validar caudal, diametro y longitud real; recalcular Hazen-Williams antes de comprar materiales.'
        }

    def _water_material_recommendation(self, water_analysis):
        return {
            'priority': 'Medio',
            'type': 'Agua y materiales',
            'message': (
                f"Perfil de agua referencial: pH {water_analysis['ph']}, "
                f"salinidad {water_analysis['salinity_ppm']} ppm, dureza {water_analysis['hardness_mg_l']} mg/L."
            ),
            'action': f"Material preliminar: {water_analysis['recommended_material']}. Confirmar con analisis de agua real."
        }

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
