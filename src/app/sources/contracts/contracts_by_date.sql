select 
  -- Fixes issue with dates
  fecha_del_contrato + INTERVAL 1 DAY as fecha_del_contrato,
  tipo_de_publicacion,
  tipo_de_contrato,
  count(*) as numero_contratos,
  sum(importe_total) as importe_total

from refined_contracts 
where fecha_del_contrato is not null 
  and fecha_del_contrato < now()
group by 1,2,3
