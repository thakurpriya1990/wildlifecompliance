from wildlifecompliance import settings
from wildlifecompliance.components.emails.emails import TemplateEmailBase

class CommandsVerifyNotificationEmail(TemplateEmailBase):
    '''
    Email template for Commands Verification executed jobs.
    '''
    subject = 'Wildlife Licensing System command: job completed'
    html_template = \
      'wildlifecompliance/emails/send_commands_verify_notification.html'
    txt_template = \
      'wildlifecompliance/emails/send_commands_verify_notification.txt'

    verified_total = 0                          # total records checked.
    recipients = [settings.NOTIFICATION_EMAIL]

    def set_subject(self, subject):
        '''
        Setter for email subject.
        '''
        self.subject = '{0}: {1}.'.format(
            'WLC Script Command',
            subject,
        )

    def set_html_template(self, template):
        '''
        Setter for html template.
        '''
        self.html_template = template

    def set_txt_template(self, template):
        '''
        Setter for txt template.
        '''
        self.txt_template = template

    def set_verified_total(self, total):
        '''
        Setter for total records verified.
        '''
        self.verified_total = total

    def out(self):
        '''
        Send out email.
        '''
        context = {'verified_total': self.verified_total}
        self.send(self.recipients, context=context)
