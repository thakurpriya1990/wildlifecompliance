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

## only generate leaf nodes
#def build_boe_roi_hierarchy(legal_case):
#    # build offences, offenders and ROI hierarchy
#    for offence in legal_case.offence_legal_case.all():
#        if not offence.offender_set.count():
#            offence_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
#                    legal_case=legal_case, 
#                    offence=offence,
#                    offender=None,
#                    record_of_interview=None,
#                    associated_doc_artifact=None)
#        else:
#            for offender in offence.offender_set.all():
#                # statements must be 'record_of_interview' only
#                if not offender.document_artifact_offender.count() or not (
#                    'record_of_interview' in [document_artifact.document_type for 
#                    document_artifact in offender.document_artifact_offender.all()]):
#                    offender_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
#                            legal_case=legal_case, 
#                            offence=offence,
#                            offender= offender,
#                            record_of_interview=None,
#                            associated_doc_artifact=None)
#                else:
#                    for document_artifact in offender.document_artifact_offender.all():
#                        if document_artifact.offence == offence and document_artifact.document_type == 'record_of_interview' and (
#                                not document_artifact.document_artifact_statement.count()):
#                            roi_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
#                                    legal_case=legal_case, 
#                                    offence=offence,
#                                    offender= offender,
#                                    record_of_interview=document_artifact,
#                                    associated_doc_artifact=None)
#                        else:
#                            for sub_document_artifact in document_artifact.document_artifact_statement.all():
#                                doc_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
#                                        legal_case=legal_case, 
#                                        offence=offence,
#                                        offender= offender,
#                                        record_of_interview=document_artifact,
#                                        associated_doc_artifact=sub_document_artifact)

# generate every node in the tree
def build_all_boe_roi_hierarchy(legal_case):
    # build offences, offenders and ROI hierarchy
    for offence in legal_case.offence_legal_case.all():
        offence_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                legal_case=legal_case, 
                offence=offence,
                offender=None,
                record_of_interview=None,
                associated_doc_artifact=None)
        for offender in offence.offender_set.all():
            offender_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                    legal_case=legal_case, 
                    offence=offence,
                    offender= offender,
                    record_of_interview=None,
                    associated_doc_artifact=None)
            if created:
                offence_level_record.children.add(offender_level_record)
            for document_artifact in offender.document_artifact_offender.all():
                if document_artifact.offence == offence and document_artifact.document_type == 'record_of_interview':
                    roi_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                            legal_case=legal_case, 
                            offence=offence,
                            offender= offender,
                            record_of_interview=document_artifact,
                            associated_doc_artifact=None)
                    if created:
                        offender_level_record.children.add(roi_level_record)
                    for sub_document_artifact in document_artifact.document_artifact_statement.all():
                        doc_level_record, created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                                legal_case=legal_case, 
                                offence=offence,
                                offender= offender,
                                record_of_interview=document_artifact,
                                associated_doc_artifact=sub_document_artifact)
                        if created:
                            roi_level_record.children.add(doc_level_record)

