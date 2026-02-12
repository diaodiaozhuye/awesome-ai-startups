"""Product validation — schema and referential integrity."""

from scrapers.validation.integrity_validator import IntegrityError, IntegrityValidator
from scrapers.validation.schema_validator import (
    ProductSchemaValidator,
    ValidationResult,
)

__all__ = [
    "IntegrityError",
    "IntegrityValidator",
    "ProductSchemaValidator",
    "ValidationResult",
]
