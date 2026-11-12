import pytest
from ixl_agent.piecewise import solve_continuity

def case(a,b,c='-2',l='<=',r='>'):
 return {'header':f'Find all values of k that make f(x) continuous at x={c}.','rows':[{'expression':a,'condition':f'ifx{l}{c}'},{'expression':b,'condition':f'ifx{r}{c}'}]}

def test_all_roots():assert solve_continuity(case('3*x^2-7*k^2','x+7'))['answer']=='-1, 1'
def test_fraction():assert solve_continuity(case('3*k*x','x+1','1'))['answer']=='2/3'
def test_undefined_point():
 with pytest.raises(ValueError):solve_continuity(case('(x^2-1)/(x-1)+k','3','1'))
def test_domain_gap():
 with pytest.raises(ValueError):solve_continuity(case('k*x','x+1','1','<','>'))
def test_untrusted():
 with pytest.raises(ValueError):solve_continuity(case('__import__("os")','x'))
