import asyncio
from app import onchain

class Resp:
    def __init__(self, data): self.data=data
    def raise_for_status(self): pass
    def json(self): return self.data

class Client:
    async def post(self, url, json):
        m=json['method']
        if m=='getTokenSupply': return Resp({'result':{'value':{'uiAmount':1000}}})
        if m=='getTokenLargestAccounts': return Resp({'result':{'value':[{'uiAmount':100},{'uiAmount':50}]}})
        return Resp({'result':{'value':{'data':{'parsed':{'info':{'mintAuthority':'x','freezeAuthority':None}}}}}})

def test_onchain_enrichment_proxy():
    x=asyncio.run(onchain.enrich_token(Client(),'MINT'))
    assert x['holder_count_proxy']==2
    assert x['concentration_risk']==15.0
    assert x['mint_authority_present'] is True
    assert x['freeze_authority_present'] is False
