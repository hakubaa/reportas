from parser.models import FinancialReport, Document

Document.verbose = True

reports = [
    {
        "doc": FinancialReport("reports/cng_2016_y.pdf"), "ticker": "cng",
        "statements": { "balance": (3, 4), "nls": (2, ), "cfs": (5, 6) }
    },
    {
        "doc": FinancialReport("reports/ambra_2016_m2.pdf"), "ticker": "amb",
        "statements": { "balance": (17, 18), "nls": (20,), "cfs": (23, 24) }
    },
    {
        "doc": FinancialReport("reports/decora_2016_q1.pdf"), "ticker": "dcr",
        "statements": { "balance": (6, 7), "nls": (5,), "cfs": (9,) }
    },
    {
        "doc": FinancialReport("reports/protektor_2016_q3.pdf"), "ticker": "prt",
        "statements": { "balance": (2, 3), "nls": (4, 5), "cfs": (8, 9) }
    },
    {
        "doc": FinancialReport("reports/pge_2016_y.pdf"), "ticker": "pge",
        "statements": { "balance": (4,), "nls": (3,), "cfs": (6,) }
    },
    {
        "doc": FinancialReport("reports/wieleton_2016_y.pdf"), "ticker": "wlt",
        "statements": { "balance": (3, 4), "nls": (5,), "cfs": (9, 10)}
    },
    {
        "doc": FinancialReport("reports/arctic_2015_q1.pdf"), "ticker": "atc",
        "statements": { "balance": (38,), "nls": (36,), "cfs": (39,)}    
    },
    {
        "doc": FinancialReport("reports/arctic_2015_q3.pdf"), "ticker": "atc",
        "statements": { "balance": (43,), "nls": (41,), "cfs": (44,)}          
    },
    {
        "doc": FinancialReport("reports/arctic_2016_q1.pdf"), "ticker": "atc",
        "statements": { "balance": (40,), "nls": (38,), "cfs": (41,)}    
    },
    {
        "doc": FinancialReport("reports/arctic_2016_q3.pdf"), "ticker": "atc",
        "statements": { "balance": (50,), "nls": (48,), "cfs": (51,)}    
    },
    {
        "doc": FinancialReport("reports/kst_2015_y.pdf"), "ticker": "kst",
        "statements": { "balance": (6,7), "nls": (5,), "cfs": (10,) }
    },
    {
        "doc": FinancialReport("reports/kst_2016_y.pdf"), "ticker": "kst",
        "statements": { "balance": (7,8), "nls": (5,), "cfs": (11,) }
    },
    {
        "doc": FinancialReport("reports/otl_2016_y.pdf"), "ticker": "otl",
        "statements": { "balance": (4,), "nls": (3,), "cfs": (5,) }
    },
    {
        "doc": FinancialReport("reports/acp_2016_y.pdf"), "ticker": "acp",
        "statements": { "balance": (10, 11), "nls": (8,), "cfs": (14, 15)}
    },
    {
        "doc": FinancialReport("reports/acp_2010_q1.pdf"), "ticker": "acp",
        "statements": { "balance": (8, 9), "nls": (6,), "cfs": (12, 13) }
    },
    {
        "doc": FinancialReport("reports/lotos_2016_m2.pdf"), "ticker": "lte",
        "statements": { "balance": (6, ), "nls": (5,), "cfs": (7,) }
    },
    {
        "doc": FinancialReport("reports/lotos_2014_y.pdf"), "ticker": "lte",
        "statements": { "balance": (5, ), "nls": (4,), "cfs": (6,) }
    },
    {
        "doc": FinancialReport("reports/pgnig_2016_y.pdf"), "ticker": "pgn",
        "statements": { "balance": (23,), "nls": (21,), "cfs": (22,) }
    },
    {
        "doc": FinancialReport("reports/kghm_2016_y.pdf"), "ticker": "kghm",
        "statements": { "balance": (29,), "nls": (27,), "cfs": (28,) }
    },
    {
        "doc": FinancialReport("reports/obl_2016_y.pdf"), "ticker": "obl",
        "statements": { "balance": (6,), "nls": (4,), "cfs": (7,) }
    },
    {
        "doc": FinancialReport("reports/graal_2015_m1.pdf",
                               consolidated=False), 
        "ticker": "grl",
        "statements": { "balance": (15,16), "nls": (17,), "cfs": (18,19) }
    },
    {
        "doc": FinancialReport("reports/rpc_2016_q3.pdf"), "ticker": "rpc",
        "statements": { "balance": (3,), "nls": (5,), "cfs": (7,8) }
    },
    {
        "doc": FinancialReport("reports/dbc_2016_q4.pdf"), "ticker": "dbc",
        "statements": { "balance": (1,), "nls": (2,), "cfs": (4,) }
    },
    {
        "doc": FinancialReport("reports/dbc_2015_y.pdf"), "ticker": "dbc",
        "statements": { "balance": (23, 24), "nls": (25,), "cfs": (27, 28)}
    },
    {
        "doc": FinancialReport("reports/ltx_2016_y.pdf", last_page=29), 
        "ticker": "ltx",
        "statements": { "balance": (5,), "nls": (6,), "cfs": (7,)}
    },
    {
        "doc": FinancialReport("reports/ltx_2016_q1.pdf"), "ticker": "ltx",
        "statements": { "balance": (5,), "nls": (6,), "cfs": (9,) }
    },
    {
        "doc": FinancialReport("reports/bdx_2016_q3.pdf"), "ticker": "bdx",
        "statements": { "balance": (2, 3), "nls": (4,), "cfs": (8, 9) }
    },
    {
        "doc": FinancialReport("reports/bdx_2012_y.pdf"), "ticker": "bdx",
        "statements": { "balance": (3, 4), "nls": (5,), "cfs": (9, 10) }
    },
    {
        "doc": FinancialReport("reports/helio_2016_m2.pdf"), "ticker": "hel",
        "statements": { "balance": (2,), "nls": (2,3), "cfs": (4, ) }
    },
    {
        "doc": FinancialReport("reports/polsat_2016_q3.pdf", first_page=70,
                               last_page=111), 
        "ticker": "cps",
        "statements": { "balance": (6, 7), "nls": (4,), "cfs": (8,9) }
    },
    {
        "doc": FinancialReport("reports/lpp_2016_q1.pdf"), "ticker": "lpp",
        "statements": { "balance": (3,4), "nls": (5,), "cfs": (7, 8) }
    },
    {
        "doc": FinancialReport("reports/gri_2016_y.pdf"), "ticker": "gri",
        "statements": { "balance": (46, 47), "nls": (45,), "cfs": (48, 49) }
    }
]

Document.verbose = False


if __name__ == "__main__":

    balance_tp = 0
    nls_tp = 0
    cfs_tp = 0

    for report in reports:
        print("Processing {!r} ...".format(report["doc"]))

        balance = report["doc"].balance
        nls = report["doc"].net_and_loss
        cfs = report["doc"].cash_flows

        statements = report["statements"]

        balance_tp += tuple(statements["balance"]) == tuple(balance)
        nls_tp += tuple(statements["nls"]) == tuple(nls)
        cfs_tp += tuple(statements["cfs"]) == tuple(cfs)

        print(" - balance: ", tuple(statements["balance"]) == tuple(balance))
        print(" - nls: ", tuple(statements["nls"]) == tuple(nls))
        print(" - cfs: ", tuple(statements["cfs"]) == tuple(cfs))

    print("Summary:")
    print(" - balance: %d (%.2f%%)" % (balance_tp, 100*balance_tp/len(reports)))
    print(" - nls: %d (%.2f%%)" % (nls_tp, 100*nls_tp/len(reports)))
    print(" - cfs: %d (%.2f%%)" % (cfs_tp, 100*cfs_tp/len(reports)))



for report in reports:
    doc = report["doc"]
    print(doc, " -> ", doc.timerange, " - ", doc.timestamp)