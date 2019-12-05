from rest_framework import serializers

from wildlifecompliance.components.call_email.serializers import EmailUserSerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate


class SanctionOutcomeDueDateSerializer(serializers.ModelSerializer):
    extended_by = EmailUserSerializer(read_only=True)
    due_date_applied = serializers.ReadOnlyField()

    class Meta:
        model = SanctionOutcomeDueDate
        exclude = ('sanction_outcome',)


class SaveSanctionOutcomeDueDateSerializer(serializers.ModelSerializer):
    sanction_outcome_id = serializers.IntegerField(required=True, write_only=True, allow_null=False)
    extended_by_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not data['reason_for_extension']:
            field_errors['Reason'] = ['To extend a due date, you must enter a reason.',]

        if field_errors:
            raise serializers.ValidationError(field_errors)

        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return data

    class Meta:
        model = SanctionOutcomeDueDate
        fields = (
            'due_date_1st',
            'due_date_2nd',
            'reason_for_extension',
            'extended_by_id',
            'sanction_outcome_id',
            'due_date_term_currently_applied',
        )