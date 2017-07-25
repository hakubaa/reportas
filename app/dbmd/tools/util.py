import io

from rparser.base import FinancialReport, PDFFileIO
from db.models import Company, RecordType
from db.util import get_records_reprs, get_companies_reprs


class FinancialReportDB(FinancialReport):
    def __init__(self, *args, session, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
            
    def get_bls_spec(self):
        return get_records_reprs(self.session, "bls", record_spec_id="name")
    
    def get_ics_spec(self):
        return get_records_reprs(self.session, "ics", record_spec_id="name")
    
    def get_cfs_spec(self):
        return get_records_reprs(self.session, "cfs", record_spec_id="name")
        
    def get_companies_spec(self):
        return get_companies_reprs(self.session)
        
        
def read_report_from_file(path, session):
    report = FinancialReportDB(
        io.TextIOWrapper(PDFFileIO(path)), session=session
    )
    return report    

def get_company(isin, session):
    company = session.query(Company).filter_by(isin=isin).first()  
    return company 

def get_record_types(session):
    rtypes = session.query(RecordType.id, RecordType.name).all()
    return [dict(zip(("id", "name"), rtype)) for rtype in rtypes]