import subprocess
import imp
import importlib
import sys
import inspect
import ctypes
import string
import re
import numbers

import nltk
from dateutil.parser import parse

import models


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


def is_date(string):
    '''Determine whether string represents date.'''
    try: 
        parse(string)
        return True
    except (ValueError, OverflowError):
        return False


def find_ngrams(text, n):
    '''Find all n-grams in th text and return list of tuples.'''
    tokens = [token.lower() for token in nltk.word_tokenize(text)]
    tokens = [token for token in tokens 
                    if token not in models.STOP_WORDS 
                       and not token.lstrip("-+(").rstrip(")").isdigit() 
                       and token not in string.punctuation
                       and not is_date(token) ]
    ngrams = [ models.NGram(*tokens) for tokens in nltk.ngrams(tokens, n) ]
    return ngrams


def find_numbers(text):
    '''Find all numbers in str and return list.'''
    numbers = re.findall(RE_NUMBER, text)
    return numbers


def isnumber(string):
    '''Test whether str represents a number.'''
    return bool(re.match(RE_NUMBER, string))


def convert_to_number(string, decimal_mark=","):
    '''Convert string to number.'''
    if isinstance(string, numbers.Number):
        return string

    if string == "" or string == "-": # '-' is often use in reports
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