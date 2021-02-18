from rest_framework import serializers

from wildlifecompliance.components.section_regulation.models import SectionRegulation


class SectionRegulationSerializer(serializers.ModelSerializer):
    act = serializers.CharField(source='act.name')

    class Meta:
        model = SectionRegulation
        #fields = '__all__'
        fields = (
            'id',
            'act',
            'name',
            'offence_text',
            'is_parking_offence',
        )
        read_only_fields = ('id',)
