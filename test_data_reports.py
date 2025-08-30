"""
Test data for the classification system based on real maintenance reports.

These are sample maintenance reports extracted from the provided image
to test the ATA, iSpec, and defect type classification systems.
"""

SAMPLE_MAINTENANCE_REPORTS = [
    {
        "id": "test_001",
        "report_text": "blended out light surface corrosion within limits per srm 51-10-02, alodined and primered area.",
        "expected_classification": {
            "ata_chapter": "51",
            "defect_types": ["corrosion"],
            "maintenance_actions": ["blend", "treat"],
            "parts": ["surface"],
            "severity": "minor"
        }
    },
    {
        "id": "test_002", 
        "report_text": "replaced cracked electrical connector on r/h aft overwing emergency exit light with serviceable one.ops ok.",
        "expected_classification": {
            "ata_chapter": "24",
            "defect_types": ["crack"],
            "maintenance_actions": ["replace"],
            "parts": ["connector", "emergency exit light"],
            "severity": "moderate"
        }
    },
    {
        "id": "test_003",
        "report_text": "removed corrosion iaw srm 51-10-02. depth is within limits of aard 53-00-00-8. alodined and primed iaw srm 51-20-01.",
        "expected_classification": {
            "ata_chapter": "51", 
            "defect_types": ["corrosion"],
            "maintenance_actions": ["remove", "treat"],
            "parts": [],
            "severity": "minor"
        }
    },
    {
        "id": "test_004",
        "report_text": "installed new bonding strap.",
        "expected_classification": {
            "ata_chapter": "24",
            "defect_types": [],
            "maintenance_actions": ["install"],
            "parts": ["bonding strap"],
            "severity": "minor"
        }
    },
    {
        "id": "test_005", 
        "report_text": "removed and recoated telescoping duct, installed and leak checked as per aard 30-11-00-1",
        "expected_classification": {
            "ata_chapter": "36",
            "defect_types": [],
            "maintenance_actions": ["remove", "treat", "install", "test"],
            "parts": ["telescoping duct"],
            "severity": "minor"
        }
    },
    {
        "id": "test_006",
        "report_text": "i have reviewed the task card and verify that the documented wips / tasks satisfy the discrepancy.ops check stats no leaks noted.",
        "expected_classification": {
            "ata_chapter": "00",  # Unknown - generic review task
            "defect_types": [],
            "maintenance_actions": ["inspect", "test"],
            "parts": [],
            "severity": "minor"
        }
    },
    {
        "id": "test_007",
        "report_text": "replaced line with serviceable part. ops and leak check good (see attachment for bpt)",
        "expected_classification": {
            "ata_chapter": "00",  # Unknown without more context
            "defect_types": [],
            "maintenance_actions": ["replace", "test"],
            "parts": ["line"],
            "severity": "minor"
        }
    },
    {
        "id": "test_008",
        "report_text": "removed and replaced bonding strap clips on r/h tank aft boost pump iaw m.m.28-22-41-4.",
        "expected_classification": {
            "ata_chapter": "28",  # Fuel system
            "defect_types": [],
            "maintenance_actions": ["remove", "replace"],
            "parts": ["bonding strap", "boost pump"],
            "severity": "minor"
        }
    },
    {
        "id": "test_009", 
        "report_text": "cleaned area, tightened all 'b' nuts around actuator, quadrant and input shaft; operated #10 spoiler panel numerous times, no leaks noted.",
        "expected_classification": {
            "ata_chapter": "27",  # Flight controls
            "defect_types": [],
            "maintenance_actions": ["clean", "tighten", "test"],
            "parts": ["actuator", "spoiler panel"],
            "severity": "minor"
        }
    },
    {
        "id": "test_010",
        "report_text": "cleaned area and tightened all 'b' nuts above #8 spoiler actuator/quadrant; operated #8 spoiler panel several times, no leaks noted.",
        "expected_classification": {
            "ata_chapter": "27",  # Flight controls
            "defect_types": [],
            "maintenance_actions": ["clean", "tighten", "test"],
            "parts": ["spoiler actuator", "spoiler panel"],
            "severity": "minor"
        }
    },
    {
        "id": "test_011",
        "report_text": "removed and replaced with correct bonding strap. strap no longer contacts duct.",
        "expected_classification": {
            "ata_chapter": "24",  # Electrical
            "defect_types": [],
            "maintenance_actions": ["remove", "replace"],
            "parts": ["bonding strap", "duct"],
            "severity": "minor"
        }
    },
    {
        "id": "test_012",
        "report_text": "Found hydraulic leak at nose gear actuator. B-nut connection showing signs of corrosion. Replaced seal and torqued to specification.",
        "expected_classification": {
            "ata_chapter": "32",  # Landing gear
            "defect_types": ["leak", "corrosion"],
            "maintenance_actions": ["replace", "tighten"],
            "parts": ["actuator", "seal"],
            "severity": "moderate"
        }
    }
]

# Additional test cases for edge cases and comprehensive testing
EDGE_CASE_REPORTS = [
    {
        "id": "edge_001",
        "report_text": "",  # Empty report
        "expected_classification": {
            "ata_chapter": "00",
            "defect_types": [],
            "maintenance_actions": [],
            "parts": [],
            "severity": "minor"
        }
    },
    {
        "id": "edge_002", 
        "report_text": "Multiple issues found: corrosion on wing structure, cracked hydraulic line, loose electrical connector.",
        "expected_classification": {
            "ata_chapter": "51",  # Structure likely dominant
            "defect_types": ["corrosion", "crack", "loose"],
            "maintenance_actions": [],
            "parts": ["structure", "line", "connector"],
            "severity": "major"  # Multiple defects
        }
    },
    {
        "id": "edge_003",
        "report_text": "CRITICAL SAFETY ISSUE: Severe crack found in primary flight control actuator. Immediate replacement required.",
        "expected_classification": {
            "ata_chapter": "27",
            "defect_types": ["crack"],
            "maintenance_actions": ["replace"],
            "parts": ["actuator"],
            "severity": "critical"
        }
    }
]

ALL_TEST_REPORTS = SAMPLE_MAINTENANCE_REPORTS + EDGE_CASE_REPORTS