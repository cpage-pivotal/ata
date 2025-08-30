"""
ATA Spec 100 Classification Module

Classifies maintenance reports according to ATA Spec 100 chapter standards.
Uses keyword matching and pattern recognition to identify the appropriate ATA chapter.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ATAClassification:
    """Result of ATA classification"""
    chapter: str
    chapter_name: str
    confidence: float
    matched_keywords: List[str]


class ATAClassifier:
    """
    Classifies maintenance reports according to ATA Spec 100 standards.
    
    Uses a combination of keyword matching and pattern recognition to determine
    the most appropriate ATA chapter for a given maintenance report.
    """
    
    # ATA Spec 100 Chapter Mapping
    ATA_CHAPTERS = {
        '05': 'Time Limits/Maintenance Checks',
        '06': 'Dimensions and Areas',
        '07': 'Lifting and Shoring',
        '08': 'Leveling and Weighing',
        '09': 'Towing and Taxiing',
        '10': 'Parking, Mooring, Storage and Return to Service',
        '11': 'Placards and Markings',
        '12': 'Servicing',
        '20': 'Standard Practices - Airframe',
        '21': 'Air Conditioning',
        '22': 'Auto Flight',
        '23': 'Communications',
        '24': 'Electrical Power',
        '25': 'Equipment/Furnishings',
        '26': 'Fire Protection',
        '27': 'Flight Controls',
        '28': 'Fuel',
        '29': 'Hydraulic Power',
        '30': 'Ice and Rain Protection',
        '31': 'Indicating/Recording Systems',
        '32': 'Landing Gear',
        '33': 'Lights',
        '34': 'Navigation',
        '35': 'Oxygen',
        '36': 'Pneumatic',
        '49': 'Airborne Auxiliary Power',
        '51': 'Standard Practices and Structures - General',
        '52': 'Doors',
        '53': 'Fuselage',
        '54': 'Nacelles/Pylons',
        '55': 'Stabilizers',
        '56': 'Windows',
        '57': 'Wings',
        '61': 'Propellers/Propulsors',
        '71': 'Power Plant - General',
        '72': 'Engine - Turbine/Turbo Prop',
        '73': 'Engine Fuel and Control',
        '74': 'Ignition',
        '75': 'Air',
        '76': 'Engine Controls',
        '77': 'Engine Indicating',
        '78': 'Exhaust',
        '79': 'Oil',
        '80': 'Starting'
    }
    
    # Keywords for each ATA chapter
    ATA_KEYWORDS = {
        '21': ['air conditioning', 'cooling', 'heating', 'temperature', 'hvac', 'conditioner', 'cabin temperature'],
        '24': ['electrical', 'power', 'battery', 'generator', 'wiring', 'connector', 'circuit', 'voltage'],
        '25': ['seat', 'galley', 'lavatory', 'cabin', 'interior', 'furnishing', 'equipment'],
        '26': ['fire', 'smoke', 'extinguisher', 'detector', 'suppression', 'fire protection'],
        '27': ['flight control', 'aileron', 'elevator', 'rudder', 'spoiler', 'trim', 'control surface'],
        '28': ['fuel', 'tank', 'pump', 'line', 'valve', 'quantity', 'fuel system'],
        '29': ['hydraulic', 'pressure', 'reservoir', 'actuator', 'pump', 'fluid', 'hydraulics'],
        '30': ['ice', 'rain', 'deicing', 'anti-ice', 'pitot', 'static', 'ice protection'],
        '31': ['instrument', 'indicator', 'display', 'gauge', 'warning', 'caution', 'alert'],
        '32': ['landing gear', 'gear', 'wheel', 'brake', 'tire', 'strut', 'nose gear', 'main gear'],
        '33': ['light', 'lighting', 'beacon', 'strobe', 'navigation light', 'landing light'],
        '34': ['navigation', 'gps', 'compass', 'radio', 'antenna', 'vor', 'ils'],
        '35': ['oxygen', 'mask', 'bottle', 'regulator', 'oxygen system'],
        '36': ['pneumatic', 'air', 'bleed', 'pressure', 'valve', 'duct'],
        '49': ['apu', 'auxiliary power', 'generator', 'bleed air'],
        '51': ['structure', 'frame', 'bulkhead', 'stringer', 'repair', 'corrosion', 'crack'],
        '52': ['door', 'hatch', 'access panel', 'cargo door', 'passenger door'],
        '53': ['fuselage', 'skin', 'panel', 'window', 'frame', 'structure'],
        '54': ['nacelle', 'pylon', 'engine mount', 'cowling'],
        '55': ['stabilizer', 'horizontal stabilizer', 'vertical stabilizer', 'fin'],
        '56': ['window', 'windshield', 'glass', 'seal'],
        '57': ['wing', 'winglet', 'flap', 'slat', 'wing box'],
        '72': ['engine', 'turbine', 'compressor', 'combustor', 'nozzle'],
        '73': ['fuel control', 'fuel metering', 'throttle', 'fuel pump'],
        '76': ['engine control', 'fadec', 'eec', 'thrust'],
        '79': ['oil', 'lubrication', 'filter', 'cooler', 'oil system']
    }
    
    # SRM (Structural Repair Manual) references for structural repairs
    SRM_PATTERNS = [
        r'srm\s*(\d{2}-\d{2}-\d{2})',
        r'per\s+srm\s*(\d{2}-\d{2}-\d{2})',
        r'area\s+within\s+limits\s+per\s+srm\s*(\d{2}-\d{2}-\d{2})'
    ]
    
    def __init__(self):
        """Initialize the ATA classifier with compiled regex patterns"""
        self.srm_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.SRM_PATTERNS]
    
    def classify(self, report_text: str) -> ATAClassification:
        """
        Classify a maintenance report according to ATA Spec 100 standards.
        
        Args:
            report_text: The maintenance report text to classify
            
        Returns:
            ATAClassification object with chapter, confidence, and matched keywords
        """
        if not report_text or not report_text.strip():
            return ATAClassification('00', 'Unknown', 0.0, [])
        
        text_lower = report_text.lower()
        chapter_scores = {}
        matched_keywords_by_chapter = {}
        
        # Check for SRM references first (these are usually structural - chapter 51)
        for regex in self.srm_regex:
            if regex.search(text_lower):
                chapter_scores['51'] = chapter_scores.get('51', 0) + 2.0
                matched_keywords_by_chapter.setdefault('51', []).append('srm reference')
        
        # Score each chapter based on keyword matches
        for chapter, keywords in self.ATA_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                # Count occurrences of each keyword
                count = text_lower.count(keyword.lower())
                if count > 0:
                    score += count
                    matched_keywords.append(keyword)
            
            if score > 0:
                chapter_scores[chapter] = score
                matched_keywords_by_chapter[chapter] = matched_keywords
        
        # Handle special cases based on context
        chapter_scores, matched_keywords_by_chapter = self._apply_contextual_rules(
            text_lower, chapter_scores, matched_keywords_by_chapter
        )
        
        # Find the chapter with the highest score
        if not chapter_scores:
            return ATAClassification('00', 'Unknown', 0.0, [])
        
        best_chapter = max(chapter_scores, key=chapter_scores.get)
        confidence = min(chapter_scores[best_chapter] / 10.0, 1.0)  # Normalize to 0-1
        
        return ATAClassification(
            chapter=best_chapter,
            chapter_name=self.ATA_CHAPTERS.get(best_chapter, 'Unknown'),
            confidence=confidence,
            matched_keywords=matched_keywords_by_chapter.get(best_chapter, [])
        )
    
    def _apply_contextual_rules(self, text: str, scores: Dict[str, float], 
                              keywords: Dict[str, List[str]]) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
        """
        Apply contextual rules to improve classification accuracy.
        
        Args:
            text: Lowercase report text
            scores: Current chapter scores
            keywords: Matched keywords by chapter
            
        Returns:
            Updated scores and keywords dictionaries
        """
        # Corrosion mentions usually indicate structural work (Chapter 51)
        if 'corrosion' in text:
            scores['51'] = scores.get('51', 0) + 3.0
            keywords.setdefault('51', []).append('corrosion')
        
        # Crack mentions usually indicate structural work (Chapter 51)  
        if 'crack' in text:
            scores['51'] = scores.get('51', 0) + 3.0
            keywords.setdefault('51', []).append('crack')
        
        # Specific part mentions
        if 'spoiler' in text:
            scores['27'] = scores.get('27', 0) + 2.0
            keywords.setdefault('27', []).append('spoiler')
        
        if 'actuator' in text and 'gear' in text:
            scores['32'] = scores.get('32', 0) + 2.0
            keywords.setdefault('32', []).append('gear actuator')
        
        if 'bonding strap' in text:
            scores['24'] = scores.get('24', 0) + 2.0
            keywords.setdefault('24', []).append('bonding strap')
        
        # Emergency equipment
        if 'emergency' in text and 'exit' in text:
            scores['25'] = scores.get('25', 0) + 2.0
            keywords.setdefault('25', []).append('emergency exit')
        
        # Telescoping duct (usually pneumatic system)
        if 'telescoping duct' in text:
            scores['36'] = scores.get('36', 0) + 2.0
            keywords.setdefault('36', []).append('telescoping duct')
        
        return scores, keywords
    
    def get_chapter_info(self, chapter: str) -> Optional[str]:
        """
        Get the name of an ATA chapter.
        
        Args:
            chapter: ATA chapter number as string
            
        Returns:
            Chapter name or None if not found
        """
        return self.ATA_CHAPTERS.get(chapter)
    
    def list_chapters(self) -> Dict[str, str]:
        """
        Get all ATA chapters and their names.
        
        Returns:
            Dictionary of chapter numbers to chapter names
        """
        return self.ATA_CHAPTERS.copy()