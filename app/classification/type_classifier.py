"""
Defect Type Classification Module

Classifies maintenance reports by defect type (corrosion, crack, wear, etc.)
and maintenance action (repair, replace, inspect, etc.).
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class DefectSeverity(Enum):
    """Severity levels for defects"""
    MINOR = "minor"
    MODERATE = "moderate" 
    MAJOR = "major"
    CRITICAL = "critical"


@dataclass
class DefectClassification:
    """Result of defect type classification"""
    defect_types: List[str]
    maintenance_actions: List[str]
    severity: DefectSeverity
    safety_critical: bool
    confidence: float
    indicators: List[str]


class DefectTypeClassifier:
    """
    Classifies maintenance reports by defect type and maintenance actions.
    
    Identifies the type of defects found (corrosion, cracks, wear, etc.) and 
    the maintenance actions performed (repair, replace, inspect, etc.).
    """
    
    # Primary defect types with their indicators
    DEFECT_TYPES = {
        'corrosion': {
            'keywords': ['corrosion', 'corroded', 'rust', 'oxidation', 'pitting', 'intergranular'],
            'severity_indicators': {
                'minor': ['light', 'surface', 'minor', 'within limits'],
                'moderate': ['moderate', 'treated', 'cleaned'],
                'major': ['heavy', 'extensive', 'deep', 'structural'],
                'critical': ['severe', 'through', 'critical', 'immediate']
            }
        },
        'crack': {
            'keywords': ['crack', 'cracked', 'fissure', 'fracture', 'split'],
            'severity_indicators': {
                'minor': ['hairline', 'surface', 'minor', 'small'],
                'moderate': ['propagating', 'growing', 'moderate'],
                'major': ['through', 'structural', 'major'],
                'critical': ['critical', 'immediate', 'safety']
            }
        },
        'wear': {
            'keywords': ['wear', 'worn', 'erosion', 'abrasion', 'chafing', 'fretting'],
            'severity_indicators': {
                'minor': ['light', 'minor', 'acceptable'],
                'moderate': ['moderate', 'noticeable'],
                'major': ['excessive', 'beyond limits'],
                'critical': ['critical', 'unsafe']
            }
        },
        'damage': {
            'keywords': ['damage', 'damaged', 'dent', 'gouge', 'scratch', 'impact'],
            'severity_indicators': {
                'minor': ['minor', 'cosmetic', 'surface'],
                'moderate': ['moderate', 'repairable'],
                'major': ['major', 'structural'],
                'critical': ['critical', 'unsafe', 'immediate']
            }
        },
        'leak': {
            'keywords': ['leak', 'leaking', 'seepage', 'weeping', 'dripping'],
            'severity_indicators': {
                'minor': ['minor', 'trace', 'slight'],
                'moderate': ['moderate', 'noticeable'],
                'major': ['major', 'significant'],
                'critical': ['severe', 'continuous', 'critical']
            }
        },
        'loose': {
            'keywords': ['loose', 'looseness', 'play', 'movement', 'slack'],
            'severity_indicators': {
                'minor': ['slight', 'minor'],
                'moderate': ['noticeable', 'moderate'],
                'major': ['excessive', 'significant'],
                'critical': ['critical', 'unsafe']
            }
        },
        'contamination': {
            'keywords': ['contamination', 'contaminated', 'dirty', 'debris', 'foreign object'],
            'severity_indicators': {
                'minor': ['minor', 'light'],
                'moderate': ['moderate', 'noticeable'],
                'major': ['heavy', 'significant'],
                'critical': ['critical', 'blocking']
            }
        },
        'misalignment': {
            'keywords': ['misaligned', 'misalignment', 'out of rig', 'binding', 'interference'],
            'severity_indicators': {
                'minor': ['slight', 'minor'],
                'moderate': ['noticeable', 'moderate'],
                'major': ['significant', 'major'],
                'critical': ['critical', 'unsafe']
            }
        }
    }
    
    # Maintenance actions with their indicators
    MAINTENANCE_ACTIONS = {
        'inspect': ['inspect', 'inspected', 'inspection', 'check', 'checked', 'examine', 'review'],
        'clean': ['clean', 'cleaned', 'cleaning', 'wash', 'washed', 'degreased'],
        'repair': ['repair', 'repaired', 'fix', 'fixed', 'mend', 'patched'],
        'replace': ['replace', 'replaced', 'change', 'changed', 'install', 'installed'],
        'remove': ['remove', 'removed', 'take out', 'extract', 'uninstall'],
        'adjust': ['adjust', 'adjusted', 'rig', 'rigged', 'align', 'aligned', 'calibrate'],
        'lubricate': ['lubricate', 'lubricated', 'grease', 'greased', 'oil', 'oiled'],
        'tighten': ['tighten', 'tightened', 'torque', 'torqued', 'secure', 'secured'],
        'test': ['test', 'tested', 'check', 'verify', 'verified', 'operate', 'operated'],
        'treat': ['treat', 'treated', 'prime', 'primed', 'coat', 'coated', 'seal', 'sealed'],
        'blend': ['blend', 'blended', 'blend out', 'smooth', 'smoothed']
    }
    
    # Safety-critical indicators
    SAFETY_CRITICAL_INDICATORS = [
        'flight safety', 'critical', 'immediate', 'emergency', 'unsafe', 'hazardous',
        'primary structure', 'flight control', 'engine', 'landing gear', 'brake'
    ]
    
    # Limit references that indicate severity assessment
    LIMIT_REFERENCES = [
        r'within\s+limits', r'out\s+of\s+limits', r'beyond\s+limits', r'exceeds?\s+limits',
        r'per\s+srm\s*\d{2}-\d{2}-\d{2}', r'allowable\s+limits', r'specification\s+limits'
    ]
    
    def __init__(self):
        """Initialize the defect type classifier"""
        self.limit_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.LIMIT_REFERENCES]
    
    def classify(self, report_text: str) -> DefectClassification:
        """
        Classify a maintenance report by defect type and maintenance actions.
        
        Args:
            report_text: The maintenance report text to classify
            
        Returns:
            DefectClassification object with defect types, actions, and severity
        """
        if not report_text or not report_text.strip():
            return DefectClassification([], [], DefectSeverity.MINOR, False, 0.0, [])
        
        text_lower = report_text.lower()
        
        # Identify defect types
        defect_types, defect_indicators = self._identify_defect_types(text_lower)
        
        # Identify maintenance actions
        maintenance_actions = self._identify_maintenance_actions(text_lower)
        
        # Determine severity
        severity = self._determine_severity(text_lower, defect_types)
        
        # Check if safety critical
        safety_critical = self._is_safety_critical(text_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(defect_types, maintenance_actions)
        
        return DefectClassification(
            defect_types=defect_types,
            maintenance_actions=maintenance_actions,
            severity=severity,
            safety_critical=safety_critical,
            confidence=confidence,
            indicators=defect_indicators
        )
    
    def _identify_defect_types(self, text: str) -> tuple[List[str], List[str]]:
        """Identify defect types present in the text"""
        found_defects = []
        indicators = []
        
        for defect_type, data in self.DEFECT_TYPES.items():
            for keyword in data['keywords']:
                if keyword in text:
                    if defect_type not in found_defects:
                        found_defects.append(defect_type)
                        indicators.append(keyword)
        
        return found_defects, indicators
    
    def _identify_maintenance_actions(self, text: str) -> List[str]:
        """Identify maintenance actions performed"""
        found_actions = []
        
        for action, keywords in self.MAINTENANCE_ACTIONS.items():
            for keyword in keywords:
                if keyword in text and action not in found_actions:
                    found_actions.append(action)
                    break
        
        return found_actions
    
    def _determine_severity(self, text: str, defect_types: List[str]) -> DefectSeverity:
        """Determine the severity of the defect(s)"""
        max_severity = DefectSeverity.MINOR
        
        # Check explicit severity indicators
        for defect_type in defect_types:
            if defect_type in self.DEFECT_TYPES:
                severity_indicators = self.DEFECT_TYPES[defect_type]['severity_indicators']
                
                for severity_level, indicators in severity_indicators.items():
                    for indicator in indicators:
                        if indicator in text:
                            candidate_severity = DefectSeverity(severity_level)
                            if self._severity_level(candidate_severity) > self._severity_level(max_severity):
                                max_severity = candidate_severity
        
        # Check for limit exceedances
        for regex in self.limit_regex:
            if regex.search(text):
                if 'out of limits' in text or 'beyond limits' in text or 'exceeds limits' in text:
                    max_severity = DefectSeverity.MAJOR
                elif 'within limits' in text and max_severity == DefectSeverity.MINOR:
                    max_severity = DefectSeverity.MINOR
        
        return max_severity
    
    def _severity_level(self, severity: DefectSeverity) -> int:
        """Convert severity enum to numeric level for comparison"""
        levels = {
            DefectSeverity.MINOR: 1,
            DefectSeverity.MODERATE: 2,
            DefectSeverity.MAJOR: 3,
            DefectSeverity.CRITICAL: 4
        }
        return levels.get(severity, 1)
    
    def _is_safety_critical(self, text: str) -> bool:
        """Determine if the issue is safety critical"""
        for indicator in self.SAFETY_CRITICAL_INDICATORS:
            if indicator in text:
                return True
        return False
    
    def _calculate_confidence(self, defect_types: List[str], actions: List[str]) -> float:
        """Calculate confidence score for the classification"""
        score = 0.0
        
        # Base score for finding defect types
        score += len(defect_types) * 0.3
        
        # Score for finding maintenance actions
        score += len(actions) * 0.2
        
        # Bonus for finding both defects and actions
        if defect_types and actions:
            score += 0.3
        
        return min(score, 1.0)
    
    def get_defect_description(self, defect_type: str) -> Optional[Dict]:
        """Get detailed information about a defect type"""
        return self.DEFECT_TYPES.get(defect_type)
    
    def list_defect_types(self) -> List[str]:
        """Get all supported defect types"""
        return list(self.DEFECT_TYPES.keys())
    
    def list_maintenance_actions(self) -> List[str]:
        """Get all supported maintenance actions"""
        return list(self.MAINTENANCE_ACTIONS.keys())