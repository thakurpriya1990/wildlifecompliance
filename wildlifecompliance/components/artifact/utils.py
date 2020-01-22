#import ast
#import requests
#import json
#import logging
#from django.conf import settings
#from django.core.exceptions import ValidationError
#from django.core.urlresolvers import reverse
#from django.http import HttpResponseRedirect
#from ledger.checkout.utils import create_basket_session, create_checkout_session, place_order_submission
#from ledger.payments.models import Invoice
#from wildlifecompliance.exceptions import BindApplicationException
#from django.db.models import Q
#from django.core.cache import cache
#from wildlifecompliance.components.artifact.models import BriefOfEvidenceRecordOfInterview, DocumentArtifact
#from wildlifecompliance.components.offence.models import Offence, Offender
#from wildlifecompliance.components.legal_case.models import LegalCase
from wildlifecompliance.components.artifact.models import BriefOfEvidenceRecordOfInterview

def build_legal_case_hierarchy(legal_case):
        # build offences, offenders and ROI hierarchy
        if legal_case.offence_legal_case.count():
            #boe_list = []
            for offence in self.offence_legal_case.all():
                offence_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                        legal_case=legal_case, 
                        offence=offence)

                for offender in offence.offender_set.all():
                    offender_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                            legal_case=legal_case, 
                            offence=offence,
                            offender= offender)
                    for document_artifact in offender.document_artifact_offender.all():
                        if document_artifact.offence == offence:
                            roi_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                                    legal_case=legal_case, 
                                    offence=offence,
                                    offender= offender,
                                    record_of_interview=document_artifact)
                            for sub_document_artifact in document_artifact.document_artifact_statement.all():
                                doc_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                                        legal_case=legal_case, 
                                        offence=offence,
                                        offender= offender,
                                        record_of_interview=document_artifact,
                                        associated_doc_artifact=sub_document_artifact)
                        #else:
                         #   print("nah not this one")
            #print("boe_list")
            #for l in boe_list:
            #    print(l)


