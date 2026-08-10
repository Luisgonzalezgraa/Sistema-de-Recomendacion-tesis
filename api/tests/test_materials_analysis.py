from app.routes import ImageAnalysisEndpoint


def test_materials_analysis_builds_drip_irrigation_bill_of_materials():
    endpoint = ImageAnalysisEndpoint()
    hydraulic = {
        "pipe_diameter": 40,
        "source_pressure": 220,
        "available_flow": 105,
        "design_sector_area": 3,
        "pipe_length": 220,
    }

    materials = endpoint._build_materials_analysis(
        hydraulic_analysis=hydraulic,
        area_hectares=3,
        estimated_drip_length=15000,
    )

    assert materials["main_pipe_type"] == "HDPE"
    assert materials["main_pipe_diameter_mm"] == 40
    assert materials["valve_diameter_mm"] == 40
    assert materials["pipe_pressure_class"] == "PN 6"
    assert materials["estimated_emitters"] == 50000
    assert len(materials["items"]) >= 8
    assert any(item["category"] == "Filtro" for item in materials["items"])


def test_materials_analysis_selects_higher_pressure_class_for_high_pressure():
    endpoint = ImageAnalysisEndpoint()
    hydraulic = {
        "pipe_diameter": 50,
        "source_pressure": 340,
        "available_flow": 180,
        "design_sector_area": 4,
        "pipe_length": 260,
    }

    materials = endpoint._build_materials_analysis(
        hydraulic_analysis=hydraulic,
        area_hectares=4,
        estimated_drip_length=20000,
    )

    assert materials["pipe_pressure_class"] == "PN 10"
    assert "120-150 mesh" in materials["filter_type"]

