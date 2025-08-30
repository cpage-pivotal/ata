#!/usr/bin/env python3
"""
Test script for the Boeing Maintenance Report Classification System.

Tests the ATA, iSpec, and defect type classifiers using sample maintenance reports.
"""

import sys
import traceback
from typing import Dict, List, Any

# Add the app directory to the path
sys.path.insert(0, '.')

from app.classification import ClassifierService
from test_data_reports import ALL_TEST_REPORTS


def test_individual_classifiers():
    """Test each classifier individually"""
    print("=" * 60)
    print("TESTING INDIVIDUAL CLASSIFIERS")
    print("=" * 60)
    
    try:
        from app.classification.ata_classifier import ATAClassifier
        from app.classification.ispec_classifier import ISpecClassifier  
        from app.classification.type_classifier import DefectTypeClassifier
        
        ata = ATAClassifier()
        ispec = ISpecClassifier()
        defect = DefectTypeClassifier()
        
        test_text = "Found corrosion on wing structure, replaced cracked hydraulic actuator"
        
        print(f"\nTest text: '{test_text}'\n")
        
        # Test ATA Classifier
        ata_result = ata.classify(test_text)
        print(f"ATA Classification:")
        print(f"  Chapter: {ata_result.chapter} - {ata_result.chapter_name}")
        print(f"  Confidence: {ata_result.confidence:.3f}")
        print(f"  Keywords: {ata_result.matched_keywords}")
        
        # Test iSpec Classifier
        ispec_result = ispec.classify(test_text)
        print(f"\niSpec Classification:")
        print(f"  Part Categories: {ispec_result.part_categories}")
        print(f"  Identified Parts: {ispec_result.identified_parts}")
        print(f"  Confidence: {ispec_result.confidence:.3f}")
        print(f"  Part Numbers: {ispec_result.part_numbers}")
        
        # Test Defect Type Classifier
        defect_result = defect.classify(test_text)
        print(f"\nDefect Type Classification:")
        print(f"  Defect Types: {defect_result.defect_types}")
        print(f"  Maintenance Actions: {defect_result.maintenance_actions}")
        print(f"  Severity: {defect_result.severity.value}")
        print(f"  Safety Critical: {defect_result.safety_critical}")
        print(f"  Confidence: {defect_result.confidence:.3f}")
        
        return True
        
    except Exception as e:
        print(f"Individual classifier test failed: {e}")
        traceback.print_exc()
        return False


def test_comprehensive_classification():
    """Test the comprehensive classification service"""
    print("\n" + "=" * 60)
    print("TESTING COMPREHENSIVE CLASSIFICATION SERVICE")
    print("=" * 60)
    
    try:
        service = ClassifierService()
        
        # Test service health
        health = service.get_health_status()
        print(f"\nService Health: {health['status']}")
        print(f"Test Results: {health.get('test_results', 'N/A')}")
        
        if health['status'] != 'healthy':
            print("Service is not healthy, skipping comprehensive tests")
            return False
            
        return True
        
    except Exception as e:
        print(f"Comprehensive classification test setup failed: {e}")
        traceback.print_exc()
        return False


def test_sample_reports(limit: int = 5):
    """Test classification on sample maintenance reports"""
    print("\n" + "=" * 60)
    print("TESTING SAMPLE MAINTENANCE REPORTS")
    print("=" * 60)
    
    try:
        service = ClassifierService()
        
        test_reports = ALL_TEST_REPORTS[:limit]
        results = []
        
        for i, report_data in enumerate(test_reports, 1):
            print(f"\n--- Test Report {i}/{len(test_reports)} (ID: {report_data['id']}) ---")
            print(f"Text: {report_data['report_text'][:100]}...")
            
            # Classify the report
            classification = service.classify_report(report_data['report_text'])
            
            # Get summary
            summary = service.get_classification_summary(classification)
            
            print(f"Results:")
            print(f"  ATA Chapter: {summary['ata_chapter']} - {summary['ata_chapter_name']}")
            print(f"  Defect Types: {summary['defect_types']}")
            print(f"  Maintenance Actions: {summary['maintenance_actions']}")
            print(f"  Parts Identified: {summary['identified_parts']}")
            print(f"  Severity: {summary['severity']}")
            print(f"  Overall Confidence: {summary['overall_confidence']}")
            
            if summary['processing_notes']:
                print(f"  Processing Notes: {summary['processing_notes']}")
            
            # Compare with expected results if available
            expected = report_data.get('expected_classification', {})
            if expected:
                print(f"\nExpected vs Actual:")
                print(f"  ATA Chapter: {expected.get('ata_chapter', 'N/A')} vs {summary['ata_chapter']}")
                if expected.get('ata_chapter') == summary['ata_chapter']:
                    print("    ✓ ATA classification matches")
                else:
                    print("    ✗ ATA classification differs")
            
            results.append({
                'report_id': report_data['id'],
                'classification': summary,
                'expected': expected
            })
            
        print(f"\n--- Summary ---")
        print(f"Processed {len(results)} reports successfully")
        
        return results
        
    except Exception as e:
        print(f"Sample reports test failed: {e}")
        traceback.print_exc()
        return []


def test_error_conditions():
    """Test error handling and edge cases"""
    print("\n" + "=" * 60)
    print("TESTING ERROR CONDITIONS")
    print("=" * 60)
    
    try:
        service = ClassifierService()
        
        # Test empty report
        empty_result = service.classify_report("")
        print(f"Empty report classification:")
        print(f"  ATA Chapter: {empty_result.ata.chapter}")
        print(f"  Overall Confidence: {empty_result.overall_confidence}")
        print(f"  Processing Notes: {empty_result.processing_notes}")
        
        # Test None input
        none_result = service.classify_report(None)
        print(f"\nNone input classification:")
        print(f"  ATA Chapter: {none_result.ata.chapter}")
        print(f"  Processing Notes: {none_result.processing_notes}")
        
        # Test very long report
        long_text = "This is a test report. " * 1000
        long_result = service.classify_report(long_text)
        print(f"\nVery long report classification:")
        print(f"  ATA Chapter: {long_result.ata.chapter}")
        print(f"  Overall Confidence: {long_result.overall_confidence}")
        
        print("\nError condition tests completed successfully")
        return True
        
    except Exception as e:
        print(f"Error condition tests failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all classification tests"""
    print("Boeing Maintenance Report Classification System - Test Suite")
    print("=" * 60)
    
    test_results = {
        'individual_classifiers': False,
        'comprehensive_service': False,
        'sample_reports': False,
        'error_conditions': False
    }
    
    # Run individual tests
    test_results['individual_classifiers'] = test_individual_classifiers()
    test_results['comprehensive_service'] = test_comprehensive_classification()
    
    if test_results['comprehensive_service']:
        # Only run these if the service is working
        sample_results = test_sample_reports(limit=8)  # Test first 8 reports
        test_results['sample_reports'] = len(sample_results) > 0
        test_results['error_conditions'] = test_error_conditions()
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in test_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(test_results.values())
    print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Classification system is ready for integration!")
    else:
        print("\n⚠️  Please review failed tests before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)