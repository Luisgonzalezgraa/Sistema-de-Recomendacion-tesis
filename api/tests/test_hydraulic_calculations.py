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

