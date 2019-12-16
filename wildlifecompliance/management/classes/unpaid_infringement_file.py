import datetime


class UinField(object):
    def __init__(self, required, field_name, length):
        self.__required = required
        self.__field_name = field_name
        self.__length = length
        self.__value = ''

    def __str__(self):
        return self.get_content()

    def get_content(self):
        # Convert to string typegt
        if not self.__value:
            value_str = ''
        elif type(self.__value) is datetime.date:
            value_str = self.__value.strftime('%d%m%Y')
        elif type(self.__value) is datetime.datetime:
            value_str = self.__value.strftime('%d%m%Y%H%M')
        else:
            value_str = str(self.__value)

        if len(value_str) >= self.__length:
            return value_str[0:self.__length]
        else:
            return value_str.ljust(self.__length, ' ')

    def set(self, text):
        self.__value = text


class UnpaidInfringementFileBase(object):

    def __init__(self, delimiter=u'\r\n'):
        self.fields_list = []
        self.delimiter = delimiter

    def get_content(self):
        ret_text = u''
        for field in self.fields_list:
            ret_text += field.get_content()
        return ret_text + self.delimiter


class UnpaidInfringementFileHeader(UnpaidInfringementFileBase):
    # 72 chars + CRLF
    agency_code = UinField(True, 'Agency Code', 6)
    uin_file_reference = UinField(True, 'UIN File Reference', 8)
    date_created = UinField(True, 'Date Created', 8)
    responsible_officer = UinField(False, 'Responsible Officer', 50)

    def __init__(self, delimiter=u'\r\n'):
        super(UnpaidInfringementFileHeader, self).__init__(delimiter)
        self.fields_list.append(self.agency_code)
        self.fields_list.append(self.uin_file_reference)
        self.fields_list.append(self.date_created)
        self.fields_list.append(self.responsible_officer)


class UnpaidInfringementFileBody(UnpaidInfringementFileBase):
    # 998 chars + CRLF
    offenders_surname = UinField(False, 'Offender\'s Surname', 50)
    offenders_other_names = UinField(False, 'Offender\'s Other Names', 50)
    offenders_date_of_birth = UinField(False, 'Offender\'s Date of Birth', 8)
    offenders_sid = UinField(False, 'Offender\'s SID', 8)
    offenders_organisation_name = UinField(False, 'Offender\'s Organisation Name', 150)
    party_indicator = UinField(True, 'Party Indicator', 1)
    offenders_gender = UinField(True, 'Offender\'s Gender', 1)
    offenders_address_line_1 = UinField(True, 'Offender\'s Address Line 1', 100)
    offenders_address_line_2 = UinField(False, 'Offender\'s Address Line 2', 100)
    offenders_address_line_3 = UinField(False, 'Offender\'s Address Line 3', 100)
    offenders_address_line_4 = UinField(False, 'Offender\'s Address Line 4', 35)
    offenders_suburb = UinField(True, 'Offender\'s Suburb', 50)
    offenders_state = UinField(True, 'Offender\'s State', 30)
    offenders_postcode = UinField(True, 'Offender\'s Postcode', 15)
    offenders_country = UinField(True, 'Offender\'s Country', 100)
    date_address_known_to_be_current = UinField(False, 'Date Address Known to be Current', 8)
    acn = UinField(False, 'Australia Company Number of Defendant(ACN)', 11)
    infringement_number = UinField(True, 'Infringement Number', 10)
    offence_datetime = UinField(True, 'Offence Date/Time', 12)
    offence_location = UinField(True, 'Offence Location', 60)
    drivers_licence_number = UinField(False, 'Drivers Licence Number', 25)
    vehicle_registration_number = UinField(False, 'Drivers Licence Number', 15)
    offence_code = UinField(True, 'Offence Code', 9)
    penalty_amount = UinField(True, 'Penalty Amount', 8)
    infringement_issue_date = UinField(True, 'Infringement Issue Date', 8)
    final_demand_letter_date = UinField(True, 'Final Demand Letter Date', 8)
    zone_speed_limit = UinField(False, 'Zone Speed Limit', 3)
    speed_reading = UinField(False, 'Speed Reading', 3)
    first_additional_cost_code = UinField(False, 'First Additional Cost Code', 2)
    first_additional_amount = UinField(False, 'First Additional Amount', 8)
    second_additional_cost_code = UinField(False, 'Second Additional Cost Code', 2)
    second_additional_amount = UinField(False, 'Second Additional Amount', 8)

    def __init__(self):
        super(UnpaidInfringementFileBody, self).__init__(delimiter=u'\r\n')
        self.fields_list.append(self.offenders_surname)
        self.fields_list.append(self.offenders_other_names)
        self.fields_list.append(self.offenders_date_of_birth)
        self.fields_list.append(self.offenders_sid)
        self.fields_list.append(self.offenders_organisation_name)
        self.fields_list.append(self.party_indicator)
        self.fields_list.append(self.offenders_gender)
        self.fields_list.append(self.offenders_address_line_1)
        self.fields_list.append(self.offenders_address_line_2)
        self.fields_list.append(self.offenders_address_line_3)
        self.fields_list.append(self.offenders_address_line_4)
        self.fields_list.append(self.offenders_suburb)
        self.fields_list.append(self.offenders_state)
        self.fields_list.append(self.offenders_postcode)
        self.fields_list.append(self.offenders_country)
        self.fields_list.append(self.date_address_known_to_be_current)
        self.fields_list.append(self.acn)
        self.fields_list.append(self.infringement_number)
        self.fields_list.append(self.offence_datetime)
        self.fields_list.append(self.offence_location)
        self.fields_list.append(self.drivers_licence_number)
        self.fields_list.append(self.vehicle_registration_number)
        self.fields_list.append(self.offence_code)
        self.fields_list.append(self.penalty_amount)
        self.fields_list.append(self.infringement_issue_date)
        self.fields_list.append(self.final_demand_letter_date)
        self.fields_list.append(self.zone_speed_limit)
        self.fields_list.append(self.speed_reading)
        self.fields_list.append(self.first_additional_cost_code)
        self.fields_list.append(self.first_additional_amount)
        self.fields_list.append(self.second_additional_cost_code)
        self.fields_list.append(self.second_additional_amount)


class UnpaidInfringementFileTrailer(UnpaidInfringementFileBase):
    # 39 chars + CRLF
    number_of_records = UinField(True, 'Number of Records', 5)
    total_penalty_amount = UinField(True, 'Total Penalty Amount', 10)
    first_additional_cost_code = UinField(False, 'First Additional Cost Code', 2)
    first_additional_cost_total = UinField(False, 'First Additional Cost Total', 10)
    second_additional_cost_code = UinField(False, 'Second Additional Cost Code', 2)
    second_additional_cost_total = UinField(False, 'Second Additional Cost Total', 10)

    def __init__(self):
        super(UnpaidInfringementFileTrailer, self).__init__(delimiter=u'\r\n')
        self.fields_list.append(self.number_of_records)
        self.fields_list.append(self.total_penalty_amount)
        self.fields_list.append(self.first_additional_cost_code)
        self.fields_list.append(self.first_additional_cost_total)
        self.fields_list.append(self.second_additional_cost_code)
        self.fields_list.append(self.second_additional_cost_total)
