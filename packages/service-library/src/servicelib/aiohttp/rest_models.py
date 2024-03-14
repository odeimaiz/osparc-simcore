from dataclasses import dataclass, field


@dataclass
class LogMessage:
    message: str
    level: str = "INFO"
    logger: str = "user"


@dataclass
class ErrorDetail:
    code: str
    message: str
    resource: str | None
    field: str | None

    @classmethod
    def from_exception(cls, err: BaseException):
        return cls(
            code=err.__class__.__name__, message=str(err), resource=None, field=None
        )


@dataclass
class ResponseErrorBody:
    message: str
    status: int
    # Optional
    logs: list[LogMessage] = field(default_factory=list)
    errors: list[ErrorDetail] = field(default_factory=list)
