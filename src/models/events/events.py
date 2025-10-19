class Event:
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}


class ErrorEvent(Event):
    pass


class SuccessEvent(Event):
    pass


class BuildingNoNameError(ErrorEvent):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)


class EventPublisher:
    def __init__(self):
        self.events = []
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def publish(self, event: Event):
        self.events.append(event)
        for obs in self.observers:
            obs.add_event(event)

    def log_all(self, logger):
        for event in self.events:
            if isinstance(event, ErrorEvent):
                logger.error(f"Error: {event.message}", extra=event.details)
            elif isinstance(event, SuccessEvent):
                logger.info(f"Success: {event.message}", extra=event.details)
            else:
                logger.info(f"Event: {event.message}", extra=event.details)


# Global publisher instance
# TODO: inject this into the classes that need it instead of a global variable
publisher = EventPublisher()


class EventHandler:
    @staticmethod
    def handle(self, event: Event):
        if isinstance(event, BuildingNoNameError):
            event.details["building_id"] = self.id
