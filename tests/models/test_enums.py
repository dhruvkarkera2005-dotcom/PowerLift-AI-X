from powerlift_ai_x.models import (
    DocumentType,
    Equipment,
    ProcessingStatus,
)


def test_equipment_values():
    assert Equipment.CLASSIC.value == "CLASSIC"
    assert Equipment.EQUIPPED.value == "EQUIPPED"
    assert Equipment.UNKNOWN.value == "UNKNOWN"


def test_document_type_values():
    assert DocumentType.RESULTS_PDF.value == "RESULTS_PDF"
    assert DocumentType.UNKNOWN.value == "UNKNOWN"


def test_processing_status_values():
    assert ProcessingStatus.PENDING.value == "PENDING"
    assert ProcessingStatus.SUCCESS.value == "SUCCESS"
    assert ProcessingStatus.FAILED.value == "FAILED"
    assert ProcessingStatus.REVIEW.value == "REVIEW"