from ...core.config import COMPANIES_INDEX_NAME, CONTRACTS_INDEX_NAME
from ...db.repositories.base import BaseRepository


class CompaniesRepository(BaseRepository):

    async def get_company(self, company_id: str) -> dict:
        return await self.client.search(index=COMPANIES_INDEX_NAME, body={
            "query": {
                "terms": {
                    "_id": [company_id]
                }
            }
        })

    async def get_company_awardings(self, company_name: str, limit=None):
        body = {
            "_source": "adjudicatario",
            "query": {
                "nested": {
                    "path": "adjudicatario",
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "adjudicatario.name": company_name
                                    }
                                }
                            ]
                        }
                    },
                }
            }
        }
        if limit is not None:
            body["from"] = 0
            body["size"] = limit
        return await self.client.search(index=CONTRACTS_INDEX_NAME, body=body)

    async def get_company_contracts(self, company_id: str) -> dict:
        return await self.client.search(index=CONTRACTS_INDEX_NAME, body={
            "query": {
                "term": {
                    "adjudicatario.id": {
                        "value": company_id,
                    }
                }
            },
            "aggs": {
                "histogram": {
                    "date_histogram": {
                        "field": "fecha-formalizacion",
                        "calendar_interval": "month"
                    }
                },
                "total": {"sum": {"field": "adjudicatario.vat_included"}},
            }
        })

    async def search_company(self, query: str) -> dict:
        return await self.client.search(index=COMPANIES_INDEX_NAME, body={
            "query": {
                "query_string": {
                    "query": query,
                    "analyze_wildcard": True,
                    "default_field": "*"
                }
            }
        })

    async def get_top_companies(self) -> dict:
        return await self.client.search(index=CONTRACTS_INDEX_NAME, body={
            "aggs": {
                "contracts": {
                    "nested": {
                        "path": "adjudicatario"
                    },
                    "aggs": {
                        "total": {
                            "terms": {
                                "field": "adjudicatario.name.keyword",
                                "exclude": "",
                                "size": 1000,
                            },
                            "aggs": {
                                "euros": {
                                    "sum": {
                                        "field": "adjudicatario.vat_included"
                                    },
                                },
                                "euros_bucket_sort": {
                                    "bucket_sort": {
                                        "sort": [
                                            {"euros": {"order": "desc"}}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        })
