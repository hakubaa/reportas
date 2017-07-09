import subprocess
import imp
import importlib
import sys
import inspect
import ctypes
import string
import itertools
import operator
import re
import numbers
from collections import Counter
from datetime import datetime
from calendar import monthrange
from functools import reduce

import numpy as np
from dateutil.parser import parse

from rparser.nlp import find_ngrams, cos_similarity


RE_NUMBER = re.compile(r"^(?:\+|-|\()?(?: )?\d+(?:(?: |\.)\d{3})*(?:[,]\d+)?(?:\))?$")
RE_FIELDS_SEPARATORS = re.compile(r"(?:\s)*(?:\||\s{2,}|\t|;)(?:\s)*")
RE_ROWS_SEPARATORS = re.compile(r"\n")
RE_ALPHABETIC_CHARS = re.compile(r"[a-zA-ZąćęłńóśźżĄĘŁŃÓŚŹŻ]")
RE_LEADING_NUMBER = re.compile(
    r"^(?:Nota)?(?:\s)*(c(\d+)(?:\.\d+)*|(M{0,4}(CM|CD|D?C{0,3})"
    r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})))(\.|\)| )(?:\s)*"
) 

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


def find_numbers(text):
    '''Find all numbers in str and return list.'''
    numbers = re.findall(RE_NUMBER, text)
    return numbers


def is_number(string, special_zeros=" -"):
    '''Test whether str represents a number.'''
    return string in special_zeros or bool(re.match(RE_NUMBER, string))


def convert_to_number(text, decimal_mark=",", special_zeros=" -"):
    '''Convert string to number.'''
    if isinstance(text, numbers.Number):
        return text

    if not is_number(text):
        return None

    if text in special_zeros:
        return 0.0

    # Determine sign of the number
    sign = -1 if re.match(r"^(-|\()", text) else 1

    # Extract actual number
    number = re.search(
        r"\d+(?:(?: |\.)\d{3})*(?:[" + decimal_mark + r"]\d+)?", text
    )
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


def find_dates(text, re_days=r"\b(01|1|28|29|30|31)", all_days=False):
    '''Find all dates in the text.'''

    if all_days:
        re_days = r"\b\d{1,2}" #(0[1-9]|[12]\d|3[01])

    quarters = {"i": 3, "ii": 6, "iii": 9, "iv": 12}
    months = {"stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, 
              "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
              "wrzenia": 9, "września": 9, "padziernika": 10, 
              "października": 10, "listopada": 11, "grudnia": 12}

    re_date_with_full_month = re.compile(
        re_days + r" (stycznia|lutego|marca|kwietnia|maja|czerwca|"
         r"lipca|sierpnia|wrze(?:ś)?nia|pa(?:ź)?dziernika|listopada|grudnia) "
         r"((?:19|20)\d{2})\b", flags = re.IGNORECASE
    )
    re_quarter = re.compile(
        r"\b(I|II|III|IV) kw(?:\.|arta)?(?:ł)?(?:y)? (\d+)\b", flags=re.IGNORECASE
    )
    re_date_day_month_year = re.compile(
        re_days + r"(?:\.|-)(1[0-2]|0[1-9])(?:\.|-)((?:19|20)\d{2})\b"
    )
    re_date_year_month_day = re.compile(
        r"\b((?:19|20)\d{2})(?:\.|-){1}(1[0-2]|0[1-9])(?:\.|-){1}\b" + re_days
    )
    re_day_and_full_month = re.compile(
        re_days + r" (stycznia|lutego|marca|kwietnia|maja|czerwca|"
         r"lipca|sierpnia|wrze(?:ś)?nia|pa(?:ź)?dziernika|listopada|grudnia)\b", 
         flags = re.IGNORECASE
    )
    re_full_month_and_year = re.compile(
        r"\b(stycznia|lutego|marca|kwietnia|maja|czerwca|"
        r"lipca|sierpnia|wrze(?:ś)?nia|pa(?:ź)?dziernika|listopada|grudnia) "
        r"((?:19|20)\d{2})\b", flags = re.IGNORECASE
    )
    re_day_and_month = re.compile(re_days + r"(?:\.|-)(1[0-2]|0[1-9])\b")
    re_month_and_year = re.compile(r"\b(1[0-2]|0[1-9])(?:\.|-)((?:19|20)\d{2})\b")
    re_year = re.compile(r"((?:19|20)\d{2})\b")

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
    else:
        text = re.sub(re_quarter, "", text) # remove from text

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
    else:
        text = re.sub(re_date_with_full_month, "", text) # remove from text

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
    else:
        text = re.sub(re_date_day_month_year, "", text) # remove from text

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
    else:
        text = re.sub(re_date_year_month_day, "", text) # remove from text

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
    else:
        text = re.sub(re_day_and_full_month, "", text) # remove from text

    # Match 01.01
    match_dates = re.finditer(re_day_and_month, text)
    for match_date in match_dates:
        day, month = match_date.groups()
        try:
            timestamps.append(
                ((None, int(month), int(day)), match_date.span(), 0)
            )
        except ValueError:
            pass # ignore errors in dates
    else:
        text = re.sub(re_day_and_month, "", text) # remove from text

    # Match 'czerwca 2016'
    match_dates = re.finditer(re_full_month_and_year, text)
    for match_date in match_dates:
        month, year = match_date.groups()
        try:
            timestamps.append((
                (int(year), months[month.lower()], None), match_date.span(), 0)
            )
        except ValueError:
            pass # ignore errors in dates
    else:
        text = re.sub(re_full_month_and_year, "", text) # remove from text

    # Match 01.2001 (month - year)
    match_dates = re.finditer(re_month_and_year, text)
    for match_date in match_dates:
        month, year = match_date.groups()
        try:
            timestamps.append((
                (int(year), int(month), None), match_date.span(), 0)
            )
        except ValueError:
            pass # ignore errors in dates
    else:
        text = re.sub(re_month_and_year, "", text) # remove from text

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
    else:
        text = re.sub(re_year, "", text) # remove from text

    # Return timestams in order compliant with their occurence.
    return sorted(timestamps, key=lambda item: item[1][0])


def determine_timerange(text):
    '''
    Determine timerange on the base of text. Return list of potential
    timeranges.
    '''
    tranges = list()

    text = text.lower() 

    # Match IV kwartały
    re_quarters = re.compile(
        r"(I|II|III|IV|1|2|3|4) +kwarta(?:ł)?y +(?:(?:19|20)\d{2})", 
        flags=re.IGNORECASE
    )

    quarters = {"i": 3, "ii": 6, "iii": 9, "iv": 12, "1": 3, "2": 6,
                "3": 9, "4": 12}

    tranges.extend(quarters[q] for q in re.findall(re_quarters, text))

    # Match IV kwartał
    re_quarter = re.compile(
        r"(I|II|III|IV|1|2|3|4) +kw(?:\.|arta)?(?:ł)?", 
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

    re_months = re.compile("(0?[1-9]|1[0-2]) miesi(?:ę|ą)?c(?:y|e)", 
                                flags=re.IGNORECASE)
    tranges.extend(int(month) for month in re.findall(re_months, text))

    re_year = re.compile("Rok zako(?:ń)?czony", flags=re.IGNORECASE)
    tranges.extend(12 for _ in re.findall(re_year, text))

    # Match 01.01.2016 - 31.12.2016
    re_timerange = re.compile(
        r"(?:(0[1-9]|[12]\d|3[01])(?:\.|-))?(0[1-9]|1[0-2])"
        r"(?:(?:\.|-)((?:19|20)\d{2}))? *(?:roku)? *(?:do|-) *(0[1-9]|[12]\d|3[01])"
        r"(?:\.|-)(0[1-9]|1[0-2])(?:(?:\.|-)((?:19|20)\d{2}))? *(?:roku)?",
        flags=re.IGNORECASE
    )

    for re_match in re.finditer(re_timerange, text):
        text_part = text[re_match.span()[0]:(re_match.span()[1]+1)]
        dt1, dt2 = map(operator.itemgetter(0), find_dates(text_part))
        diff_years = 0
        if dt1[0] is not None and dt2[0] is not None:
            if dt1[0] > dt2[0]: # sth is wrong - first date should be earlier
                continue
            diff_years = dt2[0] - dt1[0]
        if diff_years == 0 and dt1[1] > dt2[2]: # sth is wrong - the same year
            continue                            # but first date is earlier
        diff_months = 1 + dt2[1] - dt1[1]
        tranges.append(12*diff_years + diff_months)

    return tranges


def split_text_into_columns(text):
    '''Split multiline text into columns.'''
    # rows4split = list(filter(bool, text.split("\n")))
    rows4split = list(filter(bool, text.split("\n")))

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

    series = [ sr for sr in series if len(sr) > 2 ]

    wsbreaks = list()
    for sr in series:
        max_ws = max(map(operator.itemgetter(1), sr))
        # mval = sr[round(len(sr)/2)][0]
        # msr = [ (abs(val - mval), val) for val, ws in sr if max_ws - ws < 2 ]
        # wsbreaks.append(min(msr, key=operator.itemgetter(0))[1])
        msr = [ index for index, (pos, ws) in enumerate(sr) if max_ws - ws < 2 ]
        index = max([
            (index, (sr[index-1][1] if index > 1 else sr[index][1]) + 
            sr[index][1] + 
            (sr[index+1][1] if index+1 < len(sr) else sr[index][1]))
            for index in msr
        ], key=operator.itemgetter(1))[0]
        wsbreaks.append(operator.itemgetter(index)(sr)[0])

    joincols = [[] for _ in range(len(wsbreaks)+1)]
    for row in rows4split:
        breaks = sorted(list(set([0] + wsbreaks))) + [None]
        for index, (lb, ub) in enumerate(zip(breaks[:-1], breaks[1:])):
            joincols[index].append(row[lb:ub])
    # cols = [ re.sub(" + ", " ", ' '.join(col)) for col in joincols ]

    return joincols


def identify_records(rows, recspec, min_csim=0.85, require_numbers=True, 
                     convert_numbers=True):
    '''Identify records in given rows.'''
    stack = list()
    for index, row in enumerate(rows):
        # Check for presence of label and find the most similar label
        # in specification.
        label_tokens = find_ngrams(row[0], n=1, min_len=2, 
                                   remove_non_alphabetic=True)
        if label_tokens:
            csims = list(map(
                lambda spec: (
                    spec["id"], 
                    cos_similarity(spec["ngrams"], label_tokens)
                ), 
                recspec
            ))

        # Check for presence of numbers in the row
        row_numbers_count = sum(map(is_number, row))

        if label_tokens:
            if row_numbers_count:
                numbers = row[-row_numbers_count:]
            else:
                numbers = None

            try:
                s_label, s_numbers, s_csims, s_index = stack.pop()
            except IndexError:
                stack.append((label_tokens, numbers, csims, (index,)))
            else:
                if not (numbers and s_numbers):
                    ext_label = label_tokens + s_label
                    ext_csims = list(map(
                        lambda spec: (
                            spec["id"], 
                            cos_similarity(spec["ngrams"], ext_label)
                        ), 
                        recspec
                    ))

                    item_selector = operator.itemgetter(1)

                    max_csims = max(csims, key=item_selector)[1]
                    max_s_csims = max(s_csims, key=item_selector)[1]
                    max_ext_csims = max(ext_csims, key=item_selector)[1]
                    
                    if ((max_ext_csims > max_s_csims or 
                            abs(max_ext_csims - max_s_csims) < 1e-10)
                            and max_ext_csims > max_csims
                            # preceeding label has to be driving force 
                            and (
                                max_s_csims > max_csims 
                                or abs(max_s_csims - max_csims) < 1e-10
                            )): 
                        numbers = numbers or s_numbers
                        stack.append((ext_label, numbers, ext_csims, 
                                      s_index + (index,)))
                        continue

                stack.append((s_label, s_numbers, s_csims, s_index))
                stack.append((label_tokens, numbers, csims, (index,)))
                
        elif row_numbers_count:
            numbers = row[-row_numbers_count:] 
            try:
                s_label, s_numbers, s_csims, s_index = stack.pop()
            except IndexError:
                # numbers without preceeding labels - ignore them
                pass
            else:
                if s_label:
                    # probably the id of the note
                    if not s_numbers:
                        s_numbers = numbers
                    elif len(s_numbers) == 1:
                        s_numbers.extend(numbers)
                    else: # some lost numbers - ignore
                        pass 
                    stack.append((s_label, s_numbers, s_csims, 
                                  s_index + (index,)))
                else: # numbers without preceeding labels - ignore them
                    stack.append((s_label, s_numbers, s_csims, s_index))
        else:
            continue

    # Reduce stack
    ident_records = list()
    for label, numbers, csims, rows_indices in stack:
        if require_numbers and not numbers:
            continue
        max_csim = max(csims, key=operator.itemgetter(1))[1]
        if max_csim > min_csim:
            spec_id = sorted(
                ((id, csim) for id, csim in csims 
                    #if (abs(csim - max_csim) < 1e-10 and csim > min_csim)),
                    if csim > min_csim),
                key = operator.itemgetter(1)
            )
            if convert_numbers:
                numbers = [ convert_to_number(num) for num in numbers ]
            ident_records.append(
                (spec_id, numbers, rows_indices)
            )

    # Distirbution of rows
    rows_dist = reduce(
        operator.add, map(operator.itemgetter(-1), ident_records)
    )
    rows_dist_q50 = float(np.percentile(np.array(rows_dist), 50))

    # Remove duplicates/Choose the row with the highest csims
    taken_keys = set()
    taken_rows = list()
    final_records = list()

    while True:
        data = list(
            (label.pop(), numbers, index, row_no) 
            for row_no, (label, numbers, index) in enumerate(ident_records)
                if label and label[-1][0] not in taken_keys
                   and not any(set(index) & rows for rows in taken_rows)
        )  
        if not data:
            break

        for k, g in itertools.groupby(
                sorted(data, key=lambda item: item[0][0], reverse=True), 
                lambda item: item[0][0]
        ):
            group = list(g)
            max_sim = max(list(map(lambda x: x[0][1], group)))
            selected_record = sorted([ 
                (abs(record[2][0] - rows_dist_q50),) + record 
                for record in group if abs(record[0][1] - max_sim) < 1e-10 
            ], key=operator.itemgetter(0))[0][1:]
            final_records.append(selected_record[:-1])
            taken_keys.add(k)
            taken_rows.append(set(selected_record[2]))

    return sorted(final_records, key=lambda item: item[2][0], reverse=False)


def split_sentence_into_tokens(sentence, voc):
    '''Split sentence in accordance with vocabulary.'''
    stack = [(list(), sentence)]
    results =list()

    re_voc = [re.compile("^" + word, flags=re.IGNORECASE) for word in voc]

    while stack:
        tokens, sentence = stack.pop()
        tokens_match = list(filter(
            bool, (re.match(re_word, sentence) for re_word in re_voc)
        ))
        if tokens_match:
            for match in tokens_match:
                stack.append(
                    (tokens + [sentence[slice(*match.span())]], 
                     sentence[match.end():])
                )
        else:
            sentence = sentence[1:]
            if not sentence:
                if tokens:
                    results.append(' '.join(tokens))
            else:
                stack.append((tokens, sentence))

    return results


def fix_white_spaces(rows, voc, recspec=None):
    '''
    Fix broken labels. Sometimes the words are split with white spaces
    without any reason. Concatenate all words and then split long string
    into tokens.
    '''
    # Update vocabulary with tokens from specification of records.
    if recspec:
        voc = set(voc or tuple()) | set( 
            map(str, reduce(
                operator.add, 
                map(operator.itemgetter("ngrams"), recspec)
            ))
        )
        
    # Create list of bigrams, which are used when there are more then one 
    # potential solution.
    if recspec:
        zip_ngrams = map(
            lambda spec: zip(spec["ngrams"][:-1], spec["ngrams"][1:]), 
            recspec
        )
        bigrams = set()
        for item in zip_ngrams:
            bigrams.update(map(lambda ngram: ngram[0] + ngram[1], item))

    # Fix labels
    for row in rows:
        if not len(re.findall(RE_ALPHABETIC_CHARS, row[0])):
            continue
        label_without_spaces = re.sub(' ', '', row[0])
        pot_labels = split_sentence_into_tokens(label_without_spaces, voc)
        if pot_labels: # label fixed, there are some results
            if len(pot_labels) == 1: # one potential label, no much choice
                fixed_label = pot_labels[0]
            elif recspec: # more than one potentail label, use bigrams from spec
                # Choose the label with the largest number of identified bigrams
                temp_bigrams = [(index, set(find_ngrams(label, n=2))) 
                                 for index, label in enumerate(pot_labels)]
                labels_bigrams = list(filter(lambda item: bool(item[1]), 
                                             temp_bigrams))
                if labels_bigrams:
                    labels_fit = sorted([
                        (index, len(bigram & bigrams) / len(bigram)) 
                         for index, bigram in labels_bigrams
                    ], key=operator.itemgetter(1), reverse=True)
                    fixed_label = pot_labels[labels_fit[0][0]]
                else: # there are no bigrams, choose the longest unigram
                    fixed_label = max(pot_labels, key=len)
            else: # no spec, chose the longest label
                fixed_label = max(pot_labels, key=len)

        else: # unabel to fix the label, return original label
            fixed_label = row[0]

        row[0] = fixed_label

    return rows


def preprocess_labels(input_rows):
    '''Row: label (note) number_1 number_2 ... number_n'''

    rows = list(input_rows)

    # 1. Identify and fix column with label
    fields_length_by_rows = list(map(lambda row: list(map(
        lambda field: 
            len(re.findall(RE_ALPHABETIC_CHARS, field)), 
        row
    )), rows))

    for index, row in enumerate(fields_length_by_rows):
        field_with_max_chars = np.array(row).argmax()
        if field_with_max_chars > 0:
            rows[index][0:(field_with_max_chars+1)] = [
                ' '.join(rows[index][0:(field_with_max_chars+1)])
            ]

    # 2. Get rid of leading numbers for labels
    for row in rows:
        # Verify whether the first item in the row is a label
        if not len(re.findall(RE_ALPHABETIC_CHARS, row[0])):
            continue
        row[0] = re.sub(RE_LEADING_NUMBER, "", row[0])

    return rows


def split_row_into_fields(row):
    '''Split text into separate fields.'''
    return list(filter( # use filter to remove empty fields ('')
        bool, re.split(RE_FIELDS_SEPARATORS, row)
    ))


def split_text_into_rows(text):
    '''Split text into rows. Remove empty rows.'''
    rows = re.split(RE_ROWS_SEPARATORS, text)
    rows = [ (i, row) for i, row in enumerate(rows) if not row.isspace() ]
    return rows


def extract_rows(text):
    '''Create simple table. Each row as separate list of fields.'''
    table = [ (row[0], split_row_into_fields(row[1]))
             for row in split_text_into_rows(text)]
    table = [ row for row in table if row[1] ]
    return table


def identify_records_in_text(
    text, spec, voc=None, remove_nonascii=True, 
    fix_spaces=True, min_csim=0.85, require_numbers=True
):
    '''
    Identify records in the text. Preprocess the text in accordance with 
    specified parameters to find the maximal number of records.
     '''
    if remove_nonascii:
        text = remove_non_ascii(text)
    input_rows = extract_rows(text)

    temp_rows = [row[1] for row in input_rows]
    temp_rows = preprocess_labels(temp_rows)
    if fix_spaces:
        temp_rows = fix_white_spaces(temp_rows, voc, spec)

    records = identify_records(
        temp_rows, spec, require_numbers = require_numbers,
        min_csim=min_csim
    )
    return records


def identify_unit_of_measure(text):
    '''
    Identify unit of measure used to measure financial items. Return
    integer representing unit of measure (e.g. 1000 for thousands).
    '''
    re_thousands = re.compile(
        r"\btys(?:\.| |i[aą]?cach) ?(?:PLN|z[lł]?otych|z[lł]?)\b",
        flags = re.IGNORECASE
    )
    th_matches = re.findall(re_thousands, text)

    re_thousands000 = re.compile(r"\bPLN ?'?000\b", flags = re.IGNORECASE)
    th_matches.extend(re.findall(re_thousands000, text))

    re_millions = re.compile(
        r"\b(?:mln|milionach) ?(?:PLN|z[lł]?otych|z[lł]?)\b",
        flags = re.IGNORECASE
    )
    mln_matches = re.findall(re_millions, text)

    if th_matches and mln_matches: # return the most often unit
        if len(mln_matches) > len(th_matches):
            return 1000000
        else:
            return 1000

    if th_matches:
        return 1000

    if mln_matches:
        return 1000000

    return 1