from parser.models import Field


finrecords = [ 
    { 
        "statement": "cfs", "name": "CF#CFFO", 
        "repr": [ 
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności operacyjnej" 
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności operacyjnej"
            }
        ] 
    }, 
    { 
        "statement": "cfs", "name": "CF#CFFI", 
        "repr": [ 
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności inwestycyjnej" 
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności inwestycyjnej"
            }
        ] 
    }, 
    { 
        "statement": "cfs", "name": "CF#CFFF", 
        "repr": [ 
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności finansowej" 
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności finansowej"
            } 
        ] 
    },
    {
        "statement": "cfs", "name": "CF#ZSZRMB",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu zobowiązań i rozliczeń międzyokresowych biernych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#ZSN",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk/ strata netto"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#AST",
        "repr": [
            {
                "lang": "PL", "value": "Amortyzacja środków trwałych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#AWN",
        "repr": [
            {
                "lang": "PL", "value": "Amortyzacja wartości niematerialnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#WSSTWN",
        "repr": [
            {
                "lang": "PL", 
                "value": "Wpływy ze sprzedaży środków trwałych i wartości niematerialnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#WNRATWN",
        "repr": [
            {
                "lang": "PL", 
                "value": "Wydatki na nabycie rzeczowych aktywów trwałych i wartości niematerialnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#WNAF",
        "repr": [
            {
                "lang": "PL", 
                "value": "Wydatki na nabycie aktywów finansowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#KPTO",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty i przychody z tytułu odsetek"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#WTO",
        "repr": [
            {
                "lang": "PL",
                "value": "Wpływy z tytułu odsetek"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#ZSTDI",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk/strata z tytułu działalności inwestycyjnej"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#ZSR",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu rezerw"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#ZSZ",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu zapasów"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#ZSNRMC",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu należności i rozliczeń międzyokresowych czynnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#WNNPZS",
        "repr": [
            {
                "lang": "PL",
                "value": "Wydatki netto na nabycie podmiotów zależnych i stowarzyszonych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#WKP",
        "repr": [
            {
                "lang": "PL",
                "value": "Wpływy z kredytów i pożyczek"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CF#SKP",
        "repr": [
            {
                "lang": "PL",
                "value": "Spłata kredytów i pożyczek"
            }
        ]
    }
]