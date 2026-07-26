from enum import StrEnum


class ContentRefusalReason(StrEnum):
    PRIVATE_KEY_SHAPE = "private_key_shape"
    CREDENTIAL_SHAPE = "credential_shape"
    COMPACT_TOKEN_SHAPE = "compact_token_shape"
    PAYMENT_CARD_SHAPE = "payment_card_shape"
    GOVERNMENT_IDENTIFIER_SHAPE = "government_identifier_shape"


class MemoryValidationError(ValueError):
    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message


class MemoryDomainError(Exception):
    code = "memory_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)


class UnsafeMemoryPath(MemoryDomainError):
    code = "unsafe_path"


class MemorySourceUnavailable(MemoryDomainError):
    code = "storage_unavailable"


class CandidateLimitExceeded(MemoryDomainError):
    code = "candidate_limit_exceeded"


class InvalidMemoryListCursor(MemoryDomainError):
    code = "invalid_cursor"


class StaleMemoryListCursor(MemoryDomainError):
    code = "stale_cursor"


class MemoryNotFound(MemoryDomainError):
    code = "not_found"


class AmbiguousMemoryReference(MemoryDomainError):
    code = "ambiguous_reference"


class RevisionConflict(MemoryDomainError):
    code = "revision_conflict"


class WriteConflict(MemoryDomainError):
    code = "write_conflict"


class MemoryNotArchived(MemoryDomainError):
    code = "not_archived"


class DeletionOutcomeUncertain(MemoryDomainError):
    code = "deletion_outcome_uncertain"


class ReplacementOutcomeUncertain(MemoryDomainError):
    code = "replacement_outcome_uncertain"


class DisallowedMemoryContent(MemoryDomainError):
    code = "disallowed_content"

    def __init__(self, field: str, reason: ContentRefusalReason) -> None:
        super().__init__()
        self.field = field
        self.reason = reason


class MutationDisabled(MemoryDomainError):
    code = "mutation_disabled"
