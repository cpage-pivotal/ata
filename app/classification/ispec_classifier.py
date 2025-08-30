"""
iSpec 2200 Classification Module

Classifies maintenance reports according to iSpec 2200 part identification standards.
Focuses on identifying specific aircraft parts and components mentioned in maintenance reports.
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class ISpecClassification:
    """Result of iSpec 2200 classification"""
    part_categories: List[str]
    identified_parts: List[str]
    confidence: float
    part_numbers: List[str]


class ISpecClassifier:
    """
    Classifies maintenance reports according to iSpec 2200 part identification standards.
    
    Identifies specific aircraft parts, components, and part numbers mentioned in 
    maintenance reports to support parts management and inventory tracking.
    """
    
    # Major aircraft part categories from iSpec 2200
    PART_CATEGORIES = {
        'structure': {
            'keywords': ['frame', 'bulkhead', 'stringer', 'rib', 'spar', 'skin', 'panel', 'doubler'],
            'description': 'Structural components and framework'
        },
        'fasteners': {
            'keywords': ['bolt', 'screw', 'rivet', 'nut', 'washer', 'pin', 'clip', 'clamp'],
            'description': 'Fastening hardware and connecting elements'
        },
        'seals_gaskets': {
            'keywords': ['seal', 'gasket', 'o-ring', 'packing', 'weather strip'],
            'description': 'Sealing components and weather protection'
        },
        'electrical': {
            'keywords': ['connector', 'wire', 'cable', 'harness', 'switch', 'relay', 'fuse', 'breaker'],
            'description': 'Electrical components and wiring'
        },
        'hydraulic': {
            'keywords': ['actuator', 'cylinder', 'pump', 'valve', 'reservoir', 'accumulator', 'filter'],
            'description': 'Hydraulic system components'
        },
        'pneumatic': {
            'keywords': ['duct', 'valve', 'regulator', 'manifold', 'coupling', 'clamp'],
            'description': 'Pneumatic and air system components'
        },
        'mechanical': {
            'keywords': ['bearing', 'bushing', 'shaft', 'gear', 'pulley', 'spring', 'linkage'],
            'description': 'Mechanical components and moving parts'
        },
        'surfaces': {
            'keywords': ['coating', 'paint', 'primer', 'sealant', 'tape', 'film'],
            'description': 'Surface treatments and protective coatings'
        },
        'consumables': {
            'keywords': ['fluid', 'oil', 'grease', 'solvent', 'cleaner', 'compound'],
            'description': 'Consumable materials and fluids'
        }
    }
    
    # Common aircraft parts with their typical contexts
    AIRCRAFT_PARTS = {
        'landing_gear': ['strut', 'shock absorber', 'wheel', 'tire', 'brake', 'gear door', 'actuator'],
        'control_surfaces': ['aileron', 'elevator', 'rudder', 'flap', 'slat', 'spoiler', 'tab'],
        'engines': ['compressor', 'turbine', 'combustor', 'nozzle', 'cowling', 'mount'],
        'fuselage': ['window', 'door', 'access panel', 'antenna', 'static port'],
        'wings': ['leading edge', 'trailing edge', 'winglet', 'fence', 'root', 'tip'],
        'systems': ['pump', 'motor', 'generator', 'battery', 'tank', 'line', 'valve']
    }
    
    # Part number patterns (common aerospace part numbering schemes)
    PART_NUMBER_PATTERNS = [
        r'\b[A-Z]{1,3}\d{2,8}[A-Z]?\b',  # Standard aerospace part numbers
        r'\bMS\d{5,6}[A-Z]?\d*\b',       # Military Standard parts
        r'\bAN\d{3,6}[A-Z]?\d*\b',       # Army-Navy Standard parts  
        r'\bNAS\d{3,6}[A-Z]?\d*\b',      # National Aerospace Standard
        r'\b\d{6}-\d{2,4}\b',            # Dash number format
        r'\bm\.m\.\d{2}-\d{2}-\d{2}-\d+\b'  # Maintenance manual references
    ]
    
    # Tools and equipment (not aircraft parts but mentioned in maintenance)
    TOOLS_EQUIPMENT = {
        'torque', 'wrench', 'socket', 'drill', 'bit', 'gauge', 'tester', 
        'jack', 'stand', 'lift', 'hoist', 'crane', 'sling'
    }
    
    def __init__(self):
        """Initialize the iSpec classifier with compiled regex patterns"""
        self.part_number_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.PART_NUMBER_PATTERNS]
    
    def classify(self, report_text: str) -> ISpecClassification:
        """
        Classify a maintenance report to identify parts according to iSpec 2200.
        
        Args:
            report_text: The maintenance report text to classify
            
        Returns:
            ISpecClassification object with part categories and identified components
        """
        if not report_text or not report_text.strip():
            return ISpecClassification([], [], 0.0, [])
        
        text_lower = report_text.lower()
        
        # Find part categories
        part_categories = self._identify_part_categories(text_lower)
        
        # Find specific parts
        identified_parts = self._identify_specific_parts(text_lower)
        
        # Find part numbers
        part_numbers = self._extract_part_numbers(report_text)
        
        # Calculate confidence based on findings
        confidence = self._calculate_confidence(part_categories, identified_parts, part_numbers)
        
        return ISpecClassification(
            part_categories=part_categories,
            identified_parts=identified_parts,
            confidence=confidence,
            part_numbers=part_numbers
        )
    
    def _identify_part_categories(self, text: str) -> List[str]:
        """Identify which part categories are mentioned in the text"""
        categories = []
        
        for category, data in self.PART_CATEGORIES.items():
            for keyword in data['keywords']:
                if keyword in text:
                    if category not in categories:
                        categories.append(category)
                    break
        
        return categories
    
    def _identify_specific_parts(self, text: str) -> List[str]:
        """Identify specific aircraft parts mentioned in the text"""
        parts = []
        
        for part_type, part_list in self.AIRCRAFT_PARTS.items():
            for part in part_list:
                if part in text and part not in parts:
                    parts.append(part)
        
        # Add some context-specific part identification
        parts.extend(self._identify_contextual_parts(text))
        
        # Remove tools/equipment that aren't aircraft parts
        parts = [part for part in parts if part not in self.TOOLS_EQUIPMENT]
        
        return parts
    
    def _identify_contextual_parts(self, text: str) -> List[str]:
        """Identify parts based on context and patterns"""
        contextual_parts = []
        
        # Emergency equipment
        if 'emergency' in text and 'exit' in text:
            contextual_parts.append('emergency exit light')
        
        # Hydraulic actuators
        if 'hydraulic' in text and 'actuator' in text:
            contextual_parts.append('hydraulic actuator')
            
        # Bonding straps (electrical)
        if 'bonding strap' in text:
            contextual_parts.append('bonding strap')
            
        # Telescoping ducts
        if 'telescoping duct' in text:
            contextual_parts.append('telescoping duct')
            
        # Spoiler panels and components
        if 'spoiler' in text:
            contextual_parts.append('spoiler panel')
            if 'actuator' in text:
                contextual_parts.append('spoiler actuator')
        
        # Tank components
        if 'tank' in text:
            if 'boost pump' in text:
                contextual_parts.append('boost pump')
        
        return contextual_parts
    
    def _extract_part_numbers(self, text: str) -> List[str]:
        """Extract part numbers from the maintenance report"""
        part_numbers = []
        
        for regex in self.part_number_regex:
            matches = regex.findall(text)
            part_numbers.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_part_numbers = []
        for pn in part_numbers:
            if pn not in seen:
                seen.add(pn)
                unique_part_numbers.append(pn)
        
        return unique_part_numbers
    
    def _calculate_confidence(self, categories: List[str], parts: List[str], 
                           part_numbers: List[str]) -> float:
        """Calculate confidence score based on classification results"""
        score = 0.0
        
        # Base score for finding categories
        score += len(categories) * 0.1
        
        # Higher score for specific parts
        score += len(parts) * 0.2
        
        # Highest score for actual part numbers
        score += len(part_numbers) * 0.3
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def get_category_description(self, category: str) -> Optional[str]:
        """
        Get the description for a part category.
        
        Args:
            category: Part category name
            
        Returns:
            Category description or None if not found
        """
        return self.PART_CATEGORIES.get(category, {}).get('description')
    
    def list_categories(self) -> Dict[str, str]:
        """
        Get all part categories and their descriptions.
        
        Returns:
            Dictionary of category names to descriptions
        """
        return {cat: data['description'] for cat, data in self.PART_CATEGORIES.items()}