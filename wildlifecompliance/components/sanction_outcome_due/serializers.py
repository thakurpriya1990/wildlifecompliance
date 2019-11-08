from rest_framework import serializers

from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate


class SanctionOutcomeDueDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SanctionOutcomeDueDate
        exclude = ('sanction_outcome',)


class SaveSanctionOutcomeDueDateSerializer(serializers.ModelSerializer):
    sanction_outcome_id = serializers.IntegerField(required=True, write_only=True, allow_null=False)
    extended_by_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    def validate(self, data):
        # validation here
        return data

    class Meta:
        model = SanctionOutcomeDueDate
        fields = (
            'due_date_1st',
            'due_date_2nd',
            'reason_for_extension',
            'extended_by_id',
            'sanction_outcome_id',
        )