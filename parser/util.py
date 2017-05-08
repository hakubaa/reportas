import subprocess
import imp
import importlib
import sys
import inspect
import ctypes
import string
import re
import numbers

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


def pdfinfo(path, encoding="utf-8", convert_dates=True):
    '''Run pdfinfo command and intercept output & errors.''' 
    args = ["pdfinfo", path]
    if encoding: args.extend(("-enc", encoding))

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, errors = proc.communicate()

    info = dict()
    if output:
        rows = str(output, encoding=encoding).split("\n")
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