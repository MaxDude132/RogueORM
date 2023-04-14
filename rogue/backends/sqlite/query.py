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
            .where(
                table_name=self.model.table_name,
                field="id",
                comparison=self.EQUAL,
                value="(SELECT last_insert_rowid())",
            )
            .fetch_one()
        )
        return data

    def update(self, pk, data):
        self.client.execute(*self._build_update(pk, data))
        data = (
            self.__class__(self.client, self.model)
            .where(
                table_name=self.model.table_name,
                field="id",
                comparison=self.EQUAL,
                value=pk,
            )
            .fetch_one()
        )
        return data

    def delete(self):
        self.client.execute(*self._build_delete())

    def _format_fields(self):
        fields = []

        for field in self.fields:
            fields.append(".".join((self.table_name, field)))

        return fields

    def _build_select(self):
        query = f"{self.SELECT} {', '.join(self._format_fields())} {self.FROM} {self.table_name}"

        if self.where_statements:
            query = f"{query} {self._build_where()}"

        return query

    def _build_insert(self, data):
        assert not self.where_statements, "No where can be passed to an insert backend."

        if not data:
            return f"{self.INSERT} {self.table_name} DEFAULT {self.VALUES}", ()

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
        query = ""

        wheres = []
        joins = []
        for where in self.where_statements:
            if where.relation_descriptor:
                for relation in where.relation_descriptor:
                    joins.append(
                        f"{self.INNER_JOIN} {relation['right_table_name']} {self.ON} "
                        f"{relation['left_table_name']}.{relation['left_field_name']} = "
                        f"{relation['right_table_name']}.{relation['right_field_name']}"
                    )

            wheres.append(
                f"{where.table_name}.{where.field} {where.comparison} {where.value}"
            )

        return f"{query} {' '.join(joins)} {self.WHERE} {f' {self.AND} '.join(wheres)}"
