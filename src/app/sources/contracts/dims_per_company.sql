select 
  	nif_del_adjudicatario,
    tipo_de_publicacion,
    adjudicador,
    tipo_de_contrato,
    any_value(adjudicatario order by importe_total desc) as adjudicatario,
    sum(importe_total) as importe_total,
    count(*) as numero_contratos
    
from refined_contracts
group by 1,2,3,4