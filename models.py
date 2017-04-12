from functools import reduce
import operator
import itertools

import nltk

from util import pdftotext


class Document:

    def __init__(self, docpath, pgbrk='\x0c', encoding="utf-8",
                 first_page=None, last_page=None):
        self.docpath = docpath
        text, errors = pdftotext(docpath, layout=True, first_page=first_page,
                                 last_page=last_page) 
        if errors:
            raise RuntimeError("pdftotext returned exit code: %r", errors)
        self.raw_text = str(text, encoding)
        self.pages = self.raw_text.split(pgbrk)

    def __len__(self):
        return len(self.pages)

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, index):
        try:
            return self.pages[index]
        except IndexError:
            raise IndexError("page number out of range")


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

        # Filter only consequitive pages staring from the first one.
        cons_pages = map(operator.itemgetter(1), filter(
            lambda item: item[0][0] == item[1], 
            zip(cover_rates, itertools.count(cover_rates[0][0]))
        ))
        pages = [ doc[page] for page in cons_pages ]

        # Override descriptor with current results.
        doc.__dict__[self.attrname] = pages

        return pages



BALANCE_SHEET_WORDS = [
    "skonsolidowane", "sprawozdanie", "aktywa",
    "trwałe", "wartość", "firmy", "wartości", "niematerialne"
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

class FinancialReport(Document):
    balance_sheet = SelfSearchingPage("balance_sheet", BALANCE_SHEET_WORDS)
    # cash_flows = SelfSearchingPage("cash_flow", CASH_FLOW_WORDS)
    # net_and_loss = SelfSearchingPage("net_and_loss", NET_AND_LOSS_WORDS)
    pass