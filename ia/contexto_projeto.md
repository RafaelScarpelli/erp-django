# Contexto do sistema — mini-ERP

Sistema web de gestão para pequenas empresas, feito em Django. Interface em português, tema escuro,
menu lateral à esquerda. Todas as telas exigem login.

## Perfis de usuário (grupos)
- **Administrador**: acesso total, inclusive às telas administrativas da IA (Requisições, IA por usuário, Configuração da IA).
- **Gerente**: visão gerencial — vê todas as vendas e notas; cadastra produtos, categorias, clientes e fornecedores; consulta Estoque e Caixa.
- **Vendedor**: registra vendas e vê apenas as próprias vendas/notas; consulta produtos e clientes, mas não cria/edita/exclui cadastros.
- Contas a Pagar e Contas a Receber são **pessoais**: cada usuário (qualquer perfil) só lista, visualiza, altera e exclui as contas que ele mesmo lançou.

## Menu e telas
- **Dashboard**: total vendido hoje, pedidos de hoje, nº de clientes e as 5 últimas vendas.
- **Vendas** (`/vendas/`): lista com filtros por cliente, status e período. Botão **Nova Venda**:
  escolha o cliente e o status, selecione produtos e quantidades em "Adicionar Produto" (o sistema
  mostra o subtotal e bloqueia quantidade acima do estoque) e clique em **Registrar Venda**.
  Ao registrar, o estoque é baixado automaticamente e é gerada uma movimentação de saída.
  - Status: **Orçamento**, **Finalizada**, **Cancelada**.
  - **Cancelar Venda** (na tela de detalhe): só para vendas em *Orçamento*; devolve o estoque.
    Vendas finalizadas não podem ser canceladas.
  - **Emitir Nota Fiscal** (na tela de detalhe): disponível para vendas não canceladas e sem nota.
- **Produtos**: nome, categoria, descrição, preço de venda, custo, estoque atual. Filtros por nome,
  categoria e "estoque até". Estoque em vermelho = zerado, amarelo = abaixo de 5.
- **Clientes**: nome, CPF/CNPJ (com máscara automática), telefone, e-mail, endereço. Filtro por nome e documento.
- **Categorias** (Administrador/Gerente): agrupam produtos.
- **Estoque** (Administrador/Gerente): extrato somente leitura das movimentações (entradas/saídas),
  geradas automaticamente por vendas e cancelamentos. Não existe lançamento manual.
- **Notas Fiscais**: emissão **simulada**, sem integração com a SEFAZ e sem validade fiscal.
  A nota tem número sequencial, série e uma chave de acesso fictícia de 44 dígitos.
  Pode ser cancelada (cancelar a nota não devolve estoque nem cancela a venda).
- **Contas a Pagar**: descrição, fornecedor, valor, vencimento. Filtros por descrição, fornecedor,
  status e período de vencimento. Botão **Baixar** (escolhendo a forma: Dinheiro, Cartão, Pix, Boleto)
  marca como paga e gera uma *saída* no Caixa. Só contas pendentes podem ser editadas/excluídas.
  Conta pendente com vencimento passado aparece como **Atrasada**.
- **Contas a Receber**: igual, com cliente e venda vinculada opcional. A baixa gera uma *entrada* no Caixa.
- **Fornecedores** (Administrador/Gerente): nome, CNPJ, telefone, e-mail, endereço.
- **Caixa** (Administrador/Gerente): extrato somente leitura com total de entradas, saídas e saldo.
- **Assistente** (IA): esta conversa. **Meu consumo**: tokens de IA usados no mês e cota.
- **Alterar Senha** e **Sair**: no rodapé do menu.

## Regras gerais
- Exclusões pedem confirmação. Registros com vínculos (ex.: produto já vendido, cliente com contas)
  não podem ser excluídos — o sistema avisa.
- Listas são paginadas (10 por página) e mantêm os filtros ao trocar de página.
- Mensagens verdes confirmam operações; vermelhas indicam erro.
- Cada usuário tem uma cota mensal de tokens de IA definida pelo Administrador.
