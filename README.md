<div align="center">

# 📦 Sistema de Estoque

**Gerenciador de estoque desktop com interface gráfica nativa em Python**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-informational?style=flat-square)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square)]()

Interface 100% nativa, sem dependências externas. Basta ter Python instalado.

</div>

---

## 📸 Visão Geral

Sistema de gerenciamento de estoque com paleta dark terminal, desenvolvido inteiramente com a stdlib do Python (Tkinter + SQLite3). Inclui dashboard com KPIs em tempo real, gestão de pedidos, controle de estoque, relatórios e metas mensais.

---

## ✨ Funcionalidades

<details>
<summary><strong>📊 Dashboard</strong></summary>

- KPIs em tempo real: receita do dia, receita do mês, estoque baixo e valor total
- Últimos 10 pedidos com status colorido (ativo / cancelado / devolvido)
- Painel de alertas de estoque abaixo do mínimo
- Barra de progresso da meta mensal
- Atualização automática a cada 10 segundos

</details>

<details>
<summary><strong>🛒 Pedidos</strong></summary>

- Criação de pedidos com carrinho interativo (duplo clique para adicionar)
- Busca de produtos em tempo real por nome ou SKU
- Seleção de cliente, forma de pagamento e desconto
- Cancelamento de pedido com restauração automática do estoque
- Visualização detalhada por pedido
- Filtro por status: todos / ativos / cancelados / devolvidos

</details>

<details>
<summary><strong>📦 Estoque</strong></summary>

- Posição geral com indicadores visuais: **OK** / **BAIXO** / **ZERO**
- Entrada de mercadoria por fornecedor com múltiplos itens
- Ajuste manual de quantidade com log automático
- Histórico completo de movimentações (entradas, saídas, ajustes, cancelamentos)
- Totais de valor a preço de venda, custo e margem potencial

</details>

<details>
<summary><strong>🗃️ Produtos, Categorias e Fornecedores</strong></summary>

- Cadastro com SKU, preços de venda/custo e estoque mínimo
- Vinculação a categorias e fornecedores
- Ativação/desativação sem exclusão permanente
- Gerenciamento de categorias e fornecedores na mesma tela (abas)

</details>

<details>
<summary><strong>👥 Clientes</strong></summary>

- Cadastro completo: nome, e-mail, telefone, endereço, CPF/CNPJ
- Histórico de pedidos com total gasto por cliente
- Exclusão segura (bloqueada se houver pedidos ativos)

</details>

<details>
<summary><strong>📈 Relatórios</strong></summary>

| Relatório | O que mostra |
|-----------|-------------|
| **Vendas** | Total de pedidos, receita, descontos, ranking por forma de pagamento e top produtos |
| **Margem** | Lucro e margem percentual por produto vendido |
| **Estoque** | Posição atual com valor e margem potencial por item |
| **Metas** | Definição e acompanhamento de metas mensais com barra de progresso |

</details>

---

## 🚀 Instalação e uso

### Pré-requisitos

- Python **3.8 ou superior**
- Tkinter (já incluso na maioria das distribuições Python)

> **Ubuntu/Debian** — caso Tkinter não esteja disponível:
> ```bash
> sudo apt install python3-tk
> ```

### Executar

```bash
# Clone o repositório
git clone https://github.com/majestev/Sistema-de-estoque.git
cd sistema-estoque

# Execute diretamente — sem instalar nada
python estoque.py
```

Na primeira execução o sistema:
1. Cria o banco de dados automaticamente em `~/estoque.db`
2. Popula com dados de exemplo (categorias, fornecedores, produtos e clientes)

### Localização do banco de dados

Por padrão o banco é criado em `~/estoque.db`. Para usar um caminho personalizado:

```bash
# Linux / macOS
ESTOQUE_DB=/caminho/para/estoque.db python estoque.py

# Windows (PowerShell)
$env:ESTOQUE_DB="C:\caminho\para\estoque.db"; python estoque.py
```

---

## 🗂️ Estrutura do banco de dados

```
estoque.db
├── config             → Configurações da empresa
├── categorias         → Categorias de produtos
├── fornecedores       → Cadastro de fornecedores
├── produtos           → Catálogo com preços e estoque
├── clientes           → Cadastro de clientes
├── pedidos            → Cabeçalho de pedidos (status, total, pagamento)
├── pedido_itens       → Itens de cada pedido
├── entradas           → Cabeçalho de entradas de estoque
├── entrada_itens      → Itens de cada entrada
├── movimentacoes      → Log auditável de todas as movimentações
└── metas              → Metas mensais de faturamento
```

---

## ⌨️ Atalhos

| Ação | Como |
|------|------|
| Navegar entre módulos | Sidebar lateral |
| Abrir detalhes / editar | Duplo clique na linha |
| Confirmar formulário | `Enter` ou botão ✓ |
| Fechar / cancelar | `Escape` ou botão ✕ |

---

## 🏗️ Estrutura do código

O projeto é composto por um único arquivo `estoque.py`:

```
estoque.py
├── Tema & paleta de cores     → Dicionário C{} com todas as cores
├── Banco de dados             → Schema, seed, helpers e movimentações
├── Widgets base               → DarkFrame, DarkEntry, DarkButton, etc.
├── Diálogos modais            → FormDialog, CartDialog, EntradaDialog
├── Páginas                    → Dashboard, Pedidos, Estoque, Produtos,
│                                Clientes, Relatórios, Sistema
├── App                        → Janela principal, sidebar, roteamento
└── main()                     → Entry point
```

---

## 🎨 Interface

- **Tema:** dark terminal com verde neon
- **Fonte:** JetBrains Mono (fallback automático para Courier)
- **Cores de status:** 🟢 verde (OK) · 🟡 âmbar (atenção) · 🔴 vermelho (crítico/cancelado)
- **Feedback:** barra de flash na topbar com mensagem colorida por tipo de operação
- **100% nativo:** zero imagens, zero arquivos externos

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para mudanças maiores, abra uma *issue* primeiro.

1. Fork o projeto
2. Crie sua branch: `git checkout -b feature/minha-feature`
3. Commit: `git commit -m 'feat: minha feature'`
4. Push: `git push origin feature/minha-feature`
5. Abra um Pull Request

---

## 📄 Licença

Distribuído sob a licença MIT. Veja [`LICENSE`](LICENSE) para mais informações.
