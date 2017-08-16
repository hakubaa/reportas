from rparser.synthetic import TimeRange

timeranges_pot = [ # pot - period of time
    # 3-month length timeranges
    TimeRange(1, 3),
    TimeRange(4, 6),
    TimeRange(7, 9),
    TimeRange(10, 12),
    # 6-month length timeranges
    TimeRange(1, 6),
    TimeRange(7, 12),
    # 9-month length timeranges
    TimeRange(1, 9),
    # 12-month length timeranges
    TimeRange(1, 12)
]

timeranges_pit = [ #pit - point in time
    # the end month of quarter
    TimeRange(3, 3),
    TimeRange(6, 6),
    TimeRange(9, 9),
    TimeRange(12, 12)
]
    
timerange_formulas = [
    (TimeRange(1, 3), [(1, TimeRange(1, 6)), (-1, TimeRange(4, 6))]),
    (TimeRange(1, 3), [(1, TimeRange(1, 9)), (-1, TimeRange(4, 9))]),
    (TimeRange(1, 3), [(1, TimeRange(1, 9)), (-1, TimeRange(4, 6)), (-1, TimeRange(7, 9))]),
    (TimeRange(1, 3), [(1, TimeRange(1, 12)), (-1, TimeRange(4, 12))]),
    (TimeRange(1, 3), [(1, TimeRange(1, 12)), (-1, TimeRange(4, 6)), (-1, TimeRange(7, 9)), (-1, TimeRange(10, 12))]),
    
    (TimeRange(4, 6), [(1, TimeRange(1, 6)), (-1, TimeRange(1, 3))]),
    (TimeRange(4, 6), [(1, TimeRange(1, 9)), (-1, TimeRange(1, 3)), (-1, TimeRange(7, 9))]),
    (TimeRange(4, 6), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(7, 9)), (-1, TimeRange(10, 12))]),
    (TimeRange(4, 6), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(7, 12))]),
    
    (TimeRange(7, 9), [(1, TimeRange(1, 9)), (-1, TimeRange(1, 6))]),
    (TimeRange(7, 9), [(1, TimeRange(1, 9)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6))]),
    (TimeRange(7, 9), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 6)), (-1, TimeRange(10, 12))]),
    (TimeRange(7, 9), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6)), (-1, TimeRange(10, 12))]),
    
    (TimeRange(10, 12), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6)), (-1, TimeRange(7, 9))]),
    (TimeRange(10, 12), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 9))]),
    (TimeRange(10, 12), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 6)), (-1, TimeRange(7, 9))]),
    (TimeRange(10, 12), [(1, TimeRange(7, 12)), (-1, TimeRange(7, 9))]),
    
    (TimeRange(1, 6), [(1, TimeRange(1, 3)), (1, TimeRange(4, 6))]),
    (TimeRange(1, 6), [(1, TimeRange(1, 12)), (-1, TimeRange(7, 12))]),
    (TimeRange(1, 6), [(1, TimeRange(1, 9)), (-1, TimeRange(7, 9))]),
    
    (TimeRange(7, 12), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 6))]),
    (TimeRange(7, 12), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6))]),
    (TimeRange(7, 12), [(1,TimeRange (7, 9)), (1, TimeRange(10, 12))]),
    
    (TimeRange(1, 9), [(1, TimeRange(1, 3)), (1, TimeRange(4, 6)), (1, TimeRange(7, 9))]),
    (TimeRange(1, 9), [(1, TimeRange(1, 12)), (-1, TimeRange(10, 12))]),
    (TimeRange(1, 9), [(1, TimeRange(1, 6)), (1, TimeRange(7, 9))]),
    (TimeRange(1, 9), [(1, TimeRange(1, 3)), (1, TimeRange(4, 9))]),
    
    (TimeRange(1, 12), [(1, TimeRange(1, 3)), (1, TimeRange(4, 6)), (1, TimeRange(7, 9)), (1, TimeRange(10, 12))]),
    (TimeRange(1, 12), [(1, TimeRange(1, 6)), (1, TimeRange(7, 12))]),
    (TimeRange(1, 12), [(1, TimeRange(1, 9)), (1, TimeRange(10, 12))])
]

entity_formulas [
    ((0, "BLS#TOTALASSETS"), [(1, "BLS#FIXEDASSETS"), (1, "BLS#CURRENTASSETS")]),
    ((0, "BLS#FIXEDASSETS"), [(1, "BLS#TOTALASSETS"), (-1, "BLS#CURRENTASSETS")]),
    ((0, "BLS#CURRENTASSETS"), [(1, "BLS#TOTALASSETS"), (-1, "BLS#FIXEDASSETS")])
]
