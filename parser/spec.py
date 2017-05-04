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
        "statement": "cfs", "name": "CFS#CFNETTO", 
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
        "statement": "cfs", "name": "CFS#CASHSTART", 
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
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#CASHEND", 
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
            }
        ]
    },
    { 
        "statement": "cfs", "name": "CFS#CFFO", 
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
        "statement": "cfs", "name": "CFS#CFFI", 
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
                "value": "Przepływy pieniężne netto z działalności inwest."
            }
        ] 
    }, 
    { 
        "statement": "cfs", "name": "CFS#CFFF", 
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
        "statement": "cfs", "name": "CFS#ZSZOB",
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
        "statement": "cfs", "name": "CFS#ZSKO",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu kapitału obrotowego"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSRM",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu rozliczeń międzyokresowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSATPO",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu aktywów z tytułu podatku odroczonego"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSN",
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
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#UZSN",
        "repr": [
            {
                "lang": "PL",
                "value": "Udział w (zyskach) stratach netto jednostek "
                         "podporządkowanych wycenianych metodą praw własności"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSB",
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
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#AMORTST",
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
        "statement": "cfs", "name": "CFS#AMORTWN",
        "repr": [
            {
                "lang": "PL", "value": "Amortyzacja wartości niematerialnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#AMORT",
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
        "statement": "cfs", "name": "CFS#WSSTWN",
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
        "statement": "cfs", "name": "CFS#WNRATWN",
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
        "statement": "cfs", "name": "CFS#WNAF",
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
        "statement": "cfs", "name": "CFS#PZAF",
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
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty i przychody z tytułu odsetek"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#WTO",
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
        "statement": "cfs", "name": "CFS#ZSTDI",
        "repr": [
            {
                "lang": "PL",
                "value": "Zysk/strata z tytułu działalności inwestycyjnej"
            },
            {
                "lang": "PL",
                "value": "(Zysk) strata z działalności inwestycyjnej"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSR",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu rezerw"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSZ",
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
        "statement": "cfs", "name": "CFS#ZSNAL",
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
        "statement": "cfs", "name": "CFS#ZSNRMC",
        "repr": [
            {
                "lang": "PL",
                "value": "Zmiana stanu należności i rozliczeń międzyokresowych czynnych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#WNNPZS",
        "repr": [
            {
                "lang": "PL",
                "value": "Wydatki netto na nabycie podmiotów zależnych i stowarzyszonych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#WKP",
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
        "statement": "cfs", "name": "CFS#SKP",
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
        "repr": [
            {
                "lang": "PL",
                "value": "Spłata udzielonych pożyczek"
            }
        ]
    },
     {
        "statement": "cfs", "name": "CFS#UP", # przepływy inwestycyjne
        "repr": [
            {
                "lang": "PL",
                "value": "Udzielenie pożyczek"
            }
        ]
    },   
    {
        "statement": "cfs", "name": "CFS#UN",
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
        "statement": "cfs", "name": "CFS#ZSTRK",
        "repr": [
            {
                "lang": "PL",
                "value": "Zyski/straty z tytułu różnic kursowych"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#TAXUCRRENT",
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
        "repr": [
            {
                "lang": "PL",
                "value": "Dywidendy otrzymane"
            }
        ]
    },
    {
        "statement": "cfs", "name": "CFS#ZSDI",
        "repr": [
            {
                "lang": "PL",
                "value": "Zyski/straty z działalności inwestycyjnej"
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
        "statement": "cfs", "name": "CFS#TAXPAID",
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
        "statement": "cfs", "name": "CFS#NAW",
        "repr": [
            {
                "lang": "PL",
                "value": "Nabycie akcji własnych"
            }
        ]   
    },
    {
        "statement": "cfs", "name": "CFS#UAW",
        "repr": [
            {
                "lang": "PL",
                "value": "Umorzenie akcji własnych"
            }
        ]   
    },
    { # Przepływy środków pieniężnych z działalności finansowej - Wydatki
        "statement": "cfs", "name": "CFS#INTEREST",
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
# NET AND LOSS STATEMENT - NLS
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
        "statement": "nls", "name": "NLS#INCOMESALE",
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
            }
        ]
    },
    {
        "statement": "nls", "name": "NLS#INCOMESALEPRODS",
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
        "statement": "nls", "name": "NLS#INCOMESALESERVICES",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody ze sprzedaży usług"
            }
        ]
    },
    {
        "statement": "nls", "name": "NLS#INCOMESALEPGOODS",
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
        "statement": "nls", "name": "NLS#INCOMESALEPRODSANDSERVICES",
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
        "statement": "nls", "name": "NLS#COSTOFSALE",
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
        "statement": "nls", "name": "NLS#COSTMATERIALS",
        "repr": [
            {
                "lang": "PL",
                "value": "Zużycie materiałów"
            }
        ]
    },
    {
        "statement": "nls", "name": "NLS#COSTGOODS",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt własny sprzedanych towarów"
            }
        ]
    },
    {
        "statement": "nls", "name": "NLS#COSTGOODSANDMATERIALS",
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
        "statement": "nls", "name": "NLS#COSTPRODUCTS",
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
        "statement": "nls", "name": "NLS#COSTSERVICES",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszt sprzedanych usług"
            }
        ]
    },
    {
        "statement": "nls", "name": "NLS#COSTPRODUCTSANDSERVICES",
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
        "statement": "nls", "name": "NLS#NETSALEBRUTTO",
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
        "statement": "nls", "name": "NLS#COSTSELLING",
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
        "statement": "nls", "name": "NLS#COSTOFMANAGEMENT",
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
    { # NLS#COSTSELLING + NLS#COSTOFMANAGEMENT"
        "statement": "nls", "name": "NLS#COSTSELLINGANDMANAGEMENT",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty administracyjne i sprzedaży"
            }
        ]
    },
    {
        "statement": "nls", "name": "NLS#NETSALENETTO",
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
        "statement": "nls", "name": "NLS#INCOMEOP",
        "repr": [
            {
                "lang": "PL",
                "value": "Pozostałe przychody operacyjne"
            }
        ]
    },  
    {
        "statement": "nls", "name": "NLS#COSTOP",
        "repr": [
            {
                "lang": "PL",
                "value": "Pozostałe koszty operacyjne"
            }
        ]
    }, 
    {
        "statement": "nls", "name": "NLS#NETOP",
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
        "statement": "nls", "name": "NLS#INCOMEFIN",
        "repr": [
            {
                "lang": "PL",
                "value": "Przychody finansowe"
            }
        ]
    },    
    {
        "statement": "nls", "name": "NLS#COSTFIN",
        "repr": [
            {
                "lang": "PL",
                "value": "Koszty finansowe"
            }
        ]
    },   
    {
        "statement": "nls", "name": "NLS#UZJSWP",
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
        "statement": "nls", "name": "NLS#NETABANDONED",
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
        "statement": "nls", "name": "NLS#NETBRUTTO",
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
        "statement": "nls", "name": "NLS#TAX",
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
        "statement": "nls", "name": "NLS#NETNETTO",
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
        "statement": "nls", "name": "NLS#NETNETTOCONT",
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
        "statement": "nls", "name": "NLS#NETNETTOOWNERS",
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
        "statement": "nls", "name": "NLS#NETNETTOMINOR",
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
        "statement": "nls", "name": "NLS#SHARESCOUNT",    
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
    }
]