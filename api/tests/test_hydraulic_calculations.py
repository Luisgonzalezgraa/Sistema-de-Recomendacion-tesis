import pytest

from app.routes import ImageAnalysisEndpoint


def test_required_pump_power_uses_flow_head_and_efficiency():
    endpoint = ImageAnalysisEndpoint()

    hp = endpoint._required_pump_power_hp(
        flow_l_min=100,
        total_head_m=30,
        efficiency=0.60,
    )

    assert hp == pytest.approx(1.096, rel=0.01)


def test_preliminary_hydraulic_analysis_uses_configurable_assumptions():
    endpoint = ImageAnalysisEndpoint()
    assumptions = endpoint._parse_hydraulic_assumptions(
        {
            "flow_per_hectare_l_min": "40",
            "emitter_operating_pressure_kpa": "110",
            "pressure_safety_factor": "1.15",
            "pump_efficiency": "0.65",
            "max_sector_area_ha": "2",
            "minimum_flow_l_min": "10",
            "hazen_williams_c": "150",
            "pipe_diameter_large_m": "0.05",
            "pipe_diameter_small_m": "0.025",
            "minimum_pipe_length_m": "60",
            "pipe_length_factor": "1.10",
        }
    )

    result = endpoint._build_preliminary_hydraulic_analysis(
        slope_percentage=5,
        elevation_diff=6,
        area_hectares=1.5,
        assumptions=assumptions,
    )

    assert result["design_sector_area"] == 1.5
    assert result["available_flow"] == pytest.approx(60)
    assert result["flow_per_hectare"] == 40
    assert result["emitter_operating_pressure"] == 110
    assert result["pressure_safety_factor"] == 1.15
    assert result["pipe_diameter"] == 50
    assert result["source_pressure"] > result["pressure_before_safety"]


def test_preliminary_hydraulic_analysis_applies_chile_context_factors():
    endpoint = ImageAnalysisEndpoint()
    base = endpoint._parse_hydraulic_assumptions({})
    northern_sandy = endpoint._parse_hydraulic_assumptions(
        {
            "zone_chile": "norte_grande",
            "climate_profile": "arido",
            "soil_type": "arenoso",
        }
    )

    base_result = endpoint._build_preliminary_hydraulic_analysis(
        slope_percentage=5,
        elevation_diff=4,
        area_hectares=1,
        assumptions=base,
    )
    context_result = endpoint._build_preliminary_hydraulic_analysis(
        slope_percentage=5,
        elevation_diff=4,
        area_hectares=1,
        assumptions=northern_sandy,
    )

    assert context_result["context"]["zone_label"] == "Norte Grande"
    assert context_result["context"]["soil_label"] == "Arenoso"
    assert context_result["context"]["combined_demand_factor"] > 1
    assert context_result["available_flow"] > base_result["available_flow"]
    assert context_result["pressure_safety_factor"] > base_result["pressure_safety_factor"]


def test_pump_catalog_orders_compatible_pumps_first():
    endpoint = ImageAnalysisEndpoint()

    pumps = endpoint._evaluate_pump_catalog(
        required_total_head_m=30,
        required_total_pressure_kpa=294,
        required_flow_l_min=100,
    )

    assert len(pumps) > 0
    assert pumps[0]["meets_requirements"] is True
    assert pumps[0]["max_flow_l_min"] >= 100
    assert pumps[0]["max_head_m"] >= 30


def test_feasibility_blocks_design_without_compatible_pump():
    endpoint = ImageAnalysisEndpoint()
    hydraulic = endpoint._build_preliminary_hydraulic_analysis(
        slope_percentage=25,
        elevation_diff=120,
        area_hectares=3,
        assumptions=endpoint._parse_hydraulic_assumptions({}),
    )

    feasibility = endpoint._build_feasibility_assessment(
        slope_percentage=25,
        elevation_diff=120,
        area_hectares=3,
        hydraulic_analysis=hydraulic,
    )

    assert feasibility["status"] == "no_factible"
    assert feasibility["priority"] == "Alto"
    assert "No continuar" in feasibility["decision"]


def test_feasibility_low_risk_requires_specialist_final_approval():
    endpoint = ImageAnalysisEndpoint()
    hydraulic = endpoint._build_preliminary_hydraulic_analysis(
        slope_percentage=2,
        elevation_diff=1,
        area_hectares=0.2,
        assumptions=endpoint._parse_hydraulic_assumptions({}),
    )

    feasibility = endpoint._build_feasibility_assessment(
        slope_percentage=2,
        elevation_diff=1,
        area_hectares=0.2,
        hydraulic_analysis=hydraulic,
    )

    assert feasibility["status"] == "factible"
    assert feasibility["priority"] == "Bajo"
    assert "especialista" in feasibility["decision"]
