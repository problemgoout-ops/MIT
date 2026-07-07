from rest_framework import generics
from .models import FAQItem
from .serializers import FAQSerializer


class FAQListView(generics.ListAPIView):
    queryset = FAQItem.objects.filter(is_active=True).order_by('sort_order')
    serializer_class = FAQSerializer
