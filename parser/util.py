import subprocess
import imp
import importlib
import sys
import inspect
import ctypes
import string
import operator
import re
import numbers
from collections import Counter
from datetime import datetime
from calendar import monthrange

from dateutil.parser import parse


RE_NUMBER = re.compile(r"(?:\+|-|\()?\d+(?:[,. ]\d+)*(?:\))?")


def pdftotext(path, layout=True, first_page=None, last_page=None,
              encoding=None):
    '''Run pdftotext command and intercept output & errors.''' 
    args = ["pdftotext", path, "-"]
    if layout: args.append("-layout")
    if first_page: args.extend(("-f", str(first_page)))
    if last_page: args.extend(("-l", str(last_page)))
    if encoding: args.extend(("-enc", encoding))

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def pdfinfo(path, encoding=None, convert_dates=True):
    '''Run pdfinfo command and intercept output & errors.''' 
    args = ["pdfinfo", path]
    if encoding: args.extend(("-enc", encoding))

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, errors = proc.communicate()

    info = dict()
    if output:
        rows = str(output, encoding="utf-8").split("\n")
        for row in rows:
            try:
                key, value = row.split(":", 1)
            except ValueError:
                pass # ignore invalid fields
            else:
                info[key] = value.lstrip()

        if convert_dates:
            if "CreationDate" in info:
                info["CreationDate"] = parse(info["CreationDate"])
            if "ModDate" in info:
                info["ModDate"] = parse(info["ModDate"])

    return info, errors


def is_date(string):
    '''Determine whether string represents date.'''
    try: 
        parse(string)
        return True
    except (ValueError, OverflowError):
        return False


def find_numbers(text):
    '''Find all numbers in str and return list.'''
    numbers = re.findall(RE_NUMBER, text)
    return numbers


def is_number(string, special_zeros=" -"):
    '''Test whether str represents a number.'''
    return string in special_zeros or bool(re.match(RE_NUMBER, string))


def convert_to_number(string, decimal_mark=",", special_zeros=" -"):
    '''Convert string to number.'''
    if isinstance(string, numbers.Number):
        return string

    if not is_number(string):
        return None

    if string in special_zeros:
        return 0.0

    # Determine sign of the number
    sign = -1 if re.match(r"^(-|\()", string) else 1

    # Extract actual number
    number = re.search("\d+(?:[,. ]\d+)*", string)
    if not number:
        return ValueError("could not convert string to number: {!r}".
                          format(string))

    # Split number into integral & fraction part
    integral, *fraction = number.group(0).split(decimal_mark)
    integral = int(re.sub("[^0-9]", "", integral)) # remove non digits
    if fraction:
        fraction = float("." + re.sub("[^0-9]", "", fraction[0]))
    else:
        fraction = 0.0

    return sign * (integral + fraction)


def remove_non_ascii(string):
    ''' Return the string without non ASCII characters.'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


def load_module(name, attach = False, force_reload = True):
    '''Load dynamically module.'''
    if name in sys.modules and force_reload:
        module = imp.reload(sys.modules[name])
    else:
        module = importlib.import_module(name)
    if attach:
        calling_frame = inspect.stack()[1][0]
        calling_frame.f_locals.update(
            { attr: getattr(module, attr) for attr in dir(module) 
                                          if not attr.startswith("_") }
        )
        ctypes.pythonapi.PyFrame_LocalsToFast(
                ctypes.py_object(calling_frame), ctypes.c_int(0))
    return module


def find_dates(text, all_days=False):
    '''Find all dates in the text.'''

    re_days = r"(1|28|29|30|31)"
    if all_days:
        re_days = r"\d{1,2}"

    quarters = {"i": 3, "ii": 6, "iii": 9, "iv": 12}
    months = {"stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, 
              "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
              "wrzenia": 9, "września": 9, "padziernika": 10, 
              "października": 10, "listopada": 11, "grudnia": 12}

    re_date_with_full_month = re.compile(
        re_days + r" (stycznia|lutego|marca|kwietnia|maja|czerwca|"
         "lipca|sierpnia|wrze(?:ś)?nia|pa(?:ź)?dziernika|listopada|grudnia) "
         "((?:19|20)\d{2})", flags = re.IGNORECASE
    )
    re_quarter = re.compile(
        r"(I|II|III|IV) kw(?:\.|arta)?(?:ł)?(?:y)? (\d+)", flags=re.IGNORECASE
    )
    re_date_day_month_year = re.compile(
        re_days + r".(0?[1-9]|1[0-2]).((?:19|20)\d{2})"
    )
    re_date_year_month_day = re.compile(
        r"((?:19|20)\d{2})(?: \.-){1}(0?[1-9]|1[0-2])(?: \.-){1}" + re_days
    )

    re_day_and_full_month = re.compile(
        re_days + r" (stycznia|lutego|marca|kwietnia|maja|czerwca|"
         "lipca|sierpnia|wrze(?:ś)?nia|pa(?:ź)?dziernika|listopada|grudnia)", 
         flags = re.IGNORECASE
    )
    re_year = re.compile("((?:19|20)\d{2})")

    timestamps = list()

    # Match [za] I/II/III/IV kwartał 2016 [roku]
    match_dates = re.finditer(re_quarter, text)
    for match_date in match_dates:
        quarter, year = match_date.groups()
        try:
            timestamps.append(((
                int(year), quarters[quarter.lower()], 
                monthrange(int(year), quarters[quarter.lower()])[-1]
            ), match_date.span(), 1))
        except ValueError:
            pass # ignore erros in dates

    # Match '30 września 2016 roku'
    match_dates = re.finditer(re_date_with_full_month, text)
    for match_date in match_dates:
        day, month, year = match_date.groups()
        try:
            timestamps.append(((
                int(year), months[month.lower()], int(day)
            ), match_date.span(), 1))
        except ValueError:
            pass # ignore errors in dates

    # Match 30.06.2016
    match_dates = re.finditer(re_date_day_month_year, text)
    for match_date in match_dates:
        day, month, year = match_date.groups()
        try:
            timestamps.append((
                (int(year), int(month), int(day)),
                match_date.span(), 1
            ))
        except ValueError:
            pass # ignore errors in dates

    # Match 2016-03-31
    match_dates = re.finditer(re_date_year_month_day, text)
    for match_date in match_dates:
        year, month, day = match_date.groups()
        try:
            timestamps.append((
                (int(year), int(month), int(day)),
                match_date.span(), 1
            ))
        except ValueError:
            pass # ignore errors in dates

    if not timestamps: # as a last resort match partial dates
        # Match '30 września'
        match_dates = re.finditer(re_day_and_full_month, text)
        for match_date in match_dates:
            day, month = match_date.groups()
            try:
                timestamps.append(
                    ((None, months[month.lower()], int(day)), 
                     match_date.span(), 0)
                )
            except ValueError:
                pass # ignore errors in dates

        # Match '2016'
        match_dates = re.finditer(re_year, text)
        for match_date in match_dates:
            year = match_date.groups()
            try:
                timestamps.append((
                    (int(year[0]), None, None), match_date.span(), 0)
                )
            except ValueError:
                pass # ignore errors in dates

    return timestamps


def determine_timerange(text):
    '''
    Determine timerange on the base of text. Return list of potential
    timeranges.
    '''
    tranges = list()

    text = text.lower() 

    # Match IV kwartały
    re_quarters = re.compile(
        r"(I|II|III|IV|1|2|3|4) *kwarta(?:ł)?y *(?:(?:19|20)\d{2})", 
        flags=re.IGNORECASE
    )

    quarters = {"i": 3, "ii": 6, "iii": 9, "iv": 12, "1": 3, "2": 6,
                "3": 9, "4": 12}

    tranges.extend(quarters[q] for q in re.findall(re_quarters, text))

    # Match IV kwartał
    # re_quarter = re.compile(
    #     r"(I|II|III|IV|1|2|3|4) *kw(?:\.|arta)?(?:ł)? *(?:(?:19|20)\d{2})", 
    #     flags=re.IGNORECASE
    # )
    re_quarter = re.compile(
        r"(I|II|III|IV|1|2|3|4) *kw(?:\.|arta)?(?:ł)?", 
        flags=re.IGNORECASE
    )
    tranges.extend(3 for _ in re.findall(re_quarter, text))

    # Match Rok 2015
    re_year = re.compile(
        r"(?:Rok) *(?:(?:19|20)\d{2})", 
        flags=re.IGNORECASE
    )
    tranges.extend(12 for _ in re.findall(re_year, text))

    # Match Polrocze 2015
    re_midyear = re.compile(
        r"(?:P(?:ó)?(?:ł)?rocze) */? *(?:(?:19|20)\d{2})", 
        flags=re.IGNORECASE
    )
    tranges.extend(6 for _ in re.findall(re_midyear, text))

    re_months = re.compile("(0?[1-9]|1[0-2]) miesi(?:ę)?cy", 
                                flags=re.IGNORECASE)
    tranges.extend(int(month) for month in re.findall(re_months, text))

    re_year = re.compile("Rok zako(?:ń)?czony", flags=re.IGNORECASE)
    tranges.extend(12 for _ in re.findall(re_year, text))

    return tranges


def split_text_into_columns(text, ncols=None, skip_bottom=5, skip_top=5):
    '''Split multiline text into columns.'''
    rows = list(filter(bool, text.split("\n")))
    rows4split = rows[abs(skip_bottom):-abs(skip_top)]

    width = Counter(map(len, rows4split)).most_common(1)[0][0]
    mrows = [ list(row + ' '*width)[:width] for row in rows4split ]
    trows = list(map(list, zip(*mrows))) # transpose rows

    wsdist = [ sum(1 for item in row if item == ' ') for row in trows ]
    avg_wsdist = sum(wsdist) / len(wsdist)
    wsmap = [ index for index, val in enumerate(wsdist) if val > avg_wsdist]

    series = [[(wsmap[0], wsdist[wsmap[0]])]]
    prev_ws = wsmap[0]
    for ws in wsmap[1:]:
        if prev_ws + 1 == ws:
            series[-1].append((ws, wsdist[ws]))
        else:
            series.append([(ws, wsdist[ws])])
        prev_ws = ws

    series = [ sr for sr in series if len(sr) > 1 ]

    wsbreaks = list(map(lambda x: x[1][0], sorted(        
        [(len(item), max(item, key=lambda x: x[1])) for item in series], 
        key=operator.itemgetter(0), reverse=True
    )))

    wsbreaks = list(map(lambda x: x[1][0], sorted(        
        [(len(item), max(item, key=lambda x: x[1])) for item in series], 
        key=operator.itemgetter(0), reverse=True
    )[:ncols]))

    joincols = [[] for _ in range(len(wsbreaks)+1)]
    for row in rows:
        breaks = sorted(list(set([0] + wsbreaks))) + [None]
        for index, (lb, ub) in enumerate(zip(breaks[:-1], breaks[1:])):
            joincols[index].append(row[lb:ub])
    # cols = [ re.sub(" + ", " ", ' '.join(col)) for col in joincols ]

    return joincols