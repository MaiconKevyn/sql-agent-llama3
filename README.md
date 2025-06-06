# txt2sql - Agente SQL Interativo para Dados do SUS

Um agente inteligente que permite consultar dados do Sistema Único de Saúde (SUS) usando linguagem natural em português brasileiro.

## 🚀 Características

- **Interface em Português**: Totalmente localizada para usuários brasileiros
- **Consultas em Linguagem Natural**: Faça perguntas complexas sem conhecer SQL
- **Fallbacks Inteligentes**: Sistema robusto com múltiplas estratégias de resposta
- **Arquitetura Modular**: Código profissional com separação clara de responsabilidades
- **Configuração Flexível**: Fácil customização via variáveis de ambiente

## 📋 Pré-requisitos

- Python 3.8+
- Ollama com modelo llama3 instalado
- Banco de dados SQLite com dados do SUS (`sus_data.db`)

## 🛠 Instalação

1. Clone o repositório:
```bash
git clone <repositorio>
cd txt2sql