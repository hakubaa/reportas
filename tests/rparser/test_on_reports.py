import unittest
import unittest.mock as mock
import io

from rparser.core import FinancialReport, PDFFileIO
from db.core import SQLAlchemy
from db.models import RecordTypeRepr, FinancialStatementType, RecordType
from db.tools import (
    upload_records_spec, get_records_reprs, get_companies_reprs, 
    upload_companies
)
import rparser.specs.records as spec
from rparser.utils import remove_non_ascii
from rparser.nlp import find_ngrams

# reports/cng_2016_y.pdf
# reports/decora_2016_q1.pdf
# reports/polsat_2016_q3.pdf
# reports/bdx_2016_q3.pdf
# reports/pgnig_2016_y.pdf
# reports/ltx_2016_q1.pdf
# reports/lpp_2016_q1.pdf
# reports/gri_2016_y.pdf
# reports/wieleton_2016_y.pdf
# reports/rpc_2016_q3.pdf
# reports/kst_2016_y.pdf
# reports/helio_2016_m2.pdf
# reports/graal_2015_m1.pdf
# reports/arctic_2016_q3.pdf 
# reports/pge_2016_y.pdf
# reports/protektor_2016_q3.pdf
# reports/kghm_2016_y.pdf
# reports/obl_2016_y.pdf
# reports/lotos_2016_m2.pdf
# reports/otl_2016_y.pdf
# reports/acp_2010_q1.pdf
# reports/arctic_2015_q1.pdf
# reports/ltx_2016_y.pdf
# reports/acp_2016_y.pdf


def get_ftype(session, name):
    ftype = session.query(FinancialStatementType).\
                filter_by(name=name).one()        
    return ftype


class RecordsExtractorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.db = SQLAlchemy("sqlite:///:memory:")
        cls.db.create_all()

        FinancialStatementType.insert_defaults(cls.db.session)
        RecordType.insert_rtypes(cls.db.session)

        # Create vocabuluary
        cls.voc = set(map(str, find_ngrams(
            remove_non_ascii(
                " ".join(map(
                    " ".join, 
                    cls.db.session.query(RecordTypeRepr.value).all()
                ))
            ),
            n = 1, min_len=2, remove_non_alphabetic=True
        )))
        cls.voc.update(
            remove_non_ascii(word) 
            for word in ("podstawowy", "obrotowy", "rozwodniony", "połączeń", 
                         "konsolidacji", "należne", "wpłaty", "gazu", "ropy"))

        # Create specification for identifying records
        cls.spec = dict(
            bls=get_records_reprs(cls.db.session, ftype=get_ftype(cls.db.session, "bls")),
            ics=get_records_reprs(cls.db.session, ftype=get_ftype(cls.db.session, "ics")),
            cfs=get_records_reprs(cls.db.session, ftype=get_ftype(cls.db.session, "cfs"))
        )

    @classmethod
    def tearDownClass(cls):
        cls.db.drop_all()
        
    def read_report(self, path):
        doc = FinancialReport(
            io.TextIOWrapper(PDFFileIO(path), "utf-8"), 
            records_spec=self.spec, voc=self.voc
        )
        return doc

    ## reports/cng_2016_y.pdf
    def test_update_names_cng_2016_y_ics(self):
        doc = self.read_report("reports/cng_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_cng_2016_y_bls(self):
        doc = self.read_report("reports/cng_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_cng_2016_y_cfs(self):
        doc = self.read_report("reports/cng_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )
    
    ## reports/decora_2016_q1.pdf
    def test_update_names_decora_2016_q1_ics(self):
        doc = self.read_report("reports/decora_2016_q1.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
        )

    def test_update_names_decora_2016_q1_bls(self):
        doc = self.read_report("reports/decora_2016_q1.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2016, 3, 31)), (3, (2015, 12, 31))]
        )

    def test_update_names_decora_2016_q1_cfs(self):
        doc = self.read_report("reports/decora_2016_q1.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
        )

    ## reports/polsat_2016_q3.pdf
    def test_update_names_polsat_2016_q3_ics(self):
        doc = self.read_report("reports/polsat_2016_q3.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2016, 9, 30)), (3, (2015, 9, 30)), 
             (9, (2016, 9, 30)), (9, (2015, 9, 30))]
        )

    def test_update_names_polsat_2016_q3_bls(self):
        doc = self.read_report("reports/polsat_2016_q3.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2016, 9, 30)), (3, (2015, 12, 31))]
        )

    def test_update_names_polsat_2016_q3_cfs(self):
        doc = self.read_report("reports/polsat_2016_q3.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(9, (2016, 9, 30)), (9, (2015, 9, 30))]
        )

    ## reports/bdx_2016_q3.pdf
    def test_update_names_bdx_2016_q3_ics(self):
        doc = self.read_report("reports/bdx_2016_q3.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(9, (2016, 9, 30)), (9, (2015, 9, 30)), 
             (3, (2016, 9, 30)), (3, (2015, 9, 30))]
        )

    def test_update_names_bdx_2016_y3_bls(self):
        doc = self.read_report("reports/bdx_2016_q3.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(9, (2016, 9, 30)), (3, (2015, 12, 31))]
        )

    def test_update_names_bdx_2016_q3_cfs(self):
        doc = self.read_report("reports/bdx_2016_q3.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(9, (2016, 9, 30)), (9, (2015, 9, 30))]
        )  

    ## reports/pgnig_2016_y.pdf
    def test_update_names_pgnig_2016_y_ics(self):
        doc = self.read_report("reports/pgnig_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_pgnig_2016_y_bls(self):
        doc = self.read_report("reports/pgnig_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31)), (12, (2014, 12, 31))]
        )

    def test_update_names_pgnig_2016_y_cfs(self):
        doc = self.read_report("reports/pgnig_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )  

    ## reports/ltx_2016_q1.pdf
    def test_update_names_ltx_2016_q1_ics(self):
        doc = self.read_report("reports/ltx_2016_q1.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
        )

    def test_update_names_ltx_2016_q1_bls(self):
        doc = self.read_report("reports/ltx_2016_q1.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(6, (2016, 3, 31)), (6, (2015, 12, 31)), (6, (2015, 3, 31))]
        )

    def test_update_names_ltx_2016_q1_cfs(self):
        doc = self.read_report("reports/ltx_2016_q1.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
        )  

    ## reports/lpp_2016_q1.pdf
    def test_update_names_lpp_2016_q_ics(self):
        doc = self.read_report("reports/lpp_2016_q1.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
        )

    def test_update_names_lpp_2016_q_bls(self):
        doc = self.read_report("reports/lpp_2016_q1.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31)), (3, (2015, 12, 31))]
        )

    def test_update_names_lpp_2016_q_cfs(self):
        doc = self.read_report("reports/lpp_2016_q1.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
        )

    ## reports/gri_2016_y.pdf
    @unittest.skip
    def test_update_names_gri_2016_y_ics(self):
        doc = self.read_report("reports/gri_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    @unittest.skip
    def test_update_names_gri_2016_y_bls(self):
        doc = self.read_report("reports/gri_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    @unittest.skip
    def test_update_names_gri_2016_y_cfs(self):
        doc = self.read_report("reports/gri_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/wieleton_2016_y.pdf
    def test_update_names_wieleton_2016_y_ics(self):
        doc = self.read_report("reports/wieleton_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_wieleton_2016_y_bls(self):
        doc = self.read_report("reports/wieleton_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_wieleton_2016_y_cfs(self):
        doc = self.read_report("reports/wieleton_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/rpc_2016_q3.pdf
    def test_update_names_rpc_2016_q3_ics(self):
        doc = self.read_report("reports/rpc_2016_q3.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2015, 9, 30)), (9, (2015, 9, 30)),
             (3, (2016, 9, 30)), (9, (2016, 9, 30))]
        )

    def test_update_names_rpc_2016_q3_bls(self):
        doc = self.read_report("reports/rpc_2016_q3.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2015, 12, 31)), (3, (2016, 9, 30))]
        )

    def test_update_names_rpc_2016_q3_cfs(self):
        doc = self.read_report("reports/rpc_2016_q3.pdf") 
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2015, 9, 30)), (3, (2016, 9, 30))]
        )

    ## reports/kst_2016_y.pdf
    def test_update_names_kst_2016_y_ics(self):
        doc = self.read_report("reports/kst_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_kst_2016_y_bls(self):
        doc = self.read_report("reports/kst_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_kst_2016_y_cfs(self):
        doc = self.read_report("reports/kst_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/helio_2016_m2.pdf
    def test_update_names_helio_2016_m2_ics(self):
        doc = self.read_report("reports/helio_2016_m2.pdf") 
        self.assertEqual(
            doc.ics.names, 
            [(6, (2016, 12, 31)), (6, (2015, 12, 31))]
        )

    def test_update_names_helio_2016_m2_bls(self):
        doc = self.read_report("reports/helio_2016_m2.pdf") 
        self.assertEqual(
            doc.bls.names, 
            [(6, (2016, 12, 31)), (6, (2015, 12, 31)), (6, (2015, 12, 31))]
        )

    def test_update_names_helio_2016_m2_cfs(self):
        doc = self.read_report("reports/helio_2016_m2.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(6, (2016, 12, 31)), (6, (2015, 12, 31))]
        )

    ## reports/graal_2015_m1.pdf
    def test_update_names_graal_2015_m1_ics(self):
        doc = self.read_report("reports/graal_2015_m1.pdf") 
        self.assertEqual(
            doc.ics.names, 
            [(6, (2015, 6, 30)), (6, (2014, 6, 30))]
        )

    def test_update_names_graal_2015_m1_bls(self):
        doc = self.read_report("reports/graal_2015_m1.pdf") 
        self.assertEqual(
            doc.bls.names, 
            [(6, (2015, 6, 30)), (6, (2014, 12, 31)), (6, (2014, 6, 30))]
        )

    def test_update_names_graal_2015_m1_cfs(self):
        doc = self.read_report("reports/graal_2015_m1.pdf") 
        self.assertEqual(
            doc.cfs.names, 
            [(6, (2015, 6, 30)), (6, (2014, 6, 30))]
        )

    ## reports/arctic_2016_q3.pdf
    def test_update_names_arctic_2016_q3_ics(self):
        doc = self.read_report("reports/arctic_2016_q3.pdf") 
        self.assertEqual(
            doc.ics.names, 
            [(3, (2016, 9, 30)), (9, (2016, 9, 30)),
             (3, (2015, 9, 30)), (9, (2015, 9, 30))]
        )

    def test_update_names_arctic_2016_q3_bls(self):
        doc = self.read_report("reports/arctic_2016_q3.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2016, 9, 30)), (3, (2016, 6, 30)),
             (3, (2015, 12, 31)), (3, (2015, 9, 30))]
        )

    def test_update_names_arctic_2016_q3_cfs(self):
        doc = self.read_report("reports/arctic_2016_q3.pdf") 
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2016, 9, 30)), (9, (2016, 9, 30)),
             (3, (2015, 9, 30)), (9, (2015, 9, 30))]
        )

    ## reports/pge_2016_y.pdf
    def test_update_names_pge_2016_y_ics(self):
        doc = self.read_report("reports/pge_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
           [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_pge_2016_y_bls(self):
        doc = self.read_report("reports/pge_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_pge_2016_y_cfs(self):
        doc = self.read_report("reports/pge_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/protektor_2016_q3.pdf
    def test_update_names_protektor_2016_q3_ics(self):
        doc = self.read_report("reports/protektor_2016_q3.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(9, (2016, 9, 30)), (9, (2015, 9, 30))]
        )

    def test_update_names_protektor_2016_q3_bls(self):
        doc = self.read_report("reports/protektor_2016_q3.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2016, 9, 30)), (3, (2015, 12, 31))]
        )

    def test_update_names_protektor_2016_q3_cfs(self):
        doc = self.read_report("reports/protektor_2016_q3.pdf") 
        self.assertEqual(
            doc.cfs.names, 
             [(9, (2016, 9, 30)), (9, (2015, 9, 30))]

        )

    ## reports/kghm_2016_y.pdf
    def test_update_names_kghm_2016_y_ics(self):
        doc = self.read_report("reports/kghm_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_kghm_2016_y_bls(self):
        doc = self.read_report("reports/kghm_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_kghm_2016_y_cfs(self):
        doc = self.read_report("reports/kghm_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/obl_2016_y.pdf
    def test_update_names_obl_2016_y_ics(self):
        doc = self.read_report("reports/obl_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_obl_2016_y_bls(self):
        doc = self.read_report("reports/obl_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_obl_2016_y_cfs(self):
        doc = self.read_report("reports/obl_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/lotos_2016_m2.pdf
    def test_update_names_lotos_2016_m2_ics(self):
        doc = self.read_report("reports/lotos_2016_m2.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2016, 6, 30)), (6, (2016, 6, 30)),
             (3, (2015, 6, 30)), (6, (2015, 6, 30))]
        )

    def test_update_names_lotos_2016_m2_bls(self):
        doc = self.read_report("reports/lotos_2016_m2.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(6, (2016, 6, 30)), (6, (2015, 12, 31))]
        )

    def test_update_names_lotos_2016_m2_cfs(self):
        doc = self.read_report("reports/lotos_2016_m2.pdf") 
        self.assertEqual(
            doc.cfs.names, 
            [(6, (2016, 6, 30)), (6, (2015, 6, 30))]
        )

    ## reports/dbc_2015_y.pdf
    def test_update_names_dbc_2015_y_ics(self):
        doc = self.read_report("reports/dbc_2015_y.pdf") 
        self.assertEqual(
            doc.ics.names, 
            [(12, (2015, 12, 31)), (12, (2014, 12, 31))]
        )

    def test_update_names_dbc_2015_y_bls(self):
        doc = self.read_report("reports/dbc_2015_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2015, 12, 31)), (12, (2014, 12, 31))]
        )

    def test_update_names_dbc_2015_y_cfs(self):
        doc = self.read_report("reports/dbc_2015_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2015, 12, 31)), (12, (2014, 12, 31))]
        )

    ## reports/otl_2016_y.pdf
    def test_update_names_otl_2016_y_ics(self):
        doc = self.read_report("reports/otl_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_otl_2016_y_bls(self):
        doc = self.read_report("reports/otl_2016_y.pdf") 
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_otl_2016_y_cfs(self):
        doc = self.read_report("reports/otl_2016_y.pdf") 
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    ## reports/acp_2010_q1.pdf
    def test_update_names_acp_2010_q1_ics(self):
        doc = self.read_report("reports/acp_2010_q1.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(3, (2010, 3, 31)), (3, (2009, 3, 31))]
        )

    def test_update_names_acp_2010_q1_bls(self):
        doc = self.read_report("reports/acp_2010_q1.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(3, (2010, 3, 31)), (3, (2009, 12, 31)), (3, (2009, 3, 31))]
        )

    def test_update_names_acp_2010_q1_cfs(self):
        doc = self.read_report("reports/acp_2010_q1.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2010, 3, 31)), (3, (2009, 3, 31))]
        )

    ## reports/arctic_2015_q1.pdf
    def test_update_names_arctic_2015_q1_ics(self):
        doc = self.read_report("reports/arctic_2015_q1.pdf") 
        self.assertEqual(
            doc.ics.names, 
            [(3, (2015, 3, 31)), (3, (2014, 3, 31)), (12, (2014, 12, 31))]
        )

    def test_update_names_arctic_2015_q1_bls(self):
        doc = self.read_report("reports/arctic_2015_q1.pdf") 
        self.assertEqual(
            doc.bls.names, 
            [(3, (2015, 3, 31)), (3, (2014, 12, 31)), (3, (2014, 3, 31))]
        )

    def test_update_names_arctic_2015_q1_cfs(self):
        doc = self.read_report("reports/arctic_2015_q1.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(3, (2015, 3, 31)), (3, (2014, 3, 31)), (12, (2014, 12, 31))]
        )

    ## reports/ltx_2016_y.pdf
    def test_update_names_ltx_2016_y_ics(self):
        doc = self.read_report("reports/ltx_2016_y.pdf")
        self.assertEqual(
            doc.ics.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_ltx_2016_y_bls(self):
        doc = self.read_report("reports/ltx_2016_y.pdf")
        self.assertEqual(
            doc.bls.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )

    def test_update_names_ltx_2016_y_cfs(self):
        doc = self.read_report("reports/ltx_2016_y.pdf")
        self.assertEqual(
            doc.cfs.names, 
            [(12, (2016, 12, 31)), (12, (2015, 12, 31))]
        )