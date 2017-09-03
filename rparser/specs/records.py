# -*- coding: utf-8 -*-

# lotos_2014_y.pdf
# pge_2016_y.pdf
# lpp_2016_q1.pdf
# decora_2016_q1.pdf
# kghm_2016_y.pdf
# arctic_2016_q3.pdf
# dbc_2016_q4.pdf
# tpe_2016_y.pdf
# ltx_2016_y.pdf
# protektor_2016_q3.pdf
# rpc_2016_q3.pdf

finrecords = [ 
################################################################################
# CASH FLOW STATEMENT - CFS
################################################################################
    {
        "statement": "cfs", "name": "CFS#TOTALNETCASHFLOWS", 
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przepływy pieniężne netto razem"
            },
            {
                "lang": "PL",
                "value": "ZMIANA NETTO STANU ŚRODKÓW PIENIĘŻNYCH I ICH EKWIWALENTÓW"
            },
            {
                "lang": "PL",
                "value": "Zwiększenie/(zmniejszenie) netto stanu środków "
                         "pieniężnych i ich ekwiwalentów"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne netto"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CASHOPENINGBALANCE", 
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Środki pieniężne na początek okresu"
            },
            {
                "lang": "PL",
                "value": "Stan środków pieniężnych i ich ekwiwalentów na początek okresu"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne i ich ekwiwalenty na początku okresu"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne, ekwiwalenty środków pieniężnych "
                         "oraz kredyty w rachunku bieżącym na początek okresu"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CLOSINGBALANCEOFCASH",
        "timeframe": "pot", 
        "repr": [
            {
                "lang": "PL",
                "value": "Środki pieniężne na koniec okresu"
            },
            {
                "lang": "PL",
                "value": "Stan środków pieniężnych i ich ekwiwalentów na koniec okresu"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne i ich ekwiwalenty na koniec okresu"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne, ekwiwalenty środków "
                         "pieniężnych oraz kredyty w rachunku bieżącym na "
                         "koniec okresu"
            }
        ]
    },
    { 
        "statement": "cfs", "name": "CFS#NETCFFROMOPERATINGACTIVITIES",
        "timeframe": "pot",
        "repr": [ 
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności operacyjnej" 
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności operacyjnej"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne netto z działalności operacyjnej"
            }
        ] 
    }, 
    { 
        "statement": "cfs", "name": "CFS#NETCFFROMINVESTMENTACTIVITIES",
        "timeframe": "pot",
        "repr": [ 
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności inwestycyjnej" 
            },
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności inwest." 
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności inwestycyjnej"
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności inwest."
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne netto z działalności inwestycyjnej"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne netto z działalności inwest."
            },
            {
                "lang": "PL",
                "value": "Przepływy pieniężne netto z działalności inwest."
            }
        ] 
    }, 
    { 
        "statement": "cfs", "name": "CFS#NETCFFROMFINANCIALACTIVITIES",
        "timeframe": "pot", 
        "repr": [ 
            { 
                "lang": "PL", 
                "value": "Przepływy pieniężne netto z działalności finansowej" 
            },
            {
                "lang": "PL",
                "value": "Przepływy środków pieniężnych netto z działalności finansowej"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne netto z działalności finansowej"
            }
        ] 
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINSHORTTERMLIABILITIES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu zobowiązań za wyjątkiem kredytów"
            },
            {
                "lang": "PL",
                "value": "(Zmniejszenie)/Zwiększenie stanu zobowiązań z tytułu dostaw i usług"
            },
            {
                "lang": "PL",
                "value": "Zmiana stanu zobowiązań z wyjątkiem kredytów i pożyczek"
            },
            {
                "lang": "PL",
                "value": "Zmiana stanu zobowiązań krótkoterminowych, z wyjątkiem pożyczek i kredytów"
            },
            {
                "lang": "PL",
                "value": "Zmiana stanu zobowiązań"
            },
            {
                "lang": "PL",
                "value": "(Zwiększenie)/zmniejszenie stanu zobowiązań"
            },
            {
                "lang": "PL",
                "value": "Zmiana stanu zobowiązań krótkoterminowych oraz pozostałych zobowiązań"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINCURRENTASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu kapitału obrotowego"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINPREPAYMENTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu rozliczeń międzyokresowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINTAX",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu aktywów z tytułu podatku odroczonego"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#NETPROFIT",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk/strata netto"
            },
            {
                "lang": "PL",
                "value": "Zysk netto"
            },
            {
                "lang": "PL",
                "value": "Strata netto"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) netto przypadająca akcjonariuszom jednostki dominującej"
            },
            {
                "lang": "PL",
                "value": "Zysk netto za okres"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) netto za okres sprawozdawczy, przypadający"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) netto za okres sprawozdawczy"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#NETPROFITONRELATEDENTITIES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Udział w (zyskach) stratach netto jednostek "
                         "podporządkowanych wycenianych metodą praw własności"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#GROSSPROFIT",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk brutto z działalności kontynuowanej oraz zysk (strata) z działalności zaniechanej"
            },
            {
                "lang": "PL",
                "value": "Zysk / Strata przed opodatkowaniem"
            },
            {
                "lang": "PL",
                "value": "Zysk/(strata) brutto"
            },
            {
                "lang": "PL",
                "value": "Zysk brutto za okres"
            },
            {
                "lang": "PL",
                "value": "Zysk przed opodatkowaniem"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#AMORTISATIONONFIXEDASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL", "value": "Amortyzacja środków trwałych"
            },
            {
                "lang": "PL", "value": "Amortyzacja wartości rzeczowych aktywów trwałych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#AMORTISATIONONINTANGIBLEASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL", "value": "Amortyzacja wartości niematerialnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#AMORTISATION",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL", "value": "Amortyzacja"
            },
            {
                "lang": "PL", 
                "value": "Amortyzacja, likwidacja oraz odpisy aktualizujące"
            },
            {
                "lang": "PL",
                "value": "Amortyzacja ujęta w wyniku finansowym"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#DISPOSALOFFIXEDASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL", 
                "value": "Wpływy ze sprzedaży środków trwałych i wartości niematerialnych"
            },
            {
                "lang": "PL",
                "value": "Zbycie aktywów trwałych"
            },
            {
                "lang": "PL",
                "value": "Sprzedaż rzeczowych aktywów trwałych i aktywów niematerialnych"
            },
            {
                "lang": "PL",
                "value": "Zbycie aktywów niematerialnych oraz rzeczowych aktywów trwałych"
            },
            {
                "lang": "PL",
                "value": "Zbycie wartości niematerialnych i prawnych oraz "
                         "rzeczowych aktywów trwałych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#PURCHASEOFFIXEDASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL", 
                "value": "Wydatki na nabycie rzeczowych aktywów trwałych i wartości niematerialnych"
            },
            {
                "lang": "PL",
                "value": "Nabycie aktywów trwałych"
            },
            {
                "lang": "PL",
                "value": "Zakup środków trwałych i wartości niematerialnych"
            },
            {
                "lang": "PL",
                "value": "Zakup rzeczowych aktywów trwałych i aktywów niematerialnych"
            },
            {
                "lang": "PL",
                "value": "Nabycie rzeczowych aktywów trwałych i wartości niematerialnych"
            },
            {
                "lang": "PL",
                "value": "Nabycie aktywów niematerialnych oraz rzeczowych aktywów trwałych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#PURCHASEOFFINANCIALASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL", 
                "value": "Wydatki na nabycie aktywów finansowych"
            },
            {
                "lang": "PL",
                "value": "Wydatki na aktywa finansowe"
            },
            {
                "lang": "PL",
                "value": "Nabycie aktywów finansowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#REVENEUSFROMSALEOFFINANCIALASSETS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody z aktywów finansowych"
            },
            {
                "lang": "PL",
                "value": "Sprzedaż aktywów finansowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#KPTO",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty i przychody z tytułu odsetek"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#WTO",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Wpływy z tytułu odsetek"
            },
            {
                "lang": "PL",
                "value": "Odsetki otrzymane"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#PROFITONINVESTMENTACTIVITIES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk/strata z tytułu działalności inwestycyjnej"
            },
            {
                "lang": "PL",
                "value": "(Zysk) strata z działalności inwestycyjnej"
            },
            {
                "lang": "PL",
                "value": "(Zyski)/Straty z tytułu działalności inwestycyjnej"
            },
            {
                "lang": "PL",
                "value": "Zyski / strata na działalności inwestycyjnej"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINPROVISIONS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu rezerw"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEININVETORY",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu zapasów"
            },
            {
                "lang": "PL",
                "value": "Zmniejszenie stanu zapasów",
            },
            {
                "lang": "PL",
                "value": "Zwiększenie stanu zapasów"
            },
            {
                "lang": "PL",
                "value": "(Zwiększenie)/zmniejszenie stanu zapasów"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINRECEIVABLES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu należności"
            },
            {
                "lang": "PL",
                "value": "Zmniejszenie stanu należności z tytułu dostaw i usług"
            },
            {
                "lang": "PL",
                "value": "Zwiększenie stanu należności z tytułu dostaw i usług"
            },
            {
                "lang": "PL",
                "value": "Zmiana stanu należności oraz pozostałych aktywów niefinansowych"
            },
            {
                "lang": "PL",
                "value": "(Zwiększenie)/zmniejszenie stanu należności"
            },
            {
                "lang": "PL",
                "value": "Zmiana stanu należności z tytułu dostaw i usług oraz pozostałych należności"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CHANGEINRECEIVABLESANDPREPAYAMENTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu należności i rozliczeń międzyokresowych czynnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#WNNPZS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Wydatki netto na nabycie podmiotów zależnych i stowarzyszonych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#INFLOWSFROMCREDITSANDLOANS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Wpływy z kredytów i pożyczek"
            },
            {
                "lang": "PL",
                "value": "Wpływy z tytułu kredytów i pożyczek"
            },
            {
                "lang": "PL",
                "value": "Wpływy z tytułu zaciągnięcia pożyczek/kredytów"
            },
            {
                "lang": "PL",
                "value": "Wpływy z tytułu zaciągniętych kredytów"
            },
            {
                "lang": "PL",
                "value": "Wpływy z tytułu zaciągnięcia pożyczek, kredytów i emisji obligacji"
            },
            {
                "lang": "PL",
                "value": "Kredyty i pożyczki"
            },
            {
                "lang": "PL",
                "value": "Kredyty bankowe i pożyczki zaciągnięte"
            },
            {
                "lang": "PL",
                "value": "Wpływy z tytułu zaciągniętego zadłużenia"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#REPAYMENTOFCREDITSANDLOANS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Spłata kredytów i pożyczek"
            },
            {
                "lang": "PL",
                "value": "Spłata pożyczek, kredytów i papierów dłużnych"
            },
            {
                "lang": "PL",
                "value": "Spłata kredytów"
            },
            {
                "lang": "PL",
                "value": "Wydatki z tytułu spłaty kredytów"
            },
            {
                "lang": "PL",
                "value": "Spłata pożyczek, kredytów, obligacji i leasingu finansowego"
            },
            {
                "lang": "PL",
                "value": "Spłata pożyczek, kredytów i obligacji"
            },
            {
                "lang": "PL",
                "value": "Spłata kredytów bankowych i pożyczek zaciągniętych"
            },
            {
                "lang": "PL",
                "value": "Płatności z tytułu zadłużenia"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#SUP", # przepływy inwestycyjne
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Spłata udzielonych pożyczek"
            }
        ]
    },
     {
        "statement": "cfs", "name": "CFS#UP", # przepływy inwestycyjne
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Udzielenie pożyczek"
            }
        ]
    },   
    {
        "statement": "cfs", "name": "CFS#UN",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Udziały niekontrolujące"
            },
            {
                "lang": "PL",
                "value": "Zyski udziałowców mniejszościowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#EXCHANGEGAINS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zyski/straty z tytułu różnic kursowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CURRENTINCOMETAX",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Podatek dochodowy bieżący"
            },
            {
                "lang": "PL",
                "value": "Podatek dochodowy"
            }
        ]
    },
    {   # Przepływy środków pieniężnych z działalności operacyjnej
        "statement": "cfs", "name": "CFS#OID",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Odsetki i udziały w zyskach"
            },
            {
                "lang": "PL",
                "value": "Odsetki i dywidendy netto"
            },
            {
                "lang": "PL",
                "value": "Odsetki i dywidendy"
            },
            {
                "lang": "PL",
                "value": "Odsetki i udziały w zyskach (dywidendy)"
            },
            {
                "lang": "PL",
                "value": "Przychody z tytułu dywidend"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#DIVIDENDGET",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Dywidendy otrzymane"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#INCOMETAXPAID",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Podatek zapłacony"
            },
            {
                "lang": "PL",
                "value": "Podatek dochodowy zapłacony"
            }
        ]        
    },
    {
        "statement": "cfs", "name": "CFS#DIVIDENTSPAY",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Dywidendy zapłacone"
            },
            {
                "lang": "PL",
                "value": "Dywidendy wypłacone"
            },
            {
                "lang": "PL",
                "value": "Dywidendy i inne wypłaty na rzecz właścicieli"
            },
            {
                "lang": "PL",
                "value": "Dywidendy wypłacone akcjonariuszom"
            },
            {
                "lang": "PL",
                "value": "Dywidendy wypłacone akcjonariuszom Jednostki Dominującej"
            }
        ]        
    },
    {
        "statement": "cfs", "name": "CFS#PURCHASEOFOWNSHARES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Nabycie akcji własnych"
            }
        ]   
    },
    {
        "statement": "cfs", "name": "CFS#UAW",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Umorzenie akcji własnych"
            }
        ]   
    },
    { # Przepływy środków pieniężnych z działalności finansowej - Wydatki
        "statement": "cfs", "name": "CFS#INTEREST",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Odsetki zapłacone"
            },
            {
                "lang": "PL",
                "value": "Odsetki"
            },
            {
                "lang": "PL",
                "value": "Zapłacone odsetki i pozostałe koszty zadłużenia"
            }
        ]        
    },
################################################################################
# NET AND LOSS STATEMENT - ICS
################################################################################
# acp_2010_q1.pdf
# ambra_2008_y.pdf
# bdx_2012_y.pdfddddd
# cng_2016_y.pdf (to check)
# decora_2016_q1.pdf (to check)
# wieleton 2016_y.pdf (to check)
# tpe_2016_y.pdf (to check)
# kst_2016_y.pdf (to check)
# helio_2016_m2.pdf
# obl_2016_y.pdf
# ursus_2016_y.pdf

    {
        "statement": "ics", "name": "ICS#REVENUESFROMSALE",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Przychody brutto ze sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Przychody netto ze sprzedaży produktów i usług "
                         "oraz towarów i materiałów"
            },
            {
                "lang": "PL",
                "value": "Przychody"
            },
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży towarów i produktów"
            }, 
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży usług, produktów, towarów i materiałów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#REVENUESFROMSALESOFPRODUCTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży produktów"
            },
            {
                "lang": "PL",
                "value": "Przychody netto ze sprzedaży produktów"
            },
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży wyrobów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#REVENUESFROMSALESOFSERVICES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży usług"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#REVENUESFROMSALEOFGOODS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży towarów"
            },
            {
                "lang": "PL",
                "value": "Przychody netto ze sprzedaży towarów i materiałów"
            },
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży towarów i materiałów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#REVENESFROMSALESOFPRODUCTSANDSERVICES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody netto ze sprzedaży produktów i usług"
            },
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży produktów i usług"
            },
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży wyrobów i usług"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTOFSALE",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt własny sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Koszty sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Koszty sprzedanych produktów i usług oraz towarów i materiałów"
            },
            {
                "lang": "PL",
                "value": "Koszt sprzedanych towarów, produktów, materiałów i usług"
            },
            {
                "lang": "PL",
                "value": "Koszty sprzedanych produktów, towarów i materiałów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTOFMATERIALS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zużycie materiałów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTOFGOODS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt własny sprzedanych towarów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTOFGOODSANDMATERIALS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zużycie materiałów i koszt własny sprzedanych towarów"
            },
            {
                "lang": "PL",
                "value": "Koszt sprzedanych towarów i materiałów"
            },
            {
                "lang": "PL",
                "value": "Wartość sprzedanych towarów i materiałów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTOFPRODUCTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt sprzedanych produktów"
            },
            {
                "lang": "PL",
                "value": "Koszt wytworzenia sprzedanych produktów"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTOFSERVICES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt sprzedanych usług"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#COSTPOFRODUCTSANDSERVICES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt wytworzenia sprzedanych produktów i usług"
            },
            {
                "lang": "PL",
                "value": "Koszt wytworzenia sprzedanych wyrobów i usług"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#GROSSPROFITONSALES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk brutto ze sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Wynik brutto ze sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) brutto ze sprzedaży"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#SELLINGCOSTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Pozostałe koszty działalności operacyjnej"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#ADMINISTRATIVECOSTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty ogólnego zarządu"
            },
            {
                "lang": "PL",
                "value": "Wynagrodzenia i świadczenia na rzecz pracowników" 
            }
        ]
    },
    { # ICS#COSTSELLING + ICS#COSTOFMANAGEMENT"
        "statement": "ics", "name": "ICS#SELLINGANDADMINISTRATIVECOSTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty administracyjne i sprzedaży"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#NETPROFITONSALE",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk netto ze sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Zysk na sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Zysk/(strata) netto ze sprzedaży"
            },
            {
                "lang": "PL",
                "value": "Wynik ze sprzedaży"
            }
        ]
    },    
    {
        "statement": "ics", "name": "ICS#OPERATINGREVENUES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Pozostałe przychody operacyjne"
            }
        ]
    },  
    {
        "statement": "ics", "name": "ICS#OPERATINGEXPENSES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Pozostałe koszty operacyjne"
            }
        ]
    }, 
    {
        "statement": "ics", "name": "ICS#PROFITONOPERATINGACTIVITIES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk z działalności operacyjnej"
            },
            {
                "lang": "PL",
                "value": "Wynik operacyjny"
            }
        ]
    }, 
    {
        "statement": "ics", "name": "ICS#FINANCIALREVENUES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody finansowe"
            }
        ]
    },    
    {
        "statement": "ics", "name": "ICS#FINANCIALEXPENSES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty finansowe"
            }
        ]
    },   
    {
        "statement": "ics", "name": "ICS#PROFITONRELATEDPARTIES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Udział w zyskach jednostek stowarzyszonych i wspólnych przedsięwzięć"
            },
            {
                "lang": "PL",
                "value": "Zysk/strata na sprzedaży całości lub części udziałów jednostek zależnych"
            },
            {
                "lang": "PL",
                "value": "Udział w zyskach jednostek stowarzyszonych i wspólnych przedsięwzięć"
            },
            {
                "lang": "PL",
                "value": "Udział w zysku netto jednostki stowarzyszonej"
            },
            {
                "lang": "PL",
                "value": "Udział w zyskach (stratach) netto jednostek stowarzyszonych"
            },
            {
                "lang": "PL",
                "value": "ZYSK (STRATA) Z UDZIAŁÓW W JEDNOSTKACH PODPORZĄDKOWANYCH"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#NETABANDONED",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Działalność zaniechana"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) netto z działalności zaniechanej"
            },
            {
                "lang": "PL",
                "value": "Wynik netto z działalności zaniechanej"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#GROSSPROFIT",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk brutto"
            },
            {
                "lang": "PL",
                "value": "Zysk/(strata) brutto"
            },
            {
                "lang": "PL",
                "value": "Wynik brutto z działalności kontynuowanej"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) przed opodatkowaniem"
            }
        ]
    },  
    {
        "statement": "ics", "name": "ICS#INCOMETAX",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Podatek dochodowy (bieżące i odroczone obciążenie podatkowe)"
            },
            {
                "lang": "PL",
                "value": "Podatek dochodowy"
            },
            {
                "lang": "PL",
                "value": "Podatek"
            }
        ]
    }, 
    {
        "statement": "ics", "name": "ICS#NETPROFIT",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk netto"
            },
            {
                "lang": "PL",
                "value": "Zysk za okres sprawozdawczy"
            },
            {
                "lang": "PL",
                "value": "Zysk netto za okres"
            },
            {
                "lang": "PL",
                "value": "Zysk/(strata) netto"
            },
            {
                "lang": "PL",
                "value": "Wynik netto"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#NETPROFITPERSHARE",
        "timeframe": "pot",
        "reprs": [
            {
                "lang": "PL",
                "value": "Zysk netto na akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk netto na jedną akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk/strata na akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk/strata na jedną akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) na akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) na jedną akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) netto na akcję"
            },
            {
                "lang": "PL",
                "value": "Zysk (strata) netto na jedną akcję"
            },
            {
                "lang": "PL",
                "value": "Starta na akcję"
            },
            {
                "lang": "PL",
                "value": "Starta na jedną akcję"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#NETPROFITCONT",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk/(strata) netto z działalności kontynuowanej"
            },
            {
                "lang": "PL",
                "value": "Zysk netto z działalności kontynuowanej"
            },
            {
                "lang": "PL",
                "value": "Wynik netto z działalności kontynuowanej"
            }
        ]
    },    
    {
        "statement": "ics", "name": "ICS#NETPROFITTOOWNERS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Akcjonariuszom Jednostki Dominującej"
            },
            {
                "lang": "PL",
                "value": "Zysk/(strata) akcjonariuszy jednostki dominującej"
            },
            {
                "lang": "PL",
                "value": "akcjonariuszom podmiotu dominującego"
            },
            {
                "lang": "PL",
                "value": "przypadający akcjonariuszy jedn. dominującej"
            }
        ]
    },    
    {
        "statement": "ics", "name": "ICS#NETPROFITTONONOWNERS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Udziałowcom mniejszościowym"
            },
            {
                "lang": "PL",
                "value": "Zysk/(strata) mniejszości"
            },
            {
                "lang": "PL",
                "value": "udziałom niedającym kontroli"
            },
            {
                "lang": "PL",
                "value": "podmiotom niekontrolującym"
            },
            {
                "lang": "PL",
                "value": "przypadający akcjonariuszom nie posiadającym kontroli"
            },
            {
                "lang": "PL",
                "value": "AKCJONARIUSZOM MNIEJSZOŚCIOWYM"
            }
        ]
    },   
    {
        "statement": "ics", "name": "ICS#SHARESCOUNT",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Średnia ważona liczba akcji zwykłych"
            },
            {
                "lang": "PL",
                "value": "Średnia ważona ilość akcji"
            },
            {
                "lang": "PL",
                "value": "Średnia ważona liczba akcji zwykłych w (w szt.)"
            },
            {
                "lang": "PL",
                "value": "Średnia ważona ilość akcji (w sztukach)"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#EXTRAORDINARYGAINS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Zyski nadzwyczajne"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#EXTRAORDINARYLOSSES",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Straty nadzwyczajne"
            }
        ]
    },
    {
        "statement": "ics", "name": "ICS#RESULTONEXTRAORDINARYEVENTS",
        "timeframe": "pot",
        "repr": [
            {
                "lang": "PL",
                "value": "Wynik zdarzeń nadzwyczajnych"
            }
        ]
    },
################################################################################
# BALANCE SHEET
################################################################################
# acp_2010_q1.pdf
# ambra_2008_y.pdf
# bdx_2012_y.pdf
# cng_2016_y.pdf 
# decora_2016_q1.pdf 
# wieleton_2016_y.pdf
# tpe_2016_y.pdf 
# kst_2016_y.pdf 
# helio_2016_m2.pdf
# obl_2016_y.pdf
# ursus_2016_y.pdf

    {
        "statement": "bls", "name": "BLS#INTANGIBLEASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Wartości niematerialne i prawne"
            },
            {
                "lang": "PL",
                "value": "Wartości niematerialne"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#RDEXPENSES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty zakończonych prac rozwojowych"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#GOODWILL",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Wartość firmy"
            },
            {
                "lang": "PL",
                "value": "Wartość firmy z konsolidacji"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#OTHERINTANGIBLEASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Inne wartości niematerialne i prawne"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#ADVANCESINTANGIBLEASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zaliczki na wartości niematerialne i prawne"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#TANGIBLEFIXEDASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Rzeczowe aktywa trwałe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#TANGIBLEFIXEDASSETSINUSE",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Środki trwałe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#TANGIBLEFIXEDASSETSUNDERCONSTRUCTION",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Środki trwałe w budowie"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#ADVANCESFORTANGIBLEFIXEDASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zaliczki na środki trwałe w budowie"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGTERMRECEIVABLES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Należności długoterminowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGTERMINVESTMENTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Inwestycje długoterminowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#REALPROPERTY",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Nieruchomości"
            },
            {
                "lang": "PL",
                "value": "Nieruchomości inwestycyjne"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGTERMFINANCIALASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Długoterminowe aktywa finansowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#OTHERLONGTERMINVESTMENTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Inne inwestycje długoterminowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGTERMPREPAYMENTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Długoterminowe rozliczenia międzyokresowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#FIXEDASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Aktywa trwałe"
            },
            {
                "lang": "PL",
                "value": "Aktywa trwałe razem"
            },
            {
                "lang": "PL",
                "value": "Aktywa trwałe (długoterminowe) ogółem"
            },
            {
                "lang": "PL",
                "value": "Aktywa trwałe ogółem"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#CURRENTASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Aktywa obrotowe"
            },
            {
                "lang": "PL",
                "value": "Aktywa obrotowe razem"
            },
            {
                "lang": "PL",
                "value": "Aktywa obrotowe (krótkoterminowe) ogółem"
            },
            {
                "lang": "PL",
                "value": "Aktywa obrotowe ogółem"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#INVENTORY",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zapasy"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#MATERIALS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Materiały"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SEMIFINISHEDPRODUCTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Półprodukty i produkty w toku"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#FINISHEDPRODUCTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Produkty gotowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#GOODS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Towary"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#ADVANCESFORDELIVIERIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zaliczki na dostawy i usługi"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMRECEIVABLES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Należności krótkoterminowe"
            },
            { # SPLIT WHEN REQUIRED
                "lang": "PL",
                "value": "Należności z tytułu dostaw i usług"
            },
            {
                "lang": "PL",
                "value": "Należności handlowe"
            },
            {
                "lang": "PL",
                "value": "Należności handlowe oraz pozostałe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMINVESTMENTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Inwestycje krótkoterminowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMFINANCIALASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Krótkoterminowe aktywa finansowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#CASHINHAND",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "środki pieniężne i inne aktywa pieniężne"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne i depozyty krótkoterminowe"
            },
            {
                "lang": "PL",
                "value": "Środki pieniężne i ich ekwiwalenty"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#OTHERSHORTTERMINVESTMENTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Inne inwestycje krótkoterminowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMPREPAYMENTS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Krótkoterminowe rozliczenia międzyokresowe"
            },
            {
                "lang": "PL",
                "value": "Rozliczenia międzyokresowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#TOTALASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Aktywa razem"
            },
            {
                "lang": "PL",
                "value": "Suma aktywów"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#DEFERREDTAXASSETS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Aktywa z tytułu podatku odroczonego"
            },
            {
                "lang": "PL",
                "value": "Aktywa z tytułu odroczonego podatku dochodowego"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#EQUITY",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Kapitał (fundusz) własny"
            },
            {
                "lang": "PL",
                "value": "Kapitał własny"
            },
            {
                "lang": "PL",
                "value": "Kapitały własne"
            },
            {
                "lang": "PL",
                "value": "Kapitał własny ogółem"
            },
            {
                "lang": "PL",
                "value": "Kapitały własne ogółem"
            },
            {
                "lang": "PL",
                "value": "Kapitał własny razem"
            },
            {
                "lang": "PL",
                "value": "Kapitały własne razem"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#EQUITYOWNERS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Kapitał własny (przypisany akcjonariuszom Jednostki Dominującej)"
            },
            {
                "lang": "PL",
                "value": "Kapitał własny akcjonariuszy jednostki dominującej"
            },
            {
                "lang": "PL",
                "value": "Kapitały przypisane akcjonariuszom jednostki dominującej"
            },
            {
                "lang": "PL",
                "value": "Kapitał własny przypadający akcjonariuszom jednostki dominującej"
            },
            {
                "lang": "PL",
                "value": "Kapitały przypadające akcjonariuszom jednostki dominującej"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#EQUITYNOTOWNERS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Udziały mniejszości"
            },
            {
                "lang": "PL",
                "value": "Udziały niedające kontroli"
            },
            {
                "lang": "PL",
                "value": "Kapitał przypadający udziałom niedającym kontroli"
            },
            {
                "lang": "PL",
                "value": "Udziały niekontroluj1ce"
            },
            {
                "lang": "PL",
                "value": "Kapitały przypadające akcjonariuszom mniejszościowym"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SURPLUSFROMSOLDSHARES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Nadwyżka ze sprzedaży akcji powyżej ich wartości nominalnej"
            },
            {
                "lang": "PL",
                "value": "Kapitał z emisji akcji powyżej ich wartości nominalnej"
            },
            {
                "lang": "PL",
                "value": "Kapitał ze sprzedaży akcji powyżej ich wartości nominalnej"
            },
            {
                "lang": "PL",
                "value": "Nadwyżka ze sprzedaży akcji"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#OWNSHARES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Akcje własne"
            },
            {
                "lang": "PL",
                "value": "Udziały (akcje) własne (wielkość ujemna)"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHARECAPITAL",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Kapitał (fundusz) podstawowy"
            },
            {
                "lang": "PL",
                "value": "Kapitał podstawowy"
            },
            {
                "lang": "PL",
                "value": "Kapitał akcyjny"
            },
            {
                "lang": "PL",
                "value": "Kapitał zakładowy"
            },
            {
                "lang": "PL",
                "value": "Wyemitowany kapitał akcyjny"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SUPPLEMENTARYCAPITAL",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Kapitał (fundusz) zapasowy"
            },
            {
                "lang": "PL",
                "value": "Kapitał zapasowy"
            },
            {
                "lang": "PL",
                "value": "Pozostałe kapitały zapasowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#REVALUATIONRESERVE",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Kapitał (fundusz) z aktualizacji wyceny"
            },
            {
                "lang": "PL",
                "value": "Kapitał z aktualizacji wyceny"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#OTHERRESERVECAPITALS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Pozostałe kapitały (fundusze) rezerwowe"
            },
            {
                "lang": "PL",
                "value": "Pozostałe kapitały rezerwowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#RESERVECAPITALS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Kapitał rezerwowy"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#PREVIOUSYEARSPROFIT",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk (strata) z lat ubiegłych"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#NETPROFIT",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk (strata) netto"
            },
          {
                "lang": "PL",
                "value": "Zysk/(strata) netto roku bieżącego"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#PREVIOUSANDCURRENTNETPROFIT",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zyski (straty) z lat ubiegłych i wynik okresu bieżącego"
            },
            {
                "lang": "PL",
                "value": "Zyski (straty) zatrzymane"
            },
            {
                "lang": "PL",
                "value": "Zyski zatrzymane"
            }
        ]
    },

    {
        "statement": "bls", "name": "BLS#WRITEOFFNETPROFIT",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Odpisy z zysku netto w ciągu roku obrotowego (wielkość ujemna)"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LIABILITIESANDPROVISIONS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zobowiązania i rezerwy na zobowiązania"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#PROVISIONSFORLIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Rezerwy na zobowiązania"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#PROVISIONSFORTAX",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Rezerwy na podatek dochodowy"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGTERMLIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zobowiązania długoterminowe"
            },
            {
                "lang": "PL",
                "value": "Zobowiązanie długoterminowe"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania długoterminowe razem"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania długoterminowe ogółem"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#TRADELIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zobowiązania z tytułu dostaw i usług"
            },
            {
                "lang": "PL",
                "value": "Długoterminowe zobowiązania handlowe i pozostałe od pozostałych jednostek"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGTERMCREDITSANDLOANS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Długoterminowe zobowiązania z tytułu kredytów, pożyczek oraz innych instrumentów dłużnych"
            },
            {
                "lang": "PL",
                "value": "Długoterminowe kredyty, pożyczki i inne zewnętrzne źródła finansowania"
            },
            {
                "lang": "PL",
                "value": "Długoterminowe kredyty, pożyczki i wyemitowane papiery dłużne"
            },
            {
                "lang": "PL",
                "value": "Długoterminowe kredyty, pożyczki i inner instrumenty dłużne"
            },
            {
                "lang": "PL",
                "value": "Długoterminowe kredyty bankowe i pożyczki"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMCREDITSANDLOANS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Krótkoterminowe zobowiązania z tytułu kredytów, pożyczek oraz innych instrumentów dłużnych"
            },
            {
                "lang": "PL",
                "value": "Krótkoterminowe kredyty, pożyczki i inne zewnętrzne źródła finansowania"
            },
            {
                "lang": "PL",
                "value": "Krótkoterminowe kredyty bankowe i pożyczki"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#DEBTSECURITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "z tytułu emisji dłużnych papierów wartościowych"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMLIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Zobowiązania krótkoterminowe"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania krótkoterminowe razem"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania krótkoterminowe ogółem"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#SHORTTERMTRADELIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Krótkoterminowe zobowiązania handlowe"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania handlowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#ACCRUALS",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Rozliczenia międzyokresowe"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#NEGATIVEGOODWILL",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Ujemna wartość firmy"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#TOTALLIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Pasywa razem"
            },
            {
                "lang": "PL",
                "value": "Suma pasywów"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#LONGANDSHORTERMLIABILITIES",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "SUMA ZOBOWIĄZAŃ"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania ogółem"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania razem"
            },
            {
                "lang": "PL",
                "value": "Zobowiązania i rezerwy na zobowiązania razem"
            }
        ]
    },
    {
        "statement": "bls", "name": "BLS#FIXEDASSETSFORSALE",
        "timeframe": "pit",
        "repr": [
            {
                "lang": "PL",
                "value": "Aktywa trwałe przeznaczone do sprzedaży"
            },           
            {
                "lang": "PL",
                "value": "Aktywa przeznaczone do sprzedaży"
            }
        ]
    }  
]