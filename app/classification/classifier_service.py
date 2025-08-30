"""
Classifier Service - Orchestration Layer

Combines ATA, iSpec 2200, and defect type classification to provide 
comprehensive maintenance report classification.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

from .ata_classifier import ATAClassifier, ATAClassification
from .ispec_classifier import ISpecClassifier, ISpecClassification
from .type_classifier import DefectTypeClassifier, DefectClassification


@dataclass
class ComprehensiveClassification:
    """Combined result from all classification systems"""
    ata: ATAClassification
    ispec: ISpecClassification
    defect: DefectClassification
    overall_confidence: float
    processing_notes: list[str]


class ClassifierService:
    """
    Main classification service that orchestrates all classification systems.
    
    Provides a single interface for classifying maintenance reports using:
    - ATA Spec 100 chapter classification
    - iSpec 2200 part identification
    - Defect type and severity classification
    """
    
    def __init__(self):
        """Initialize all classifier components"""
        self.logger = logging.getLogger(__name__)
        
        try:
            self.ata_classifier = ATAClassifier()
            self.ispec_classifier = ISpecClassifier()
            self.defect_classifier = DefectTypeClassifier()
            self.logger.info("All classifiers initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize classifiers: {e}")
            raise
    
    def classify_report(self, report_text: str, report_metadata: Optional[Dict] = None) -> ComprehensiveClassification:
        """
        Perform comprehensive classification of a maintenance report.
        
        Args:
            report_text: The maintenance report text to classify
            report_metadata: Optional metadata (aircraft type, date, etc.)
            
        Returns:
            ComprehensiveClassification with results from all classification systems
        """
        if not report_text or not report_text.strip():
            return self._create_empty_classification("Empty or invalid report text")
        
        processing_notes = []
        
        try:
            # ATA Classification
            ata_result = self.ata_classifier.classify(report_text)
            self.logger.debug(f"ATA classification: {ata_result.chapter} - {ata_result.chapter_name}")
            
            # iSpec 2200 Classification
            ispec_result = self.ispec_classifier.classify(report_text)
            self.logger.debug(f"iSpec classification: {len(ispec_result.identified_parts)} parts identified")
            
            # Defect Type Classification
            defect_result = self.defect_classifier.classify(report_text)
            self.logger.debug(f"Defect classification: {defect_result.defect_types}")
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(ata_result, ispec_result, defect_result)
            
            # Apply cross-validation rules
            self._cross_validate_classifications(ata_result, ispec_result, defect_result, processing_notes)
            
            # Add metadata-based enhancements if available
            if report_metadata:
                self._apply_metadata_enhancements(ata_result, ispec_result, defect_result, 
                                                report_metadata, processing_notes)
            
            return ComprehensiveClassification(
                ata=ata_result,
                ispec=ispec_result,
                defect=defect_result,
                overall_confidence=overall_confidence,
                processing_notes=processing_notes
            )
            
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            processing_notes.append(f"Classification error: {str(e)}")
            return self._create_empty_classification("Classification processing error")
    
    def _create_empty_classification(self, reason: str) -> ComprehensiveClassification:
        """Create an empty classification result with error information"""
        from .ata_classifier import ATAClassification
        from .ispec_classifier import ISpecClassification
        from .type_classifier import DefectClassification, DefectSeverity
        
        return ComprehensiveClassification(
            ata=ATAClassification('00', 'Unknown', 0.0, []),
            ispec=ISpecClassification([], [], 0.0, []),
            defect=DefectClassification([], [], DefectSeverity.MINOR, False, 0.0, []),
            overall_confidence=0.0,
            processing_notes=[reason]
        )
    
    def _calculate_overall_confidence(self, ata: ATAClassification, 
                                    ispec: ISpecClassification, 
                                    defect: DefectClassification) -> float:
        """Calculate overall confidence score based on individual classifier results"""
        # Weighted average of individual confidences
        weights = {
            'ata': 0.4,      # ATA classification is most important
            'ispec': 0.3,    # Part identification is very important
            'defect': 0.3    # Defect classification is important
        }
        
        overall = (
            ata.confidence * weights['ata'] +
            ispec.confidence * weights['ispec'] +
            defect.confidence * weights['defect']
        )
        
        return min(overall, 1.0)
    
    def _cross_validate_classifications(self, ata: ATAClassification, 
                                      ispec: ISpecClassification, 
                                      defect: DefectClassification,
                                      notes: list) -> None:
        """Apply cross-validation rules between different classification results"""
        
        # Validate ATA chapter consistency with parts
        if ata.chapter == '32' and 'landing gear' not in ' '.join(ispec.identified_parts).lower():
            if any('gear' in part.lower() for part in ispec.identified_parts):
                notes.append("ATA 32 (Landing Gear) consistent with gear-related parts")
            else:
                notes.append("ATA 32 classification but no landing gear parts identified")
        
        if ata.chapter == '27' and 'spoiler' in ' '.join(ispec.identified_parts).lower():
            notes.append("ATA 27 (Flight Controls) consistent with spoiler parts")
        
        # Validate structural repairs (ATA 51) with corrosion/crack defects
        if ata.chapter == '51' and ('corrosion' in defect.defect_types or 'crack' in defect.defect_types):
            notes.append("ATA 51 (Structures) consistent with structural defect types")
        
        # Check for electrical work indicators
        if '24' in ata.chapter and 'electrical' in ispec.part_categories:
            notes.append("ATA 24 (Electrical) consistent with electrical parts")
        
        # Validate safety-critical flags
        if defect.safety_critical and ata.chapter in ['27', '32', '72']:  # Flight controls, landing gear, engines
            notes.append("Safety-critical defect in critical system is appropriately flagged")
    
    def _apply_metadata_enhancements(self, ata: ATAClassification, 
                                    ispec: ISpecClassification, 
                                    defect: DefectClassification,
                                    metadata: Dict, notes: list) -> None:
        """Apply enhancements based on report metadata"""
        
        aircraft_type = metadata.get('aircraft_type', '').lower()
        report_date = metadata.get('report_date')
        
        # Aircraft-specific part validation
        if aircraft_type:
            if '737' in aircraft_type and 'winglet' in ispec.identified_parts:
                notes.append(f"Winglet parts consistent with {aircraft_type} aircraft")
            
            notes.append(f"Classification applied to {aircraft_type} maintenance report")
        
        # Time-based patterns (could be extended for fleet management)
        if report_date:
            notes.append(f"Report classified for maintenance performed on {report_date}")
    
    def get_classification_summary(self, classification: ComprehensiveClassification) -> Dict[str, Any]:
        """
        Generate a summary of the classification results for API responses.
        
        Args:
            classification: The comprehensive classification result
            
        Returns:
            Dictionary summary suitable for JSON serialization
        """
        return {
            'ata_chapter': classification.ata.chapter,
            'ata_chapter_name': classification.ata.chapter_name,
            'defect_types': classification.defect.defect_types,
            'maintenance_actions': classification.defect.maintenance_actions,
            'identified_parts': classification.ispec.identified_parts,
            'part_categories': classification.ispec.part_categories,
            'severity': classification.defect.severity.value,
            'safety_critical': classification.defect.safety_critical,
            'overall_confidence': round(classification.overall_confidence, 3),
            'processing_notes': classification.processing_notes
        }
    
    def to_dict(self, classification: ComprehensiveClassification) -> Dict[str, Any]:
        """Convert classification result to dictionary for storage/serialization"""
        return {
            'ata': asdict(classification.ata),
            'ispec': asdict(classification.ispec), 
            'defect': {
                **asdict(classification.defect),
                'severity': classification.defect.severity.value  # Convert enum to string
            },
            'overall_confidence': classification.overall_confidence,
            'processing_notes': classification.processing_notes
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all classifiers"""
        try:
            # Test each classifier with a simple test case
            test_text = "Found corrosion on wing structure"
            
            ata_test = self.ata_classifier.classify(test_text)
            ispec_test = self.ispec_classifier.classify(test_text)
            defect_test = self.defect_classifier.classify(test_text)
            
            return {
                'status': 'healthy',
                'ata_classifier': 'operational',
                'ispec_classifier': 'operational', 
                'defect_classifier': 'operational',
                'test_results': {
                    'ata_chapter': ata_test.chapter,
                    'parts_identified': len(ispec_test.identified_parts),
                    'defects_found': len(defect_test.defect_types)
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'ata_classifier': 'unknown',
                'ispec_classifier': 'unknown',
                'defect_classifier': 'unknown'
            }