"""
Geospatial Analysis Module
Handles image processing, DEM generation, and slope calculations
"""
import numpy as np
import cv2
from typing import Tuple, List, Optional
import logging
from app.models.data_models import GeoPoint, TopographicAnalysis, DigitalElevationModel
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class GeospatialAnalyzer:
    """
    Handles geospatial analysis including image processing and elevation calculations
    """
    
    def __init__(self):
        """Initialize the geospatial analyzer"""
        self.logger = logger
    
    def process_aerial_image(self, image_path: str) -> np.ndarray:
        """
        Process aerial image for analysis
        
        Args:
            image_path: Path to the aerial image file
            
        Returns:
            Processed image as numpy array
            
        Raises:
            ValueError: If image cannot be read
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image from {image_path}")
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            self.logger.info(f"Successfully processed image: {image_path}")
            return blurred
            
        except Exception as e:
            self.logger.error(f"Error processing aerial image: {str(e)}")
            raise
    
    def generate_dem_from_elevation_data(
        self, 
        elevation_points: List[Tuple[float, float, float]]
    ) -> np.ndarray:
        """
        Generate Digital Elevation Model from elevation points
        
        Args:
            elevation_points: List of (latitude, longitude, elevation) tuples
            
        Returns:
            2D numpy array representing the DEM
        """
        try:
            if not elevation_points or len(elevation_points) < 3:
                raise ValueError("At least 3 elevation points are required")
            
            # Convert to numpy array
            points = np.array(elevation_points)
            
            # Find grid bounds
            lat_min, lat_max = points[:, 0].min(), points[:, 0].max()
            lon_min, lon_max = points[:, 1].min(), points[:, 1].max()
            elevations = points[:, 2]
            
            # Create interpolated grid (simplified approach)
            grid_resolution = 100  # points per degree
            lat_grid = np.linspace(lat_min, lat_max, grid_resolution)
            lon_grid = np.linspace(lon_min, lon_max, grid_resolution)
            
            # Simple nearest-neighbor interpolation for now
            dem = np.zeros((grid_resolution, grid_resolution))
            for i, lat in enumerate(lat_grid):
                for j, lon in enumerate(lon_grid):
                    # Find nearest elevation point
                    distances = np.sqrt(
                        (points[:, 0] - lat)**2 + (points[:, 1] - lon)**2
                    )
                    nearest_idx = np.argmin(distances)
                    dem[i, j] = elevations[nearest_idx]
            
            self.logger.info(f"Generated DEM with resolution {grid_resolution}x{grid_resolution}")
            return dem
            
        except Exception as e:
            self.logger.error(f"Error generating DEM: {str(e)}")
            raise
    
    def calculate_slope(
        self, 
        point_start: GeoPoint, 
        point_end: GeoPoint
    ) -> TopographicAnalysis:
        """
        Calculate slope between two geographic points
        
        Args:
            point_start: Starting geographic point
            point_end: Ending geographic point
            
        Returns:
            TopographicAnalysis object with slope calculations
            
        Raises:
            ValueError: If elevation data is missing
        """
        try:
            if point_start.elevation is None or point_end.elevation is None:
                raise ValueError("Elevation data is required for slope calculation")
            
            # Calculate elevation difference
            elevation_diff = point_end.elevation - point_start.elevation
            
            # Calculate horizontal distance (approximate using Haversine formula)
            horizontal_distance = self._haversine_distance(
                point_start.latitude, point_start.longitude,
                point_end.latitude, point_end.longitude
            )
            
            if horizontal_distance == 0:
                raise ValueError("Start and end points cannot be the same")
            
            # Calculate slope
            slope_radians = np.arctan(elevation_diff / horizontal_distance)
            slope_degrees = np.degrees(slope_radians)
            slope_percentage = (elevation_diff / horizontal_distance) * 100
            
            result = TopographicAnalysis(
                point_start=point_start,
                point_end=point_end,
                elevation_difference=elevation_diff,
                slope_percentage=slope_percentage,
                slope_radians=float(slope_radians),
                slope_degrees=float(slope_degrees),
                distance=horizontal_distance
            )
            
            self.logger.info(
                f"Calculated slope: {slope_percentage:.2f}% "
                f"({slope_degrees:.2f}°) between points"
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating slope: {str(e)}")
            raise
    
    def calculate_slope_from_dem(
        self,
        dem: np.ndarray,
        x1: int, y1: int,
        x2: int, y2: int,
        pixel_size: float = 1.0
    ) -> float:
        """
        Calculate slope directly from DEM cells
        
        Args:
            dem: Digital Elevation Model array
            x1, y1: Starting cell coordinates
            x2, y2: Ending cell coordinates
            pixel_size: Physical size of each pixel (meters)
            
        Returns:
            Slope percentage between the cells
        """
        try:
            if not (0 <= x1 < dem.shape[0] and 0 <= y1 < dem.shape[1]):
                raise ValueError(f"Invalid start coordinates ({x1}, {y1})")
            if not (0 <= x2 < dem.shape[0] and 0 <= y2 < dem.shape[1]):
                raise ValueError(f"Invalid end coordinates ({x2}, {y2})")
            
            elevation_diff = dem[x2, y2] - dem[x1, y1]
            
            # Calculate horizontal distance in pixels
            pixel_distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            horizontal_distance = pixel_distance * pixel_size
            
            if horizontal_distance == 0:
                return 0.0
            
            slope_percentage = (elevation_diff / horizontal_distance) * 100
            return float(slope_percentage)
            
        except Exception as e:
            self.logger.error(f"Error calculating slope from DEM: {str(e)}")
            raise
    
    def extract_slope_map(self, dem: np.ndarray, pixel_size: float = 1.0) -> np.ndarray:
        """
        Extract slope map from DEM using gradient calculation
        
        Args:
            dem: Digital Elevation Model
            pixel_size: Physical size of each pixel
            
        Returns:
            Slope map as percentage
        """
        try:
            # Calculate gradients
            gx, gy = np.gradient(dem, pixel_size)
            
            # Calculate slope as percentage
            slope_map = np.sqrt(gx**2 + gy**2) * 100
            
            self.logger.info(f"Slope map extracted. Range: {slope_map.min():.2f}% - {slope_map.max():.2f}%")
            return slope_map
            
        except Exception as e:
            self.logger.error(f"Error extracting slope map: {str(e)}")
            raise
    
    def identify_critical_zones(
        self,
        slope_map: np.ndarray,
        slope_threshold: float = 15.0
    ) -> List[Tuple[int, int, float]]:
        """
        Identify critical zones with high slopes
        
        Args:
            slope_map: Slope percentage map
            slope_threshold: Threshold for identifying critical zones
            
        Returns:
            List of (x, y, slope) tuples for critical zones
        """
        try:
            critical_indices = np.where(slope_map > slope_threshold)
            critical_zones = [
                (x, y, float(slope_map[x, y]))
                for x, y in zip(critical_indices[0], critical_indices[1])
            ]
            
            self.logger.info(
                f"Identified {len(critical_zones)} critical zones "
                f"with slope > {slope_threshold}%"
            )
            return critical_zones
            
        except Exception as e:
            self.logger.error(f"Error identifying critical zones: {str(e)}")
            raise
    
    def create_dem_metadata(
        self,
        source: str,
        bounding_box: dict,
        resolution: float
    ) -> DigitalElevationModel:
        """
        Create DEM metadata object
        
        Args:
            source: Source of elevation data
            bounding_box: Bounding box coordinates
            resolution: Resolution in meters per pixel
            
        Returns:
            DigitalElevationModel object
        """
        return DigitalElevationModel(
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow().isoformat(),
            source=source,
            bounding_box=bounding_box,
            resolution=resolution
        )
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula
        
        Args:
            lat1, lon1: Starting point coordinates (degrees)
            lat2, lon2: Ending point coordinates (degrees)
            
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
