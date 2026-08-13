"""Domain exceptions mapped to explicit analysis statuses by the pipeline."""


class AnalysisError(Exception):
    """Base error for expected analysis failures."""


class InputValidationError(AnalysisError):
    """The source cannot support a Mixing v1 analysis."""


class DecoderError(AnalysisError):
    """The source could not be decoded safely."""


class SeparationError(AnalysisError):
    """Source separation is unavailable or failed applicability checks."""


class ProfileError(AnalysisError):
    """A genre profile is missing, incompatible, or cannot be released."""
