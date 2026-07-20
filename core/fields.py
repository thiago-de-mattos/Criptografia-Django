# importa o fernet que faz a criptografia e a descriptografia e
# invalid token que é uma exceção quando a chave de segurança esta errada ou foi alterada
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

#Função responsavel pela criptografia
def get_fernet() -> Fernet:
    #Le a chave de criptografia do settings.py,não esqueça de criar a chave de segurança 
    #e guarde em variavel de ambiente, na .env (ex: FIELD_ENCRYPTION_KEY no .env)
    key = settings.FIELD_ENCRYPTION_KEY
    
    #Transforma a chave em bytes.
    if isinstance(key, str):
        key = key.encode()
    # e retorna a chave criptografada    
    return Fernet(key)

# classe para compartilhar funcionalidades
class EncryptedFieldMixin:
    def get_internal_type(self):
        return "TextField"

    def get_prep_value(self, value):

        #só faz  a preparação do valor
        value = super().get_prep_value(value)

        # se estiver vazio não criptografa
        if value is None or value == "":
            return value
        
        #aqui pega e faz a criptografia
        token = get_fernet().encrypt(str(value).encode())
        return token.decode()

    #para ler um dado do banco
    def from_db_value(self, value, expression, connection):

        #mesma coias se estiver vazio não faz nada
        if value is None or value == "":
            return value
        
        #aqui decripta
        try:
            decrypted = get_fernet().decrypt(value.encode())
            return decrypted.decode()
        except InvalidToken:
            raise ValueError("Nao foi possivel descriptografar o campo.")

    def to_python(self, value):
        return value


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    pass


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    pass
