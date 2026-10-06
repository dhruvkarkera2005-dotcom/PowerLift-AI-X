import pytest
from pydantic import ValidationError

from powerlift_ai_x.models import SourceRecord


def test_valid_source_record():
    source = SourceRecord(
        source_id="SRC001",
        federation="Example Federation",
        competition="Example Nationals",
        year=2026,
        document_type="RESULTS_PDF",
        source_location="data/raw/example.pdf",
    )

    assert source.source_id == "SRC001"
    assert source.federation == "Example Federation"
    assert source.competition == "Example Nationals"
    assert source.year == 2026
    assert source.document_type == "RESULTS_PDF"
    assert source.extraction_status == "PENDING"
    assert source.parser_status == "PENDING"
    assert source.validation_status == "PENDING"


def test_source_id_is_required():
    with pytest.raises(ValidationError):
        SourceRecord(
            source_id="",
            document_type="RESULTS_PDF",
            source_location="data/raw/example.pdf",
        )


def test_document_type_is_required():
    with pytest.raises(ValidationError):
        SourceRecord(
            source_id="SRC002",
            document_type="",
            source_location="data/raw/example.pdf",
        )
def test_invalid_document_type_is_rejected():
    with pytest.raises(ValidationError):
        SourceRecord(
            source_id="SRC003",
            document_type="NOT_A_REAL_DOCUMENT_TYPE",
            source_location="data/raw/example.pdf",
        )