import pytest
from ixl_agent.table_chain import solve_table_chain

def sample(target="Find(g∘f)'(0)."):
 return {'tables':[{'header':['x','f(x)',"f'(x)"],'rows':[['-9','-2','3'],['-7','-1','2'],['0','6','2']]},{'header':['x','g(x)',"g'(x)"],'rows':[['0','-1','2'],['2','-3','5'],['6','5','9']]}],'target':target}
def test_chain_order():assert solve_table_chain(sample())['answer']=='18'
def test_missing_lookup():
 with pytest.raises(KeyError):solve_table_chain(sample("Find(f∘g)'(0)."))
def test_duplicate_column():
 d=sample();d['tables'][0]['header'][2]='f(x)'
 with pytest.raises(ValueError):solve_table_chain(d)
def test_bad_value():
 d=sample();d['tables'][0]['rows'][0][0]='x'
 with pytest.raises(ValueError):solve_table_chain(d)
