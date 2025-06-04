---
title: Ranking
---

```sql years
select 
  distinct 
    date_part('year', fecha_del_contrato) as año 
  from contracts_by_date
```

<Dropdown
    data={years} 
    name=años
    value=año
    multiple=true
    selectAllByDefault=true
/>

```sql company_ranking
  select 
    left(adjudicatario, 30) as adjudicatario,
    sum(amount_per_company_and_year.importe_total) as importe_total

  from amount_per_company_and_year
  left join all_companies on amount_per_company_and_year.nif_del_adjudicatario = all_companies.nif_del_adjudicatario
  where año_del_contrato IN ${inputs.años.value}
  group by 1
  order by 2 desc
  limit 50
```


```sql contracting_authority_ranking
select 
  left(adjudicador, 30) as adjudicador,
  sum(importe_total) as importe_total

from amount_per_contracting_authority_and_year
where año_del_contrato IN ${inputs.años.value}
group by 1
order by 2 desc
limit 50
```

<Tabs>
    <Tab label="Empresas">


        <BarChart 
            data={company_ranking}
            x=adjudicatario
            y=importe_total
            yFmt=eur0m
            swapXY=true
        /> 
    </Tab>
    <Tab label="Adjudicadores">


        <BarChart 
            data={contracting_authority_ranking}
            x=adjudicador
            y=importe_total
            yFmt=eur0m
            swapXY=true
        /> 
    </Tab>
</Tabs>

<LicenseNotice />