from rest_framework import viewsets
from rest_framework import generics
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class AbstractViewSet(viewsets.ModelViewSet):
    ordering_fields = ["updated", "created"]
    ordering = ["-updated"]


@method_decorator(csrf_exempt, name='dispatch')
class AbstractGenericViewSet(generics.GenericAPIView):
    pass
