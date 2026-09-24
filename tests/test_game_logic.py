"""Regression tests for the Game Glitch Investigator.

Every test below pins down one of the bugs that was found and fixed. Each test
names the glitch it guards against, so if someone reintroduces it the failure
message points straight at the original symptom.

The first half tests the pure logic in logic_utils.py. The second half drives
the real Streamlit script with streamlit.testing.v1.AppTest, because several of
the glitches lived in the app's state handling and render order rather than in
the helper functions.
"""

import random
import sys
from pathlib import Path

import pytest

# Make the project root importable so `pytest` works from any directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logic_utils import (  # noqa: E402
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

# ---------------------------------------------------------------------------
# Bug 1: check_guess sent the player the wrong way.
# "Too high" used to tell the player to go HIGHER, so a correct binary search
# walked away from the secret.
# ---------------------------------------------------------------------------


def test_matching_guess_is_a_win():
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in message


def test_guess_above_secret_is_told_to_go_lower():
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert "LOWER" in message
    assert "HIGHER" not in message


def test_guess_below_secret_is_told_to_go_higher():
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in message
    assert "LOWER" not in message


def test_hint_direction_is_never_inverted():
    """The hint must always point back toward the secret."""
    secret = 50
    for guess in (1, 2, 49, 51, 99, 100):
        outcome, message = check_guess(guess, secret)
        if guess > secret:
            assert (outcome, "LOWER" in message) == ("Too High", True), guess
        else:
            assert (outcome, "HIGHER" in message) == ("Too Low", True), guess


# ---------------------------------------------------------------------------
# Bug 2: parse_guess accepted negative numbers.
# The secret is always >= 1, so a negative guess could never win but still
# burned an attempt.
# ---------------------------------------------------------------------------


def test_negative_guess_is_rejected():
    ok, value, error = parse_guess("-5")
    assert ok is False
    assert value is None
    assert "negative" in error.lower()


def test_negative_float_string_is_rejected():
    """int(float("-0.5")) is 0, so the sign has to be checked before truncating."""
    ok, value, error = parse_guess("-0.5")
    assert ok is False
    assert value is None
    assert "negative" in error.lower()


def test_positive_guess_is_accepted():
    assert parse_guess("42") == (True, 42, None)


def test_float_string_is_truncated_to_an_int():
    ok, value, error = parse_guess("7.9")
    assert (ok, value, error) == (True, 7, None)


@pytest.mark.parametrize("raw", [None, ""])
def test_missing_input_asks_for_a_guess(raw):
    ok, value, error = parse_guess(raw)
    assert ok is False
    assert value is None
    assert error == "Enter a guess."


def test_non_numeric_input_is_rejected():
    ok, value, error = parse_guess("fifty")
    assert ok is False
    assert value is None
    assert error == "That is not a number."


# ---------------------------------------------------------------------------
# Bug 3: New Game drew the secret from a hardcoded 1-100 range instead of the
# difficulty range. These pin the ranges the rest of the app relies on.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("difficulty", "expected"),
    [
        ("Easy", (1, 20)),
        ("Normal", (1, 100)),
        ("Hard", (1, 50)),
        ("Impossible", (1, 100)),  # unknown difficulty falls back to the default
    ],
)
def test_range_for_difficulty(difficulty, expected):
    assert get_range_for_difficulty(difficulty) == expected


# ---------------------------------------------------------------------------
# Bug 4 (scoring side): attempts used to start at 1 before any guess was made,
# which also shifted every score. With attempts starting at 0, the first guess
# is attempt 1 and a first-try win is worth 80.
# ---------------------------------------------------------------------------


def test_first_attempt_win_scores_80():
    assert update_score(current_score=0, outcome="Win", attempt_number=1) == 80


def test_win_points_never_drop_below_10():
    assert update_score(current_score=0, outcome="Win", attempt_number=99) == 10


def test_unknown_outcome_leaves_the_score_alone():
    assert update_score(current_score=25, outcome="Nonsense", attempt_number=3) == 25


# ---------------------------------------------------------------------------
# App-level regressions, driven through the real Streamlit script.
# ---------------------------------------------------------------------------

AppTest = pytest.importorskip(
    "streamlit.testing.v1",
    reason="streamlit's AppTest harness is required for the app-level tests",
).AppTest

APP_PATH = str(PROJECT_ROOT / "app.py")
TIMEOUT = 30


def _start_app(secret=None, difficulty=None):
    """Run app.py once and hand back the AppTest, optionally with a fixed secret."""
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    if secret is not None:
        # app.py only draws a random secret when one is not already in state.
        at.session_state.secret = secret
    at.run()
    if difficulty is not None:
        at.selectbox[0].set_value(difficulty).run()
    return at


def _guess(at, value):
    """Type a guess and press Submit."""
    at.text_input[0].set_value(str(value))
    at.button[0].click().run()
    return at


def _status_line(at):
    """The 'Attempts left' banner drawn by the most recent run."""
    return at.info[-1].value


def test_app_starts_with_zero_attempts():
    """Bug: attempts started at 1, so 'attempts left' was off by one all game."""
    at = _start_app(secret=50)

    assert at.session_state.attempts == 0
    assert "Attempts left: 8" in _status_line(at)
    assert not at.exception


def test_status_line_reflects_the_guess_just_made():
    """Bug: the status line and debug panel were drawn above the Submit button,
    so they always reported the *previous* run's attempts and history."""
    at = _start_app(secret=50)
    _guess(at, 60)

    assert at.session_state.attempts == 1
    assert at.session_state.history == [60]
    # Same run that recorded the guess must already show the new count.
    assert "Attempts left: 7" in _status_line(at)


def test_hint_stays_numeric_on_even_attempts():
    """Bug: on every even attempt the secret was cast to a string, so the guess
    was compared as text ("9" > "50") and the hint pointed the wrong way."""
    at = _start_app(secret=50)

    _guess(at, 60)  # attempt 1 (odd)
    assert "LOWER" in at.warning[-1].value

    _guess(at, 9)  # attempt 2 (even) - string compare would call this "too high"
    assert "HIGHER" in at.warning[-1].value
    assert at.session_state.history == [60, 9]


def test_negative_guess_is_rejected_in_the_app():
    """Bug: negative guesses sailed through parse_guess and were compared."""
    at = _start_app(secret=50)
    _guess(at, -5)

    assert "negative" in at.error[-1].value.lower()
    assert at.session_state.status == "playing"
    assert not at.exception


def test_winning_guess_ends_the_game():
    at = _start_app(secret=50)
    _guess(at, 50)

    assert at.session_state.status == "won"
    assert any("You won!" in s.value for s in at.success)


@pytest.mark.parametrize(
    ("status", "notice"),
    [("won", "already won"), ("lost", "Game over")],
)
def test_debug_panel_still_renders_after_the_game_ends(status, notice):
    """Bug: st.stop() ended the run before the status line and debug panel were
    redrawn, so they froze on stale values once the game was over.

    This runs the script exactly once, already in a finished state, so nothing
    left over from an earlier run can mask a missing element.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.session_state.secret = 50
    at.session_state.status = status
    at.session_state.attempts = 3
    at.session_state.score = 70
    at.session_state.history = [10, 20, 30]
    at.run()

    assert any(notice in e.value for e in list(at.success) + list(at.error))
    # The status line and debug panel are still drawn, with the current counts.
    assert len(at.info) == 1
    assert "Attempts left: 5" in _status_line(at)
    assert len(at.expander) == 1
    assert not at.exception


def test_losing_ends_the_game_after_the_attempt_limit():
    at = _start_app(secret=50, difficulty="Hard")  # Hard allows 5 attempts

    for _ in range(5):
        _guess(at, 60)

    assert at.session_state.attempts == 5
    assert at.session_state.status == "lost"
    assert any("Out of attempts" in e.value for e in at.error)


def test_new_game_resets_every_piece_of_state(monkeypatch):
    """Bug: New Game only reset attempts and the secret. Score, status and
    history survived from the old round, and the confirmation message was
    swallowed by st.rerun() before it could render."""
    randint_calls = []

    def recording_randint(low, high):
        randint_calls.append((low, high))
        return high

    monkeypatch.setattr(random, "randint", recording_randint)

    at = _start_app(secret=50)
    _guess(at, 60)
    at.session_state.score = 42
    at.session_state.status = "lost"

    at.button[1].click().run()  # New Game

    assert at.session_state.attempts == 0
    assert at.session_state.score == 0
    assert at.session_state.status == "playing"
    assert at.session_state.history == []
    assert any("New game started" in s.value for s in at.success)


def test_new_game_draws_the_secret_from_the_difficulty_range(monkeypatch):
    """Bug: New Game always drew from a hardcoded 1-100, ignoring difficulty."""
    randint_calls = []

    def recording_randint(low, high):
        randint_calls.append((low, high))
        return high

    monkeypatch.setattr(random, "randint", recording_randint)

    at = _start_app(secret=50, difficulty="Easy")  # Easy is 1-20
    at.button[1].click().run()  # New Game

    assert randint_calls[-1] == (1, 20)
    assert 1 <= at.session_state.secret <= 20
