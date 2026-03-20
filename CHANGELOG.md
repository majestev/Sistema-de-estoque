# Changelog

Todas as mudanças notáveis neste projeto serão documentadas aqui.

---

## [2.0.0] — 2025

### Adicionado
- Interface gráfica completa em Tkinter com tema dark terminal
- Dashboard com KPIs em tempo real e atualização automática a cada 10s
- Módulo de Pedidos com carrinho interativo e filtro por status
- Módulo de Estoque com log de movimentações auditável
- Módulo de Produtos com abas para categorias e fornecedores
- Módulo de Clientes com histórico de compras por cliente
- Módulo de Relatórios: vendas, margem, estoque e metas mensais
- Configurações da empresa persistidas no banco de dados
- Suporte a variável de ambiente `ESTOQUE_DB` para caminho customizado do banco
- Seed automático com dados de exemplo na primeira execução
- Fallback de fonte: JetBrains Mono → Courier

### Técnico
- SQLite com WAL mode e foreign keys habilitadas
- Registro automático de movimentações em todas as operações de estoque
- Cancelamento de pedido restaura estoque automaticamente
- Zero dependências externas (apenas stdlib Python)
