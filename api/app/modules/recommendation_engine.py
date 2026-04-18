"""
Recommendation Engine Module
Generates technical recommendations for irrigation system design
"""
import logging
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
import uuid
from datetime import datetime

from app.models.data_models import (
    TopographicAnalysis, WaterComposition, HydraulicAnalysis,
    TubingMaterial, RecommendationResult
)

logger = logging.getLogger(__name__)


class TubingMaterialRepository:
    """Repository for tubing material specifications"""
    
    # Library of compatible materials
    MATERIALS = {
        'HDPE_16mm': TubingMaterial(
            name='HDPE 16mm',
            material_type='HDPE',
            internal_diameter=16,
            external_diameter=20,
            wall_thickness=2,
            hazen_williams_c=150,
            recommended_pressure=2.5,
            compatibility_notes=[
                'Excellent chemical resistance',
                'Suitable for fertilizer injection',
                'Good durability in UV exposure'
            ]
        ),
        'HDPE_12mm': TubingMaterial(
            name='HDPE 12mm',
            material_type='HDPE',
            internal_diameter=12,
            external_diameter=15,
            wall_thickness=1.5,
            hazen_williams_c=150,
            recommended_pressure=2.0,
            compatibility_notes=[
                'Lower flow capacity',
                'Suitable for smaller fields',
                'Good for low-pressure systems'
            ]
        ),
        'PVC_20mm': TubingMaterial(
            name='PVC 20mm',
            material_type='PVC',
            internal_diameter=20,
            external_diameter=24,
            wall_thickness=2,
            hazen_williams_c=140,
            recommended_pressure=8.0,
            compatibility_notes=[
                'Higher pressure capacity',
                'More rigid than HDPE',
                'Requires sun protection',
                'Higher installation cost'
            ]
        ),
        'PE_16mm': TubingMaterial(
            name='PE 16mm',
            material_type='PE',
            internal_diameter=16,
            external_diameter=20,
            wall_thickness=2,
            hazen_williams_c=145,
            recommended_pressure=1.5,
            compatibility_notes=[
                'Lower cost than HDPE',
                'Lower pressure rating',
                'Good for low-slope systems'
            ]
        ),
    }
    
    @classmethod
    def get_all_materials(cls) -> List[TubingMaterial]:
        """Get all available materials"""
        return list(cls.MATERIALS.values())
    
    @classmethod
    def get_material_by_name(cls, name: str) -> TubingMaterial:
        """Get material by name"""
        return cls.MATERIALS.get(name)


class RecommendationEngine:
    """
    Generates technical recommendations based on analysis results
    """
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.logger = logger
        self.material_repo = TubingMaterialRepository()
    
    def recommend_tubing_materials(
        self,
        water_composition: WaterComposition,
        hydraulic_analysis: HydraulicAnalysis,
        flow_rate: float
    ) -> List[TubingMaterial]:
        """
        Recommend suitable tubing materials
        
        Args:
            water_composition: Water quality parameters
            hydraulic_analysis: Hydraulic analysis results
            flow_rate: Design flow rate (m³/s)
            
        Returns:
            List of recommended tubing materials (ranked by suitability)
        """
        try:
            recommendations = []
            
            for material in self.material_repo.get_all_materials():
                score = 0
                reasons = []
                
                # Check pressure compatibility
                if hydraulic_analysis.initial_pressure <= material.recommended_pressure:
                    score += 30
                    reasons.append(f"Pressure compatible ({material.recommended_pressure} bar rated)")
                else:
                    score -= 20
                    reasons.append(f"Pressure may exceed rating ({material.recommended_pressure} bar)")
                
                # Check water composition compatibility
                if water_composition.salinity < 500:  # Normal salinity range
                    score += 20
                    reasons.append("Good chemical compatibility")
                
                if water_composition.ph >= 5.5 and water_composition.ph <= 8.5:
                    score += 20
                    reasons.append("pH is within acceptable range")
                
                # Check flow rate appropriateness
                max_flow_capacity = (material.internal_diameter / 16) * 2  # Simplified capacity
                if 0.5 < flow_rate < max_flow_capacity:
                    score += 15
                    reasons.append("Appropriate flow capacity")
                elif flow_rate < 0.5:
                    score += 10
                
                # Material cost consideration
                if material.material_type == 'HDPE':
                    score += 10
                    reasons.append("Good cost-performance ratio")
                
                if score > 0:
                    material.compatibility_notes = reasons
                    recommendations.append((material, score))
            
            # Sort by score (descending)
            recommendations.sort(key=lambda x: x[1], reverse=True)
            recommended_materials = [m[0] for m in recommendations if m[1] > 0]
            
            self.logger.info(f"Recommended {len(recommended_materials)} tubing materials")
            return recommended_materials
            
        except Exception as e:
            self.logger.error(f"Error recommending tubing materials: {str(e)}")
            raise
    
    def recommend_pump_power(
        self,
        hydraulic_analysis: HydraulicAnalysis
    ) -> float:
        """
        Recommend pump power with safety factor
        
        Args:
            hydraulic_analysis: Hydraulic analysis results
            
        Returns:
            Recommended pump power (HP) with safety margin
        """
        try:
            # Apply 20% safety factor for real-world conditions
            safety_factor = 1.2
            recommended_power = hydraulic_analysis.required_pump_power * safety_factor
            
            self.logger.info(f"Recommended pump power: {recommended_power:.2f} HP")
            return recommended_power
            
        except Exception as e:
            self.logger.error(f"Error recommending pump power: {str(e)}")
            raise
    
    def generate_design_notes(
        self,
        topographic_analysis: TopographicAnalysis,
        hydraulic_analysis: HydraulicAnalysis,
        water_composition: WaterComposition
    ) -> List[str]:
        """
        Generate additional design notes and recommendations
        
        Args:
            topographic_analysis: Topographic analysis results
            hydraulic_analysis: Hydraulic analysis results
            water_composition: Water quality parameters
            
        Returns:
            List of design notes and recommendations
        """
        notes = []
        
        # Topography-based notes
        if abs(topographic_analysis.slope_percentage) > 20:
            notes.append(
                f"High slope ({topographic_analysis.slope_percentage:.1f}%): "
                "Consider dividing into multiple zones with pressure regulators"
            )
        elif abs(topographic_analysis.slope_percentage) < 2:
            notes.append(
                f"Low slope ({topographic_analysis.slope_percentage:.1f}%): "
                "Minimal elevation effects; standard design acceptable"
            )
        
        # Hydraulic-based notes
        if hydraulic_analysis.emitter_flow < 1.0:
            notes.append("Low emitter flow rate; verify with manufacturer specifications")
        elif hydraulic_analysis.emitter_flow > 5.0:
            notes.append("High emitter flow rate; ensure adequate water supply")
        
        # Water quality notes
        if water_composition.salinity > 1000:
            notes.append(
                f"High salinity ({water_composition.salinity} mg/L): "
                "Use salt-resistant materials; monitor for clogging"
            )
        
        if water_composition.ph < 6.5 or water_composition.ph > 8.5:
            notes.append(
                f"Out-of-range pH ({water_composition.ph}): "
                "Consider water treatment before use"
            )
        
        if water_composition.hardness > 300:
            notes.append(
                f"High water hardness ({water_composition.hardness} ppm): "
                "Implement drip line flushing schedule"
            )
        
        # Fertilizer/pesticide notes
        if water_composition.fertilizer_content:
            notes.append(
                f"Fertilizer detected ({water_composition.fertilizer_content}): "
                "Use drip-compatible formulations; check for emitter compatibility"
            )
        
        if water_composition.pesticide_content:
            notes.append(
                f"Pesticide detected ({water_composition.pesticide_content}): "
                "Verify system compatibility; use in-line filters if needed"
            )
        
        # General recommendations
        notes.append("Recommend annual system maintenance and flushing")
        notes.append("Install pressure gauges at system inlet and outlet for monitoring")
        notes.append("Use in-line filters (minimum 200 microns) to prevent clogging")
        
        return notes
    
    def generate_recommendations(
        self,
        topographic_analysis: TopographicAnalysis,
        water_composition: WaterComposition,
        hydraulic_analysis: HydraulicAnalysis
    ) -> RecommendationResult:
        """
        Generate complete recommendations for irrigation system design
        
        Args:
            topographic_analysis: Topographic analysis results
            water_composition: Water composition analysis
            hydraulic_analysis: Hydraulic analysis results
            
        Returns:
            Complete recommendation result
        """
        try:
            # Get recommended materials
            recommended_materials = self.recommend_tubing_materials(
                water_composition=water_composition,
                hydraulic_analysis=hydraulic_analysis,
                flow_rate=hydraulic_analysis.flow_rate
            )
            
            # Get recommended pump power
            recommended_power = self.recommend_pump_power(hydraulic_analysis)
            
            # Generate design notes
            design_notes = self.generate_design_notes(
                topographic_analysis,
                hydraulic_analysis,
                water_composition
            )
            
            # Calculate confidence score (0-1)
            confidence = self._calculate_confidence(hydraulic_analysis, design_notes)
            
            # Create recommendation result
            result = RecommendationResult(
                project_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat(),
                topographic_analysis=topographic_analysis,
                water_composition=water_composition,
                hydraulic_analysis=hydraulic_analysis,
                recommended_tubings=recommended_materials,
                recommended_pump_power=recommended_power,
                design_notes=design_notes,
                confidence_score=confidence
            )
            
            self.logger.info(f"Generated recommendations with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_confidence(
        hydraulic_analysis: HydraulicAnalysis,
        design_notes: List[str]
    ) -> float:
        """
        Calculate confidence score for recommendations
        
        Args:
            hydraulic_analysis: Hydraulic analysis results
            design_notes: List of design notes
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.8  # Start with base confidence
        
        # Reduce confidence based on warnings
        confidence -= len(hydraulic_analysis.design_warnings) * 0.05
        
        # Reduce confidence based on design notes (as proxy for complexity)
        if len(design_notes) > 5:
            confidence -= 0.1
        
        # Ensure within bounds
        confidence = max(0.1, min(1.0, confidence))
        
        return confidence
