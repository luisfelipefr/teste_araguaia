# Pipeline Comercial

Pipeline local para processar as exportações de faturamento e o cadastro de clientes até a camada Gold.

## Requisitos

- Python 3.11 ou superior
- Ambiente virtual recomendado

## Preparação

Coloque os arquivos CSV recebidos em:

```text
dados/entrada/
```

## Criar o ambiente virtual

Na raiz do projeto, execute:

```text
python -m venv .venv
```

Ative o ambiente no PowerShell:

```text
.\.venv\Scripts\Activate.ps1
```

Com o ambiente ativo, instale as dependências:

```text
python -m pip install -r requirements.txt
```

## Executar o pipeline

Na raiz do projeto, execute:

```text
python -m src.pipeline
```

O comando executa, nesta ordem:

1. Inventário dos arquivos.
2. Ingestão na Bronze.
3. Limpeza e tipagem na Silver.
4. Regras de negócio na Gold.
5. Gravação das tabelas Gold em SQLite.

## Executar os testes

```text
python -m pytest -q
```

Para sair do ambiente virtual:

```text
deactivate
```

## Saídas principais

```text
dados/inventario.json
dados/bronze/
dados/silver/faturamento.csv
dados/silver/clientes.csv
dados/silver/quarantine_faturamento.csv
dados/gold/comercial_margem_consultor.csv
dados/gold/comercial_margem_detalhada.csv
dados/gold/comercial_margem_cliente.csv
dados/gold/comercial.sqlite
```

O arquivo `comercial.sqlite` pode ser aberto no DataGrip usando uma conexão SQLite.

## Consultar a Gold

Exemplo de consulta da margem do Pedro Alves:

```sql
SELECT
    competencia,
    receita_total,
    custo_total,
    ROUND(margem * 100, 2) AS margem_percentual
FROM comercial_margem_consultor
WHERE nome_vendedor = 'Pedro Alves'
ORDER BY competencia;
```

## Decisões importantes

- A exportação de 05/11 é usada para outubro, pois contém os itens da exportação de 03/11 e mais 210 linhas.
- `vlr_custo` e `valor_custo_total` são normalizados para `custo`.
- Devoluções e estornos preservam seus valores negativos.
- A chave `nr_documento + item` identifica uma linha do faturamento.
- Duplicidades são enviadas para quarentena e não entram na Gold.
