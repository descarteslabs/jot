import sys
from os import access

import rollbar

from . import log
from .base import Target
from . import error as jot_error

class RollbarTarget(Target):
    "A target that sends stack traces to rollbar"

    @staticmethod
    def report_unhandled_exceptions(exit_code=9091):
        def hook(exc_type, exc, exc_traceback):
            # report everything except KeyboardInterrupt
            if not issubclass(exc_type, KeyboardInterrupt):
                jot_error("Unhandled Exception", exc)
                rollbar.wait()
            sys.exit(exit_code)

        sys.excepthook = hook

    def __init__(self, access_token=None, environment="development", level=log.NOTHING, **kwargs):
        if rollbar.SETTINGS["access_token"] is None:
            if access_token is None:
                raise RuntimeError("Please supply your access token")
            rollbar.init(access_token, environment, **kwargs)
        elif access_token is not None and access_token != rollbar.SETTINGS["access_token"]:
            raise RuntimeError("Rollbar can only use one access token at a time")

        super().__init__(level)

    def log(self, level, message, tags, span=None):
        request = tags.pop("request", None)
        level_name = log.name(level)
        rollbar.report_message(message, level_name, request, tags)

    def error(self, message, exception, tags, span=None):
        exc_info = (type(exception), exception, exception.__traceback__)
        level = "warning" if isinstance(exception, Warning) else "error"
        request = tags.pop("request", None)
        tags["message"] = message
        rollbar.report_exc_info(exc_info, request, tags, level=level)
