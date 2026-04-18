"""
Hydraulic Analysis Module
Handles hydraulic calculations for irrigation system design
"""
import numpy as np
import logging
from typing import Tuple, List, Optional
from dataclasses import dataclass
from app.models.data_models import HydraulicAnalysis, WaterComposition, TopographicAnalysis

logger = logging.getLogger(__name__)


class HydraulicCalculator:
    """
    Performs hydraulic calculations for drip irrigation systems
    Implements equations from Hazen-Williams and drip emitter behavior
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize hydraulic calculator
        
        Args:
            config: Configuration dictionary with hydraulic parameters
        """
        self.config = config or {}
        self.water_density = self.config.get('water_density', 1000)  # kg/m³
        self.gravity = self.config.get('gravity', 9.81)  # m/s²
        self.hazen_williams_c = self.config.get('hazen_williams_c', 150)  # HDPE
        self.logger = logger
    
    def calculate_hazen_williams_loss(
        self,
        length: float,
        flow_rate: float,
        diameter: float,
        c_coefficient: float
    ) -> float:
        """
        Calculate friction loss using Hazen-Williams equation
        
        Reference: Industries (1997)
        hf = 10.67 * L * (Q^1.852) / (C^1.852 * D^4.87)
        
        Args:
            length: Pipe length (m)
            flow_rate: Flow rate (m³/s)
            diameter: Internal pipe diameter (m)
            c_coefficient: Hazen-Williams roughness coefficient
            
        Returns:
            Friction loss (m), which equals pressure loss in bar approximately
        """
        try:
            if length <= 0:
                raise ValueError("Pipe length must be positive")
            if flow_rate < 0:
                raise ValueError("Flow rate cannot be negative")
            if diameter <= 0:
                raise ValueError("Diameter must be positive")
            if c_coefficient <= 0:
                raise ValueError("C coefficient must be positive")
            
            # Hazen-Williams formula
            hf = 10.67 * length * (flow_rate ** 1.852) / (c_coefficient ** 1.852 * diameter ** 4.87)
            
            # Convert height loss to pressure loss (1 m water column ≈ 0.098 bar)
            pressure_loss_bar = hf * 0.098
            
            self.logger.debug(
                f"Hazen-Williams loss: {hf:.4f}m height = {pressure_loss_bar:.4f} bar"
            )
            return pressure_loss_bar
            
        except Exception as e:
            self.logger.error(f"Error calculating Hazen-Williams loss: {str(e)}")
            raise
    
    def calculate_elevation_pressure_change(
        self,
        elevation_change: float
    ) -> float:
        """
        Calculate pressure change due to elevation difference
        
        Reference: ΔP = ρ * g * Δh
        
        Args:
            elevation_change: Elevation difference (m), positive = uphill
            
        Returns:
            Pressure change (bar)
        """
        try:
            # Pressure change
            pressure_change_pa = self.water_density * self.gravity * elevation_change
            
            # Convert to bar (1 bar = 100000 Pa)
            pressure_change_bar = pressure_change_pa / 100000
            
            self.logger.debug(
                f"Elevation pressure change: {elevation_change:.2f}m = {pressure_change_bar:.4f} bar"
            )
            return pressure_change_bar
            
        except Exception as e:
            self.logger.error(f"Error calculating elevation pressure change: {str(e)}")
            raise
    
    def calculate_emitter_flow(
        self,
        pressure: float,
        emitter_coefficient: float,
        emitter_exponent: float
    ) -> float:
        """
        Calculate emitter flow rate using characteristic equation
        
        Reference: q = k * P^x
        
        Args:
            pressure: Operating pressure (bar)
            emitter_coefficient: Emitter coefficient k
            emitter_exponent: Discharge exponent x (typically 0.5-0.6 for non-compensated)
            
        Returns:
            Flow rate (L/h)
        """
        try:
            if pressure < 0:
                logger.warning(f"Negative pressure {pressure} bar detected")
            if emitter_exponent < 0 or emitter_exponent > 1:
                raise ValueError("Emitter exponent should be between 0 and 1")
            
            # q = k * P^x
            flow_lh = emitter_coefficient * (pressure ** emitter_exponent)
            
            self.logger.debug(
                f"Emitter flow: {flow_lh:.4f} L/h at {pressure:.2f} bar"
            )
            return flow_lh
            
        except Exception as e:
            self.logger.error(f"Error calculating emitter flow: {str(e)}")
            raise
    
    def calculate_required_pump_power(
        self,
        flow_rate: float,
        total_head: float
    ) -> float:
        """
        Calculate required pump power
        
        Power (HP) = (Flow (L/min) * Pressure (bar)) / 600
        
        Args:
            flow_rate: Total system flow rate (m³/s)
            total_head: Total dynamic head (bar)
            
        Returns:
            Required pump power (HP)
        """
        try:
            if flow_rate < 0:
                raise ValueError("Flow rate cannot be negative")
            if total_head < 0:
                raise ValueError("Head cannot be negative")
            
            # Convert m³/s to L/min
            flow_lmin = flow_rate * 60000
            
            # Power formula
            power_hp = (flow_lmin * total_head) / 600
            
            self.logger.debug(f"Required pump power: {power_hp:.2f} HP")
            return power_hp
            
        except Exception as e:
            self.logger.error(f"Error calculating pump power: {str(e)}")
            raise
    
    def calculate_uniformity_coefficient(
        self,
        pressure_min: float,
        pressure_max: float,
        emitter_exponent: float
    ) -> float:
        """
        Estimate uniformity coefficient based on pressure variation
        
        Reference: Solomon (1985), Chen et al. (2022)
        
        Args:
            pressure_min: Minimum operating pressure (bar)
            pressure_max: Maximum operating pressure (bar)
            emitter_exponent: Emitter discharge exponent
            
        Returns:
            Uniformity coefficient (0-1)
        """
        try:
            if pressure_min < 0 or pressure_max < 0:
                raise ValueError("Pressures cannot be negative")
            if pressure_min >= pressure_max:
                raise ValueError("Minimum pressure must be less than maximum")
            
            # Approximate uniformity based on pressure ratio
            pressure_ratio = pressure_min / pressure_max
            
            # Flow uniformity approximates pressure uniformity raised to exponent
            flow_uniformity = pressure_ratio ** emitter_exponent
            
            # Christiansen's uniformity coefficient approximation
            cu = 1 - (1.27 * (1 - flow_uniformity) / np.sqrt(100))  # Simplified
            cu = max(0, min(1, cu))  # Constrain between 0 and 1
            
            self.logger.debug(f"Uniformity coefficient: {cu:.4f}")
            return cu
            
        except Exception as e:
            self.logger.error(f"Error calculating uniformity coefficient: {str(e)}")
            raise
    
    def perform_hydraulic_analysis(
        self,
        topographic_analysis: TopographicAnalysis,
        water_composition: WaterComposition,
        pipe_length: float,
        pipe_diameter: float,
        flow_rate: float,
        emitter_coefficient: float = 0.95,
        emitter_exponent: float = 0.55
    ) -> HydraulicAnalysis:
        """
        Perform complete hydraulic analysis for the irrigation system
        
        Args:
            topographic_analysis: Topographic analysis results
            water_composition: Water quality parameters
            pipe_length: Pipe length (m)
            pipe_diameter: Internal pipe diameter (m)
            flow_rate: Design flow rate (m³/s)
            emitter_coefficient: Emitter k coefficient
            emitter_exponent: Emitter x exponent
            
        Returns:
            HydraulicAnalysis object with results
        """
        try:
            # Calculate pressure changes
            elevation_pressure = self.calculate_elevation_pressure_change(
                topographic_analysis.elevation_difference
            )
            
            # Friction loss
            friction_loss = self.calculate_hazen_williams_loss(
                length=pipe_length,
                flow_rate=flow_rate,
                diameter=pipe_diameter,
                c_coefficient=self.hazen_williams_c
            )
            
            # Assume starting pressure of 1.5 bar (typical for drip systems)
            initial_pressure = 1.5
            
            # Calculate final pressure
            # Uphill: pressure decreases
            # Downhill: pressure increases
            final_pressure = initial_pressure - friction_loss - elevation_pressure
            
            # Ensure minimum operating pressure
            if final_pressure < 0.2:
                self.logger.warning(f"Final pressure {final_pressure:.2f} bar is critically low")
            
            # Average pressure for emitter calculation
            avg_pressure = (initial_pressure + final_pressure) / 2
            
            # Calculate emitter flow
            emitter_flow = self.calculate_emitter_flow(
                pressure=avg_pressure,
                emitter_coefficient=emitter_coefficient,
                emitter_exponent=emitter_exponent
            )
            
            # Calculate uniformity
            uniformity = self.calculate_uniformity_coefficient(
                pressure_min=min(initial_pressure, final_pressure),
                pressure_max=max(initial_pressure, final_pressure),
                emitter_exponent=emitter_exponent
            )
            
            # Calculate pump power
            total_head = initial_pressure + elevation_pressure + friction_loss
            pump_power = self.calculate_required_pump_power(
                flow_rate=flow_rate,
                total_head=total_head
            )
            
            # Generate design warnings
            warnings = []
            if abs(elevation_pressure) > 0.5:
                warnings.append(
                    f"High elevation change ({topographic_analysis.elevation_difference}m): "
                    f"Significant pressure variation ({elevation_pressure:.2f} bar)"
                )
            if friction_loss > 0.3:
                warnings.append(
                    f"High friction loss ({friction_loss:.2f} bar): "
                    f"Consider increasing pipe diameter or reducing flow"
                )
            if uniformity < 0.7:
                warnings.append(
                    f"Low uniformity coefficient ({uniformity:.2f}): "
                    f"Consider using pressure regulators or compensating emitters"
                )
            if final_pressure < 0.5:
                warnings.append(
                    f"Final pressure critically low ({final_pressure:.2f} bar): "
                    f"System may not operate properly"
                )
            
            result = HydraulicAnalysis(
                flow_rate=flow_rate,
                initial_pressure=initial_pressure,
                final_pressure=final_pressure,
                pressure_loss=friction_loss + elevation_pressure,
                hazen_williams_loss=friction_loss,
                elevation_pressure_change=elevation_pressure,
                emitter_flow=emitter_flow,
                required_pump_power=pump_power,
                design_warnings=warnings
            )
            
            self.logger.info(f"Hydraulic analysis complete. Warnings: {len(warnings)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error performing hydraulic analysis: {str(e)}")
            raise
