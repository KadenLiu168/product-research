"""Small shared DataForSEO configuration, send, and envelope boundary."""

import base64
import inspect
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Union

from product_research_providers import ProviderConfigurationError


DATAFORSEO_BASE_URL = "https://api.dataforseo.com"


def _non_empty_string(value, field_name):
    if type(value) is not str:
        raise ProviderConfigurationError("invalid DataForSEO configuration")
    if value == "":
        raise ProviderConfigurationError("invalid DataForSEO configuration")
    return value


@dataclass(frozen=True, repr=False)
class DataForSEOConfiguration:
    _login: str
    _password: str

    def __init__(self, login, password):
        object.__setattr__(self, "_login", _non_empty_string(login, "login"))
        object.__setattr__(self, "_password", _non_empty_string(password, "password"))

    @classmethod
    def from_environment(cls, environ: Optional[Mapping[str, str]] = None):
        values = os.environ if environ is None else environ
        try:
            login = values["DATAFORSEO_LOGIN"]
            password = values["DATAFORSEO_PASSWORD"]
        except (KeyError, TypeError):
            raise ProviderConfigurationError("invalid DataForSEO configuration") from None
        return cls(login, password)

    def __repr__(self):
        return "DataForSEOConfiguration(login=<redacted>, password=<redacted>)"

    def __str__(self):
        return self.__repr__()


@dataclass(frozen=True)
class DataForSEOWireRequest:
    endpoint: str
    payload: object

    def __post_init__(self):
        if type(self.endpoint) is not str or not self.endpoint.startswith("/v3/"):
            raise ValueError("invalid DataForSEO endpoint")
        try:
            serialized = json.dumps(self.payload, ensure_ascii=False, allow_nan=False)
            copied = json.loads(serialized)
        except (TypeError, ValueError):
            raise ValueError("invalid DataForSEO payload") from None
        object.__setattr__(self, "payload", copied)

    def __repr__(self):
        return f"DataForSEOWireRequest(endpoint={self.endpoint!r}, payload={self.payload!r})"


@dataclass(frozen=True)
class DataForSEOHTTPResponse:
    status_code: int
    body: Union[str, bytes]

    def __post_init__(self):
        if type(self.status_code) is not int or self.status_code < 100:
            raise TypeError("status_code must be an HTTP status integer")
        if type(self.body) not in (str, bytes):
            raise TypeError("body must be text or bytes")


DataForSEOHttpResponse = DataForSEOHTTPResponse


class DataForSEOProtocolError(ValueError):
    pass


def _protocol_mapping(value, field_name):
    if type(value) is not dict:
        raise DataForSEOProtocolError(f"malformed DataForSEO {field_name}")
    return value


def _protocol_string(value, field_name, allow_none=False):
    if value is None and allow_none:
        return
    if type(value) is not str or (not allow_none and not value):
        raise DataForSEOProtocolError(f"malformed DataForSEO {field_name}")


def _protocol_int(value, field_name):
    if type(value) is not int:
        raise DataForSEOProtocolError(f"malformed DataForSEO {field_name}")


def _protocol_number(value, field_name):
    if type(value) not in (int, float) or type(value) is bool:
        raise DataForSEOProtocolError(f"malformed DataForSEO {field_name}")


def _validate_protocol_task(task, expected_endpoint, require_result):
    _protocol_mapping(task, "task")
    required = ("id", "status_code", "status_message", "time", "cost", "result_count", "path", "data")
    if require_result:
        required += ("result",)
    if any(key not in task for key in required):
        raise DataForSEOProtocolError("incomplete DataForSEO task")
    _protocol_string(task["id"], "task id")
    _protocol_int(task["status_code"], "task status")
    _protocol_string(task["status_message"], "task status message")
    _protocol_string(task["time"], "task time")
    _protocol_number(task["cost"], "task cost")
    _protocol_int(task["result_count"], "task result count")
    if task["result_count"] < 0:
        raise DataForSEOProtocolError("impossible task result count")
    if type(task["path"]) is not list or not task["path"] or any(type(item) is not str or not item for item in task["path"]):
        raise DataForSEOProtocolError("malformed task path")
    if "/".join(task["path"]) != expected_endpoint.strip("/"):
        raise DataForSEOProtocolError("unexpected DataForSEO task path")
    if type(task["data"]) not in (dict, list):
        raise DataForSEOProtocolError("malformed task data")
    if "result" in task:
        if type(task["result"]) is not list or task["result_count"] != len(task["result"]):
            raise DataForSEOProtocolError("malformed task result")
    elif task["result_count"] != 0:
        raise DataForSEOProtocolError("malformed task result")


def parse_live_response(response: DataForSEOHTTPResponse, expected_endpoint: str):
    """Return ``("success", task-or-none)`` or ``("failed", None)``.

    This shared parser owns only the HTTP/envelope/task protocol. Operation
    result validation remains in the SEARCH module.
    """

    if type(response) is not DataForSEOHTTPResponse:
        raise DataForSEOProtocolError("malformed DataForSEO HTTP response")
    if response.status_code < 200 or response.status_code >= 300:
        return "failed", None
    try:
        text = response.body.decode("utf-8") if type(response.body) is bytes else response.body
        envelope = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DataForSEOProtocolError("malformed DataForSEO JSON") from None
    _protocol_mapping(envelope, "envelope")
    required = ("version", "status_code", "status_message", "time", "cost", "tasks_count", "tasks_error", "tasks")
    if any(key not in envelope for key in required):
        raise DataForSEOProtocolError("incomplete DataForSEO envelope")
    _protocol_string(envelope["version"], "version")
    _protocol_int(envelope["status_code"], "status_code")
    _protocol_string(envelope["status_message"], "status_message")
    _protocol_string(envelope["time"], "time")
    _protocol_number(envelope["cost"], "cost")
    _protocol_int(envelope["tasks_count"], "tasks_count")
    _protocol_int(envelope["tasks_error"], "tasks_error")
    if envelope["tasks_count"] < 0 or envelope["tasks_error"] < 0 or envelope["tasks_error"] > envelope["tasks_count"]:
        raise DataForSEOProtocolError("impossible DataForSEO task count")
    if type(envelope["tasks"]) is not list or envelope["tasks_count"] != len(envelope["tasks"]):
        raise DataForSEOProtocolError("malformed DataForSEO tasks")
    status = envelope["status_code"]
    if status == 40102:
        if not envelope["tasks"]:
            return "success", None
        if len(envelope["tasks"]) != 1:
            raise DataForSEOProtocolError("impossible DataForSEO task count")
        task = envelope["tasks"][0]
        _validate_protocol_task(task, expected_endpoint, require_result=False)
        if task["result_count"] != 0:
            raise DataForSEOProtocolError("impossible no-result task")
        return "success", None
    if status != 20000:
        if len(envelope["tasks"]) > 1:
            raise DataForSEOProtocolError("one Live request must contain at most one task")
        for task in envelope["tasks"]:
            _validate_protocol_task(task, expected_endpoint, require_result=False)
        return "failed", None
    if envelope["tasks_count"] != 1:
        raise DataForSEOProtocolError("one Live request must contain one task")
    task = envelope["tasks"][0]
    _validate_protocol_task(task, expected_endpoint, require_result=False)
    if task["status_code"] == 40102:
        if task["result_count"] != 0:
            raise DataForSEOProtocolError("impossible no-result task")
        return "success", None
    if task["status_code"] != 20000:
        return "failed", None
    _validate_protocol_task(task, expected_endpoint, require_result=True)
    return "success", task


def _urllib_send(request: DataForSEOWireRequest, headers: Mapping[str, str]):
    body = json.dumps(
        request.payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    http_request = urllib.request.Request(
        DATAFORSEO_BASE_URL + request.endpoint,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    try:
        with urllib.request.urlopen(http_request) as response:
            return DataForSEOHTTPResponse(response.status, response.read())
    except urllib.error.HTTPError as error:
        return DataForSEOHTTPResponse(error.code, error.read())


def _accepts_two_arguments(send: Callable) -> bool:
    try:
        signature = inspect.signature(send)
    except (TypeError, ValueError):
        return True
    parameters = tuple(signature.parameters.values())
    if any(parameter.kind is parameter.VAR_POSITIONAL for parameter in parameters):
        return True
    positional = tuple(
        parameter
        for parameter in parameters
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    )
    return len(positional) >= 2


def authenticated_sender(configuration: DataForSEOConfiguration, send: Optional[Callable] = None):
    """Close credentials over the actual send boundary only."""

    if type(configuration) is not DataForSEOConfiguration:
        raise ProviderConfigurationError("invalid DataForSEO configuration")
    actual_send = _urllib_send if send is None else send
    if not callable(actual_send):
        raise TypeError("send must be callable")
    def send_once(request: DataForSEOWireRequest):
        token = base64.b64encode(
            f"{configuration._login}:{configuration._password}".encode("utf-8")
        ).decode("ascii")
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }
        if _accepts_two_arguments(actual_send):
            return actual_send(request, headers)
        return actual_send(request)

    return send_once
