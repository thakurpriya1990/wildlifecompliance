
class UinField:
    def __init__(self, required, field_name, length):
        self.__required = required
        self.__field_name = field_name
        self.__length = length
        self.__text = ''

    def __str__(self):
        return self.export()

    def export(self):
        if len(self.__text) >= self.__length:
            return self.__text[0:self.__length]
        else:
            return self.__text.ljust(self.__length, ' ')

    def set(self, text):
        self.__text = text

    def get(self):
        return self.__text


class UnpaidInfringementFile:
    # Header Record
    agency_code = UinField(True, 'Agency Code', 6)
    uin_file_reference = UinField(True, 'UIN File Reference', 8)
    date_created = UinField(True, 'Date Created', 8)
    responsible_officer = UinField(False, 'Responsible Officer', 50)

    # Infringement Record
    offenders_surname = UinField(False, 'Offender\'s Surname', 50)
    offenders_other_names = UinField(False, 'Offender\'s Other Surnames', 50)
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
    vehicle_registration_number = UinField(False, 'Drivers Licence Number', 25)
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

    # Trailer Record
    number_of_records = UinField(True, 'Number of Records', 5)
    total_penalty_amount = UinField(True, 'Total Penalty Amount', 10)
    first_additional_cost_code_trailer = UinField(False, 'First Additional Cost Code', 2)
    first_additional_cost_total = UinField(False, 'First Additional Cost Total', 10)
    second_additional_cost_code_trailer = UinField(False, 'Second Additional Cost Code', 2)
    second_additional_cost_total = UinField(False, 'Second Additional Cost Total', 10)

    def __init__(self):
        self.headers = [self.agency_code,
                        self.uin_file_reference,
                        self.date_created,
                        self.responsible_officer]
        self.body = [self.offenders_surname,
                     self.offenders_other_names,
                     self.offenders_date_of_birth,
                     self.offenders_sid,
                     self.offenders_organisation_name,
                     self.party_indicator,
                     self.offenders_gender,
                     self.offenders_address_line_1,
                     self.offenders_address_line_2,
                     self.offenders_address_line_3,
                     self.offenders_address_line_4,
                     self.offenders_suburb,
                     self.offenders_state,
                     self.offenders_postcode,
                     self.offenders_country,
                     self.date_address_known_to_be_current,
                     self.acn,
                     self.infringement_number,
                     self.offence_datetime,
                     self.offence_location,
                     self.drivers_licence_number,
                     self.vehicle_registration_number,
                     self.offence_code,
                     self.penalty_amount,
                     self.infringement_issue_date,
                     self.final_demand_letter_date,
                     self.zone_speed_limit,
                     self.speed_reading,
                     self.first_additional_cost_code,
                     self.first_additional_amount,
                     self.second_additional_cost_code,
                     self.second_additional_amount,]
        self.trailer = [self.number_of_records,
                        self.total_penalty_amount,
                        self.first_additional_cost_code_trailer,
                        self.first_additional_cost_total,
                        self.second_additional_cost_code_trailer,
                        self.second_additional_cost_total]

    def export(self):
        return self.export_fields(self.headers) + self.export_fields(self.body) + self.export_fields(self.trailer)

    def export_fields(self, fields):
        ret_text = ''
        for field in fields:
            ret_text += field.export()
        return ret_text
