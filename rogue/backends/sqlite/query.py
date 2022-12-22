from ..base import BaseQueryBuilder
from ..errors import OperationalError


class QueryBuilder(BaseQueryBuilder):
    def fetch_one(self):
        data = self.client.execute(self._build_select()).fetchone()
        return self._format_output_data([data])

    def fetch_all(self):
        data = self.client.execute(self._build_select()).fetchall()
        return self._format_output_data(data)

    def insert(self, data):
        self.client.execute(*self._build_insert(data))
        data = (
            self.__class__(self.client, self.model)
            .where("id", self.EQUAL, "(SELECT last_insert_rowid())")
            .fetch_one()
        )
        return data

    def update(self, pk, data):
        self.client.execute(*self._build_update(pk, data))
        data = (
            self.__class__(self.client, self.model)
            .where("id", self.EQUAL, pk)
            .fetch_one()
        )
        return data

    def delete(self):
        self.client.execute(*self._build_delete())

    def _build_select(self):
        query = f"{self.SELECT} {', '.join(self.fields.keys())} {self.FROM} {self.table_name}"

        if self.where_statements:
            query = f"{query} {self._build_where()}"

        return query

    def _build_insert(self, data):
        assert not self.where_statements, "No where can be passed to an insert backend."

        self._validate_data(data)
        headers, formatted_data = self._format_input_data(data)

        return (
            f"{self.INSERT} {self.table_name} ({', '.join(headers)}) {self.VALUES} ("
            f"{', '.join(['?' for _ in range(len(headers))])})",
            formatted_data,
        )

    def _build_update(self, pk, data):
        self._validate_data(data)
        headers, formatted_data = self._format_input_data(data)

        formatted_column_updates = [f"{col_name} = ?" for col_name in headers]

        return (
            f"{self.UPDATE} {self.table_name} SET {', '.join(formatted_column_updates)}",
            formatted_data,
        )

    def _build_delete(self):
        query = f"{self.DELETE} {self.FROM} {self.table_name}"

        if self.where_statements:
            query = f"{query} {self._build_where()}"

        return query, ()

    def _build_where(self):
        query = f"{self.WHERE} "
        query += f" {self.AND} ".join(
            [
                f"{where.field} {where.comparison} {where.value}"
                for where in self.where_statements
            ]
        )
        return query
