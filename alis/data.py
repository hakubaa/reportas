from models import Document

Document.verbose = True

reports = [
    {
        "doc": Document("reports/cng_2016_y.pdf"), "ticker": "cng",
        "statements": { "balance": (3, 4), "nls": (2, ), "cfs": (5, 6) }
    },
    {
        "doc": Document("reports/ambra_2016_m2.pdf"), "ticker": "amb",
        "statements": { "balance": (17, 18), "nls": (20, 21), "cfs": (23, 24) }
    },
    {
        "doc": Document("reports/decora_2016_q1.pdf"), "ticker": "dcr",
        "statements": { "balance": (6, 7), "nls": (5,), "cfs": (9,) }
    },
    {
        "doc": Document("reports/protektor_2016_q3.pdf"), "ticker": "prt",
        "statements": { "balance": (2, 3), "nls": (4, 5), "cfs": (8, 9) }
    },
    {
        "doc": Document("reports/pge_2016_y.pdf"), "ticker": "pge",
        "statements": { "balance": (4,), "nls": (3,), "cfs": (6,) }
    },
    {
        "doc": Document("reports/wieleton 2016_y.pdf"), "ticker": "wlt",
        "statements": { "balance": (3, 4), "nls": (5,), "cfs": (9, 10)}
    },
    {
        "doc": Document("reports/arctic_2015_q1.pdf"), "ticker": "atc",
        "statements": { "balance": (38,), "nls": (36,), "cfs": (39,)}    
    },
    {
        "doc": Document("reports/arctic_2015_q3.pdf"), "ticker": "atc",
        "statements": { "balance": (43,), "nls": (41,), "cfs": (44,)}          
    },
    {
        "doc": Document("reports/arctic_2016_q1.pdf"), "ticker": "atc",
        "statements": { "balance": (40,), "nls": (38,), "cfs": (41,)}    
    },
    {
        "doc": Document("reports/arctic_2016_q3.pdf"), "ticker": "atc",
        "statements": { "balance": (50,), "nls": (48,), "cfs": (51,)}    
    },
    {
        "doc": Document("reports/kst_2015_y.pdf"), "ticker": "kst",
        "statements": { "balance": (6,7), "nls": (5,), "cfs": (10,) }
    },
    {
        "doc": Document("reports/kst_2016_y.pdf"), "ticker": "kst",
        "statements": { "balance": (7,8), "nls": (5,), "cfs": (11,) }
    },
    {
        "doc": Document("reports/otl_2016_y.pdf"), "ticker": "otl",
        "statements": { "balance": (4,), "nls": (3,), "cfs": (5,) }
    },
    {
        "doc": Document("reports/acp_2016_y.pdf"), "ticker": "acp",
        "statements": { "balance": (10, 11), "nls": (8,), "cfs": (14, 15)}
    },
    {
        "doc": Document("reports/acp_2010_q1.pdf"), "ticker": "acp",
        "statements": { "balance": (8, 9), "nls": (6,), "cfs": (12, 13) }
    },
    {
        "doc": Document("reports/lotos_2016_m2.pdf"), "ticker": "lte",
        "statements": { "balance": (6, ), "nls": (5,), "cfs": (7,) }
    },
    {
        "doc": Document("reports/lotos_2014_y.pdf"), "ticker": "lte",
        "statements": { "balance": (5, ), "nls": (4,), "cfs": (6,) }
    },
    {
        "doc": Document("reports/pgnig_2016_y.pdf"), "ticker": "pgn",
        "statements": { "balance": (23,), "nls": (21,), "cfs": (22,) }
    }
]
