select 
  	date_part('year', fecha_del_contrato) as año_del_contrato,
  	adjudicador,
    sum(importe_total) as importe_total,
    count(*) as numero_contratos
    
from refined_contracts
group by 1,2