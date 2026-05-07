# 🧪 API Lab Kit

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Providers](https://img.shields.io/badge/Providers-4-green)](./providers.md)
[![Status](https://img.shields.io/badge/Status-Active-success)]()

**A compact, isolated Python lab for validating real AI provider APIs before main-project integration.**

[🚀 Quick Start](#-quick-start) • [📋 API Support](#-api-support) • [🔧 Usage](#-usage) • [📚 Documentation](#-documentation)

</div>

---

## 📖 About

API Lab Kit é uma **camada de economia de tokens** para sua IDE, agent de código ou automação local. Em vez de gastar contexto lendo documentação repetidamente e chutando payloads dentro da aplicação principal, este kit oferece um **fluxo isolado de testes reais** com os provedores de IA.

### Por que usar?

✅ **Rodar o código antes de integrar** - Teste exatamente as ferramentas de API que você quer usar  
✅ **Com suas próprias chaves** - Execute testes com o `.env` local atual do repositório  
✅ **Validação completa** - Auth, streaming, tools/functions, structured outputs e vision em isolamento  
✅ **Evidência real** - Salve o formato exato da resposta para planejar adapters TypeScript  
✅ **Workspace limpo** - Evite que código experimental polua o projeto principal  
✅ **Secrets seguros** - Mantenha `.env`, virtualenvs e outputs reais fora do git  

### Fluxo recomendado

```
Docs oficiais → Python lab → Output real → TypeScript adapter → Implementação principal
```

---

## 🤖 API Support

| Provider | Python SDK | TypeScript SDK | Streaming | Tools/Functions | Structured Output | Vision | Status |
|----------|:-----------:|:--------------:|:---------:|:---------------:|:-----------------:|:------:|--------|
| **OpenAI** | `openai` | `openai` | ✅ | ✅ | ✅ | ✅ | ✓ Scaffolded |
| **Google Gemini** | `google-genai` | `@google/genai` | ✅ | ✅ | ✅ | ✅ | ✓ Scaffolded |
| **Anthropic Claude** | `anthropic` | `@anthropic-ai/sdk` | ✅ | ✅ | ✅ | ✅ | ✓ Scaffolded |
| **xAI Grok** | `xai-sdk` | `@ai-sdk/xai` | ✅ | ✅ | ✅ | ✅ | ✓ Scaffolded |

📖 Veja [providers.md](./providers.md) para links da documentação oficial de cada provedor.

---

## 🚀 Quick Start

### 1️⃣ Configuração inicial

```bash
cd api-lab-kit
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# Instale as dependências
python -m pip install -r requirements.txt
```

### 2️⃣ Configure suas API keys

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env com suas chaves de API
# Adicione as chaves necessárias para os provedores que deseja testar
```

### 3️⃣ Execute um teste

```bash
python run_lab.py --provider xai --case basic
```

Outputs são salvos automaticamente em `outputs/` como JSON.

Para checar quais providers estão prontos sem fazer chamadas de API:

```bash
python run_lab.py --status
```

### Como usar o API Builder Lab

Use o lab antes de pedir qualquer integracao final no app principal. O objetivo e gerar um output real pequeno, salvar a evidencia local e evitar retrabalho.

1. Configure `.env` com a key do provider que voce quer testar.
2. Rode `python run_lab.py --status` para confirmar quais keys estao presentes, sem fazer chamada de API.
3. Escolha um provider e um case focado.
4. Rode `python run_lab.py --provider <provider> --case <case>`.
5. Leia o resumo tecnico impresso no terminal.
6. Abra o JSON em `outputs/` se precisar ver o shape real da resposta.
7. So planeje TypeScript ou integracao principal quando o case tiver `status: ok`.

Exemplo xAI completo:

```bash
python run_lab.py --status
python run_lab.py --provider xai --case auth
python run_lab.py --provider xai --case basic
python run_lab.py --provider xai --case stream
python run_lab.py --provider xai --case tools
```

Para pedir isso a um agent/coding assistant, use o `SKILL.md` como instrucao:

```txt
Use api-lab-kit/SKILL.md.
Provider: xai
Case: basic
Execute pelo API Builder Lab com run_lab.py.
Nao exponha keys.
Leia o JSON salvo em outputs/.
Responda usando o template tecnico da skill.
Nao implemente TypeScript ainda.
```

Docs oficiais nao precisam ser relidas em toda execucao. Consulte docs do provider quando o case for novo, falhar, mudar SDK/payload, ou quando o output real entrar em conflito com o plano.

---

## 🔧 Usage

### Estrutura de testes

Cada provedor possui **casos de teste isolados**:

| Provedor | Casos disponíveis |
|----------|----------------|
| `openai` | `auth`, `basic`, `stream`, `tools`, `structured` |
| `gemini` | `auth`, `basic`, `stream`, `tools`, `vision` |
| `anthropic` | `auth`, `basic`, `stream`, `tools` |
| `xai` | `auth`, `basic`, `stream`, `tools` |

### Exemplos de execução

```bash
# Testes básicos
python run_lab.py --provider openai --case auth
python run_lab.py --provider openai --case basic
python run_lab.py --provider gemini --case stream

# Recursos avançados
python run_lab.py --provider anthropic --case tools
python run_lab.py --provider openai --case structured
python run_lab.py --provider gemini --case vision
```

Os scripts diretos em `labs/` continuam disponíveis para debug, mas `run_lab.py` é o executor padrão porque lê o output e imprime o resumo técnico no formato da skill.

### Variáveis de ambiente

**Obrigatórias** (adicione suas chaves no `.env`):
```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
XAI_API_KEY=...
```

**Opcionais** (override de modelos):
```env
OPENAI_MODEL=gpt-4
GEMINI_MODEL=gemini-2.0-flash
ANTHROPIC_MODEL=claude-3-5-sonnet
XAI_MODEL=grok-2
```

---

## 📊 Outputs

Cada teste gera um arquivo JSON em `outputs/`:

```
outputs/YYYY-MM-DD_provider_case_result.json
```

**Exemplo de output:**
```json
{
  "provider": "openai",
  "test_name": "basic",
  "timestamp": "2026-05-07T10:30:45Z",
  "status": "ok",
  "model_used": "gpt-4-turbo",
  "latency_ms": 245,
  "request_summary": "Single chat completion request",
  "response_summary": "Generated response with usage stats",
  "raw_response_without_secrets": {...}
}
```

> 💡 **Nota:** JSONs de output são ignorados pelo git por padrão. Mantenha esses arquivos localmente para respostas específicas da sua conta e metadados temporários dos provedores.

---

## 📁 Estrutura do projeto

```
api-lab-kit/
├── labs/                          # Scripts de teste para cada provedor
│   ├── openai_lab.py             # OpenAI test cases
│   ├── gemini_lab.py             # Google Gemini test cases
│   ├── anthropic_lab.py          # Anthropic Claude test cases
│   └── xai_lab.py                # xAI Grok test cases
│
├── outputs/                       # Resultados dos testes (local only)
│   └── *.json                     # Output JSONs (gitignored)
│
├── .env.example                   # Template de variáveis de ambiente
├── requirements.txt               # Dependências Python
├── README.md                      # Este arquivo
├── SKILL.md                       # Instruções de uso para agents/IDEs
├── workflow.md                    # Descrição do fluxo de trabalho
└── providers.md                   # Documentação dos provedores
```

---

## 📚 Documentation

- **[SKILL.md](./SKILL.md)** - Guia para agents (VS Code Copilot, Claude, etc.)
- **[workflow.md](./workflow.md)** - Fluxo de trabalho detalhado
- **[providers.md](./providers.md)** - Links e referências de cada provedor

---

## ✅ Rules & Best Practices

| Regra | Por quê |
|-------|--------|
| Use docs oficiais quando investigar ou corrigir | Execucao repetida usa output real; docs entram em caso novo, falha ou mudanca de SDK |
| Use Python antes de TypeScript | Validação rápida sem compilação |
| Mantenha cada caso de teste focado | Isolamento facilita debug |
| Use `.env` apenas para secrets | Segurança de chaves de API |
| Salve os outputs reais | Evidência para planning do adapter |
| Não mova código experimental para o app | Risco de código quebrado em produção |
| Comite docs e scripts, não JSON outputs | Evita secrets e dados temporários |

---

## 🔐 Security

- ✅ Nunca faça hardcode de chaves de API
- ✅ Nunca imprima chaves de API completas
- ✅ Nunca salve secrets em arquivos de output
- ✅ Use `.env` e mantenha fora do git (já configurado)
- ✅ Outputs com dados sensíveis permanecem locais

---

## 🛠️ Tech Stack

| Componente | Versão |
|-----------|--------|
| Python | 3.8+ |
| OpenAI SDK | Latest |
| Google GenAI | Latest |
| Anthropic SDK | Latest |
| xAI SDK | Latest |
| Pydantic | Latest |

---

## 📝 Next Steps

1. ✅ Clone ou fork este repositório
2. ✅ Copie `.env.example` para `.env` e adicione suas chaves
3. ✅ Configure o virtualenv e instale dependências
4. ✅ Execute um lab case: `python run_lab.py --provider xai --case basic`
5. ✅ Inspecione o output JSON em `outputs/`
6. ✅ Use os resultados para planejar seu adapter TypeScript

---

## 📄 License

MIT License - veja [LICENSE](../../LICENSE) para detalhes.

---

## 🤝 Contributing

Contribuições são bem-vindas! Para melhorias, bugs ou novos casos de teste:

1. Fork este repositório
2. Crie uma branch (`git checkout -b feature/sua-feature`)
3. Commit suas mudanças (`git commit -m 'Add feature'`)
4. Push para a branch (`git push origin feature/sua-feature`)
5. Abra um Pull Request

---

<div align="center">

**Desenvolvido com ❤️ para economizar tokens e acelerar integração de IA**

[⬆ Voltar ao topo](#-api-lab-kit)

</div>
