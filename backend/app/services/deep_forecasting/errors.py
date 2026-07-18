class DeepForecastingDisabledError(RuntimeError):
    pass


class DeepDependencyUnavailableError(RuntimeError):
    pass


class DeepModelUnavailableError(ValueError):
    pass


class DeepConfigurationError(ValueError):
    pass


class DeepDatasetNotReadyError(RuntimeError):
    pass


class DeepSequenceValidationError(ValueError):
    pass


class DeepCovariateCoverageError(ValueError):
    pass


class DeepLeakageDetectedError(ValueError):
    pass


class DeepHardwareConfigurationError(ValueError):
    pass


class DeepArtifactStorageError(RuntimeError):
    pass
