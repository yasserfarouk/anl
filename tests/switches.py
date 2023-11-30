import os

__all__ = [
    "anl_RUNALL_TESTS",
    "anl_FASTRUN",
    "anl_RUN2019",
    "anl_RUN2020",
    "anl_RUN2021_TOURNAMENT",
    "anl_RUN2021_ONESHOT",
    "anl_RUN2021_ONESHOT_SYNC",
    "anl_RUN2021_STD",
    "anl_RUN_TUTORIAL2",
    "anl_RUN_GENIUS",
    "anl_RUN_TOURNAMENTS",
    "anl_RUN_STD_TOURNAMENTS",
    "anl_RUN_COLLUSION_TOURNAMENTS",
    "anl_RUN_SABOTAGE_TOURNAMENTS",
    "anl_RUN_TEMP_FAILING",
]


def is_enabled(val: str) -> bool:
    return os.environ.get(val, "").lower() in ("true", "yes")


def isnot_disabled(val: str) -> bool:
    return os.environ.get(val, "").lower() not in ("false", "no")


anl_RUNALL_TESTS = is_enabled("anl_RUNALL_TESTS")
anl_ON_GITHUB = is_enabled("GITHUB_ACTIONS")
anl_FASTRUN = (is_enabled("anl_FASTRUN") or anl_ON_GITHUB) and not anl_RUNALL_TESTS
anl_RUN_TEMP_FAILING = is_enabled("anl_RUN_TEMP_FAILING")
anl_RUN2021_ONESHOT = isnot_disabled("anl_RUN2021_ONESHOT")
anl_RUN2021_STD = isnot_disabled("anl_RUN2021_STD")
anl_RUN_GENIUS = is_enabled("anl_RUN_GENIUS")
anl_RUN_TOURNAMENTS = is_enabled("anl_RUN_TOURNAMENTS")
anl_RUN_STD_TOURNAMENTS = is_enabled("anl_RUN_STD_TOURNAMENTS")
anl_RUN_COLLUSION_TOURNAMENTS = is_enabled("anl_RUN_COLLUSION_TOURNAMENTS")
anl_RUN_SABOTAGE_TOURNAMENTS = is_enabled("anl_RUN_SABOTAGE_TOURNAMENTS")
anl_RUN2021_TOURNAMENT = isnot_disabled("anl_RUN2021_TOURNAMENT")
anl_RUN2021_ONESHOT_SYNC = isnot_disabled("anl_RUN2021_ONESHOT_SYNC")
anl_RUN2019 = is_enabled("anl_RUN2019")
anl_RUN2020 = is_enabled("anl_RUN2020")
anl_RUN_TUTORIAL2 = isnot_disabled("anl_RUN_TUTORIAL2")
anl_RUN_NOTEBOOKS = isnot_disabled("anl_RUN_NOTEBOOKS")
anl_RUN_SCHEDULER = is_enabled("anl_RUN_SCHEDULER")
