from importlib import import_module

MODULE_PACKAGES = ("custom.action", "custom.reco")


def register_all() -> None:
    for package_name in MODULE_PACKAGES:
        module = import_module(package_name)
        register = getattr(module, "register_all", None)
        if register is not None:
            register()


__all__ = ["register_all"]
