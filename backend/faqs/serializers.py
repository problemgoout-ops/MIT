from rest_framework import serializers
from .models import FAQItem


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['question', 'answer']
