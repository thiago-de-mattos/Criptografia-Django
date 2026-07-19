# SEP — Criptografia de Dados de Pacientes

Esse módulo cuida de uma coisa simples de explicar mas chata de acertar: os dados
sensíveis de pacientes (nome, CPF, prontuário) precisam ficar protegidos no banco,
mas continuar utilizáveis pela aplicação no dia a dia. Se um dia o banco vazar ou
alguém tiver acesso indevido, esses campos devem estar ilegíveis. Foi isso que a
gente construiu aqui.

**Autor:** Thiago
**Status:** Em Desenvolvimento

Se você é do time e está vendo isso pela primeira vez, a ideia deste README é te
dar tudo que você precisa pra rodar o projeto, entender as decisões que foram
tomadas, e usar o que já foi construído sem precisar me perguntar nada — mas me
chama se travar em algo.

## O que esse módulo faz, em resumo

- Criptografa automaticamente nome, CPF e os textos de prontuário antes de salvar
  no banco, e descriptografa sozinho quando você lê via Django (você nem percebe
  que está acontecendo, é transparente).
- Tem um jeito de mascarar esses dados na hora de exibir (tipo mostrar só os
  últimos 4 dígitos do CPF), sem precisar descriptografar coisa nenhuma no
  processo.
- Tem uma API REST simples de teste, pra você poder mexer nisso tudo pelo
  Thunder Client/Postman sem precisar abrir o shell do Django toda hora.

## Por que não usamos uma lib pronta

A ideia inicial era usar `django-cryptography`, mas essa biblioteca não é mais
mantida ativamente e **quebra em Django 6** (ela depende de um módulo que foi
removido). Em vez de ficar refém disso, implementamos nosso próprio campo
criptografado usando `cryptography.fernet` direto — é a mesma lib de
criptografia por baixo, só que sem intermediário abandonado. Bônus: essa mesma
abordagem funcionaria igualzinho num serviço em FastAPI, se algum dia
precisarmos.

## Estrutura dos arquivos

```
core/
├── fields.py       # EncryptedCharField e EncryptedTextField (o coração da criptografia)
├── models.py       # Prontuario, usando os campos criptografados
├── masking.py      # mask_cpf, mask_nome, mask_telefone, mask_email
├── serializers.py  # serializers da API (um normal, um mascarado)
├── views.py        # o CRUD da API + endpoints de busca e mascarado
└── urls.py         # rotas da API
```

## Como rodar isso na sua máquina

### 1. Instale as dependências

```bash
pip install cryptography python-dotenv djangorestframework
```

Sim, precisa instalar o `djangorestframework` — é o que faz a API REST
funcionar. Sem ele os endpoints não existem.

Depois, adicione `'rest_framework'` ao `INSTALLED_APPS` no `settings.py`, junto
com o app onde está o `models.py`:

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'core',
]
```

### 2. Gere sua chave de criptografia

Você só faz isso uma vez por ambiente. **Guarde essa chave com cuidado** — se
ela for trocada ou perdida, tudo que já está criptografado no banco vira
ilegível pra sempre, sem volta.

```bash
python manage.py shell
```
```python
from cryptography.fernet import Fernet
Fernet.generate_key()
```

### 3. Crie o `.env` na raiz do projeto

```
FIELD_ENCRYPTION_KEY=cole-sua-chave-aqui
```

E confirma que ele está no `.gitignore` — essa chave nunca pode ir pro
GitHub.

### 4. Configure o `settings.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY")

if not FIELD_ENCRYPTION_KEY:
    raise ValueError("FIELD_ENCRYPTION_KEY nao encontrada. Verifique o .env.")
```

### 5. Rode as migrações

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Como usar no dia a dia

### Salvando um prontuário

Não tem segredo nenhum — você usa o model normalmente, a criptografia acontece
sozinha por trás:

```python
from core.models import Prontuario

Prontuario.objects.create(
    paciente_nome="Maria da Silva",
    cpf="12345678900",
    queixa_principal="Paciente relata episódios de ansiedade.",
    evolucao_queixa="Segunda sessão, melhora parcial.",
    historico_tratamento="Iniciou terapia em 2024.",
    tags_busca="ansiedade",
)
```

### Lendo de volta

```python
p = Prontuario.objects.get(id=1)
print(p.paciente_nome)  # "Maria da Silva" — já vem descriptografado
```

### Buscando por conteúdo (o pulo do gato)

Aqui tem uma pegadinha que você vai esbarrar se não souber: campos
criptografados **não aceitam** `icontains`. Isso:

```python
Prontuario.objects.filter(queixa_principal__icontains="ansiedade")  # NÃO funciona, retorna vazio
```

...simplesmente não funciona, porque o que está gravado no banco é um token
cifrado, não o texto em si. Pra resolver isso, tem um campo separado
(`tags_busca`), que fica de propósito fora da criptografia, só pra permitir
busca:

```python
Prontuario.objects.filter(tags_busca__icontains="ansiedade")  # Funciona
```

Então, na prática: sempre que salvar um prontuário, pensa em quais termos
fariam sentido alguém buscar depois, e coloca eles em `tags_busca`.

### Mascarando pra exibição

Isso é diferente de criptografia — é só pra controlar o que aparece na tela.
O dado real continua protegido no banco; isso aqui só decide o quanto mostrar:

```python
from core.masking import mask_cpf, mask_nome

p = Prontuario.objects.get(id=1)
print(mask_cpf(p.cpf))             # "***.***.789-00"
print(mask_nome(p.paciente_nome))  # "Maria d* S*****"
```

Também tem `mask_telefone` e `mask_email`, se precisar.

### Usando a API pra testar rápido

Se você não quer ficar abrindo o shell do Django toda hora, a API já resolve:

| Método | Endpoint | O que faz |
|---|---|---|
| GET | `/api/prontuarios/` | lista tudo |
| POST | `/api/prontuarios/` | cria um novo |
| GET | `/api/prontuarios/{id}/` | detalhe de um |
| PATCH | `/api/prontuarios/{id}/` | atualiza parte |
| DELETE | `/api/prontuarios/{id}/` | remove |
| GET | `/api/prontuarios/buscar/?q=ansiedade` | busca via tags_busca |
| GET | `/api/prontuarios/mascarado/` | lista com nome/CPF já mascarados |

Sobe o servidor com `python manage.py runserver` e testa direto no Thunder
Client ou Postman.

## O que já foi testado de verdade (não é só teoria)

- Inserção e leitura via ORM — funciona, transparente.
- Consulta direta no banco (SQLite/DBeaver) confirma que os campos
  criptografados ficam ilegíveis — só aparece um token tipo `gAAAAAB...`.
- `icontains` em campo criptografado realmente não funciona (testamos e deu
  vazio); `tags_busca` resolve.
- Performance: com 5 campos criptografados por registro, o custo veio em torno
  de 0,15ms por registro — irrelevante numa listagem paginada normal, mas
  vale evitar carregar campos criptografados à toa em relatórios grandes
  (usa `.only()` pra isso).
- A API inteira (todos os endpoints da tabela acima) testada via curl, retorno
  batendo com o esperado.

## Se algo não funcionar

- Erro de `baseconv` ou parecido ao rodar migração → provavelmente você está
  usando uma lib antiga de criptografia (tipo `django-cryptography`) num
  Django novo. Usa o `fields.py` daqui, que resolve isso.
- `FIELD_ENCRYPTION_KEY nao encontrada` → confere se o `.env` existe na raiz
  do projeto (mesma pasta do `manage.py`) e se o `load_dotenv` está sendo
  chamado antes de ler a variável no `settings.py`.
- Busca não encontra nada mesmo o dado existindo → você provavelmente está
  buscando direto no campo criptografado. Usa `tags_busca`.