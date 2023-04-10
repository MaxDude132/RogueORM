from importlib import import_module
from inspect import ismodule
from rogue.settings import settings


def get_through_model(
    model_has_definition,
    model_inherits_field,
    model_has_definition_reverse_name,
    model_inherits_field_reverse_name,
    nullable=False,
):
    from .base import ModelMeta, Model
    from .fields import Field

    through_name = (
        f"{model_has_definition.__name__}"
        f"{model_has_definition_reverse_name.title().replace('_', '')}"
        f"{model_inherits_field.__name__}"
        f"{model_inherits_field_reverse_name.title().replace('_', '')}Through"
    )

    return ModelMeta(
        through_name,
        (Model,),
        {
            "__annotations__": {
                _get_field_name(model_has_definition): Field[model_has_definition](
                    reverse_name=model_has_definition_reverse_name, nullable=nullable
                ),
                _get_field_name(model_inherits_field): Field[model_inherits_field](
                    reverse_name=model_inherits_field_reverse_name, nullable=nullable
                ),
            }
        },
    )


def _get_field_name(model):
    return model.table_name


def get_all_models():
    # Likely to have a circular import in the future, so we import directly in the function
    from .base import Model

    _import_all_models()

    subclasses = _get_subclasses(Model)
    return subclasses


def _import_all_models():
    # Models have to be imported first to be in the subclasses list
    models_folder = settings.MODELS_FOLDER
    import_module(models_folder)


def _get_subclasses(cls):
    subclasses = []
    for subclass in cls.__subclasses__():
        if subclass.__subclasses__():
            subclasses.extend(_get_subclasses(subclass))
        else:
            subclasses.append(subclass)

    return subclasses
