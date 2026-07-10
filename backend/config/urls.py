from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from leads.views import LeadCreateView
from faqs.views import FAQListView


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('assistent/admin/', admin.site.urls),
    path('api/leads/', LeadCreateView.as_view(), name='lead-create'),
    path('api/faqs/', FAQListView.as_view(), name='faq-list'),
    path('api/health/', health_check, name='health-check'),
]
