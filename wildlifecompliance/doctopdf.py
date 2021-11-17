import logging
import os
from django.conf import settings
from docxtpl import DocxTemplate
from wildlifecompliance.components.main.models import SanctionOutcomeWordTemplate
from wildlifecompliance.components.sanction_outcome.models import AllegedCommittedOffence


logger = logging.getLogger(__name__)


def convert_to_pdf(doc, pdf_filename):
    temp_directory = settings.BASE_DIR + "/tmp/"
    try:
        os.stat(temp_directory)
    except:
        os.mkdir(temp_directory)
    f_name = temp_directory + pdf_filename
    new_doc_file = f_name + '.docx'
    new_pdf_file = f_name + '.pdf'
    doc.save(new_doc_file)
    os.system("libreoffice --headless --convert-to pdf " + new_doc_file + " --outdir " + temp_directory)
    file_contents = None
    with open(new_pdf_file, 'rb') as f:
        file_contents = f.read()
    os.remove(new_doc_file)
    os.remove(new_pdf_file)
    return file_contents


def retrieve_context(sanction_outcome):
    try:
        offender = sanction_outcome.get_offender()[0]
    except:
        raise Exception('No offender found for the Sanction Outcome: {}'.format(sanction_outcome.lodgement_number))

    offender_family_name = offender.last_name if offender.last_name else ''
    offender_given_name = offender.first_name if offender.first_name else ''
    offender_dob = offender.dob.strftime('%d/%m/%Y') if offender.dob else ''
    offender_postcode = offender.residential_address.postcode if offender.residential_address else ''
    offender_residential_address = offender.residential_address if offender.residential_address else ''
    offender_email = offender.email if offender.email else ''
    rego = sanction_outcome.registration_number if sanction_outcome.registration_number else ''
    offence_date = sanction_outcome.offence.offence_occurrence_datetime.strftime('%d/%m/%Y') if sanction_outcome.offence.offence_occurrence_datetime else ''
    offence_time = sanction_outcome.offence.offence_occurrence_datetime.strftime('%I:%M %p') if sanction_outcome.offence.offence_occurrence_datetime else ''
    offence_location = sanction_outcome.offence.location if sanction_outcome.offence.location else ''
    responsible_officer_name = sanction_outcome.responsible_officer.get_full_name() if sanction_outcome.responsible_officer else ''
    issue_date = sanction_outcome.date_of_issue.strftime('%d/%m/%Y') if sanction_outcome.date_of_issue else ''
    issue_time = sanction_outcome.time_of_issue.strftime('%I:%M %p') if sanction_outcome.time_of_issue else ''
    remediation_actions = sanction_outcome.remediation_actions.all() if sanction_outcome.remediation_actions else ''
    regionDistrict = sanction_outcome.regionDistrictName if sanction_outcome.regionDistrictName else ''
    context = {
        'lodgement_number': sanction_outcome.lodgement_number,
        'offender_family_name': offender_family_name,
        'offender_given_name': offender_given_name,
        'offender_date_of_birth': offender_dob,
        'offender_postcode': offender_postcode,
        'offender_residential_address': offender_residential_address,
        'offender_email': offender_email,
        'offender_phone_number': offender.phone_number,
        'offender_mobile_number': offender.mobile_number,
        'registration_number': rego,
        'offence_location': offence_location,
        'offence_date': offence_date,
        'offence_time': offence_time,
        # 'offence_details': sanction_outcome.offence.details,
        'offence_details': sanction_outcome.description,
        'responsible_officer_name': responsible_officer_name,
        'issue_date': issue_date,
        'issue_time': issue_time,
        'remediation_actions': remediation_actions,
        'region_district': regionDistrict,
    }
    return context


def create_infringement_notice_pdf_contents(pdf_filename, sanction_outcome):
    acos = AllegedCommittedOffence.objects.filter(sanction_outcome=sanction_outcome, included=True)
    if acos.count() == 1:
        alleged_offence = acos[0].alleged_offence
    else:
        # Should not reach here.  For an infringement notice, there should be only one alleged offence.
        str = 'Sanction Outcome: {} has {} alleged offences.  There should be 1.'.format(sanction_outcome.lodgement_nubmer, acos.count())
        logger.error(str)
        raise Exception(str)

    # Retrieve the latest template which matches the Act and SanctionOutcome type.
    so_outcome_template = SanctionOutcomeWordTemplate.objects.filter(act=alleged_offence.act, sanction_outcome_type=sanction_outcome.type).order_by('-id').first()
    if not so_outcome_template:
        raise Exception('Template not found for the Act: {} and Sanction Outcome type: {}'.format(alleged_offence.act, sanction_outcome.type))

    path_to_template = so_outcome_template._file.path
    doc = DocxTemplate(path_to_template)
    context = retrieve_context(sanction_outcome)
    doc.render(context)

    file_contents = convert_to_pdf(doc, pdf_filename)
    return file_contents


def create_caution_notice_pdf_contents(pdf_filename, sanction_outcome):
    acos = AllegedCommittedOffence.objects.filter(sanction_outcome=sanction_outcome, included=True)
    if acos.count() > 0:
        alleged_offences = [item.alleged_offence for item in acos.all()]
    else:
        # Should not reach here.  For an infringement notice, there should be only one alleged offence.
        str = 'Sanction Outcome: {} has no alleged offences.  Caution notices cannot be created.'.format(sanction_outcome.lodgement_nubmer)
        logger.error(str)
        raise Exception(str)

    # Check the ACT type.  Act types cannot be mixed in a Sanction Outcome
    act = None
    for ao in alleged_offences:
        if not act:
            act = ao.act
        else:
            if act != ao.act:
                raise Exception('Different ACT types are present in the Sanction Outcome: {}'.format(sanction_outcome.lodgement_number))

    so_outcome_template = SanctionOutcomeWordTemplate.objects.filter(act=act, sanction_outcome_type=sanction_outcome.type).order_by('-id').first()
    if not so_outcome_template:
        raise Exception('Template not found for the Act: {} and Sanction Outcome type: {}'.format(act, sanction_outcome.type))

    path_to_template = so_outcome_template._file.path
    doc = DocxTemplate(path_to_template)
    context = retrieve_context(sanction_outcome)
    doc.render(context)

    file_contents = convert_to_pdf(doc, pdf_filename)
    return file_contents


def create_letter_of_advice_pdf_contents(pdf_filename, sanction_outcome):
    acos = AllegedCommittedOffence.objects.filter(sanction_outcome=sanction_outcome, included=True)
    if acos.count() > 0:
        alleged_offences = [item.alleged_offence for item in acos.all()]
    else:
        # Should not reach here.  For an infringement notice, there should be only one alleged offence.
        str = 'Sanction Outcome: {} has no alleged offences.  Caution notices cannot be created.'.format(sanction_outcome.lodgement_nubmer)
        logger.error(str)
        raise Exception(str)

    # Check the ACT type.  Act types cannot be mixed in a Sanction Outcome
    act = None
    for ao in alleged_offences:
        if not act:
            act = ao.act
        else:
            if act != ao.act:
                raise Exception('Different ACT types are present in the Sanction Outcome: {}'.format(sanction_outcome.lodgement_number))

    so_outcome_template = SanctionOutcomeWordTemplate.objects.filter(act=act, sanction_outcome_type=sanction_outcome.type).order_by('-id').first()
    if not so_outcome_template:
        raise Exception('Template not found for the Act: {} and Sanction Outcome type: {}'.format(act, sanction_outcome.type))

    path_to_template = so_outcome_template._file.path
    doc = DocxTemplate(path_to_template)
    context = retrieve_context(sanction_outcome)
    doc.render(context)

    file_contents = convert_to_pdf(doc, pdf_filename)
    return file_contents


def create_remediation_notice_pdf_contents(pdf_filename, sanction_outcome):
    acos = AllegedCommittedOffence.objects.filter(sanction_outcome=sanction_outcome, included=True)
    if acos.count() > 0:
        alleged_offences = [item.alleged_offence for item in acos.all()]
    else:
        # Should not reach here.  For an infringement notice, there should be only one alleged offence.
        str = 'Sanction Outcome: {} has no alleged offences.  Caution notices cannot be created.'.format(sanction_outcome.lodgement_nubmer)
        logger.error(str)
        raise Exception(str)

    so_outcome_template = SanctionOutcomeWordTemplate.objects.filter(sanction_outcome_type=sanction_outcome.type).order_by('-id').first()
    if not so_outcome_template:
        raise Exception('Template not found for the Sanction Outcome type: {}'.format(sanction_outcome.type))

    path_to_template = so_outcome_template._file.path
    doc = DocxTemplate(path_to_template)
    context = retrieve_context(sanction_outcome)
    doc.render(context)

    file_contents = convert_to_pdf(doc, pdf_filename)
    return file_contents