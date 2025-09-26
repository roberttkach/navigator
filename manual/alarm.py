"""Manual scenarios for alarm-related behaviours."""
from __future__ import annotations

import asyncio
from typing import Callable
from unittest.mock import AsyncMock, Mock

from navigator.app.usecase.alarm import Alarm
from navigator.core.value.message import Scope

from .common import monitor


def _gateway() -> Mock:
    gateway = Mock()
    gateway.alert = AsyncMock()
    return gateway


def reliance() -> None:
    """Verify default alert text resolution."""

    scope = Scope(chat=1, lang="en")
    provider: Callable[[Scope], str] = Mock(return_value="alert text")
    gateway = _gateway()
    alarm = Alarm(gateway=gateway, alert=provider, telemetry=monitor())

    asyncio.run(alarm.execute(scope))

    provider.assert_called_once_with(scope)
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, "alert text")


def override() -> None:
    """Ensure manual alert text bypasses provider."""

    scope = Scope(chat=1, lang="en")
    provider: Callable[[Scope], str] = Mock(return_value="fallback")
    gateway = _gateway()
    alarm = Alarm(gateway=gateway, alert=provider, telemetry=monitor())

    asyncio.run(alarm.execute(scope, text="override"))

    provider.assert_not_called()
    assert gateway.alert.await_count == 1
    assert gateway.alert.await_args.args == (scope, "override")


__all__ = ["reliance", "override"]
