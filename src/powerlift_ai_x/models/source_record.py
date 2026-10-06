from typing import Optional

from pydantic import BaseModel, Field

from powerlift_ai_x.models.enums import DocumentType, ProcessingStatus


class SourceRecord(BaseModel):
    """
    Metadata describing one PowerLift-AI-X source document.
    """

    source_id: str = Field(min_length=1)

    federation: Optional[str] = None
    competition: Optional[str] = None
    year: Optional[int] = None

    document_type: DocumentType

    source_location: str = Field(min_length=1)

    extraction_status: ProcessingStatus = ProcessingStatus.PENDING
    parser_status: ProcessingStatus = ProcessingStatus.PENDING
    validation_status: ProcessingStatus = ProcessingStatus.PENDING