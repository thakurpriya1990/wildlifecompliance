from wildlifecompliance.components.artifact.models import (
        BriefOfEvidenceRecordOfInterview, 
        BriefOfEvidenceOtherStatements,
        BriefOfEvidencePhysicalArtifacts,
        BriefOfEvidenceDocumentArtifacts,
        )


def generate_boe_document_artifacts(legal_case):
    # get all associated primary DocumentArtifacts
    #for artifact in legal_case.legal_case_document_artifacts_primary.all():
    #for artifact in legal_case.briefofevidencedocumentartifacts_set.all():
    for artifact in legal_case.legal_case_document_artifacts.all():
        artifact, created = BriefOfEvidenceDocumentArtifacts.objects.get_or_create(
                legal_case=legal_case,
                document_artifact=artifact
                )

def update_boe_document_artifacts_ticked(legal_case, boe_document_artifacts_ticked):
    # get all associated BriefOfEvidenceDocumentArtifacts records
    queryset = BriefOfEvidenceDocumentArtifacts.objects.filter(legal_case__id=legal_case.id)
    for record in queryset:
        if record.id in boe_document_artifacts_ticked:
            record.ticked = True
        else:
            record.ticked = False
        record.save()

def generate_boe_physical_artifacts(legal_case):
    # get all associated primary PhysicalArtifacts
    #for artifact in legal_case.legal_case_physical_artifacts_primary.all():
    for artifact in legal_case.legal_case_physical_artifacts.all():
        artifact, created = BriefOfEvidencePhysicalArtifacts.objects.get_or_create(
                legal_case=legal_case,
                physical_artifact=artifact
                )

def update_boe_physical_artifacts_ticked(legal_case, boe_physical_artifacts_ticked):
    # get all associated BriefOfEvidencePhysicalArtifacts records
    print("update_boe_physical_artifacts_ticked")
    queryset = BriefOfEvidencePhysicalArtifacts.objects.filter(legal_case__id=legal_case.id)
    for record in queryset:
        if record.id in boe_physical_artifacts_ticked:
            record.ticked = True
        else:
            record.ticked = False
        record.save()

# generate every node in the tree
def build_all_boe_other_statements_hierarchy(legal_case):
    for statement_document_artifact in legal_case.legal_case_document_artifacts.all():
        if statement_document_artifact.document_type in ['witness_statement', 'expert_statement', 'officer_statement']:
            # get person string according to document_type
            person = None
            if not statement_document_artifact.document_type == 'officer_statement' and statement_document_artifact.person_providing_statement:
                person = statement_document_artifact.person_providing_statement
            else:
                person = statement_document_artifact.officer_interviewer
            statement_level_record, statement_level_record_created = BriefOfEvidenceOtherStatements.objects.get_or_create(
                    legal_case=legal_case,
                    person=person,
                    statement=statement_document_artifact,
                    associated_doc_artifact=None)
            if statement_level_record_created:
                # get or create parent record, then add statement level record to children
                person_level_record, person_level_record_created = BriefOfEvidenceOtherStatements.objects.get_or_create(
                        legal_case=legal_case,
                        person=person,
                        statement=None,
                        associated_doc_artifact=None)
                person_level_record.children.add(statement_level_record)
                # now find associated_doc_artifacts
                for associated_doc in statement_document_artifact.document_artifact_statement.all():
                    associated_doc_level_record, associated_doc_level_record_created = BriefOfEvidenceOtherStatements.objects.get_or_create(
                            legal_case=legal_case,
                            person=person,
                            statement=statement_document_artifact,
                            associated_doc_artifact=associated_doc)
                    if associated_doc_level_record_created:
                        statement_level_record.children.add(associated_doc_level_record)

def update_boe_other_statements_ticked(legal_case, boe_other_statements_ticked):
    # get all associated BriefOfEvidenceRecordOfInterview records
    queryset = BriefOfEvidenceOtherStatements.objects.filter(legal_case__id=legal_case.id)
    for record in queryset:
        if record.id in boe_other_statements_ticked:
            record.ticked = True
        else:
            record.ticked = False
        record.save()

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
            offender_level_record, offender_level_record_created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                    legal_case=legal_case, 
                    offence=offence,
                    offender= offender,
                    record_of_interview=None,
                    associated_doc_artifact=None)
            if offender_level_record_created:
                #print('add offender level record {} to offence {}'.format(offender_level_record, offence_level_record))
                offence_level_record.children.add(offender_level_record)
            for document_artifact in offender.document_artifact_offender.all():
                if document_artifact.offence == offence and document_artifact.document_type == 'record_of_interview':
                    roi_level_record, roi_level_record_created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                            legal_case=legal_case, 
                            offence=offence,
                            offender= offender,
                            record_of_interview=document_artifact,
                            associated_doc_artifact=None)
                    if roi_level_record_created:
                        #print('add roi level record {} to offender {}'.format(roi_level_record, offender_level_record))
                        offender_level_record.children.add(roi_level_record)
                    for sub_document_artifact in document_artifact.document_artifact_statement.all():
                        doc_level_record, doi_level_record_created = BriefOfEvidenceRecordOfInterview.objects.get_or_create(
                                legal_case=legal_case, 
                                offence=offence,
                                offender= offender,
                                record_of_interview=document_artifact,
                                associated_doc_artifact=sub_document_artifact)
                        if doi_level_record_created:
                            #print('add doc level record {} to roi {}'.format(doc_level_record, roi_level_record))
                            roi_level_record.children.add(doc_level_record)

def update_boe_roi_ticked(legal_case, boe_roi_ticked):
    #print("boe_roi_ticked")
    #print(boe_roi_ticked)
    # get all associated BriefOfEvidenceRecordOfInterview records
    queryset = BriefOfEvidenceRecordOfInterview.objects.filter(legal_case__id=legal_case.id)
    for record in queryset:
        if record.id in boe_roi_ticked:
            record.ticked = True
        else:
            record.ticked = False
        record.save()


