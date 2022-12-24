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
