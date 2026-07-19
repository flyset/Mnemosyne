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


class DisallowedMemoryContent(MemoryDomainError):
    code = "disallowed_content"


class MutationDisabled(MemoryDomainError):
    code = "mutation_disabled"
