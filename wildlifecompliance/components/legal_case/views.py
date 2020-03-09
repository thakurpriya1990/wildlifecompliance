import traceback
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views import View
from rest_framework import serializers, views, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from wildlifecompliance.components.legal_case.generate_pdf import create_document_pdf_bytes
from wildlifecompliance.components.legal_case.models import LegalCase, LegalCaseUserAction


#class GenerateLegalCaseDocumentView(views.APIView):
#class GenerateLegalCaseDocumentView(View):

    #def post(request):
def generate_legal_case_document(request):
    print(request.POST)
    try:
        document_label = ''
        if request.POST.get("document_type") == 'brief_of_evidence':
            document_label = "Brief of Evidence"
        elif request.POST.get("document_type") == 'prosecution_brief':
            document_label = "Prosecution Brief"
        section_list = ''
        if request.POST.get('include_statement_of_facts'):
            section_list += "Statement of Facts"
        if request.POST.get('include_case_information_form'):
            if section_list:
                section_list += ", "
            section_list += "Case Information Form"
        if request.POST.get('include_offences_offenders_roi'):
            if section_list:
                section_list += ", "
            section_list += "Offences, Offenders and Records of Interview"
        if request.POST.get('include_witness_officer_other_statements'):
            if section_list:
                section_list += ", "
            section_list += "Witness Statements, Officer Statements, Expert Statements"
        if request.POST.get('include_physical_artifacts'):
            if section_list:
                section_list += ", "
            section_list += "List of Exhibits, Sensitive Unused and Non-sensitive Unused Materials"
        if request.POST.get('include_document_artifacts'):
            if section_list:
                section_list += ", "
            section_list += "List of Photographic, Video and Sound Exhibits"

        legal_case_id = request.POST.get('legal_case_id', '')
        legal_case = None
        if legal_case_id:
            legal_case = LegalCase.objects.get(id=legal_case_id)
        http_response = create_document_pdf_bytes(legal_case, request.POST)
        #print("http_response")
        #print(http_response)
        #if returned_document:
        if http_response:
            legal_case.log_user_action(
                    LegalCaseUserAction.ACTION_GENERATE_DOCUMENT.format(
                    document_label,
                    legal_case.number,
                    section_list
                    ), request)
            return http_response
        else:
            return Response()
    except Exception as e:
        print(traceback.print_exc())
        raise e


