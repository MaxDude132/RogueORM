import os
from importlib import import_module
from dotenv import load_dotenv

from rogue.settings import default_settings


load_dotenv()


SETTINGS_FILE_VAR_NAME = "ROGUE_ORM_SETTINGS"
DEFAULT_SETTINGS_FILE_NAME = "settings.py"


def _get_settings():
    settings_file = os.getenv(SETTINGS_FILE_VAR_NAME, DEFAULT_SETTINGS_FILE_NAME)

    try:
        settings_module = import_module(settings_file)
    except ImportError:
        settings_module = default_settings

        # For now, use the default settings if no setting was set in
        # environment variables. Eventually, we might want to enforce
        # the use of a settings file.
        # raise ValueError(
        #     f"{SETTINGS_FILE_VAR_NAME} was not properly set in "
        #     "the environment variables. This is required to use RogueORM."
        # )

    for setting in dir(default_settings):
        if setting.isupper() and not hasattr(settings_module, setting):
            setattr(settings_module, setting, getattr(default_settings, setting))

    return settings_module


settings = _get_settings()
