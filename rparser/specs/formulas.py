from rparser.synthetic import Timeframe


timeframes_pot = [ # pot - period of time
    # 3-month length Timeframes
    Timeframe(1, 3),
    Timeframe(4, 6),
    Timeframe(7, 9),
    Timeframe(10, 12),
    # 6-month length Timeframes
    Timeframe(1, 6),
    Timeframe(7, 12),
    # 9-month length Timeframes
    Timeframe(1, 9),
    # 12-month length Timeframes
    Timeframe(1, 12)
]

timeframes_pit = [ #pit - point in time
    # the end month of quarter
    Timeframe(3, 3),
    Timeframe(6, 6),
    Timeframe(9, 9),
    Timeframe(12, 12)
]
    
timeframe_formulas = [
    (Timeframe(1, 3), [(Timeframe(1, 6), 1), (Timeframe(4, 6), -1)]),
    (Timeframe(1, 3), [(Timeframe(1, 9), 1), (Timeframe(4, 9), -1)]),
    (Timeframe(1, 3), [(Timeframe(1, 9), 1), (Timeframe(4, 6), -1), (Timeframe(7, 9), -1)]),
    (Timeframe(1, 3), [(Timeframe(1, 12), 1), (Timeframe(4, 12), -1)]),
    (Timeframe(1, 3), [(Timeframe(1, 12), 1), (Timeframe(4, 6), -1), (Timeframe(7, 9), -1), (Timeframe(10, 12), -1)]),
    
    (Timeframe(4, 6), [(Timeframe(1, 6), 1), (Timeframe(1, 3), -1)]),
    (Timeframe(4, 6), [(Timeframe(1, 9), 1), (Timeframe(1, 3), -1), (Timeframe(7, 9), -1)]),
    (Timeframe(4, 6), [(Timeframe(1, 12), 1), (Timeframe(1, 3), -1), (Timeframe(7, 9), -1), (Timeframe(10, 12), -1)]),
    (Timeframe(4, 6), [(Timeframe(1, 12), 1), (Timeframe(1, 3), -1), (Timeframe(7, 12), -1)]),
    
    (Timeframe(7, 9), [(Timeframe(1, 9), 1), (Timeframe(1, 6), -1)]),
    (Timeframe(7, 9), [(Timeframe(1, 9), 1), (Timeframe(1, 3), -1), (Timeframe(4, 6), -1)]),
    (Timeframe(7, 9), [(Timeframe(1, 12), 1), (Timeframe(1, 6), -1), (Timeframe(10, 12), -1)]),
    (Timeframe(7, 9), [(Timeframe(1, 12), 1), (Timeframe(1, 3), -1), (Timeframe(4, 6), -1), (Timeframe(10, 12), -1)]),
    
    (Timeframe(10, 12), [(Timeframe(1, 12), 1), (Timeframe(1, 3), -1), (Timeframe(4, 6), -1), (Timeframe(7, 9), -1)]),
    (Timeframe(10, 12), [(Timeframe(1, 12), 1), (Timeframe(1, 9), -1)]),
    (Timeframe(10, 12), [(Timeframe(1, 12), 1), (Timeframe(1, 6), -1), (Timeframe(7, 9), -1)]),
    (Timeframe(10, 12), [(Timeframe(7, 12), 1), (Timeframe(7, 9), -1)]),
    
    (Timeframe(1, 6), [(Timeframe(1, 3), 1), (Timeframe(4, 6), 1)]),
    (Timeframe(1, 6), [(Timeframe(1, 12), 1), (Timeframe(7, 12), -1)]),
    (Timeframe(1, 6), [(Timeframe(1, 9), 1), (Timeframe(7, 9), -1)]),
    
    (Timeframe(7, 12), [(Timeframe(1, 12), 1), (Timeframe(1, 6), -1)]),
    (Timeframe(7, 12), [(Timeframe(1, 12), 1), (Timeframe(1, 3), -1), (Timeframe(4, 6), -1)]),
    (Timeframe(7, 12), [(Timeframe (7, 9), 1), (Timeframe(10, 12), 1)]),
    
    (Timeframe(1, 9), [(Timeframe(1, 3), 1), (Timeframe(4, 6), 1), (Timeframe(7, 9), 1)]),
    (Timeframe(1, 9), [(Timeframe(1, 12), 1), (Timeframe(10, 12), -1)]),
    (Timeframe(1, 9), [(Timeframe(1, 6), 1), (Timeframe(7, 9), 1)]),
    (Timeframe(1, 9), [(Timeframe(1, 3), 1), (Timeframe(4, 9), 1)]),
    
    (Timeframe(1, 12), [(Timeframe(1, 3), 1), (Timeframe(4, 6), 1), (Timeframe(7, 9), 1), (Timeframe(10, 12), 1)]),
    (Timeframe(1, 12), [(Timeframe(1, 6), 1), (Timeframe(7, 12), 1)]),
    (Timeframe(1, 12), [(Timeframe(1, 9), 1), (Timeframe(10, 12), 1)])
]

entity_formulas = [
    ("BLS@TOTALASSETS", [("BLS@FIXEDASSETS", 1), ("BLS@CURRENTASSETS", 1)]),
    ("BLS@FIXEDASSETS", [("BLS@TOTALASSETS", 1), ("BLS@CURRENTASSETS", -1)]),
    ("BLS@CURRENTASSETS", [("BLS@TOTALASSETS", 1), ("BLS@FIXEDASSETS", -1)]),
    ("BLS@TOTALLIABILITIES", [("BLS@EQUITY", 1), ("BLS@LONGANDSHORTERMLIABILITIES", 1)]),
    ("BLS@LONGANDSHORTERMLIABILITIES", [("BLS@EQUITY", -1), ("BLS@TOTALLIABILITIES", 1)]),
    ("BLS@EQUITY", [("BLS@TOTALLIABILITIES", 1), ("BLS@LONGANDSHORTERMLIABILITIES", -1)]),
    ("BLS@TOTALASSETS", [("BLS@TOTALLIABILITIES", 1)]),
    ("BLS@TOTALLIABILITIES", [("BLS@TOTALASSETS", 1)]),

    ("ICS@NETPROFIT", [("ICS@NETPROFITCONT", 1), ("ICS@NETABANDONED", 1)]),
    ("ICS@NETPROFITCONT", [("ICS@NETPROFIT", 1), ("ICS@NETABANDONED", -1)]),

    ("ICS@NETPROFIT", [("ICS@GROSSPROFIT", 1), ("ICS@INCOMETAX", -1)]),
    ("ICS@GROSSPROFIT", [("ICS@NETPROFIT", 1), ("ICS@INCOMETAX", 1)]),

    ("ICS@NETPROFIT", [("ICS@NETPROFITTOOWNERS", 1), ("ICS@NETPROFITTONONOWNERS", 1)]),
    ("ICS@NETPROFITTOOWNERS", [("ICS@NETPROFIT", 1), ("ICS@NETPROFITTONONOWNERS", -1)]),
]