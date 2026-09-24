"""browser-use chat model adapter for GigaChat API."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, TypeVar, overload

from pydantic import BaseModel

from bench_eval.retry_utils import retry_backoff_seconds

T = TypeVar("T", bound=BaseModel)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _serialize_browser_messages(messages: list[Any]) -> list[Any]:
    """Sync wrapper; use _aserialize_browser_messages when uploads are needed."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Upload path unavailable inside running loop without client async call from sync.
            return _serialize_browser_messages_sync(messages, client=None)
    except RuntimeError:
        pass
    return asyncio.run(_aserialize_browser_messages(messages, client=None))


def _serialize_browser_messages_sync(
    messages: list[Any],
    *,
    client: Any | None,
) -> list[Any]:
    from browser_use.llm.openai.serializer import OpenAIMessageSerializer
    from gigachat.models.chat import Messages, MessagesRole

    role_map = {
        "system": MessagesRole.SYSTEM,
        "user": MessagesRole.USER,
        "assistant": MessagesRole.ASSISTANT,
        "function": MessagesRole.FUNCTION,
    }
    gigachat_messages: list[Messages] = []
    for msg in OpenAIMessageSerializer.serialize_messages(messages):
        role = role_map.get(msg.get("role", "user"), MessagesRole.USER)
        content = msg.get("content")
        text_parts: list[str] = []
        attachments: list[str] = []
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                part_type = str(part.get("type") or "")
                if part_type == "text":
                    text_parts.append(str(part.get("text", "")))
                    continue
                if part_type in {"image_url", "image"}:
                    file_id = part.get("file_id") or part.get("gigachat_file_id")
                    if file_id:
                        attachments.append(str(file_id))
                        continue
                    image_url = part.get("image_url")
                    url = image_url.get("url") if isinstance(image_url, dict) else image_url
                    url = str(url or "")
                    if url.startswith("file://") and client is not None:
                        from pathlib import Path

                        local_path = Path(url.removeprefix("file://"))
                        if local_path.is_file():
                            uploaded = client.upload_file(local_path, purpose="general")
                            attachments.append(str(getattr(uploaded, "id_", None) or uploaded.id))
                            continue
                    text_parts.append("[image omitted: upload via GigaChat file_id or file:// path]")
        else:
            text_parts.append(str(content or ""))
        message_kwargs: dict[str, Any] = {
            "role": role,
            "content": "\n".join(text_parts),
        }
        if attachments:
            message_kwargs["attachments"] = attachments[:1]
        gigachat_messages.append(Messages(**message_kwargs))
    return gigachat_messages


async def _aserialize_browser_messages(
    messages: list[Any],
    *,
    client: Any | None,
) -> list[Any]:
    from browser_use.llm.openai.serializer import OpenAIMessageSerializer
    from gigachat.models.chat import Messages, MessagesRole

    role_map = {
        "system": MessagesRole.SYSTEM,
        "user": MessagesRole.USER,
        "assistant": MessagesRole.ASSISTANT,
        "function": MessagesRole.FUNCTION,
    }
    gigachat_messages: list[Messages] = []
    for msg in OpenAIMessageSerializer.serialize_messages(messages):
        role = role_map.get(msg.get("role", "user"), MessagesRole.USER)
        content = msg.get("content")
        text_parts: list[str] = []
        attachments: list[str] = []
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                part_type = str(part.get("type") or "")
                if part_type == "text":
                    text_parts.append(str(part.get("text", "")))
                    continue
                if part_type in {"image_url", "image"}:
                    file_id = part.get("file_id") or part.get("gigachat_file_id")
                    if file_id:
                        attachments.append(str(file_id))
                        continue
                    image_url = part.get("image_url")
                    url = image_url.get("url") if isinstance(image_url, dict) else image_url
                    url = str(url or "")
                    if url.startswith("file://") and client is not None:
                        from pathlib import Path

                        local_path = Path(url.removeprefix("file://"))
                        if local_path.is_file():
                            uploaded = await client.aupload_file(local_path, purpose="general")
                            attachments.append(str(getattr(uploaded, "id_", None) or uploaded.id))
                            continue
                    text_parts.append("[image omitted: upload via GigaChat file_id or file:// path]")
        else:
            text_parts.append(str(content or ""))
        message_kwargs: dict[str, Any] = {
            "role": role,
            "content": "\n".join(text_parts),
        }
        if attachments:
            message_kwargs["attachments"] = attachments[:1]
        gigachat_messages.append(Messages(**message_kwargs))
    return gigachat_messages


def _extract_completion_text(completion: Any) -> str:
    if not completion.choices:
        raise ValueError("GigaChat response has no choices")
    message = completion.choices[0].message
    content = getattr(message, "content", None)
    if content:
        return str(content)
    raise ValueError("GigaChat response has no assistant text content")


def _extract_usage(completion: Any) -> Any | None:
    from browser_use.llm.views import ChatInvokeUsage

    usage = getattr(completion, "usage", None)
    if usage is None:
        return None
    return ChatInvokeUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        prompt_cached_tokens=None,
        prompt_cache_creation_tokens=None,
        prompt_image_tokens=None,
        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(usage, "total_tokens", 0) or 0,
    )


@dataclass
class ChatGigaChat:
    """GigaChat adapter implementing browser-use BaseChatModel protocol."""

    model: str
    temperature: float | None = 0.2
    max_retries: int = 5
    credentials: str | None = None
    access_token: str | None = None
    base_url: str | None = None
    auth_url: str | None = None
    scope: str | None = None
    user: str | None = None
    password: str | None = None
    timeout: float | None = None
    verify_ssl_certs: bool | None = None
    ca_bundle_file: str | None = None
    cert_file: str | None = None
    key_file: str | None = None
    key_file_password: str | None = None
    _client: Any = field(default=None, init=False, repr=False)

    @property
    def provider(self) -> str:
        return "gigachat"

    @property
    def name(self) -> str:
        return str(self.model)

    def _client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_retries": self.max_retries,
        }
        optional = {
            "credentials": self.credentials,
            "access_token": self.access_token,
            "base_url": self.base_url,
            "auth_url": self.auth_url,
            "scope": self.scope,
            "user": self.user,
            "password": self.password,
            "timeout": self.timeout,
            "verify_ssl_certs": self.verify_ssl_certs,
            "ca_bundle_file": self.ca_bundle_file,
            "cert_file": self.cert_file,
            "key_file": self.key_file,
            "key_file_password": self.key_file_password,
        }
        kwargs.update({key: value for key, value in optional.items() if value is not None})
        return kwargs

    def _get_client(self) -> Any:
        if self._client is None:
            from gigachat import GigaChat

            self._client = GigaChat(**self._client_kwargs())
        return self._client

    @classmethod
    def from_env(
        cls,
        *,
        model: str,
        temperature: float | None = 0.2,
        max_retries: int = 5,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> ChatGigaChat:
        verify_raw = os.getenv("GIGACHAT_VERIFY_SSL_CERTS")
        verify_ssl_certs = _env_bool("GIGACHAT_VERIFY_SSL_CERTS", True) if verify_raw is not None else None
        timeout_raw = os.getenv("GIGACHAT_TIMEOUT")
        return cls(
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            credentials=os.getenv("GIGACHAT_CREDENTIALS"),
            access_token=api_key or os.getenv("GIGACHAT_TOKEN"),
            base_url=base_url or os.getenv("GIGACHAT_BASE_URL"),
            auth_url=os.getenv("GIGACHAT_AUTH_URL"),
            scope=os.getenv("GIGACHAT_SCOPE"),
            user=os.getenv("GIGACHAT_USER"),
            password=os.getenv("GIGACHAT_PASSWORD"),
            timeout=float(timeout_raw) if timeout_raw else None,
            verify_ssl_certs=verify_ssl_certs,
            ca_bundle_file=os.getenv("GIGACHAT_CA_BUNDLE_FILE"),
            cert_file=os.getenv("GIGACHAT_CERT_FILE"),
            key_file=os.getenv("GIGACHAT_KEY_FILE"),
            key_file_password=os.getenv("GIGACHAT_KEY_FILE_PASSWORD"),
        )

    @overload
    async def ainvoke(
        self,
        messages: list[Any],
        output_format: None = None,
        **kwargs: Any,
    ) -> Any: ...

    @overload
    async def ainvoke(
        self,
        messages: list[Any],
        output_format: type[T],
        **kwargs: Any,
    ) -> Any: ...

    async def ainvoke(
        self,
        messages: list[Any],
        output_format: type[T] | None = None,
        **kwargs: Any,
    ) -> Any:
        from browser_use.llm.exceptions import ModelProviderError
        from browser_use.llm.views import ChatInvokeCompletion
        from gigachat.models.chat import Chat

        client = self._get_client()
        gigachat_messages = await _aserialize_browser_messages(messages, client=client)
        payload: dict[str, Any] = {"messages": gigachat_messages, "model": self.model}
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                if output_format is None:
                    completion = await client.achat(Chat(**payload))
                    return ChatInvokeCompletion(
                        completion=_extract_completion_text(completion),
                        usage=_extract_usage(completion),
                    )

                completion, parsed = await client.achat_parse(
                    Chat(**payload),
                    response_format=output_format,
                    strict=True,
                )
                return ChatInvokeCompletion(
                    completion=parsed,
                    usage=_extract_usage(completion),
                )
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                await _async_sleep(retry_backoff_seconds(attempt))

        if last_error is not None:
            status_code = getattr(last_error, "status_code", None)
            raise ModelProviderError(
                message=str(last_error),
                status_code=status_code,
                model=self.name,
            ) from last_error
        raise ModelProviderError(message="GigaChat request failed", model=self.name)


async def _async_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
