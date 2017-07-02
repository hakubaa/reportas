import json

from sqlalchemy.orm.query import Query
from flask import request


def apply_query_parameters(query):
    limit = int(request.args.get("limit", 0))
    offset = int(request.args.get("offset", 0))
    sort = request.args.get("sort")
    if sort: sort = "".join(sort.split()) # remove all whitespaces

    if isinstance(query, Query):
        if sort:
            for field in sort.split(","):
                index = 1 if field.startswith("-") else 0
                try:
                    model = query.column_descriptions[0]["type"]
                    column = model.__table__.columns[field[index:]]
                    if index:
                        column = column.desc()
                except KeyError:
                    continue
                else:
                    query = query.order_by(column)   
        query = query.limit(limit or None).offset(offset or None)
        return query.all()
    else:
        if sort:
            for field in sort.split(","):
                index = 1 if field.startswith("-") else 0
                try:
                    query = sorted(
                        query, key=lambda x: getattr(x, field[index:]),
                        reverse = bool(index)
                    )
                except AttributeError:
                    continue
        if not limit: limit = len(query)
        query = query[offset:(offset+limit)]
        return query


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)