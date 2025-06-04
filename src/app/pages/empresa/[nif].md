#  <Value data={company} />.

```sql company
select distinct
  adjudicatario

from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
```


```sql tipo_de_publicaciones
select 
  distinct 
    tipo_de_publicacion
  from dims_per_company
  where nif_del_adjudicatario = '${params.nif}'
```

<Dropdown
    data={tipo_de_publicaciones} 
    name=tipo_de_publicacion
    value=tipo_de_publicacion
    multiple=true
    selectAllByDefault=true
/>

```sql tipo_de_contratos
select 
  distinct 
    tipo_de_contrato
  from dims_per_company
  where nif_del_adjudicatario = '${params.nif}'
```

<Dropdown
    data={tipo_de_contratos} 
    name=tipo_de_contrato
    value=tipo_de_contrato
    multiple=true
    selectAllByDefault=true
/>


```sql contracts_by_contracting_authority
select
 adjudicador as name,
 count(*) as value
from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
  and tipo_de_publicacion in ${inputs.tipo_de_publicacion.value}
  and tipo_de_contrato in ${inputs.tipo_de_contrato.value}
group by 1
order by 2 desc
```

<ECharts
  config={{
    title: {
      text: 'Contratos por Centro Adjudicador',
      left: 'center'
    },
    tooltip: {
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '70%'],
        startAngle: 180,
        endAngle: 360,
        data: [...contracts_by_contracting_authority],
      }
    ]
  }}
/>


<Grid cols=2>

<div>

```sql contracts_by_type
select
 tipo_de_contrato as name,
 count(*) as value
from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
  and tipo_de_publicacion in ${inputs.tipo_de_publicacion.value}
  and tipo_de_contrato in ${inputs.tipo_de_contrato.value}
group by 1
order by 2 desc
```

<ECharts
  config={{
    title: {
      text: 'Contratos por Tipo de Contrato',
      left: 'center'
    },
    tooltip: {
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '70%'],
        startAngle: 180,
        endAngle: 360,
        data: [...contracts_by_type],
      }
    ]
  }}
/>
</div>
<div>

```sql contracts_by_publication_type
select
 tipo_de_publicacion as name,
 count(*) as value
from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
  and tipo_de_publicacion in ${inputs.tipo_de_publicacion.value}
  and tipo_de_contrato in ${inputs.tipo_de_contrato.value}
group by 1
order by 2 desc
```

<ECharts
  config={{
    title: {
      text: 'Contratos por Tipo de Publicación',
      left: 'center'
    },
    tooltip: {
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '70%'],
        startAngle: 180,
        endAngle: 360,
        data: [...contracts_by_publication_type],
      }
    ]
  }}
/>
</div>
</Grid>

<Grid cols=2>

<div>

```sql amount_by_type
select
 tipo_de_contrato as name,
 sum(importe_total) as value
from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
  and tipo_de_publicacion in ${inputs.tipo_de_publicacion.value}
  and tipo_de_contrato in ${inputs.tipo_de_contrato.value}
group by 1
order by 2 desc
```

<BarChart
    data={amount_by_type}
    x=name
    y=value
    title="Importe Total por Tipo de Contrato"
    swapXY=true
    YFmt=eur0k
/>
</div>
<div>

```sql amount_by_publication_type
select
 tipo_de_publicacion as name,
 sum(importe_total) as value
from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
  and tipo_de_publicacion in ${inputs.tipo_de_publicacion.value}
  and tipo_de_contrato in ${inputs.tipo_de_contrato.value}
group by 1
order by 2 desc

```

<BarChart
    data={amount_by_publication_type}
    x=name
    y=value
    title="Importe Total por Tipo de Publicación"
    swapXY=true
    YFmt=eur0k
/>
</div>

</Grid>

<div>

```sql amount_by_contracting_authority
select
 adjudicador as name,
 sum(importe_total) as value
from dims_per_company
where nif_del_adjudicatario = '${params.nif}'
  and tipo_de_publicacion in ${inputs.tipo_de_publicacion.value}
  and tipo_de_contrato in ${inputs.tipo_de_contrato.value}
group by 1
order by 2 desc
```

<BarChart
    data={amount_by_contracting_authority}
    x=name
    y=value
    title="Importe por Centro Adjudicador"
    swapXY=true
    YFmt=eur0k
/>
</div>

<BigLink url={`https://contratos-publicos.comunidad.madrid/contratos?nif_adjudicatario=${params.nif}&estado_situacion=Resuelta`}>
    Ver Contratos
</BigLink>
