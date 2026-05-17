from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError

from brave.exceptions import BraveError


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)
MAX_VALIDATION_ERRORS = 10
MAX_PAYLOAD_KEYS = 20


class BraveResponseValidationError(BraveError):
    """Raised when a Brave API response cannot be parsed into a response model."""

    def __init__(
        self,
        model: Type[BaseModel],
        validation_error: ValidationError,
        *,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        response_type: Optional[str] = None,
        payload_keys: Iterable[str] = (),
        payload_key_count: int = 0,
    ) -> None:
        self.model = model
        self.validation_error = validation_error
        self.validation_errors = validation_error.errors(include_input=False)[:MAX_VALIDATION_ERRORS]
        self.context = {
            "model": model.__name__,
            "endpoint": endpoint,
            "status_code": status_code,
            "url": url,
            "response_type": response_type,
            "payload_keys": tuple(payload_keys),
            "payload_key_count": payload_key_count,
        }
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        error_count = len(self.validation_errors)
        first_error = self.validation_errors[0] if self.validation_errors else {}
        location = ".".join(str(part) for part in first_error.get("loc", ())) or "<response>"
        detail = first_error.get("msg", "validation failed")
        return (
            f"Could not parse Brave response as {self.model.__name__}: "
            f"{error_count} validation error(s); first at {location}: {detail}; context={self.context}"
        )


def parse_response(
    model: Type[ResponseModelT],
    payload: object,
    *,
    endpoint: Optional[str] = None,
    status_code: Optional[int] = None,
    url: Optional[str] = None,
) -> ResponseModelT:
    """Validate a Brave API payload and raise a contextual package error on failure."""

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        context = _response_context(payload)
        raise BraveResponseValidationError(
            model,
            exc,
            endpoint=endpoint,
            status_code=status_code,
            url=url,
            response_type=context["response_type"],
            payload_keys=context["payload_keys"],
            payload_key_count=context["payload_key_count"],
        ) from exc


def _response_context(payload: object) -> Dict[str, object]:
    if isinstance(payload, dict):
        keys = tuple(str(key) for key in payload.keys())
        return {
            "response_type": payload.get("type"),
            "payload_keys": keys[:MAX_PAYLOAD_KEYS],
            "payload_key_count": len(keys),
        }

    return {
        "response_type": None,
        "payload_keys": (),
        "payload_key_count": 0,
    }
