import logging
import os
from django.conf import settings
from docxtpl import DocxTemplate
from wildlifecompliance.components.main.models import SanctionOutcomeWordTemplate
from wildlifecompliance.components.sanction_outcome.models import AllegedCommittedOffence


logger = logging.getLogger(__name__)


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
    try:
        so_outcome_template = SanctionOutcomeWordTemplate.objects.filter(act=alleged_offence.act, sanction_outcome_type=sanction_outcome.type).order_by('-id').first()
    except:
        raise Exception('Template not found for the Act: {} and Sanction Outcome type: {}'.format(alleged_offence.act, sanction_outcome.type))

    path_to_template = so_outcome_template._file.path

    doc = DocxTemplate(path_to_template)

    try:
        offender = sanction_outcome.get_offender()[0]
    except:
        raise Exception('No offender found for the Sanction Outcome: {}'.format(sanction_outcome.lodgement_number))
    offender_dob = offender.dob.strftime('%d/%m/%Y') if offender.dob else ''
    offender_postcode = offender.residential_address.postcode if offender.residential_address else ''
    offender_email = offender.email if offender.email else ''
    rego = sanction_outcome.registration_number if sanction_outcome.registration_number else ''
    offence_datetime = sanction_outcome.offence.offence_occurrence_datetime if sanction_outcome.offence.offence_occurrence_datetime else ''
    responsible_officer_name = sanction_outcome.responsible_officer.get_full_name() if sanction_outcome.responsible_officer else ''
    issue_date = sanction_outcome.date_of_issue.strftime('%d/%m/%Y')
    issue_time = sanction_outcome.time_of_issue.strftime('%I:%M %p')

    context = {
        'lodgement_number': sanction_outcome.lodgement_number,
        'offender_family_name': offender.last_name,
        'offender_given_name': offender.first_name,
        'offender_date_of_birth': offender_dob,
        'offender_postcode': offender_postcode,
        'offender_residential_address': offender.residential_address,
        'offender_email': offender_email,
        'registration_number': rego,
        'offence_location': sanction_outcome.offence.location,
        'offence_date': offence_datetime.strftime('%d/%m/%Y'),
        'offence_time': offence_datetime.strftime('%I:%M %p'),
        'sanction_outcome_description': sanction_outcome.description,
        'responsible_officer_name': responsible_officer_name,
        'issue_date': issue_date,
        'issue_time': issue_time,
    }

    doc.render(context)

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
