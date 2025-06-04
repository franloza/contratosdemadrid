---
title: Estadísticas Generales
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

```sql contract_types
select 
  distinct 
    tipo_de_contrato 
  from contracts_by_date
```

<Dropdown
    data={contract_types} 
    name=tipos_contrato
    value=tipo_de_contrato
    multiple=true
    selectAllByDefault=true
/>

```sql publication_types
select 
  distinct 
    tipo_de_publicacion 
  from contracts_by_date
```

<Dropdown
    data={publication_types} 
    name=tipos_publicacion
    value=tipo_de_publicacion
    multiple=true
    selectAllByDefault=true
/>


```sql amounts_by_year
  select
      date_trunc('year', fecha_del_contrato) as año,
      sum(importe_total) as importe_total,
      sum(numero_contratos) as numero_contratos
  from contracts_by_date
  where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
    AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
    AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
  group by 1
  order by 1
```

```sql amounts_by_quarter
select
    date_trunc('quarter', fecha_del_contrato) as trimestre,
    sum(importe_total) as importe_total,
    sum(numero_contratos) as numero_contratos
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1
order by 1
```

```sql amounts_by_month
select
    date_trunc('month', fecha_del_contrato) as mes,
    sum(importe_total) as importe_total,
    sum(numero_contratos) as numero_contratos
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1
order by 1
```

```sql amounts_by_day
select
    fecha_del_contrato as dia,
    sum(importe_total) as importe_total,
    sum(numero_contratos) as numero_contratos
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1
order by 1
```

```sql pub_type_contracts_annual
select
    date_trunc('year', fecha_del_contrato) as año,
    tipo_de_publicacion,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_contracts_annual
select
    date_trunc('year', fecha_del_contrato) as año,
    tipo_de_contrato,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_amount_annual
select
    date_trunc('year', fecha_del_contrato) as año,
    tipo_de_publicacion,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_amount_annual
select
    date_trunc('year', fecha_del_contrato) as año,
    tipo_de_contrato,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_contracts_quarterly
select
    date_trunc('quarter', fecha_del_contrato) as trimestre,
    tipo_de_publicacion,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_contracts_quarterly
select
    date_trunc('quarter', fecha_del_contrato) as trimestre,
    tipo_de_contrato,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_amount_quarterly
select
    date_trunc('quarter', fecha_del_contrato) as trimestre,
    tipo_de_publicacion,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_amount_quarterly
select
    date_trunc('quarter', fecha_del_contrato) as trimestre,
    tipo_de_contrato,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_contracts_monthly
select
    date_trunc('month', fecha_del_contrato) as mes,
    tipo_de_publicacion,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_contracts_monthly
select
    date_trunc('month', fecha_del_contrato) as mes,
    tipo_de_contrato,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_amount_monthly
select
    date_trunc('month', fecha_del_contrato) as mes,
    tipo_de_publicacion,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_amount_monthly
select
    date_trunc('month', fecha_del_contrato) as mes,
    tipo_de_contrato,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_contracts_daily
select
    fecha_del_contrato as dia,
    tipo_de_publicacion,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_contracts_daily
select
    fecha_del_contrato as dia,
    tipo_de_contrato,
    sum(numero_contratos) as count_contracts
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql pub_type_amount_daily
select
    fecha_del_contrato as dia,
    tipo_de_publicacion,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

```sql contract_type_amount_daily
select
    fecha_del_contrato as dia,
    tipo_de_contrato,
    sum(importe_total) as total_importe
from contracts_by_date
where date_part('year', fecha_del_contrato) IN ${inputs.años.value}
  AND tipo_de_contrato IN ${inputs.tipos_contrato.value}
  AND tipo_de_publicacion IN ${inputs.tipos_publicacion.value}
group by 1, 2
order by 1, 2
```

<Tabs>
    <Tab label="Anual">
        <LineChart
            data={amounts_by_year}
            x=año
            y=numero_contratos
            y2=importe_total
            y2SeriesType=bar
            title="Número de Contratos y Importe Total por Año"
            y2Fmt=eur0m
        />
        <Grid cols=2>
            <BarChart data={pub_type_contracts_annual} x=año y=count_contracts series=tipo_de_publicacion title="Contratos por Tipo de Publicación (Anual)"/>
            <BarChart data={contract_type_contracts_annual} x=año y=count_contracts series=tipo_de_contrato title="Contratos por Tipo de Contrato (Anual)"/>
            <BarChart data={pub_type_amount_annual} x=año y=total_importe series=tipo_de_publicacion title="Importe Total por Tipo de Publicación (Anual)" yFmt=eur0m/>
            <BarChart data={contract_type_amount_annual} x=año y=total_importe series=tipo_de_contrato title="Importe Total por Tipo de Contrato (Anual)" yFmt=eur0m/>
        </Grid>
    </Tab>
    <Tab label="Trimestral">
        <LineChart
            data={amounts_by_quarter}
            x=trimestre
            y=numero_contratos
            y2=importe_total
            y2SeriesType=bar
            title="Número de Contratos y Importe Total por Trimestre"
            y2Fmt=eur0m
        />
        <Grid cols=2>
            <BarChart data={pub_type_contracts_quarterly} x=trimestre y=count_contracts series=tipo_de_publicacion title="Contratos por Tipo de Publicación (Trimestral)"/>
            <BarChart data={contract_type_contracts_quarterly} x=trimestre y=count_contracts series=tipo_de_contrato title="Contratos por Tipo de Contrato (Trimestral)"/>
            <BarChart data={pub_type_amount_quarterly} x=trimestre y=total_importe series=tipo_de_publicacion title="Importe Total por Tipo de Publicación (Trimestral)" yFmt=eur0m/>
            <BarChart data={contract_type_amount_quarterly} x=trimestre y=total_importe series=tipo_de_contrato title="Importe Total por Tipo de Contrato (Trimestral)" yFmt=eur0m/>
        </Grid>
    </Tab>
    <Tab label="Mensual">
        <LineChart
            data={amounts_by_month}
            x=mes
            y=numero_contratos
            y2=importe_total
            y2SeriesType=bar
            title="Número de Contratos y Importe Total por Mes"
            y2Fmt=eur0m
        />
        <Grid cols=2>
            <BarChart data={pub_type_contracts_monthly} x=mes y=count_contracts series=tipo_de_publicacion title="Contratos por Tipo de Publicación (Mensual)"/>
            <BarChart data={contract_type_contracts_monthly} x=mes y=count_contracts series=tipo_de_contrato title="Contratos por Tipo de Contrato (Mensual)"/>
            <BarChart data={pub_type_amount_monthly} x=mes y=total_importe series=tipo_de_publicacion title="Importe Total por Tipo de Publicación (Mensual)" yFmt=eur0m/>
            <BarChart data={contract_type_amount_monthly} x=mes y=total_importe series=tipo_de_contrato title="Importe Total por Tipo de Contrato (Mensual)" yFmt=eur0m/>
        </Grid>
    </Tab>
    <Tab label="Diario">
        <BarChart
            data={amounts_by_day}
            x=dia
            y=numero_contratos
            y2=importe_total
            y2SeriesType=line
            title="Número de Contratos y Importe Total por Día"
            y2Fmt=eur0m
        />
        <Grid cols=2>
            <BarChart data={pub_type_contracts_daily} x=dia y=count_contracts series=tipo_de_publicacion title="Contratos por Tipo de Publicación (Diario)"/>
            <BarChart data={contract_type_contracts_daily} x=dia y=count_contracts series=tipo_de_contrato title="Contratos por Tipo de Contrato (Diario)"/>
            <BarChart data={pub_type_amount_daily} x=dia y=total_importe series=tipo_de_publicacion title="Importe Total por Tipo de Publicación (Diario)" yFmt=eur0m/>
            <BarChart data={contract_type_amount_daily} x=dia y=total_importe series=tipo_de_contrato title="Importe Total por Tipo de Contrato (Diario)" yFmt=eur0m/>
        </Grid>
    </Tab>
</Tabs>

<LicenseNotice />