import json

from sqlalchemy.orm.query import Query
from flask import request, current_app

import db.utils as dbutil
import rparser.utils as putil
from rparser.core import FinancialReport


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


def parse_text(session, text, spec_name=None):
    if not spec_name:
        spec = dbutil.get_records_reprs(session, "bls") +\
                   dbutil.get_records_reprs(session, "nls") +\
                   dbutil.get_records_reprs(session, "cfs")
    elif spec_name in ("bls", "nls", "cfs"):
        spec = dbutil.get_records_reprs(session, spec_name)

    voc = dbutil.create_vocabulary(session)

    records = putil.identify_records_in_text(text=text, spec=spec, voc=voc)
    data = list()
    for (name, sim), numbers, row_no in records:
        data.append({"name": name, "numbers": numbers, "row_no": row_no})

    return data


def parse_file(filepath, session):
    voc = dbutil.create_vocabulary(session)

    spec = dict(
        bls=dbutil.get_records_reprs(session, "bls"),
        nls=dbutil.get_records_reprs(session, "nls"),
        cfs=dbutil.get_records_reprs(session, "cfs")
    )
    cspec = dbutil.get_companies_reprs(session)

    doc = FinancialReport(filepath, spec=spec, voc=voc, cspec=cspec)

    return doc.as_dict()


def allowed_file(filename):
    exts = current_app.config.get("ALLOWED_EXTENSIONS")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in exts