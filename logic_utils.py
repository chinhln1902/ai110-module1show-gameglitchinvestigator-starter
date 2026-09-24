def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            number = float(raw)
        else:
            number = int(raw)
    except Exception:
        return False, None, "That is not a number."

    # FIXME: Logic breaks here - negative guesses were accepted even though the
    # secret is always >= 1, so they could never be correct. Reject them instead.
    # The check has to happen BEFORE truncating: int(float("-0.5")) is 0, so a
    # negative fraction used to sneak through this guard as a guess of zero.
    if number < 0:
        return False, None, "No negative numbers! Guess a positive number in range."

    return True, int(number), None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIXME: Logic breaks here - the hint text was inverted: a guess that is
    # too high told the player to go HIGHER. Direction now matches the outcome.
    if guess > secret:
        return "Too High", "📉 Too high - go LOWER!"
    return "Too Low", "📈 Too low - go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
