from rparser.models import FinancialReport, Document

Document.verbose = True

reports = [
    {
        "doc": FinancialReport("reports/cng_2016_y.pdf"), "ticker": "cng",
        "statements": { "bls": (3, 4), "ics": (2, ), "cfs": (5, 6) },
        "tables": [ (1, []) ]
    },
    {
        "doc": FinancialReport("reports/ambra_2016_m2.pdf"), "ticker": "amb",
        "statements": { "bls": (17, 18), "ics": (20,), "cfs": (23, 24) }
    },
    {
        "doc": FinancialReport("reports/decora_2016_q1.pdf"), "ticker": "dcr",
        "statements": { "bls": (6, 7), "ics": (5,), "cfs": (9,) }
    },
    {
        "doc": FinancialReport("reports/protektor_2016_q3.pdf"), "ticker": "prt",
        "statements": { "bls": (2, 3), "ics": (4, 5), "cfs": (8, 9) }
    },
    {
        "doc": FinancialReport("reports/pge_2016_y.pdf"), "ticker": "pge",
        "statements": { "bls": (4,), "ics": (3,), "cfs": (6,) }
    },
    {
        "doc": FinancialReport("reports/wieleton_2016_y.pdf"), "ticker": "wlt",
        "statements": { "bls": (3, 4), "ics": (5,6), "cfs": (9, 10)}
    },
    {
        "doc": FinancialReport("reports/arctic_2015_q1.pdf"), "ticker": "atc",
        "statements": { "bls": (38,), "ics": (36,), "cfs": (39,)}    
    },
    {
        "doc": FinancialReport("reports/arctic_2015_q3.pdf"), "ticker": "atc",
        "statements": { "bls": (43,), "ics": (41,), "cfs": (44,)}          
    },
    {
        "doc": FinancialReport("reports/arctic_2016_q1.pdf"), "ticker": "atc",
        "statements": { "bls": (40,), "ics": (38,), "cfs": (41,)}    
    },
    {
        "doc": FinancialReport("reports/arctic_2016_q3.pdf"), "ticker": "atc",
        "statements": { "bls": (50,), "ics": (48,), "cfs": (51,)}    
    },
    {
        "doc": FinancialReport("reports/kst_2015_y.pdf"), "ticker": "kst",
        "statements": { "bls": (6,7), "ics": (5,), "cfs": (10,) }
    },
    {
        "doc": FinancialReport("reports/kst_2016_y.pdf"), "ticker": "kst",
        "statements": { "bls": (7,8), "ics": (5,), "cfs": (11,) }
    },
    {
        "doc": FinancialReport("reports/otl_2016_y.pdf"), "ticker": "otl",
        "statements": { "bls": (4,), "ics": (3,), "cfs": (5,) }
    },
    {
        "doc": FinancialReport("reports/acp_2016_y.pdf"), "ticker": "acp",
        "statements": { "bls": (10, 11), "ics": (8,), "cfs": (14, 15)}
    },
    {
        "doc": FinancialReport("reports/acp_2010_q1.pdf"), "ticker": "acp",
        "statements": { "bls": (8, 9), "ics": (6,), "cfs": (12, 13) }
    },
    {
        "doc": FinancialReport("reports/lotos_2016_m2.pdf"), "ticker": "lte",
        "statements": { "bls": (6, ), "ics": (5,), "cfs": (7,) }
    },
    {
        "doc": FinancialReport("reports/lotos_2014_y.pdf"), "ticker": "lte",
        "statements": { "bls": (5, ), "ics": (4,), "cfs": (6,) }
    },
    {
        "doc": FinancialReport("reports/pgnig_2016_y.pdf"), "ticker": "pgn",
        "statements": { "bls": (23,), "ics": (21,), "cfs": (22,) }
    },
    {
        "doc": FinancialReport("reports/kghm_2016_y.pdf"), "ticker": "kghm",
        "statements": { "bls": (29,), "ics": (27,), "cfs": (28,) }
    },
    {
        "doc": FinancialReport("reports/obl_2016_y.pdf"), "ticker": "obl",
        "statements": { "bls": (6,), "ics": (4,), "cfs": (7,) }
    },
    {
        "doc": FinancialReport("reports/graal_2015_m1.pdf",
                               consolidated=False), 
        "ticker": "grl",
        "statements": { "bls": (15,16), "ics": (17,), "cfs": (18,19) }
    },
    {
        "doc": FinancialReport("reports/rpc_2016_q3.pdf"), "ticker": "rpc",
        "statements": { "bls": (3,), "ics": (5,), "cfs": (7,8) }
    },
    {
        "doc": FinancialReport("reports/dbc_2016_q4.pdf"), "ticker": "dbc",
        "statements": { "bls": (1,), "ics": (2,), "cfs": (4,) }
    },
    {
        "doc": FinancialReport("reports/dbc_2015_y.pdf"), "ticker": "dbc",
        "statements": { "bls": (23, 24), "ics": (25,), "cfs": (27, 28)}
    },
    {
        "doc": FinancialReport("reports/ltx_2016_y.pdf", last_page=29), 
        "ticker": "ltx",
        "statements": { "bls": (5,), "ics": (6,), "cfs": (7,)}
    },
    {
        "doc": FinancialReport("reports/ltx_2016_q1.pdf"), "ticker": "ltx",
        "statements": { "bls": (5,), "ics": (6,), "cfs": (9,) }
    },
    {
        "doc": FinancialReport("reports/bdx_2016_q3.pdf"), "ticker": "bdx",
        "statements": { "bls": (2, 3), "ics": (4,), "cfs": (8, 9) }
    },
    {
        "doc": FinancialReport("reports/bdx_2012_y.pdf"), "ticker": "bdx",
        "statements": { "bls": (3, 4), "ics": (5,), "cfs": (9, 10) }
    },
    {
        "doc": FinancialReport("reports/helio_2016_m2.pdf"), "ticker": "hel",
        "statements": { "bls": (2,), "ics": (2,3), "cfs": (4, ) }
    },
    {
        "doc": FinancialReport("reports/polsat_2016_q3.pdf", first_page=70,
                               last_page=111), 
        "ticker": "cps",
        "statements": { "bls": (6, 7), "ics": (4,), "cfs": (8,9) }
    },
    {
        "doc": FinancialReport("reports/lpp_2016_q1.pdf"), "ticker": "lpp",
        "statements": { "bls": (3,4), "ics": (5,), "cfs": (7, 8) }
    },
    {
        "doc": FinancialReport("reports/gri_2016_y.pdf"), "ticker": "gri",
        "statements": { "bls": (46, 47), "ics": (45,), "cfs": (48, 49) }
    }
]

Document.verbose = False


if __name__ == "__main__":

    bls_tp = 0
    ics_tp = 0
    cfs_tp = 0

    for report in reports:
        print("Processing {!r} ...".format(report["doc"]))

        bls = report["doc"].bls_pages
        ics = report["doc"].ics_pages
        cfs = report["doc"].cfs_pages

        statements = report["statements"]

        bls_tp += tuple(statements["bls"]) == tuple(bls)
        ics_tp += tuple(statements["ics"]) == tuple(ics)
        cfs_tp += tuple(statements["cfs"]) == tuple(cfs)

        print(" - bls: ", tuple(statements["bls"]) == tuple(bls))
        print(" - ics: ", tuple(statements["ics"]) == tuple(ics))
        print(" - cfs: ", tuple(statements["cfs"]) == tuple(cfs))

    print("Summary:")
    print(" - bls: %d (%.2f%%)" % (bls_tp, 100*bls_tp/len(reports)))
    print(" - ics: %d (%.2f%%)" % (ics_tp, 100*ics_tp/len(reports)))
    print(" - cfs: %d (%.2f%%)" % (cfs_tp, 100*cfs_tp/len(reports)))