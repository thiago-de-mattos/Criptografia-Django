from rest_framework import serializers
from .models import Prontuario
from .masking import mask_cpf, mask_nome


class ProntuarioSerializer(serializers.ModelSerializer):
    """
    Serializer 'normal' -- retorna os dados JA DESCRIPTOGRAFADOS
    (o Django faz isso sozinho ao ler do banco). Uso: endpoints
    internos, onde quem esta vendo tem permissao pro dado completo.
    """
    class Meta:
        model = Prontuario
        fields = [
            "id", "paciente_nome", "cpf",
            "queixa_principal", "evolucao_queixa", "historico_tratamento",
            "tags_busca", "criado_em",
        ]


class ProntuarioMascaradoSerializer(serializers.ModelSerializer):
    """
    Serializer para telas/relatorios de baixo privilegio: mascara
    CPF e nome antes de devolver na resposta. O dado real continua
    intacto no banco -- isso e so uma transformacao na saida.
    """
    cpf = serializers.SerializerMethodField()
    paciente_nome = serializers.SerializerMethodField()

    class Meta:
        model = Prontuario
        fields = ["id", "paciente_nome", "cpf", "tags_busca", "criado_em"]

    def get_cpf(self, obj):
        return mask_cpf(obj.cpf)

    def get_paciente_nome(self, obj):
        return mask_nome(obj.paciente_nome)