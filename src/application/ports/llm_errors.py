class LLMError(Exception):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMTransportError(LLMError):
    pass


class LLMResponseShapeError(LLMError):
    pass
