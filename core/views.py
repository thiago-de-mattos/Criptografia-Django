from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from clinica.models import Prontuario
from clinica.serializers import ProntuarioSerializer, ProntuarioMascaradoSerializer


class ProntuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de teste para o model Prontuario.

    Endpoints gerados automaticamente pelo router (ver urls.py):
      GET    /api/prontuarios/            -> lista (dados completos, descriptografados)
      POST   /api/prontuarios/            -> cria um novo registro (criptografa automaticamente)
      GET    /api/prontuarios/{id}/       -> detalhe de um registro
      PUT    /api/prontuarios/{id}/       -> atualiza um registro (substitui tudo)
      PATCH  /api/prontuarios/{id}/       -> atualiza parcialmente
      DELETE /api/prontuarios/{id}/       -> remove um registro

    Endpoints extras (custom actions):
      GET /api/prontuarios/buscar/?q=ansiedade   -> busca por tags_busca
      GET /api/prontuarios/mascarado/            -> lista com nome/CPF mascarados
    """
    queryset = Prontuario.objects.all().order_by("-criado_em")
    serializer_class = ProntuarioSerializer

    @action(detail=False, methods=["get"])
    def buscar(self, request):
        """
        Busca por conteudo usando o campo auxiliar NAO criptografado
        (tags_busca), ja que campos criptografados nao suportam
        icontains. Ex: /api/prontuarios/buscar/?q=ansiedade
        """
        termo = request.query_params.get("q", "")
        if not termo:
            return Response(
                {"erro": "Informe o parametro ?q= com o termo de busca."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        resultados = self.get_queryset().filter(tags_busca__icontains=termo)
        serializer = self.get_serializer(resultados, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def mascarado(self, request):
        """
        Lista com nome e CPF mascarados -- simula uma tela/relatorio
        de baixo privilegio, sem expor o dado sensivel completo.
        """
        resultados = self.get_queryset()
        serializer = ProntuarioMascaradoSerializer(resultados, many=True)
        return Response(serializer.data)