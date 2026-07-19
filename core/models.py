from django.db import models
from .fields import EncryptedCharField, EncryptedTextField

class Prontuario(models.Model):
    paciente_nome = EncryptedCharField(max_length=100)
    cpf = EncryptedCharField(max_length=11)
    
    queixa_principal = EncryptedTextField()
    evolucao_queixa = EncryptedTextField()
    historico_tratamento = EncryptedTextField()

    # Campo pensado pra busca (vai ficar de fora da criptografia depois)
    tags_busca = models.CharField(max_length=255, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prontuario de {self.paciente_nome}"
