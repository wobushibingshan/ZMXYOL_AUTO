import os


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def interface_version() -> str:
    return get_env("PI_INTERFACE_VERSION")


def client_name() -> str:
    return get_env("PI_CLIENT_NAME")


def client_version() -> str:
    return get_env("PI_CLIENT_VERSION")


def client_language() -> str:
    return get_env("PI_CLIENT_LANGUAGE")


def maafw_version() -> str:
    return get_env("PI_CLIENT_MAAFW_VERSION")


def pi_version() -> str:
    return get_env("PI_VERSION")


def controller() -> str:
    return get_env("PI_CONTROLLER")


def resource() -> str:
    return get_env("PI_RESOURCE")
