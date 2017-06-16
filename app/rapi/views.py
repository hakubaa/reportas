from app.rapi import api
from app.rapi import resources as res


api.add_resource(res.Root, "/", endpoint="root")
api.add_resource(res.CompanyList, "/companies", endpoint="company_list")
api.add_resource(res.CompanyDetail, "/companies/<int:id>", endpoint="company")
api.add_resource(res.CompanyReprList, "/companies/<int:id>/reprs", 
                 endpoint="crepr_list")
api.add_resource(res.RecordTypeList, "/rtypes", endpoint="rtype_list")
api.add_resource(res.RecordTypeDetail, "/rtypes/<int:id>", endpoint="rtype")
api.add_resource(res.RecordTypeReprList, "/rtypes/<int:id>/reprs",
                 endpoint="rtype_repr_list")
api.add_resource(res.RecordTypeReprDetail, "/rtypes/<int:id>/reprs/<int:rid>",
                 endpoint="rtype_repr")