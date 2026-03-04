class DigitalTwinError(Exception): pass
class StateDerivationError(DigitalTwinError): pass
class ForecastingError(DigitalTwinError): pass
class DriftDetectedError(DigitalTwinError): pass
