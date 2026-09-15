"""Regression tests for scripts/post_daily_jokes.py.

Bug history (2026-09-15): the daily joke run crashed with

    KeyError: 'mark'
    scripts/post_daily_jokes.py:215  prof = ACCOUNT_PROFILES[uname]

TEAM_HANDLES contains handles with no ACCOUNT_PROFILES entry, and the selection
code indexed the profiles dict directly. This file pins that behaviour shut.
"""
import importlib.util
import random
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "post_daily_jokes.py"


@pytest.fixture(scope="module")
def jokes():
    spec = importlib.util.spec_from_file_location("post_daily_jokes", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_team_handle_is_resolvable_to_a_profile(jokes):
    """No handle offered to the selector may be missing from the profile lookup."""
    for handle in jokes.TEAM_HANDLES:
        assert jokes.profile_for(handle) is not None, f"no profile for team handle {handle!r}"


def test_every_account_profile_is_resolvable(jokes):
    for handle in jokes.ACCOUNTS:
        assert jokes.profile_for(handle) is not None


def test_profile_contract(jokes):
    """Whatever a profile comes from, it must expose the keys the poster reads."""
    for handle in list(jokes.ACCOUNTS) + list(jokes.TEAM_HANDLES):
        prof = jokes.profile_for(handle)
        assert set(prof) >= {"topics", "tags", "series", "series_p"}
        assert isinstance(prof["topics"], list) and prof["topics"]
        assert isinstance(prof["tags"], list) and prof["tags"]


def test_unknown_handle_does_not_raise(jokes):
    """A bad handle must degrade, never crash the batch."""
    prof = jokes.profile_for("definitely-not-a-real-account")
    assert isinstance(prof, dict) and prof["tags"]


@pytest.mark.parametrize("seed", range(200))
def test_team_handle_branch_never_keyerrors(jokes, seed):
    """Reproduces the original crash: hammer the 15% team-handle branch."""
    rng = random.Random(seed)
    for _ in range(40):
        uname = rng.choice(jokes.TEAM_HANDLES)
        jokes.profile_for(uname)  # must not raise KeyError
