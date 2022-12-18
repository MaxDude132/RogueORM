from ..base import BaseQueryBuilder


class QueryBuilder(BaseQueryBuilder):
    def get_all(self):
        query = self._build_query()
        print(query)
        result = self.client.execute(query)
        print(result)
        return

    def _get_select(self):
        table_fields = []
        return f"{self.SELECT} {', '.join(table_fields)} {self.FROM} {self.table_name}"

    def _build_select(self):
        query = f"{self.SELECT} {', '.join(self.fields.keys())} {self.FROM} {self.table_name}"

        if self.where_statements:
            query = f"{query} {self._build_where()}"

        return query

    def _build_where(self):
        query = "WHERE "
        query += " AND ".join(
            [
                f"{where.field} {where.comparison} {where.value}"
                for where in self.where_statements
            ]
        )
        return query
