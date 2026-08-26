from importlib import import_module

ACTION_MODULES: tuple[str, ...] = (
    "check_announcement_task",
    "check_exploration_count",
    "check_one_click_domination_cost",
    "check_remaining_count",
    "CheckChaosRelicCount",
)


def register_all() -> None:
    for module_name in ACTION_MODULES:
        import_module(f"{__name__}.{module_name}")


__all__ = ["register_all"]
