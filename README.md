# Notes Analyzer

Aplicativo desktop em Python + Flet para analisar automaticamente as notas criadas/modificadas no dia, classificar com IA e manter um histórico navegável.

## ✨ Funcionalidades

- Análise automática das notas do dia com IA (modelo `llama-3.3-70b-versatile` via Groq).
- Classificação por categoria, destino sugerido e justificativa.
- Suporte a duas fontes de notas:
	- **Local**: arquivos `.txt` e `.md` em uma pasta.
	- **Antinote (macOS)**: leitura direta do banco de dados do app Antinote.
- Histórico persistente em SQLite com:
	- mapa de calor mensal;
	- linha do tempo por dia;
	- exclusão com desfazer;
	- reprocessamento de nota com IA;
	- resumo diário com cache (e opção de regenerar).
- Configurações personalizáveis de prompt e categorias de classificação.

## 🧱 Stack

- **Python** 3.10+
- **Flet** (UI desktop)
- **Groq SDK** (integração com IA)
- **SQLite** (histórico local)

## ✅ Requisitos

- Python 3.10 ou superior
- Chave de API da Groq
- macOS, Linux ou Windows para uso com pasta local
- **macOS** para integração com Antinote

## 🚀 Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## ▶️ Execução

```bash
python3 -m src.main
```

## ⚙️ Configuração inicial

Na primeira execução:

1. Abra a aba **Configurações**.
2. Preencha a **Chave da API** (Groq).
3. Escolha a **Fonte das notas**:
	 - **Buscar notas locais**: selecione a pasta com seus `.txt` e `.md`.
	 - **Buscar notas no Antinote**: requer Antinote instalado no macOS.
4. Ajuste o **Prompt Base** (opcional).
5. Revise/edite as **Categorias**.
6. Clique em **Salvar Configurações**.

## 🖥️ Como usar

### Dashboard

- Clique em **Analisar Notas de Hoje**.
- O app lê apenas notas criadas/modificadas no dia atual.
- Ao final, exibe cartões com:
	- nome do arquivo;
	- categoria;
	- destino sugerido;
	- justificativa (ou erro).

### Histórico

- Visualize volume mensal no **mapa de calor**.
- Explore a **linha do tempo** por dia.
- Selecione notas para excluir em lote.
- Reabra uma nota e **reprocesse com IA**.
- Gere **Resumo do dia** (com cache local para consultas futuras).

## 🗂️ Estrutura do projeto

```text
src/
	main.py                  # Ponto de entrada da aplicação
	models/schemas.py        # Modelos de dados (config, nota, resultado)
	services/
		ai_service.py          # Integração com Groq (análise e resumo)
		notes_service.py       # Leitura de notas locais do dia
		antinote_service.py    # Leitura de notas do Antinote (macOS)
		history_service.py     # Persistência SQLite e operações de histórico
	views/
		dashboard_view.py      # Tela de análise
		history_view.py        # Tela de histórico
		settings_view.py       # Tela de configurações
	utils/config_manager.py  # Persistência de configurações
assets/
	icon.png                 # Ícone da aplicação
```

## 💾 Persistência local

- **Histórico SQLite**: `~/.notes_analyzer/historico_app.db`
- **Configurações**:
	- Preferencialmente via `client_storage` do Flet.
	- Fallback local em `.notes_analyzer_config.json` na raiz do projeto.

## 🔍 Regras de leitura das notas

- Fonte local aceita apenas arquivos com extensão `.txt` e `.md`.
- Somente arquivos criados ou modificados na data atual são considerados.
- Arquivos sem permissão de leitura ou com codificação inválida são ignorados.

## 🧪 Verificação rápida

Após instalar, você pode validar a sintaxe:

```bash
python3 -m compileall src
python3 -m py_compile src/main.py
```

## 🛠️ Troubleshooting

### “API Key não configurada”

- Abra **Configurações**, informe a chave da Groq e salve.

### “Pasta não encontrada” / “Sem permissão”

- Verifique o caminho da pasta de notas e permissões de leitura.

### “Banco do Antinote não encontrado”

- A integração Antinote funciona no macOS e espera o banco em:
	`~/Library/Containers/com.chabomakers.Antinote/Data/Documents/notes.sqlite3`

### Erro 401/403/429/5xx da API

- 401/403: chave inválida ou sem permissão.
- 429: limite de requisições excedido.
- 5xx: instabilidade temporária no servidor.

## 📌 Roadmap sugerido

- Exportar histórico para CSV/JSON.
- Filtro por período na timeline.
- Suporte a múltiplos provedores de IA.

## 🤝 Contribuição

1. Faça um fork.
2. Crie uma branch de feature (`feature/minha-feature`).
3. Commit suas mudanças.
4. Abra um Pull Request.

## 📄 Licença

Defina a licença desejada para o repositório (ex.: MIT) e adicione o arquivo `LICENSE`.
