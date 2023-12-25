import os

__all__ = [
    "ANL_RUNALL_TESTS",
    "ANL_FASTRUN",
    "ANL_RUN_TUTORIAL2",
    "ANL_RUN_GENIUS",
    "ANL_RUN_TOURNAMENTS",
    "ANL_RUN_TEMP_FAILING",
]


def is_enabled(val: str) -> bool:
    return os.environ.get(val, "").lower() in ("true", "yes")


def isnot_disabled(val: str) -> bool:
    return os.environ.get(val, "").lower() not in ("false", "no")


ANL_RUNALL_TESTS = is_enabled("ANL_RUNALL_TESTS")
ANL_ON_GITHUB = is_enabled("GITHUB_ACTIONS")
ANL_FASTRUN = (is_enabled("ANL_FASTRUN") or ANL_ON_GITHUB) and not ANL_RUNALL_TESTS
ANL_RUN_TEMP_FAILING = is_enabled("ANL_RUN_TEMP_FAILING")
ANL_RUN_GENIUS = is_enabled("ANL_RUN_GENIUS")
ANL_RUN_TOURNAMENTS = is_enabled("ANL_RUN_TOURNAMENTS")
ANL_RUN_TUTORIAL2 = isnot_disabled("ANL_RUN_TUTORIAL2")
ANL_RUN_NOTEBOOKS = isnot_disabled("ANL_RUN_NOTEBOOKS")
