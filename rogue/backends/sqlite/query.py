from ..base import BaseQueryBuilder
from ..errors import OperationalError


class QueryBuilder(BaseQueryBuilder):
    def fetch_one(self):
        data = self.client.execute(self._build_query(self.SELECT)).fetchone()
        return self._format_data([data])

    def fetch_many(self, limit=None):
        if limit is None:
            raise ValueError("limit parameter must be passed.")

        data = self.client.execute(self._build_query(self.SELECT)).fetchmany(size=limit)
        return self._format_data(data)

    def fetch_all(self):
        data = self.client.execute(self._build_query(self.SELECT)).fetchall()
        return self._format_data(data)

    def insert(self, data):
        data = self.client.execute(self._build_query(self.INSERT, data))
        data = self.client.execute(
            f"{self.SELECT} {', '.join(self.fields.keys())} {self.FROM} {self.table_name} {self.WHERE} id = (select last_insert_rowid())"
        ).fetchone()
        return self._format_data([data])

    def _build_select(self):
        query = f"{self.SELECT} {', '.join(self.fields.keys())} {self.FROM} {self.table_name}"

        if self.where_statements:
            query = f"{query} {self._build_where()}"

        return query

    def _build_insert(self, data):
        if data is None or len(data) == 0:
            raise OperationalError("Cannot insert without data.")

        if self.where_statements:
            raise OperationalError("No where can be passed to an insert Manager.")

        if isinstance(data, dict):
            data = [data]

        headers = list(data[0])
        formatted_data = []
        for row in data:
            formatted_data.append(", ".join([str(row[header]) for header in headers]))

        return (
            f"{self.INSERT} {self.table_name} ({', '.join(headers)}) {self.VALUES} ("
            f"{', '.join(formatted_data)})"
        )

    def _build_where(self):
        query = f"{self.WHERE} "
        query += f" {self.AND} ".join(
            [
                f"{where.field} {where.comparison} {where.value}"
                for where in self.where_statements
            ]
        )
        return query
