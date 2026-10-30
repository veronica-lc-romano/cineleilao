
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Leilao
from .serializers import LeilaoSerializer
from .services import encerrar_leilao


class EhLeiloeiro(permissions.BasePermission):
    message = "Somente usuários com papel leiloeiro podem criar leilões."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.papel == "leiloeiro"
        )


class ListaCriaLeiloesView(generics.ListCreateAPIView):
    serializer_class = LeilaoSerializer

    def get_queryset(self):
        return Leilao.objects.select_related("criado_por").all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), EhLeiloeiro()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


class DetalheLeilaoView(generics.RetrieveAPIView):
    queryset = Leilao.objects.select_related("criado_por").all()
    serializer_class = LeilaoSerializer
    permission_classes = [permissions.AllowAny]


class EncerrarLeilaoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        resultado = encerrar_leilao(
            leilao_id=pk,
            usuario=request.user,
        )
        return Response(resultado, status=status.HTTP_200_OK)
