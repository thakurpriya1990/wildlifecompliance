import logging
import json

from abc import ABC

from wildlifecompliance.components.licences.models import SectionQuestion, SectionGroup

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

    # SECTION_TYPES = ['group', 'group2', 'expander_table', 'species-all']
    SECTION_TYPES = ['group', ]

    def __init__(self, licence_sections):
        self.licence_sections = licence_sections

    # def get_options(self, section_question, question):
    #     options = []
    #     special_types = ['radiobuttons', 'multi-select', ]
    #     if question.option.count() > 0:
    #         for op in question.option.all().order_by(
    #             '-wildlifecompliance_masterlistquestion_option.id'
    #         ):
    #             op_dict = {
    #                 'label': op.label,
    #                 'value': op.label.replace(" ", "").lower(),
    #             }
    #             options.append(op_dict)

    #     # For multi-select type questions, the isRequired flag goes to the
    #     # first option dict instead of question dict
    #     if 'isRequired' in section_question.get_tag_list(

    #     ) and question.answer_type in special_types:
    #         if options:
    #             options[0]['isRequired'] = 'true'

    #     return options

    def get_options2(self, section_question, question):
        options = []
        special_types = ['radiobuttons', 'multi-select', ]
        if len(section_question.get_options()) > 0:

            for op in section_question.get_options():
                op_dict = {
                    'label': op['label'],
                    'value': op['label'].replace(" ", "").lower(),
                }

                # establish special fields for options.
                for c in op['conditions']:
                    if c['value'] != '' and c['value']:
                        key = c['label']
                        op_dict[key] = c['value']

                options.append(op_dict)

        # For multi-select type questions, the isRequired flag goes to the
        # first option dict instead of question dict
        if 'isRequired' in section_question.get_tag_list(

        ) and question.answer_type in special_types:
            if options:
                options[0]['isRequired'] = 'true'

        return options

    # def get_special_conditions(self, section_question, section, option):
    #     conditions = []

    #     options = section_question.question.option.filter(
    #         label=option['label']
    #     ).order_by(
    #         '-wildlifecompliance_masterlistquestion_option.id')

    #     section_question = SectionQuestion.objects.filter(
    #         section=section,
    #         parent_question=section_question.question,
    #         parent_answer__in=options
    #     ).first()

    #     if section_question and section_question.apply_special_conditions:

    #         for c in section_question.special_conditions.all():

    #             op_dict = {
    #                 'label': c.label,
    #                 'value': c.value
    #             }
    #             conditions.append(op_dict)

    #     return conditions

    # def get_checkbox_option_children(
    #     self, section_question, question, section, parent_name=''
    # ):
    #     conditions = {}
    #     options = question.option.all().order_by(
    #         '-wildlifecompliance_masterlistquestion_option.id')
    #     options_list = []
    #     special_types = ['checkbox', ]
    #     group_types = ['checkbox', 'radiobuttons', 'multi-select']
    #     option_count = 0
    #     for op in options:
    #         op_name = '{}-{}'.format(parent_name, option_count)
    #         op_dict = {
    #                 'name': op_name,
    #                 'label': op.label,
    #                 'type': 'checkbox',
    #                 'group': parent_name
    #         }
    #         condition_questions = SectionQuestion.objects.filter(
    #             section=section,
    #             parent_question=question,
    #             parent_answer=op
    #         ).order_by('order')
    #         if condition_questions:
    #             option_section = []
    #             option_children = []
    #             condition_question_count = 1
    #             for q in condition_questions:

    #                 question_name = '{}-On-{}'.format(
    #                     op_name, condition_question_count)
    #                 child = {
    #                     'name': question_name,
    #                     'type': q.question.answer_type,
    #                     'label': q.question.question,
    #                 }
    #                 if q.question.answer_type in special_types:
    #                     qo_children = self.get_checkbox_option_children(
    #                         q, q.question, section, question_name
    #                     )
    #                     child['children'] = qo_children
    #                     child['type'] = 'group'
    #                 else:
    #                     if q.question.option.count() > 0:
    #                         q_options = self.get_options2(q, q.question)
    #                         child['options'] = q_options

    #                     if q.question.children_questions.exists():
    #                         q_conditions = self.get_condition_children2(
    #                             q.question, section, question_name
    #                         )
    #                         child['conditions'] = q_conditions

    #                 if q.tag:
    #                     for t in q.tag:
    #                         if t == 'isRequired':
    #                             if q.question.answer_type not in group_types:
    #                                 child[t] = 'true'
    #                         else:
    #                             child[t] = 'true'

    #                 option_children.append(child)
    #                 condition_question_count += 1
    #             section_group_name = op_name+'-OnGroup'
    #             option_section_dict = {
    #                 'name': section_group_name,
    #                 'type': 'group',
    #                 'label': '',
    #                 'children': option_children
    #             }
    #             option_section.append(option_section_dict)
    #             conditions['on'] = option_section
    #             op_dict['conditions'] = conditions
    #         options_list.append(op_dict)
    #         option_count += 1

    #     if 'isRequired' in section_question.get_tag_list():
    #         if options_list:
    #             options_list[0]['isRequired'] = 'true'

    #     return options_list

    def get_checkbox_option_children2(
        self, section_question, question, section, parent_name=''
    ):
        conditions = {}
        # options = question.option.all().order_by(
        #     '-wildlifecompliance_masterlistquestion_option.id')
        options = []
        options_list = []
        special_types = ['checkbox', ]
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        expander_types = ['expander_table']
        declaration = ['declaration']
        option_count = 0

        if len(question.get_options()) > 0:
            for op in question.get_options():
                op_dict = {
                    'label': op.label,
                    'value': op.label.replace(" ", "").lower(),
                    'id': op.value,
                }
                options.append(op_dict)

        for op in options:
            conditions = {}
            op_name = '{}-{}'.format(parent_name, option_count)
            op_dict = {
                    'name': op_name,
                    'label': op['label'],
                    'type': 'checkbox',
                    'group': parent_name
            }
            condition_questions = SectionQuestion.objects.filter(
                section=section,
                parent_question=question,
                parent_answer=op['id']
            ).order_by('order')
            if condition_questions:
                option_section = []
                option_children = []
                option_groupings = []
                option_repeatable = False
                condition_question_count = 1
                for q in condition_questions:

                    question_name = '{}-On-{}'.format(
                        op_name, condition_question_count)
                    child = {
                        'name': question_name,
                        'type': q.question.answer_type,
                        'label': q.question.question,
                    }

                    # check for Section Groupings.
                    if q.section_group \
                            and q.section_group not in option_groupings:
                        #original code
                        # q_group_children = self.get_group_children2(
                        #     q, section, question_name)

                        # if q.section_group.repeatable:
                        #     option_repeatable = ['isRepeatable']

                        # option_children = q_group_children
                        # option_type = q.section_group.TYPE_GROUP2
                        # condition_question_count = len(q_group_children)
                        # option_label = q.section_group.group_label

                        # option_groupings.append(q.section_group)
                        #original code end
                        #PA code begin
                        if section_question.section_group:
                            if section_question.section_group != q.section_group:
                                q_group_children = self.get_group_children2(
                                    q, section, question_name)

                                if q.section_group.repeatable:
                                    option_repeatable = ['isRepeatable']

                                option_children = q_group_children
                                option_type = q.section_group.TYPE_GROUP2
                                condition_question_count = len(q_group_children)
                                option_label = q.section_group.group_label

                                option_groupings.append(q.section_group)
                        else:
                            no_parent_section_group=True
                            q_group_children = self.get_group_children2(
                                    q, section, question_name,no_parent_section_group)

                            if q.section_group.repeatable:
                                option_repeatable = ['isRepeatable']

                            option_children = q_group_children
                            option_type = q.section_group.TYPE_GROUP2
                            condition_question_count = len(q_group_children)
                            option_label = q.section_group.group_label

                            option_groupings.append(q.section_group)


                    elif q.question.answer_type in declaration:

                        child['type'] = 'checkbox'

                    elif q.question.answer_type in special_types:
                        qo_children = self.get_checkbox_option_children2(
                            q, q.question, section, question_name
                        )
                        child['children'] = qo_children
                        child['type'] = 'group'

                    elif q.question.answer_type in expander_types:

                        child['label'] = ''

                        q_header_children = self.get_header_children2(
                            q, q.question, section, question_name
                        )
                        child['header'] = q_header_children

                        q_expander_children = self.get_expander_children2(
                            q, q.question, section, question_name
                        )

                        if q_expander_children:
                            child['expander'] = q_expander_children

                    else:
                        if len(q.question.get_options()) > 0:
                            q_options = self.get_options2(q, q.question)
                            child['options'] = q_options

                        if q.question.children_questions.exists():
                            q_conditions = self.get_condition_children2(
                                q, q.question, section, question_name
                            )
                            child['conditions'] = q_conditions

                    if q.tag:
                        for t in q.tag:
                            if t == 'isRequired':
                                if q.question.answer_type not in group_types:
                                    child[t] = 'true'
                            else:
                                child[t] = 'true'

                    if not option_groupings:
                        option_children.append(child)
                        condition_question_count += 1
                        option_type = 'group'
                        option_label = ''

                section_group_name = op_name+'-OnGroup'
                option_section_dict = {
                    'name': section_group_name,
                    'type': option_type,
                    'label': option_label,
                    'children': option_children
                }
                if option_repeatable:
                    option_section_dict['isRepeatable'] = True
                option_section.append(option_section_dict)
                conditions['on'] = option_section
                op_dict['conditions'] = conditions
            options_list.append(op_dict)
            option_count += 1

        if 'isRequired' in section_question.get_tag_list():
            if options_list:
                options_list[0]['isRequired'] = 'true'

        return options_list

    # def get_condition_children(self, question, section, parent_name=''):
    #     conditions = {}
    #     options = question.option.all().order_by(
    #         '-wildlifecompliance_masterlistquestion_option.id'
    #     )
    #     special_types = ['checkbox', ]
    #     group_types = ['checkbox', 'radiobuttons', 'multi-select']
    #     option_count = 0

    #     for op in options:
    #         condition_questions = SectionQuestion.objects.filter(
    #             section=section, parent_question=question, parent_answer=op
    #         ).order_by('order')
    #         if condition_questions:
    #             option_section = []
    #             option_children = []
    #             condition_question_count = 1

    #             for q in condition_questions:
    #                 question_name = '{}-{}{}'.format(
    #                     parent_name, op.label.replace(" ", ""),
    #                     condition_question_count
    #                 )

    #                 child = {
    #                     'name': question_name,
    #                     'type': q.question.answer_type,
    #                     'label': q.question.question,
    #                 }
    #                 if q.question.answer_type in special_types:
    #                     q_option_children = self.get_checkbox_option_children(
    #                         q, q.question, section, question_name
    #                     )
    #                     child['children'] = q_option_children
    #                     child['type'] = 'group'

    #                 else:
    #                     if q.question.option.count() > 0:
    #                         q_options = self.get_options2(q, q.question)
    #                         child['options'] = q_options

    #                     if q.question.children_questions.exists():

    #                         q_conditions = self.get_condition_children2(
    #                             q.question, section, question_name
    #                         )
    #                         child['conditions'] = q_conditions

    #                 if q.tag:
    #                     for t in q.tag:
    #                         if t == 'isRequired':
    #                             if q.question.answer_type not in group_types:
    #                                 child[t] = 'true'
    #                         else:
    #                             child[t] = 'true'

    #                 # if q.question.help_text_url:
    #                 #     child['help_text_url']='{0}/anchor={1}'.format(
    #                 # help_site_url, question_name)

    #                 # create_richtext_help(q.question, question_name)
    #                 option_children.append(child)
    #                 condition_question_count += 1
    #             # section_group_name=parent_name+'-'+op.label+'Group'
    #             # section_group_name = parent_name + '-' + op.label.replace(
    #             #     " ", ""
    #             # ) + 'Group'
    #             # option_section_dict = {
    #             #     'name': section_group_name,
    #             #     'type': 'group',
    #             #     'label': '',
    #             #     'children': option_children
    #             # }
    #             # option_section.append(option_section_dict)
    #             option_section.append(option_children[0])
    #             conditions[op.label.replace(" ", "").lower()] = option_section
    #             option_count += 1
    #     return conditions

    # def get_condition_children2_original(self, question, section, parent_name=''):
    #     conditions = {}
    #     # options = question.option.all().order_by(
    #     #     '-wildlifecompliance_masterlistquestion_option.id'
    #     # )
    #     options = []
    #     special_types = ['checkbox', ]
    #     group_types = ['checkbox', 'radiobuttons', 'multi-select']
    #     declaration = ['declaration']
    #     option_count = 0

    #     if len(question.get_options()) > 0:
    #         for op in question.get_options():
    #             op_dict = {
    #                 'label': op.label,
    #                 'value': op.label.replace(" ", "").lower(),
    #                 'id': op.value,
    #             }
    #             options.append(op_dict)

    #     for op in options:
    #         condition_questions = SectionQuestion.objects.filter(
    #             section=section,
    #             parent_question=question,
    #             parent_answer=op['id']
    #         ).order_by('order')

    #         if condition_questions:
    #             option_section = []
    #             option_children = []
    #             condition_question_count = 1

    #             for q in condition_questions:
    #                 question_name = '{}-{}{}'.format(
    #                     parent_name, op['label'].replace(" ", ""),
    #                     condition_question_count
    #                 )

    #                 child = {
    #                     'name': question_name,
    #                     'type': q.question.answer_type,
    #                     'label': q.question.question,
    #                 }
    #                 if q.question.answer_type in special_types:
    #                     q_option_children = self.get_checkbox_option_children2(
    #                         q, q.question, section, question_name
    #                     )
    #                     child['children'] = q_option_children
    #                     child['type'] = 'group'

    #                 elif q.question.answer_type in declaration:

    #                     child['type'] = 'checkbox'

    #                 else:
    #                     if len(q.question.get_options()) > 0:
    #                         q_options = self.get_options2(q, q.question)
    #                         child['options'] = q_options

    #                     if q.question.children_questions.exists():

    #                         q_conditions = self.get_condition_children2(
    #                             q.question, section, question_name
    #                         )
    #                         child['conditions'] = q_conditions

    #                 if q.tag:
    #                     for t in q.tag:
    #                         if t == 'isRequired':
    #                             if q.question.answer_type not in group_types:
    #                                 child[t] = 'true'
    #                         else:
    #                             child[t] = 'true'

    #                 option_children.append(child)
    #                 condition_question_count += 1

    #             option_section.append(option_children[0])
    #             conditions[
    #                 op['label'].replace(" ", "").lower()
    #             ] = option_section
    #             option_count += 1
    #     return conditions

    def get_condition_children2(self, section_question, question, section, parent_name=''):
        conditions = {}
        # options = question.option.all().order_by(
        #     '-wildlifecompliance_masterlistquestion_option.id'
        # )
        options = []
        special_types = ['checkbox', ]
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        declaration = ['declaration']
        option_count = 0

        if len(question.get_options()) > 0:
            for op in question.get_options():
                op_dict = {
                    'label': op.label,
                    'value': op.label.replace(" ", "").lower(),
                    'id': op.value,
                }
                options.append(op_dict)

        for op in options:
            condition_questions = SectionQuestion.objects.filter(
                section=section,
                parent_question=question,
                parent_answer=op['id']
            ).order_by('order')

            if condition_questions:
                option_section = []
                option_children = []
                option_groupings=[]
                condition_question_count = 1

                for q in condition_questions:
                    question_name = '{}-{}{}'.format(
                        parent_name, op['label'].replace(" ", ""),
                        condition_question_count
                    )

                    child = {
                        'name': question_name,
                        'type': q.question.answer_type,
                        'label': q.question.question,
                    }

                    if q.section_group \
                            and q.section_group not in option_groupings:
                        #original code
                        # q_group_children = self.get_group_children2(
                        #     q, section, question_name)

                        # if q.section_group.repeatable:
                        #     option_repeatable = ['isRepeatable']

                        # option_children = q_group_children
                        # option_type = q.section_group.TYPE_GROUP2
                        # condition_question_count = len(q_group_children)
                        # option_label = q.section_group.group_label

                        # option_groupings.append(q.section_group)
                        #original code end
                        #PA code begin
                        #If the parent question has same group as the question then group children are already generated.
                        if section_question.section_group:
                            if section_question.section_group != q.section_group:
                                q_group_children = self.get_group_children2(
                                    q, section, question_name)

                                if q.section_group.repeatable:
                                    option_repeatable = ['isRepeatable']

                                option_children = q_group_children
                                option_type = q.section_group.TYPE_GROUP2
                                condition_question_count = len(q_group_children)
                                option_label = q.section_group.group_label

                                option_groupings.append(q.section_group)
                        else:
                            no_parent_section_group=True
                            q_group_children = self.get_group_children2(
                                    q, section, question_name,no_parent_section_group)

                            if q.section_group.repeatable:
                                option_repeatable = ['isRepeatable']

                            option_children = q_group_children
                            option_type = q.section_group.TYPE_GROUP2
                            condition_question_count = len(q_group_children)
                            option_label = q.section_group.group_label

                            option_groupings.append(q.section_group)

                    elif q.question.answer_type in special_types:
                        q_option_children = self.get_checkbox_option_children2(
                            q, q.question, section, question_name
                        )
                        child['children'] = q_option_children
                        child['type'] = 'group'

                    elif q.question.answer_type in declaration:

                        child['type'] = 'checkbox'

                    else:
                        if len(q.question.get_options()) > 0:
                            q_options = self.get_options2(q, q.question)
                            child['options'] = q_options

                        if q.question.children_questions.exists():

                            q_conditions = self.get_condition_children2(
                                q, q.question, section, question_name
                            )
                            child['conditions'] = q_conditions

                    if q.tag:
                        for t in q.tag:
                            if t == 'isRequired':
                                if q.question.answer_type not in group_types:
                                    child[t] = 'true'
                            else:
                                child[t] = 'true'

                    if not option_groupings:
                        option_children.append(child)
                        condition_question_count += 1
                        option_type='group'
                        option_label=''

                section_group_name=parent_name+'-'+op['label'].replace(" ","")+'Group'
                option_section_dict={
                    'name':section_group_name,
                    'type': option_type,
                    'label':option_label,
                    'children': option_children
                }
                option_section.append(option_section_dict)
                conditions[
                    op['label'].replace(" ", "").lower()
                ] = option_section
                option_count += 1
        return conditions

    # def get_group_children(self, question, section, parent_name=''):
    #     grouped_children = []
    #     # options = question.option.all().order_by(
    #     #     '-wildlifecompliance_masterlistquestion_option.id'
    #     # )
    #     special_types = ['checkbox', ]
    #     group_types = ['checkbox', 'radiobuttons', 'multi-select']
    #     expander_types = ['expander_table']
    #     section_count = 0

    #     group_questions = SectionQuestion.objects.filter(
    #         section=question.section, parent_question=question.question
    #     ).order_by('order')

    #     # option_section = []
    #     # option_children = []
    #     group_question_count = 1

    #     for q in group_questions:

    #         question_name = '{}-{}{}'.format(
    #             parent_name,
    #             q.question.answer_type,
    #             group_question_count
    #         )

    #         child = {
    #             'name': question_name,
    #             'type': q.question.answer_type,
    #             'label': q.question.question,
    #         }
    #         if q.question.answer_type in special_types:

    #             child['type'] = q.question.answer_type

    #             options = q.question.option.all().order_by(
    #                 '-wildlifecompliance_masterlistquestion_option.id')

    #             for o in options:
    #                 q_checkbox_children = SectionQuestion.objects.filter(
    #                     section=question.section,
    #                     parent_question=q.question,
    #                     parent_answer=o,
    #                 )
    #                 for q in q_checkbox_children:
    #                     for c in q.special_conditions.all():
    #                         child[c.label] = c.value

    #         elif q.question.answer_type in expander_types:

    #             child['label'] = ''

    #             q_header_children = self.get_header_children2(
    #                 q, q.question, section, question_name
    #             )
    #             child['header'] = q_header_children

    #             q_expander_children = self.get_expander_children2(
    #                 q, q.question, section, question_name
    #             )

    #             if q_expander_children:
    #                 child['expander'] = q_expander_children

    #         else:
    #             if q.question.option.count() > 0:
    #                 q_options = self.get_options2(q, q.question)
    #                 child['options'] = q_options

    #             if q.question.children_questions.exists():

    #                 q_conditions = self.get_condition_children2(
    #                     q.question, section, question_name
    #                 )
    #                 child['conditions'] = q_conditions

    #         if q.tag:
    #             for t in q.tag:
    #                 if t == 'isRequired':
    #                     if q.question.answer_type not in group_types:
    #                         child[t] = 'true'
    #                 else:
    #                     child[t] = 'true'

    #         group_question_count += 1
    #         grouped_children.append(child)

    #     section_count += 1
    #     return grouped_children



    def get_group_children2(self, question, section, parent_name='', no_parent_section_group=False):
        grouped_children = []
        # options = question.option.all().order_by(
        #     '-wildlifecompliance_masterlistquestion_option.id'
        # )
        special_types = ['checkbox', ]
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        expander_types = ['expander_table']
        declaration = ['declaration']
        select_types = ['select', 'multi-select']
        section_count = 0

        group_questions = SectionQuestion.objects.filter(
            section=question.section, section_group=question.section_group
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
                'label': q.question.question,
            }

            if q.parent_answer and not no_parent_section_group:
                # Question already added as part of option groupings.
                continue

            if q.question.answer_type in special_types:

                child['type'] = q.question.answer_type

                # options = q.question.option.all().order_by(
                #     '-wildlifecompliance_masterlistquestion_option.id')
                options = []
                # if len(question.get_options()) > 0:
                #     for op in question.get_options():
                #         op_dict = {
                #             'label': op.label,
                #             'value': op.label.replace(" ", "").lower(),
                #             'id': op.value,
                #         }
                #         options.append(op_dict)

                #PA code begin
                qo_children = self.get_checkbox_option_children2(
                            q, q.question, section, question_name
                        )
                child['children'] = qo_children
                child['type'] = 'group'
                #PA code end

                for o in options:
                    q_checkbox_children = SectionQuestion.objects.filter(
                        section=question.section,
                        parent_question=q.question,
                        parent_answer=o,
                    )
                    for q in q_checkbox_children:
                        for c in q.special_conditions.all():
                            child[c.label] = c.value

            elif q.question.answer_type in declaration:

                child['type'] = 'checkbox'

            elif q.question.answer_type in expander_types:

                child['label'] = ''

                q_header_children = self.get_header_children2(
                    q, q.question, section, question_name
                )
                child['header'] = q_header_children

                q_expander_children = self.get_expander_children2(
                    q, q.question, section, question_name
                )

                if q_expander_children:
                    child['expander'] = q_expander_children

            elif q.question.answer_type in select_types:
                '''
                NOTE: Select type option are defaulted from Masterlist
                not from the SectionQuestion. Conditions are NOT added.
                '''
                if len(q.question.get_options()) > 0:
                    opts = [
                        {
                            'label': o.label,
                            'value': o.label.replace(" ", "").lower(),
                            'conditions': ''
                        } for o in q.question.get_options()
                    ]
                    q.set_property_cache_options(opts)
                    sq_options = self.get_options2(
                        q, q.question
                    )

                    child['options'] = sq_options

            else:
                if len(q.question.get_options()) > 0:
                    q_options = self.get_options2(q, q.question)
                    child['options'] = q_options

                if q.question.children_questions.exists():

                    q_conditions = self.get_condition_children2(
                       q, q.question, section, question_name
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

    # def get_header_children(self, sq, question, section, parent_name=''):
    #     header_children = []
    #     header_types = ['header']

    #     group_questions = SectionQuestion.objects.filter(
    #         section=sq.section, parent_question=sq.question
    #     ).order_by('order')

    #     header_question_count = 0

    #     for q in group_questions:

    #         if q.question.answer_type not in header_types:
    #             continue

    #         question_name = '{}-Header{}'.format(
    #             parent_name,
    #             # question.question.question.replace(" ", ""),
    #             header_question_count
    #         )

    #         column_type = SectionQuestion.objects.filter(
    #             section=sq.section, parent_question=q.question
    #         ).first()

    #         header = {
    #             'name': question_name,
    #             'type': column_type.question.answer_type,
    #             'label': q.question.question,
    #         }

    #         header_question_count += 1
    #         header_children.append(header)

    #     return header_children

    def get_header_children2(self, sq, question, section, parent_name=''):
        header_children = []

        headers = question.get_headers()

        header_question_count = 0

        for h in headers:

            if h['value'] == '':
                continue

            question_name = '{}-Header{}'.format(
                parent_name,
                header_question_count
            )

            header = {
                'name': question_name,
                'type': h['value'],
                'label': h['label'],
            }

            header_question_count += 1
            header_children.append(header)

        return header_children

    def get_expander_children2(self, sq, question, section, parent_name=''):
        expander_children = []

        expanders = question.get_expanders()

        expander_question_count = 0

        for e in expanders:

            if e['value'] == '':
                continue

            expander_name = '{}-Expander{}'.format(
                parent_name,
                expander_question_count
            )

            expander = {
                'name': expander_name,
                'type': e['value'],
                'label': e['label'],
            }

            expander_question_count += 1
            expander_children.append(expander)

        return expander_children

    # def get_expander_children(self, sq, question, section, parent_name=''):
    #     expander_children = []
    #     special_types = ['checkbox', ]
    #     group_types = ['checkbox', 'radiobuttons', 'multi-select']
    #     expander_types2 = ['expander_table']
    #     # type_count = 0

    #     group_questions = SectionQuestion.objects.filter(
    #         section=sq.section, parent_question=sq.question
    #     ).order_by('order')

    #     expander_question_count = 0

    #     for q in group_questions:

    #         if q.question.answer_type != 'expander':
    #             continue

    #         expander_name = '{}-Expander{}'.format(
    #             parent_name,
    #             # question.question.question.replace(" ", ""),
    #             expander_question_count
    #         )

    #         expander_type = SectionQuestion.objects.filter(
    #             section=sq.section, parent_question=q.question
    #         ).first()

    #         expander = {
    #             'name': expander_name,
    #             'type': expander_type.question.answer_type,
    #             'label': expander_type.question.question,
    #         }

    #         # NOTE: a recursive call here for groupings within the expander.
    #         if expander_type.question.answer_type in special_types:

    #             expander['type'] = q.question.answer_type

    #             options = q.question.option.all().order_by(
    #                 '-wildlifecompliance_masterlistquestion_option.id')

    #             for o in options:
    #                 q_checkbox_children = SectionQuestion.objects.filter(
    #                     section=question.section,
    #                     parent_question=q.question,
    #                     parent_answer=o,
    #                 )
    #                 for q in q_checkbox_children:
    #                     for c in q.special_conditions.all():
    #                         expander[c.label] = c.value

    #         elif expander_type.question.answer_type in expander_types2:

    #             expander['label'] = ''

    #             q_header_children = self.get_header_children2(
    #                 expander_type, expander_type.question,
    #                 section, expander_name
    #             )
    #             expander['header'] = q_header_children

    #             q_expander_children = self.get_expander_children2(
    #                 expander_type, expander_type.question,
    #                 section, expander_name
    #             )

    #             if q_expander_children:
    #                 expander['expander'] = q_expander_children

    #         else:
    #             if expander_type.question.option.count() > 0:
    #                 q_options = self.get_options2(
    #                     expander_type, expander_type.question
    #                 )
    #                 expander['options'] = q_options

    #             if expander_type.question.children_questions.exists():

    #                 q_conditions = self.get_condition_children2(
    #                     expander_type.question, section, expander_name
    #                 )
    #                 expander['conditions'] = q_conditions

    #         if expander_type.tag:
    #             e_type = expander_type
    #             for t in e_type.tag:
    #                 if t == 'isRequired':
    #                     if e_type.question.answer_type not in group_types:
    #                         expander[t] = 'true'
    #                 else:
    #                     expander[t] = 'true'

    #         expander_question_count += 1
    #         expander_children.append(expander)

    #     return expander_children

    def get_licence_schema(self):
        '''
        '''
        section_count = 0
        schema = []
        special_types = ['checkbox', ]
        select_types = ['select', 'multi-select']
        expander_types = ['expander_table']
        declaration = ['declaration']

        # 'isRequired' tag for following types is added to first option dict
        # instead of question.
        group_types = ['checkbox', 'radiobuttons', 'multi-select']
        groupings = []

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
                        'group',
                        sq_count
                    )
                    sc = {
                        'name': sq_name,
                        'type': sq.question.answer_type,
                        'label': sq.question.question,
                    }

                    if sq.section_group and sq.section_group in groupings:
                        # Question already added as part of groupings.
                        continue

                    if sq.section_group and sq.section_group not in groupings:

                        sq_group_children = self.get_group_children2(
                            sq, section, sq_name)
                        group_label = sq.section_group.group_label

                        sc['children'] = sq_group_children
                        sc['type'] = sq.section_group.TYPE_GROUP2
                        sc['label'] = group_label

                        if sq.section_group.repeatable:
                            sq.tag = ['isRepeatable']

                        groupings.append(sq.section_group)

                    elif sq.question.answer_type in expander_types:

                        sc['label'] = ''

                        q_header_children = self.get_header_children2(
                            sq, sq.question, section, sq_name
                        )
                        sc['header'] = q_header_children

                        q_expander_children = self.get_expander_children2(
                            sq, sq.question, section, sq_name
                        )

                        if q_expander_children:
                            sc['expander'] = q_expander_children

                    elif sq.question.answer_type in declaration:

                        sc['type'] = 'checkbox'

                    elif sq.question.answer_type in special_types:

                        sq_opt_children = self.get_checkbox_option_children2(
                            sq, sq.question, section, sq_name)

                        sc['children'] = sq_opt_children
                        sc['type'] = 'group'

                    elif sq.question.answer_type in select_types:
                        '''
                        NOTE: Select type option are defaulted from Masterlist
                        not from the SectionQuestion. Conditions are NOT added.
                        '''
                        if len(sq.question.get_options()) > 0:
                            opts = [
                                {
                                    'label': o.label,
                                    'value': o.label.replace(" ", "").lower(),
                                    'conditions': ''
                                } for o in sq.question.get_options()
                            ]
                            sq.set_property_cache_options(opts)
                            sq_options = self.get_options2(
                                sq, sq.question
                            )

                            sc['options'] = sq_options
                            sc['type'] = sq.question.answer_type

                    else:

                        if len(sq.question.get_options()) > 0:
                            sq_options = self.get_options2(sq, sq.question)

                            # establish special fields for options.
                            # if sq.question.answer_type in [
                            #     'checkbox', 'radiobuttons'
                            # ]:
                            #     for o in sq_options:

                            #         sq_fields = self.get_special_conditions(
                            #             sq, section, o
                            #         )
                            #         for f in sq_fields:
                            #             key = f['label']
                            #             o[key] = f['value']

                            sc['options'] = sq_options

                    # if sq.question.children_questions.exists() \
                    #         and sc['type'] != 'group':
                    if sq.question.children_questions.exists() \
                            and (sc['type'] != 'group' and sc['type'] != SectionGroup.TYPE_GROUP2):
                        sq_children = self.get_condition_children2(
                            sq,sq.question, section, sq_name
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
