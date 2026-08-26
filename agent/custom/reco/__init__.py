from importlib import import_module

RECO_MODULES: tuple[str, ...] = ()


def register_all() -> None:
    for module_name in RECO_MODULES:
        import_module(f"{__name__}.{module_name}")


__all__ = ["register_all"]
