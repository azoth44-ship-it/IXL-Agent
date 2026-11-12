import pytest
from ixl_agent.goal import Goal
from ixl_agent.math_solver import solve,expression
from ixl_agent.browser import extract_score

@pytest.mark.parametrize('text,target,minutes', [('Reach SmartScore 80 within 3 minutes',80,3),('Reach SmartScore 90 with maximum reliability',90,None),('Complete a practice section',100,None),('Maximize progress within 5 minutes',None,5)])
def test_goals(text,target,minutes):
    g=Goal.parse(text); assert (g.target_score,g.minutes)==(target,minutes)

@pytest.mark.parametrize('text,answer',[('Calculate: 2+3','5'),('Solve: 2*x+3=7','2'),('Solve: x^2-5*x+6=0','2, 3'),('Differentiate: x^3','3*x**2'),('Calculate: 1/3+1/6','1/2'),('Factor: x^2-1','(x - 1)*(x + 1)'),('Integrate: 2*x','x**2 + C')])
def test_math(text,answer):
    r=solve(text); assert r.answer==answer; assert r.verification_status=='verified'

@pytest.mark.parametrize('text',['Graph: find the slope','Geometry: find missing angle','Calculate: __import__("os").system("whoami")','Calculate: 1/0','Solve: x=x','Calculate: 2**10000','A train travels ...'])
def test_abstain(text): assert not solve(text).answer

@pytest.mark.parametrize('text,score',[('SmartScore 80',80),('80',80),('Score 80',None),('SmartScore 101',None),('loading',None),('80 90',None)])
def test_score(text,score): assert extract_score(text)==score

def test_deadline():
    g=Goal.create(80,.01); g.started_at-=2
    assert g.expired and not g.reached(None) and g.reached(80)

def test_rational_derivative():
    from ixl_agent.math_solver import expression,x
    import sympy as s
    r=solve('Differentiate: (x^2+1)/(x-1)')
    assert r.verification_status=='verified'
    assert s.cancel(expression(r.answer)-(x**2-2*x-1)/(x-1)**2)==0
