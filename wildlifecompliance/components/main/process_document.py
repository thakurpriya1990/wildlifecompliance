from django.core.files.storage import default_storage 
import os
from django.core.files.base import ContentFile
import traceback
from wildlifecompliance.components.main.models import TemporaryDocument


def process_generic_document(request, instance, document_type=None, *args, **kwargs):
    try:
        action = request.data.get('action')
        input_name = request.data.get('input_name')
        comms_log_id = request.data.get('comms_log_id')
        comms_instance = None
        # returned_file_data = None

        if document_type == 'comms_log' and comms_log_id and comms_log_id is not 'null':
            comms_instance = instance.comms_logs.get(
                    id=comms_log_id)
        elif document_type == 'comms_log':
            comms_instance = instance.comms_logs.create()

        if action == 'list':
            pass

        elif action == 'delete':
            delete_document(request, instance, comms_instance, document_type, input_name)

        elif action == 'cancel':
            deleted = cancel_document(request, instance, comms_instance, document_type, input_name)

        elif action == 'save':
            save_document(request, instance, comms_instance, document_type, input_name)

        # HTTP Response varies by action and instance type
        if comms_instance and action == 'cancel' and deleted:
            return deleted
        elif comms_instance:
            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in comms_instance.documents.all() if d._file]
            return {'filedata': returned_file_data,
                    'comms_instance_id': comms_instance.id}

        elif document_type == 'renderer_documents' and input_name:
            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        input_name=d.input_name,
                        ) for d in instance.renderer_documents.filter(input_name=input_name) if d._file]
            return {'filedata': returned_file_data}

        elif document_type == 'issuance_documents':
            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in instance.issuance_documents.all() if d._file]
            return {'filedata': returned_file_data}

        elif document_type == 'court_outcome':
            returned_file_data = [dict(
                file=d._file.url,
                id=d.id,
                name=d.name,
            ) for d in instance.court_proceedings.court_outcome_documents.all() if d._file]
            return {'filedata': returned_file_data}

        elif document_type == 'inspection_report':
            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in instance.report.all() if d._file]
            return {'filedata': returned_file_data}

        elif document_type == 'prosecution_notice':
            returned_file_data = [dict(
                file=d._file.url,
                id=d.id,
                name=d.name,
            ) for d in instance.prosecution_notices.all() if d._file]
            return {'filedata': returned_file_data}

        elif document_type == 'court_hearing_notice':
            returned_file_data = [dict(
                file=d._file.url,
                id=d.id,
                name=d.name,
            ) for d in instance.court_hearing_notices.all() if d._file]
            return {'filedata': returned_file_data}

        elif document_type == 'generated_documents':
            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in instance.generated_documents.all() if d._file]
            return {'filedata': returned_file_data}

        else:
            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in instance.documents.all() if d._file]
            return {'filedata': returned_file_data}

    except Exception as e:
        print(traceback.print_exc())
        raise e


def delete_document(request, instance, comms_instance, document_type, input_name=None):
    # PhysicalArtifact renderer docs delete
    if document_type == 'renderer_documents' and 'document_id' in request.data and input_name:
        document_id = request.data.get('document_id')
        document = instance.renderer_documents.get(id=document_id, input_name=input_name)

    # Application Issuance docs delete
    elif document_type == 'issuance_documents' and 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = instance.issuance_documents.get(id=document_id)

    # inspection report delete
    elif document_type == 'inspection_report' and 'document_id' in request.data:
        #import ipdb; ipdb.set_trace();
        document_id = request.data.get('document_id')
        document = instance.report.get(id=document_id)

    # generated documents delete
    elif document_type == 'generated_documents' and 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = instance.generated_documents.get(id=document_id)

    # court outcome delete
    elif document_type == 'court_outcome' and 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = instance.court_proceedings.court_outcome_documents.get(id=document_id)

    # prosecution notice delete
    elif document_type == 'prosecution_notice' and 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = instance.prosecution_notices.get(id=document_id)

    # court hearing notice delete
    elif document_type == 'court_hearing_notice' and 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = instance.court_hearing_notices.get(id=document_id)

    # comms_log doc store delete
    elif comms_instance and 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = comms_instance.documents.get(id=document_id)

    # default doc store delete
    elif 'document_id' in request.data:
        document_id = request.data.get('document_id')
        document = instance.documents.get(id=document_id)

    if document._file and os.path.isfile(
            document._file.path):
        os.remove(document._file.path)

    if document:
        document.delete()


def cancel_document(request, instance, comms_instance, document_type, input_name=None):
        # PhysicalArtifact renderer documents cancel
        if document_type == 'renderer_documents':
            document_list = instance.renderer_documents.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # Application issuance documents cancel
        elif document_type == 'issuance_documents':
            document_list = instance.issuance_documents.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # Court outcome documents cancel
        elif document_type == 'court_outcome':
            document_list = instance.court_proceedings.court_outcome_documents.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # inspection report cancel
        elif document_type == 'inspection_report':
            document_list = instance.report.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # prosecution notice cancel
        elif document_type == 'prosecution_notice':
            document_list = instance.prosecution_notices.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # court hearing notice cancel
        elif document_type == 'court_hearing_notice':
            document_list = instance.court_hearing_notices.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # generated documents cancel
        elif document_type == 'generated_documents':
            document_list = instance.generated_documents.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()

        # comms_log doc cancel
        elif comms_instance:
            document_list = comms_instance.documents.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()
            return comms_instance.delete()

        # default doc cancel
        else:
            document_list = instance.documents.all()

            for document in document_list:
                if document._file and os.path.isfile(
                        document._file.path):
                    os.remove(document._file.path)
                document.delete()


def save_document(request, instance, comms_instance, document_type, input_name=None):
        # Match model related_name to instance or comms_instance, eg.
        # sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='documents')..
        # this document can be accessed or created by 'instance.documents'

        # PhysicalArtifact renderer document save
        if document_type == 'renderer_documents' and 'filename' in request.data and input_name:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.renderer_documents.get_or_create(
                input_name=input_name, name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/renderer_documents/{}/{}'.format(
                    instance._meta.model_name, instance.id, input_name, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()
        # Application issuance document save
        elif document_type == 'issuance_documents' and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            parent_application = instance.application
            document = instance.issuance_documents.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/{}/{}/{}'.format(
                    'applications', parent_application.id, instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()
        # inspection report save
        elif document_type == 'inspection_report' and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.report.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/report/{}'.format(
                    instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()
        # generated documents save
        elif document_type == 'generated_documents' and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.generated_documents.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/generated_documents/{}'.format(
                    instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()

        # inspection report save
        elif document_type == 'court_outcome' and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.court_proceedings.court_outcome_documents.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/court_outcome_documents/{}'.format(
                    instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()

        # prosecution notice save
        elif document_type == 'prosecution_notice' and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.prosecution_notices.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/prosecution_notices/{}'.format(
                    instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()

        # prosecution notice save
        elif document_type == 'court_hearing_notice' and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.court_hearing_notices.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/court_hearing_notices/{}'.format(
                    instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()

        # comms_log doc store save
        elif comms_instance and 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = comms_instance.documents.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/communications/{}/documents/{}'.format(
                    instance._meta.model_name, instance.id, comms_instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()

        # default doc store save
        elif 'filename' in request.data:
            filename = request.data.get('filename')
            _file = request.data.get('_file')

            document = instance.documents.get_or_create(
                name=filename)[0]
            path = default_storage.save(
                'wildlifecompliance/{}/{}/documents/{}'.format(
                    instance._meta.model_name, instance.id, filename), ContentFile(
                    _file.read()))

            document._file = path
            document.save()


# For transferring files from temp doc objs to comms_log objs
def save_comms_log_document_obj(instance, comms_instance, temp_document):
    document = comms_instance.documents.get_or_create(
        name=temp_document.name)[0]
    path = default_storage.save(
        'wildlifecompliance/{}/{}/communications/{}/documents/{}'.format(
            instance._meta.model_name, 
            instance.id, 
            comms_instance.id, 
            temp_document.name
            ), 
            temp_document._file
        )

    document._file = path
    document.save()

# For transferring files from temp doc objs to default doc objs
def save_default_document_obj(instance, temp_document):
    document = instance.documents.get_or_create(
        name=temp_document.name)[0]
    path = default_storage.save(
        'wildlifecompliance/{}/{}/documents/{}'.format(
            instance._meta.model_name, 
            instance.id, 
            temp_document.name
            ), 
            temp_document._file
        )

    document._file = path
    document.save()

# For transferring files from temp doc objs to issuance doc objs
def save_issuance_document_obj(instance, temp_document):
    document = instance.issuance_documents.get_or_create(
        name=temp_document.name)[0]
    path = default_storage.save(
        'wildlifecompliance/applications/{}/{}/{}/{}'.format(
            instance.application_id,
            instance._meta.model_name,
            instance.id,
            temp_document.name
            ),
        temp_document._file
        )

    document._file = path
    document.save()

# For transferring files from temp doc objs to physical artifact renderer objs
def save_renderer_document_obj(instance, temp_document, input_name):
    document = instance.renderer_documents.get_or_create(
            input_name=input_name,
            name=temp_document.name)[0]
    path = default_storage.save(
        'wildlifecompliance/{}/{}/renderer_documents/{}/{}'.format(
            instance._meta.model_name,
            instance.id,
            input_name,
            temp_document.name
            ),
            temp_document._file
        )

    document._file = path
    document.save()

