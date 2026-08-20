"""
VELES OS Update State

Defines the lifecycle state of a VELES OS update transaction.

This module is intentionally isolated from filesystem installation.
It only tracks and validates update state transitions.
"""

from __future__ import annotations


class UpdateState:
    """Tracks and validates VELES OS update lifecycle state."""

    IDLE = "idle"
    CHECKING = "checking"
    STAGING = "staging"
    VERIFYING = "verifying"
    READY = "ready"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"

    VALID_STATES = {
        IDLE,
        CHECKING,
        STAGING,
        VERIFYING,
        READY,
        INSTALLING,
        INSTALLED,
        FAILED,
    }

    TRANSITIONS = {
        IDLE: {
            CHECKING,
        },
        CHECKING: {
            STAGING,
            READY,
            FAILED,
        },
        STAGING: {
            VERIFYING,
            FAILED,
        },
        VERIFYING: {
            READY,
            FAILED,
        },
        READY: {
            INSTALLING,
            IDLE,
        },
        INSTALLING: {
            INSTALLED,
            FAILED,
        },
        INSTALLED: {
            IDLE,
        },
        FAILED: {
            IDLE,
        },
    }

    def __init__(
        self,
        state=None,
    ):
        initial_state = (
            state
            if state is not None
            else self.IDLE
        )

        self._validate_state(
            initial_state
        )

        self._state = initial_state

    # --------------------------------------------------
    # STATE
    # --------------------------------------------------

    @property
    def state(self):
        """Return the current state."""

        return self._state

    @property
    def terminal(self):
        """Return True when the current state is terminal."""

        return self._state in {
            self.INSTALLED,
            self.FAILED,
        }

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    @classmethod
    def _validate_state(
        cls,
        state,
    ):
        """Validate a state value."""

        if state not in cls.VALID_STATES:
            raise ValueError(
                f"Invalid update state: {state}"
            )

    @classmethod
    def can_transition(
        cls,
        current,
        target,
    ):
        """Return True when a state transition is valid."""

        cls._validate_state(
            current
        )

        cls._validate_state(
            target
        )

        return target in cls.TRANSITIONS.get(
            current,
            set(),
        )

    # --------------------------------------------------
    # TRANSITION
    # --------------------------------------------------

    def transition(
        self,
        target,
    ):
        """Transition to another valid update state."""

        self._validate_state(
            target
        )

        if not self.can_transition(
            self._state,
            target,
        ):
            raise RuntimeError(
                "Invalid update state transition: "
                f"{self._state} -> {target}"
            )

        self._state = target

        return self._state

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    def reset(self):
        """Reset a completed or failed transaction to idle."""

        if self._state == self.IDLE:
            return self._state

        if not self.can_transition(
            self._state,
            self.IDLE,
        ):
            raise RuntimeError(
                "Cannot reset update state from: "
                f"{self._state}"
            )

        self._state = self.IDLE

        return self._state

    # --------------------------------------------------
    # FAILURE
    # --------------------------------------------------

    def fail(self):
        """Transition the transaction into failed state."""

        if self._state == self.FAILED:
            return self._state

        if not self.can_transition(
            self._state,
            self.FAILED,
        ):
            raise RuntimeError(
                "Cannot fail update transaction from: "
                f"{self._state}"
            )

        self._state = self.FAILED

        return self._state