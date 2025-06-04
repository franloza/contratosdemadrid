---
title: Buscador de Empresas
---

```sql count_contracts
select sum(numero_contratos) as numero_contratos from contracts_by_date
```

```sql count_companies
select count(*)::int as numero_adjudicatarios from all_companies
```

Busca entre **<Value data={count_companies} fmt=num0 />** empresas adjudicatarias, obtenidas de **<Value data={count_contracts} fmt=num0 />**  contratos públicos de la Comunidad de Madrid.

Una aplicación web interactiva para explorar y analizar la contratación pública en la Comunidad de Madrid.

Desarrollada por [Fran Lozano](https://franloza.com) con el objetivo de fomentar la transparencia y facilitar el acceso a la información. 

Inspirada en [Contratos de Cantabria](https://contratosdecantabria.es), desarrollada por [Jaime Gómez-Obregón](https://contratosdecantabria.es/wtf).

<TextInput
    name=company_search
    placeholder="NIF o Razón Social"
/>

```sql searched_companies

  select
    adjudicatario,
    nif_del_adjudicatario,
    '/empresa/' || nif_del_adjudicatario as company_link,
    importe_total,
    numero_contratos
  from all_companies
  where (adjudicatario ilike '%${inputs.company_search}%' or nif_del_adjudicatario ilike '${inputs.company_search}%')
    and trim('${inputs.company_search}') != ''
  order by numero_contratos desc
  limit 10 

```
{#if searched_companies.length !== 0}

<DataTable
    data={searched_companies}
    link=company_link
    emptySet=pass
    emptyMessage="No se encontraron resultados"
>
    <Column id=adjudicatario title="Adjudicatario"/>
    <Column id=nif_del_adjudicatario title="NIF"/>
    <Column id=importe_total title="Importe Total" fmt=eur0k contentType=bar />
    <Column id=numero_contratos title="Nº Contratos" contentType=bar />
</DataTable>

{/if}

¿ No sabes por donde empezar? Mira en el [ranking](/ranking) o prueba con alguna de estas empresas:

```sql random_companies

with companies as (
  select
      adjudicatario,
      '/empresa/' || nif_del_adjudicatario as company_link,
      numero_contratos
    from all_companies
    where numero_contratos > 5
)

select * from companies
using sample 10
order by numero_contratos desc

```

{#each random_companies as random_companies}

<BigLink url='{random_companies.company_link}/'>
    {random_companies.adjudicatario}
</BigLink>

{/each}

<LicenseNotice />
