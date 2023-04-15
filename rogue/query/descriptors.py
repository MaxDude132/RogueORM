class RelationDescriptor:
    def __init__(self, *trackings):
        from rogue.models.fields import RelationField

        self._trackings = trackings
        self._formatted_trackings = []

        for tracking in self._trackings:
            if isinstance(tracking, RelationField):
                self._formatted_trackings.append(
                    {
                        "left_table_name": tracking._parent.table_name,
                        "left_field_name": tracking.name,
                        "right_table_name": tracking._foreign_model.table_name,
                        "right_field_name": "id",
                    }
                )

    def __iter__(self):
        return iter(self._formatted_trackings)
