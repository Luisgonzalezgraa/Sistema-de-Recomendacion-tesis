"""
Data models and schemas for the API
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class GeoPoint:
    """Representation of a geographic point with coordinates"""
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict):
        return GeoPoint(**data)


@dataclass
class TopographicAnalysis:
    """Results of topographic analysis"""
    point_start: GeoPoint
    point_end: GeoPoint
    elevation_difference: float  # meters
    slope_percentage: float  # percentage
    slope_radians: float  # radians
    slope_degrees: float  # degrees
    distance: float  # meters (horizontal distance)
    
    def to_dict(self):
        data = asdict(self)
        data['point_start'] = self.point_start.to_dict()
        data['point_end'] = self.point_end.to_dict()
        return data


@dataclass
class WaterComposition:
    """Water quality and composition parameters"""
    density: float  # kg/m³
    temperature: float  # °C
    ph: float  # pH value
    salinity: float  # mg/L
    hardness: float  # mg/L CaCO3
    fertilizer_content: Optional[str] = None  # Type of fertilizer
    pesticide_content: Optional[str] = None  # Type of pesticide
    other_components: Optional[List[str]] = None  # Other components
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict):
        return WaterComposition(**{k: v for k, v in data.items() if k in WaterComposition.__dataclass_fields__})


@dataclass
class HydraulicAnalysis:
    """Results of hydraulic analysis"""
    flow_rate: float  # m³/s
    initial_pressure: float  # bar
    final_pressure: float  # bar
    pressure_loss: float  # bar
    hazen_williams_loss: float  # bar (friction loss)
    elevation_pressure_change: float  # bar
    emitter_flow: float  # L/h
    required_pump_power: float  # HP
    design_warnings: List[str]
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TubingMaterial:
    """Tubing material specifications"""
    name: str
    material_type: str  # HDPE, PVC, PE, etc.
    internal_diameter: float  # mm
    external_diameter: float  # mm
    wall_thickness: float  # mm
    hazen_williams_c: float  # roughness coefficient
    recommended_pressure: float  # bar
    compatibility_notes: List[str]
    cost_per_meter: Optional[float] = None  # Currency units
    
    def to_dict(self):
        return asdict(self)


@dataclass
class RecommendationResult:
    """Final recommendation results"""
    project_id: str
    timestamp: str
    topographic_analysis: TopographicAnalysis
    water_composition: WaterComposition
    hydraulic_analysis: HydraulicAnalysis
    recommended_tubings: List[TubingMaterial]
    recommended_pump_power: float  # HP
    design_notes: List[str]
    confidence_score: float  # 0-1
    
    def to_dict(self):
        data = asdict(self)
        data['topographic_analysis'] = self.topographic_analysis.to_dict()
        data['water_composition'] = self.water_composition.to_dict()
        data['hydraulic_analysis'] = self.hydraulic_analysis.to_dict()
        data['recommended_tubings'] = [t.to_dict() for t in self.recommended_tubings]
        return data
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DigitalElevationModel:
    """Digital Elevation Model (DEM) representation"""
    id: str
    created_at: str
    source: str  # 'drone', 'google_elevation', 'combined'
    bounding_box: Dict[str, float]  # min_lat, max_lat, min_lon, max_lon
    resolution: float  # meters per pixel
    elevation_points: Optional[List[Dict[str, float]]] = None  # lat, lon, elevation
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class APIResponse:
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'errors': self.errors,
            'timestamp': self.timestamp
        }
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
