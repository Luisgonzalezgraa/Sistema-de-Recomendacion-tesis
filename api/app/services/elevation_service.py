"""
External API Services
Handles integration with external APIs like Google Elevation API
"""
import requests
import logging
from typing import List, Tuple, Optional, Dict, Any
from app.models.data_models import GeoPoint

logger = logging.getLogger(__name__)


class GoogleElevationService:
    """Service for fetching elevation data from Google Elevation API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Google Elevation Service
        
        Args:
            api_key: Google Maps API key
        """
        self.api_key = api_key
        self.base_url = 'https://maps.googleapis.com/maps/api/elevation/json'
        self.logger = logger
        self.request_timeout = 10  # seconds
    
    def get_elevation(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[float]:
        """
        Get elevation for a single point
        
        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude
            
        Returns:
            Elevation in meters, or None if request fails
        """
        try:
            params = {
                'locations': f'{latitude},{longitude}',
                'key': self.api_key
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and len(data['results']) > 0:
                elevation = data['results'][0]['elevation']
                self.logger.debug(f"Retrieved elevation {elevation}m for ({latitude}, {longitude})")
                return elevation
            else:
                self.logger.warning(
                    f"Google API returned status: {data['status']} for ({latitude}, {longitude})"
                )
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error fetching elevation: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching elevation: {str(e)}")
            return None
    
    def get_elevations_batch(
        self,
        points: List[Tuple[float, float]]
    ) -> List[Optional[float]]:
        """
        Get elevation for multiple points (batch request)
        
        Args:
            points: List of (latitude, longitude) tuples
            
        Returns:
            List of elevations in meters (None for failed requests)
        """
        try:
            if not points:
                return []
            
            if len(points) > 512:
                self.logger.warning("Batch size exceeds 512 points; splitting request")
                results = []
                for i in range(0, len(points), 512):
                    batch = points[i:i+512]
                    results.extend(self.get_elevations_batch(batch))
                return results
            
            # Format locations string
            locations = '|'.join(f'{lat},{lon}' for lat, lon in points)
            
            params = {
                'locations': locations,
                'key': self.api_key
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                elevations = [result['elevation'] for result in data['results']]
                self.logger.debug(f"Retrieved {len(elevations)} elevation points")
                return elevations
            else:
                self.logger.warning(f"Google API returned status: {data['status']}")
                return [None] * len(points)
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error in batch elevation fetch: {str(e)}")
            return [None] * len(points)
        except Exception as e:
            self.logger.error(f"Error in batch elevation fetch: {str(e)}")
            return [None] * len(points)
    
    def get_geo_points_with_elevation(
        self,
        geo_points: List[GeoPoint]
    ) -> List[GeoPoint]:
        """
        Fill in missing elevation data for geographic points
        
        Args:
            geo_points: List of GeoPoint objects (elevation may be None)
            
        Returns:
            List of GeoPoint objects with elevation data filled in
        """
        try:
            # Identify points needing elevation data
            points_needing_elevation = [
                i for i, point in enumerate(geo_points)
                if point.elevation is None
            ]
            
            if not points_needing_elevation:
                self.logger.debug("All points already have elevation data")
                return geo_points
            
            # Extract coordinates for API call
            coordinates = [
                (geo_points[i].latitude, geo_points[i].longitude)
                for i in points_needing_elevation
            ]
            
            # Fetch elevations
            elevations = self.get_elevations_batch(coordinates)
            
            # Update points
            result_points = geo_points.copy()
            for idx, point_idx in enumerate(points_needing_elevation):
                if elevations[idx] is not None:
                    result_points[point_idx].elevation = elevations[idx]
            
            self.logger.info(
                f"Updated {len([e for e in elevations if e is not None])} points "
                f"with elevation data"
            )
            return result_points
            
        except Exception as e:
            self.logger.error(f"Error updating geo points with elevation: {str(e)}")
            return geo_points
    
    def verify_api_key(self) -> bool:
        """
        Verify that the API key is valid
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Test with a simple query
            params = {
                'locations': '0,0',
                'key': self.api_key
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.request_timeout
            )
            
            data = response.json()
            
            # Check for authentication errors
            if data['status'] in ['REQUEST_DENIED', 'INVALID_REQUEST']:
                self.logger.error(f"API key verification failed: {data['status']}")
                if 'error_message' in data:
                    self.logger.error(f"Error message: {data['error_message']}")
                return False
            
            self.logger.info("API key verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying API key: {str(e)}")
            return False


class MockElevationService:
    """Mock service for testing without API key"""
    
    def __init__(self):
        """Initialize mock service"""
        self.logger = logger
    
    def get_elevation(
        self,
        latitude: float,
        longitude: float
    ) -> float:
        """
        Return mock elevation data
        
        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude
            
        Returns:
            Mock elevation based on coordinates
        """
        # Simple mock that varies based on coordinates
        base_elevation = 100
        variation = abs((latitude * 10) % 500) + abs((longitude * 10) % 500)
        return base_elevation + variation
    
    def get_elevations_batch(
        self,
        points: List[Tuple[float, float]]
    ) -> List[float]:
        """Return mock elevations for batch"""
        return [self.get_elevation(lat, lon) for lat, lon in points]
    
    def get_geo_points_with_elevation(
        self,
        geo_points: List[GeoPoint]
    ) -> List[GeoPoint]:
        """Fill elevation data with mock values"""
        for point in geo_points:
            if point.elevation is None:
                point.elevation = self.get_elevation(point.latitude, point.longitude)
        return geo_points
    
    def verify_api_key(self) -> bool:
        """Always returns True for mock"""
        return True


def create_elevation_service(api_key: str) -> GoogleElevationService:
    """
    Factory function to create elevation service
    
    Args:
        api_key: Google Maps API key
        
    Returns:
        GoogleElevationService instance
    """
    if api_key and api_key != 'test_key':
        return GoogleElevationService(api_key)
    else:
        logger.warning("Using mock elevation service (no valid API key)")
        return MockElevationService()
