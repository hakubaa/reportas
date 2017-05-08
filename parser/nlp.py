from functools import reduce
import operator
import math
import re
import numbers
import itertools

import nltk
import string

from parser.util import is_date


# polish stop words (source: wikipedia)
STOP_WORDS = set("a, aby, ach, acz, aczkolwiek, aj, albo, ale, ależ, ani, aż, bardziej, bardzo, bo, bowiem, by, byli, bynajmniej, być, był, była, było, były, będzie, będą, cali, cała, cały, ci, cię, ciebie, co, cokolwiek, coś, czasami, czasem, czemu, czy, czyli, daleko, dla, dlaczego, dlatego, do, dobrze, dokąd, dość, dużo, dwa, dwaj, dwie, dwoje, dziś, dzisiaj, gdy, gdyby, gdyż, gdzie, gdziekolwiek, gdzieś, i, ich, ile, im, inna, inny, innych, iż, ja, ją, jak, jakaś, jakby, jaki, jakichś, jakie, jakiś, jakiż, jakkolwiek, jako, jakoś, je, jeden, jedna, jedno, jednak, jednakże, jego, jej, jemu, jest, jestem, jeszcze, jeśli, jeżeli, już, ją, każdy, kiedy, kilka, kimś, kto, ktokolwiek, ktoś, która, które, którego, której, który, których, którym, którzy, ku, lat, lecz, lub, ma, mają, mało, mam, mi, mimo, między, mną, mnie, mogą, moi, moim, moja, moje, może, możliwe, można, mój, mu, musi, my, na, nad, nam, nami, nas, nasi, nasz, nasza, nasze, naszego, naszych, natomiast, natychmiast, nawet, nią, nic, nich, nie, niech, niego, niej, niemu, nigdy, nim, nimi, niż, no, o, obok, od, około, on, ona, one, oni, ono, oraz, oto, owszem, pan, pana, pani, po, pod, podczas, pomimo, ponad, ponieważ, powinien, powinna, powinni, powinno, poza, prawie, przecież, przed, przede, przedtem, przez, przy, roku, również, sama, są, się, skąd, sobie, sobą, sposób, swoje, ta, tak, taka, taki, takie, także, tam, te, tego, tej, temu, ten, teraz, też, to, tobą, tobie, toteż, trzeba, tu, tutaj, twoi, twoim, twoja, twoje, twym, twój, ty, tych, tylko, tym, u, w, wam, wami, was, wasz, wasza, wasze, we, według, wiele, wielu, więc, więcej, wszyscy, wszystkich, wszystkie, wszystkim, wszystko, wtedy, wy, właśnie, z, za, zapewne, zawsze, ze, zł, znowu, znów, został, żaden, żadna, żadne, żadnych, że, żeby, pln, '000, ..., .., -, +".replace(" ", "").split(","))


class NGram:

    def __init__(self, *args):
        if not args:
            raise TypeError("init expected at least 1 arguments, got 0")
        if not all(isinstance(arg, str) for arg in args):
            raise TypeError("init expected str arguments")
        self._tokens = list(args)

    def __repr__(self):
        return "NGram('{}')".format("', '".join(self._tokens))

    def __str__(self):
        return ' '.join(self)

    def __hash__(self):
        hashes = (hash(token + str(index)) for index, token in enumerate(self))
        return reduce(operator.xor, hashes)

    def __eq__(self, other):
        if isinstance(other, str):
            other = (other,)
        if len(self) != len(other):
            return False
        return tuple(self) == tuple(other)

    def __lt__(self, other):
        if self == other: return False
        for t1, t2 in zip(self, other):
            if t1 < t2:
                return True
            elif t1 > t2:
                return False
        return len(self) < len(other)

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, index):
        cls = type(self)
        if isinstance(index, slice):
            return cls(*self._tokens[index])
        elif isinstance(index, numbers.Integral):
            return self._tokens[index]
        else:
            msg = "{cls.__name__} indices must be integers"
            raise TypeError(msg.format(cls=cls))

    def __iter__(self):
        return iter(self._tokens)

    def __add__(self, other):
        return NGram(*itertools.chain(self, other))

    def __iadd__(self, other):
        self._tokens = list(itertools.chain(self, other))
        return self


def find_ngrams(text, n, min_len=0, remove_non_alphabetic=False, 
                remove_stop_words=True, remove_dates=True,
                return_tuples=False):
    '''Find all n-grams in th text and return list of tuples.'''
    tokens = [token.lower() for token in nltk.tokenize.wordpunct_tokenize(text)]
    tokens = [token for token in tokens 
                    if remove_stop_words and token not in STOP_WORDS 
                       and not token.lstrip("-+(").rstrip(")").isdigit() 
                       and token not in string.punctuation
                       and remove_dates and not is_date(token) 
                       and len(token) >= min_len ]
    if remove_non_alphabetic:
        regex = re.compile(r"[^a-zA-Z]")
        tokens = filter(bool, (re.sub(regex, "", token) for token in tokens))
    ngrams = list(nltk.ngrams(tokens, n))
    if not return_tuples:
        ngrams = [ NGram(*tokens) for tokens in ngrams ]
    return ngrams


def cos_similarity(a, b):
    '''Calculate cos similarity between two iterables.'''
    return len(set(a) & set(b)) / (math.sqrt(len(set(a))) * math.sqrt(len(set(b))))