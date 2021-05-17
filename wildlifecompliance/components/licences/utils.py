import logging
import json

from abc import ABC

from wildlifecompliance.components.licences.models import SectionQuestion

logger = logging.getLogger(__name__)
# logger = logging


class LicenceUtility(ABC):
    '''
    An abstract base helper utility for Licences.
    '''
    logger_title = '{0}'.format('LicenceUtility')


class LicencePurposeUtil(LicenceUtility):
    """
    Helper utility for Licence Purpose.
    """
    licence = None

    def __init__(self, purpose):
        self.licence = purpose

    def is_valid_age_for(self, user):
        '''
        Check user date of birth minimum age required for licence.
        '''
        from datetime import date
        logger.debug('LicencePurposeUtil.is_valid_age_for() - start')
        valid = False
        today = date.today()
        # calculate age within the year.
        # yy = 1 if ((today.month, today.day) < born.month, born.day)) else 0
        # age = today.year - born.year - yy
        difference = (today.year - user.dob.year - (
            (today.month, today.day) < (user.dob.month, user.dob.day)
        )) - self.licence.minimum_age
        valid = True if difference > -1 else False

        logger.debug('LicencePurposeUtil.is_valid_age_for() - end')
        return valid


class LicenceSchemaUtility(LicenceUtility):
    '''
    A LicenceUtility for licence schema.
    '''
    licence_sections = None

    SECTION_TYPES = ['group', 'group2', 'expander_table', 'species-all']

    def __init__(self, licence_sections):
        self.licence_sections = licence_sections

    def get_options(self, section_question, question):
        options = []
        special_types = ['radiobuttons', 'multi-select', ]
        if question.option.count() > 0:
            for op in question.option.all().order_by(
                '-wildlifecompliance_masterlistquestion_option.id'
            ):
                op_dict = {
                    'label': op.label,
                    'value': op.label.replace(" ", "").lower(),
                }
                options.append(op_dict)

        # For multi-select type questions, the isRequired flag goes to the
        # first option dict instead of question dict
        if 'isRequired' in section_question.get_tag_list(

        ) and question.answer_type in special_types:
            if options:
                options[0]['isRequired'] = 'true'

        return options

    def get_special_conditions(self, section_question, section, option):
        conditions = []

        options = section_question.question.option.filter(
            label=option['label']
        ).order_by(
            '-wildlifecompliance_masterlistquestion_option.id')

        section_question = SectionQuestion.objects.filter(
            section=section,
            parent_question=section_question.question,
            parent_answer__in=options
        ).first()

        if section_question and section_question.apply_special_conditions:

            for c in section_question.special_conditions.all():

                op_dict = {
                    'label': c.label,
                    'value': c.value
                }
                conditions.append(op_dict)

        return conditions

    def get_checkbox_option_children(
        self, section_question, question, section, parent_name=''
    ):
        conditions = {}
        options = question.option.all().order_by(
            '-wildlifecompliance_masterlistquestion_option.id')
        options_list = []
        special_types = ['checkbox', ]
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        option_count = 0
        for op in options:
            op_name = '{}-{}'.format(parent_name, option_count)
            op_dict = {
                    'name': op_name,
                    'label': op.label,
                    'type': 'checkbox',
                    'group': parent_name
            }
            condition_questions = SectionQuestion.objects.filter(
                section=section,
                parent_question=question,
                parent_answer=op
            ).order_by('order')
            if condition_questions:
                option_section = []
                option_children = []
                condition_question_count = 1
                for q in condition_questions:

                    question_name = '{}-On-{}'.format(
                        op_name, condition_question_count)
                    child = {
                        'name': question_name,
                        'type': q.question.answer_type,
                        'label': q.question.question,
                    }
                    if q.question.answer_type in special_types:
                        qo_children = self.get_checkbox_option_children(
                            q, q.question, section, question_name
                        )
                        child['children'] = qo_children
                        child['type'] = 'group'
                    else:
                        if q.question.option.count() > 0:
                            q_options = self.get_options(q, q.question)
                            child['options'] = q_options

                        if q.question.children_question.exists():
                            q_conditions = self.get_condition_children(
                                q.question, section, question_name
                            )
                            child['conditions'] = q_conditions

                    if q.tag:
                        for t in q.tag:
                            if t == 'isRequired':
                                if q.question.answer_type not in group_types:
                                    child[t] = 'true'
                            else:
                                child[t] = 'true'

                    option_children.append(child)
                    condition_question_count += 1
                section_group_name = op_name+'-OnGroup'
                option_section_dict = {
                    'name': section_group_name,
                    'type': 'group',
                    'label': '',
                    'children': option_children
                }
                option_section.append(option_section_dict)
                conditions['on'] = option_section
                op_dict['conditions'] = conditions
            options_list.append(op_dict)
            option_count += 1

        if 'isRequired' in section_question.get_tag_list():
            if options_list:
                options_list[0]['isRequired'] = 'true'

        return options_list

    def get_condition_children(self, question, section, parent_name=''):
        conditions = {}
        options = question.option.all().order_by(
            '-wildlifecompliance_masterlistquestion_option.id'
        )
        special_types = ['checkbox', ]
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        option_count = 0

        for op in options:
            condition_questions = SectionQuestion.objects.filter(
                section=section, parent_question=question, parent_answer=op
            ).order_by('order')
            if condition_questions:
                option_section = []
                option_children = []
                condition_question_count = 1

                for q in condition_questions:
                    question_name = '{}-{}{}'.format(
                        parent_name, op.label.replace(" ", ""),
                        condition_question_count
                    )

                    child = {
                        'name': question_name,
                        'type': q.question.answer_type,
                        'label': q.question.question,
                    }
                    if q.question.answer_type in special_types:
                        q_option_children = self.get_checkbox_option_children(
                            q, q.question, section, question_name
                        )
                        child['children'] = q_option_children
                        child['type'] = 'group'

                    else:
                        if q.question.option.count() > 0:
                            q_options = self.get_options(q, q.question)
                            child['options'] = q_options

                        if q.question.children_questions.exists():

                            q_conditions = self.get_condition_children(
                                q.question, section, question_name
                            )
                            child['conditions'] = q_conditions

                    if q.tag:
                        for t in q.tag:
                            if t == 'isRequired':
                                if q.question.answer_type not in group_types:
                                    child[t] = 'true'
                            else:
                                child[t] = 'true'

                    # if q.question.help_text_url:
                    #     child['help_text_url']='{0}/anchor={1}'.format(
                    # help_site_url, question_name)

                    # create_richtext_help(q.question, question_name)
                    option_children.append(child)
                    condition_question_count += 1
                # section_group_name=parent_name+'-'+op.label+'Group'
                # section_group_name = parent_name + '-' + op.label.replace(
                #     " ", ""
                # ) + 'Group'
                # option_section_dict = {
                #     'name': section_group_name,
                #     'type': 'group',
                #     'label': '',
                #     'children': option_children
                # }
                # option_section.append(option_section_dict)
                option_section.append(option_children[0])
                conditions[op.label.replace(" ", "").lower()] = option_section
                option_count += 1
        return conditions

    def get_group_children(self, question, section, parent_name=''):
        grouped_children = []
        # options = question.option.all().order_by(
        #     '-wildlifecompliance_masterlistquestion_option.id'
        # )
        special_types = ['checkbox', ]
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        expander_types = ['expander_table']
        section_count = 0

        group_questions = SectionQuestion.objects.filter(
            section=question.section, parent_question=question.question
        ).order_by('order')

        # option_section = []
        # option_children = []
        group_question_count = 1

        for q in group_questions:

            question_name = '{}-{}{}'.format(
                parent_name,
                q.question.answer_type,
                group_question_count
            )

            child = {
                'name': question_name,
                'type': q.question.answer_type,
                'label': '',
            }
            if q.question.answer_type in special_types:

                q_option_children = self.get_checkbox_option_children(
                    q, q.question, section, question_name
                )
                child['children'] = q_option_children
                child['type'] = 'group'

            elif q.question.answer_type in expander_types:

                child['label'] = ''

                q_header_children = self.get_header_children(
                    q, q.question, section, question_name
                )
                child['header'] = q_header_children

                q_expander_children = self.get_expander_children(
                    q, q.question, section, question_name
                )
                child['expander'] = q_expander_children

            else:
                if q.question.option.count() > 0:
                    q_options = self.get_options(q, q.question)
                    child['options'] = q_options

                if q.question.children_questions.exists():

                    q_conditions = self.get_condition_children(
                        q.question, section, question_name
                    )
                    child['conditions'] = q_conditions

            if q.tag:
                for t in q.tag:
                    if t == 'isRequired':
                        if q.question.answer_type not in group_types:
                            child[t] = 'true'
                    else:
                        child[t] = 'true'

            group_question_count += 1
            grouped_children.append(child)

        section_count += 1
        return grouped_children

    def get_header_children(self, sq, question, section, parent_name=''):
        header_children = []
        header_types = ['header']

        group_questions = SectionQuestion.objects.filter(
            section=sq.section, parent_question=sq.question
        ).order_by('order')

        header_question_count = 0

        for q in group_questions:

            if q.question.answer_type not in header_types:
                continue

            question_name = '{}-Header{}'.format(
                parent_name,
                # question.question.question.replace(" ", ""),
                header_question_count
            )

            column_type = SectionQuestion.objects.filter(
                section=sq.section, parent_question=q.question
            ).first()

            header = {
                'name': question_name,
                'type': column_type.question.answer_type,
                'label': q.question.question,
            }

            # if q.question.option.count() > 0:
            #     q_options = self.get_options(q, q.question)
            #     header['options'] = q_options

            # if q.question.children_questions.exists():

            #     q_conditions = self.get_condition_children(
            #         q.question, section, question_name
            #     )
            #     header['conditions'] = q_conditions

            header_question_count += 1
            header_children.append(header)

        return header_children

    def get_expander_children(self, sq, question, section, parent_name=''):
        expander_children = []
        expander_types = ['expander']
        # type_count = 0

        group_questions = SectionQuestion.objects.filter(
            section=sq.section, parent_question=sq.question
        ).order_by('order')

        expander_question_count = 0

        for q in group_questions:

            if q.question.answer_type not in expander_types:
                continue

            expander_name = '{}-Expander{}'.format(
                parent_name,
                # question.question.question.replace(" ", ""),
                expander_question_count
            )

            expander_type = SectionQuestion.objects.filter(
                section=sq.section, parent_question=q.question
            ).first()

            expander = {
                'name': expander_name,
                'type': expander_type.question.answer_type,
                'label': expander_type.question.question,
            }

            # NOTE: a recursive call here for groupings within the expander.

            if expander_type.question.answer_type in self.SECTION_TYPES:

                ex_group_children = self.get_group_children(
                    expander_type, expander_type.question, section)

                expander['children'] = ex_group_children

            # if q.question.option.count() > 0:
            #     q_options = self.get_options(q, q.question)
            #     header['options'] = q_options

            # if q.question.children_questions.exists():

            #     q_conditions = self.get_condition_children(
            #         q.question, section, question_name
            #     )
                # header['conditions'] = q_conditions

            expander_question_count += 1
            expander_children.append(expander)

        return expander_children

    def get_licence_schema(self):
        '''
        '''
        section_count = 0
        schema = []
        special_types = ['checkbox', ]

        # 'isRequired' tag for following types is added to first option dict
        # instead of question.
        group_types = ['checkbox', 'radiobuttons', 'multi-select']

        for section in self.licence_sections:
            section_name = 'Section{}'.format(section_count)
            section_dict = {
                'name': section_name,
                'type': 'section',
                'label': section.section_label,
            }
            section_children = []
            section_questions = SectionQuestion.objects.filter(
                section=section,
                parent_question__isnull=True,
                parent_answer__isnull=True
            ).order_by('order')

            if section_questions:
                sq_count = 0
                for sq in section_questions:

                    sq_name = '{}-{}{}'.format(
                        section_name,
                        sq.question.answer_type,
                        sq_count
                    )
                    sc = {
                        'name': sq_name,
                        'type': sq.question.answer_type,
                        'label': sq.question.question,
                    }

                    if sq.question.answer_type in self.SECTION_TYPES:

                        sq_group_children = self.get_group_children(
                            sq, sq.question, sq_name)

                        sc['children'] = sq_group_children
                        sc['type'] = sq.question.answer_type

                    elif sq.question.answer_type in special_types:

                        sq_option_children = self.get_checkbox_option_children(
                            sq, sq.question, section, sq_name)

                        sc['children'] = sq_option_children
                        sc['type'] = 'checkbox'

                    else:

                        if sq.question.option.count() > 0:
                            sq_options = self.get_options(sq, sq.question)

                            # establish special fields for options.
                            if sq.question.answer_type in [
                                'checkbox', 'radiobuttons'
                            ]:
                                for o in sq_options:

                                    sq_fields = self.get_special_conditions(
                                        sq, section, o
                                    )
                                    for f in sq_fields:
                                        key = f['label']
                                        o[key] = f['value']

                            sc['options'] = sq_options

                    if sq.question.children_questions.exists():
                        sq_children = self.get_condition_children(
                            sq.question, section, sq_name
                        )
                        if sq_children:
                            sc['conditions'] = sq_children

                    if sq.tag:
                        for t in sq.tag:
                            if t == 'isRequired':
                                if sq.question.answer_type not in group_types:
                                    sc[t] = 'true'
                            else:
                                sc[t] = 'true'

                    section_children.append(sc)
                    sq_count += 1
            if section_children:
                section_dict['children'] = section_children
            section_count += 1
            schema.append(section_dict)
        new_schema = json.dumps(schema)

        return json.loads(new_schema)
