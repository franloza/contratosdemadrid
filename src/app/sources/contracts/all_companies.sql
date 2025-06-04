with companies as (

select 
  	nif_del_adjudicatario,
    adjudicatario,
    sum(importe_total) as importe_total,
    count(*) as numero_contratos
    
from refined_contracts
group by 1,2

)

select
  nif_del_adjudicatario,
  any_value(adjudicatario order by numero_contratos desc) as adjudicatario,
  sum(importe_total) as importe_total,
  count(*) as numero_contratos

from companies
group by nif_del_adjudicatario