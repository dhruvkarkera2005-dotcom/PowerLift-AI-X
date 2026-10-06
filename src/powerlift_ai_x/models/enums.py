from enum import StrEnum


class Equipment(StrEnum):
    CLASSIC = "CLASSIC"
    EQUIPPED = "EQUIPPED"
    UNKNOWN = "UNKNOWN"


class DocumentType(StrEnum):
    RESULTS_PDF = "RESULTS_PDF"
    UNKNOWN = "UNKNOWN"


class ProcessingStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVIEW = "REVIEW"