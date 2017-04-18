# -*- coding: utf-8 -*

from functools import reduce
import operator
import itertools
import reprlib
import numbers

import nltk

import util


# polish stop words (source: wikipedia)
STOP_WORDS = set("a, aby, ach, acz, aczkolwiek, aj, albo, ale, ależ, ani, aż, bardziej, bardzo, bo, bowiem, by, byli, bynajmniej, być, był, była, było, były, będzie, będą, cali, cała, cały, ci, cię, ciebie, co, cokolwiek, coś, czasami, czasem, czemu, czy, czyli, daleko, dla, dlaczego, dlatego, do, dobrze, dokąd, dość, dużo, dwa, dwaj, dwie, dwoje, dziś, dzisiaj, gdy, gdyby, gdyż, gdzie, gdziekolwiek, gdzieś, i, ich, ile, im, inna, inne, inny, innych, iż, ja, ją, jak, jakaś, jakby, jaki, jakichś, jakie, jakiś, jakiż, jakkolwiek, jako, jakoś, je, jeden, jedna, jedno, jednak, jednakże, jego, jej, jemu, jest, jestem, jeszcze, jeśli, jeżeli, już, ją, każdy, kiedy, kilka, kimś, kto, ktokolwiek, ktoś, która, które, którego, której, który, których, którym, którzy, ku, lat, lecz, lub, ma, mają, mało, mam, mi, mimo, między, mną, mnie, mogą, moi, moim, moja, moje, może, możliwe, można, mój, mu, musi, my, na, nad, nam, nami, nas, nasi, nasz, nasza, nasze, naszego, naszych, natomiast, natychmiast, nawet, nią, nic, nich, nie, niech, niego, niej, niemu, nigdy, nim, nimi, niż, no, o, obok, od, około, on, ona, one, oni, ono, oraz, oto, owszem, pan, pana, pani, po, pod, podczas, pomimo, ponad, ponieważ, powinien, powinna, powinni, powinno, poza, prawie, przecież, przed, przede, przedtem, przez, przy, roku, również, sama, są, się, skąd, sobie, sobą, sposób, swoje, ta, tak, taka, taki, takie, także, tam, te, tego, tej, temu, ten, teraz, też, to, tobą, tobie, toteż, trzeba, tu, tutaj, twoi, twoim, twoja, twoje, twym, twój, ty, tych, tylko, tym, u, w, wam, wami, was, wasz, wasza, wasze, we, według, wiele, wielu, więc, więcej, wszyscy, wszystkich, wszystkie, wszystkim, wszystko, wtedy, wy, właśnie, z, za, zapewne, zawsze, ze, zł, znowu, znów, został, żaden, żadna, żadne, żadnych, że, żeby, pln, '000, ..., .., -, +".replace(" ", "").split(","))


class NGram:

    def __init__(self, *args):
        if not args:
            raise TypeError("init expected at least 1 arguments, got 0")
        if not all(isinstance(arg, str) for arg in args):
            raise TypeError("init expected str arguments")
        self._tokens = list(args)

    def __repr__(self):
        return "NGram('{}')".format("', '".join(self._tokens))

    def __hash__(self):
        hashes = (hash(token + str(index)) for index, token in enumerate(self))
        return reduce(operator.xor, hashes)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        return tuple(self) == tuple(other)

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


class Document:

    verbose = False

    def __init__(self, docpath, pgbrk='\x0c', encoding="UTF-8",
                 first_page=None, last_page=None):
        if Document.verbose:
            print("Loading document '{}' ... ".format(docpath), end="")
        self.docpath = docpath
        text, errors = util.pdftotext(docpath, layout=True, first_page=first_page,
                                 last_page=last_page) 
        if errors:
            raise RuntimeError("pdftotext returned exit code: %r", errors)
        self.raw_text = str(text, encoding)
        self.pages = self.raw_text.split(pgbrk)
        if Document.verbose:
            print("DONE")

    def __len__(self):
        return len(self.pages)

    def __hash__(self):
        return hash(self.raw_text)

    def __eq__(self, other):
        if len(self.raw_text) != len(other.raw_text):
            return False
        return self.raw_text == other.raw_text

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, index):
        try:
            return self.pages[index]
        except IndexError:
            raise IndexError("page number out of range")

    def __repr__(self):
        return "Document('{}')".format(self.docpath)


class SelfSearchingPage:

    def __init__(self, attrname, distwords):
        self.distwords = [word.lower() for word in distwords]
        self.attrname = attrname

    def _calc_simple_cover_rate(self, text):
        '''
        Calculate simple cover rate of text with distinctive words. Return two 
        elements tuple containing number of words in the text and cover rate.
        '''
        tokens = [token.lower() for token in nltk.word_tokenize(text)]
        if not tokens:
            return 0, 0
        common_words = [word for word in self.distwords if word in tokens]
        return len(common_words) / len(tokens), len(tokens)

    def __get__(self, doc, owner):
        # Sort doc's pages by cover rate.
        cover_rates = [ (number,) + self._calc_simple_cover_rate(page) 
                        for number, page in enumerate(doc) ]
        cover_rates = sorted(cover_rates, key=lambda x: x[1], reverse=True)

        # Filter only consequitive pages staring from the first one with
        # the highest cover rate.
        cons_pages = map(operator.itemgetter(1), filter(
            lambda item: item[0][0] == item[1], 
            zip(cover_rates, itertools.count(cover_rates[0][0]))
        ))
        pages = [ doc[page] for page in cons_pages ]

        # Override descriptor with current results.
        doc.__dict__[self.attrname] = pages

        return pages



BALANCE_SHEET_WORDS = [
    #"skonsolidowane", "sprawozdanie", 
    "aktywa", "trwałe", "wartość", "firmy", "wartości", "niematerialne"
    "rzeczowe" "nieruchomości", "inwestycyjne", 
    #"finansowe",
    "odroczonego", "podatku", "dochodowego",
    "obrotowe", "zapasy", "należności", "handlowe",
    "bieżącego", "środki", "pieniężne", "ekwiwalenty",
    "pasywa", "kapitały", "własne", "kapitał", 
    "podstawowy", "zapasowy", "aktualizacji",
    "wyceny", "różnice", "kursowe", "rezerwowy",
    "akcje", "własne", "niepodzielone", "wyniki"
    #"przypisane", "akcjonariuszom", "jednostki", "dominującej",
    "udziały", "niedające", "kontroli", "zobowiązania", "długoterminowe",
    "kredyty", "pożyczki", "wyemitowane", "papiery", "dłużne",
    "rezerwa", "odroczony", "podatek", "dochodowy"
    #"świadczenia", "pracownicze", 
    "krótkoterminowe",
    "handlowe", "tytułu", "bieżącego", "podatku",
    "rezerwy", "zobowiązań", "pasywów", "wartość", "księgowa", "akcji",
    "rozwodniona"
]

CASH_FLOW_WORDS = [
    
]



# NGram("skonsolidowane", "sprawozdanie"),
# NGram("przepływów", "pieniężnych"),
# NGram("środki", "pieniężne", "netto", "działalności", "finansowej"),
# NGram("środki", "pieniężne")
# NGram("środki", "pieniężne", "ekwiwalenty")

# NGram("działalność", "operacyjna")
# NGram("amorytzacja")
# NGram("przepływy", "operacyjne")
# NGram("zmiana", "stanu", "zapasów")
# NGram("zmiana", "stanu", "należności")
# NGram("zmiana", "stanu", "zobowiązań")
# NGram("zmiana", "stanu", "rezerw")
# NGram("działalność", "inwestycyjna")
# NGram("działalności", "inwestycyjnej")
# NGram("sprzedaż", "rzeczowych", "aktywów")
# NGram("nabycie", "rzeczowych", "aktywów", "trwałych")



# "przepływów" 
# "pieniężnych" 
# "działalność"
# "finansowa"
# "wpływy"
# "zaciągniętych" 
# "kredytów" 
# "pożyczek"
#   Wpływy z innych źródeł finansowania (umowa faktoringu)
#   Dywidendy dla akcjonariuszy jednostki dominującej
# "spłata"
# "odsetki"
#  zapłacone dotyczące działalności finansowej
# "środki pieniężne" 
# "netto" z działalności finansowej


#  Środki pieniężne netto z działalności
#    Środki pieniężne i ich ekwiwalenty na początek okresu
#    Efekt zmiany kursów walut
#  Środki pieniężne i ich ekwiwalenty na końcu okresu
#  Struktura środków pieniężnych i ich ekwiwalentów:
#    Środki o nieograniczonej możliwości dysponowania
#    Środki o ograniczonej możliwości dysponowania


#  * w tym 1.999 tys. zł należące do Energii Park Trzemoszna (spółka zależna) utrzymywane na rachunku o ograniczonej
#  możliwości dysponowania.



class FinancialReport(Document):
    balance_sheet = SelfSearchingPage("balance_sheet", BALANCE_SHEET_WORDS)
    # cash_flows = SelfSearchingPage("cash_flow", CASH_FLOW_WORDS)
    # net_and_loss = SelfSearchingPage("net_and_loss", NET_AND_LOSS_WORDS)
    pass


