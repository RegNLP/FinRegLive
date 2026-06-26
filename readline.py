# Step 11B - Readline Compatibility Stub
#
# Role:
#   Prevent pytest startup from importing a crashing native readline module in
#   this local Python environment.
#
# Why this exists:
#   The current conda/macOS Python crashes on `import readline` before pytest
#   can run any project tests. Pytest imports readline early as a terminal
#   capture workaround, so this lightweight stub keeps test startup stable.
#
# Input:
#   Optional readline-style calls from test tooling.
#
# Output:
#   No-op functions that satisfy simple imports without native readline.


def parse_and_bind(*args: object, **kwargs: object) -> None:
    return None


def set_completer(*args: object, **kwargs: object) -> None:
    return None
