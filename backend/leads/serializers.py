from rest_framework import serializers
from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    honeypot = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    class Meta:
        model = Lead
        fields = [
            'last_name', 'first_name', 'telegram', 'email',
            'task_description',
            'utm_source', 'utm_medium', 'utm_campaign',
            'utm_content', 'utm_term', 'page_url',
            'honeypot',
        ]

    def validate_honeypot(self, value):
        if value:
            raise serializers.ValidationError('Spam detected')
        return value

    def validate_email(self, value):
        if not value or '@' not in value:
            raise serializers.ValidationError('Некорректный email')
        return value
