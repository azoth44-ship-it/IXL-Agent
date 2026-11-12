import re
import sympy as s
from .math_solver import expression,x
k=s.Symbol('k',real=True)

def solve_continuity(data):
    rows=data['rows']; symbols={'x':x,'k':k}
    if len(rows)!=2:raise ValueError('Only two-branch cases are verified')
    match=re.fullmatch(r'Find all values of k that make f\(x\) continuous at x=(.+)\.',data['header'])
    if not match:raise ValueError('Unexpected question instructions')
    boundary=expression(match[1],symbols)
    if boundary.free_symbols:raise ValueError('Unknown boundary')
    branches=[];sides=[];included=[]
    for row in rows:
        m=re.fullmatch(r'ifx(<=|>=|<|>)(.+)',row['condition'])
        if not m or s.simplify(expression(m[2],symbols)-boundary)!=0:raise ValueError('Inconsistent branch domain')
        branch=expression(row['expression'],symbols)
        branches.append(branch);sides.append('-' if '<' in m[1] else '+');included.append('=' in m[1])
    if set(sides)!={'-','+'} or sum(included)!=1:raise ValueError('Domain does not define a continuous junction')
    limits=[s.limit(e,x,boundary,dir=side) for e,side in zip(branches,sides)]
    if any(v.has(s.oo,-s.oo,s.zoo,s.nan) for v in limits):raise ValueError('Nonfinite limit')
    residual=s.cancel(limits[0]-limits[1]);num,den=s.fraction(residual)
    if s.degree(num,k) not in (1,2):raise ValueError('Unsupported number of solutions')
    roots=s.solveset(residual,k,domain=s.S.Reals)
    if not isinstance(roots,s.FiniteSet) or not roots:raise ValueError('Cannot return a finite nonempty solution list')
    valid=[]
    for root in sorted(roots,key=s.default_sort_key):
        if not root.is_Rational:raise ValueError('Exact input format for irrational root requires review')
        values=[s.simplify(s.limit(e.subs(k,root),x,boundary,dir=side)) for e,side in zip(branches,sides)]
        at=branches[included.index(True)].subs({k:root,x:boundary})
        if at.has(s.oo,-s.oo,s.zoo,s.nan) or s.simplify(values[0]-values[1])!=0 or s.simplify(values[0]-at)!=0:raise ValueError('Independent continuity check failed')
        valid.append(str(root))
    return {'answer':', '.join(valid),'boundary':str(boundary),'limits':[str(v) for v in limits],'verification':'All real solutions checked using both directional limits and actual included branch value'}

PIECEWISE_DOM=r'''q=>{
 function walk(n){
  if(!n)throw new Error('Missing mathematical structure');
  if(n.nodeType===3)return n.textContent;
  if(n.nodeType!==1 || n.getAttribute('aria-hidden')==='true')return '';
  const c=n.classList;
  if(c.contains('vFrac'))return '('+walk(n.querySelector(':scope > .numerator'))+')/('+walk(n.querySelector(':scope > .denominator'))+')';
  if(c.contains('wholeExp'))return '('+walk(n.querySelector(':scope > .base'))+')^('+walk(n.querySelector(':scope > .exponent'))+')';
  const parts=[...n.childNodes].map(walk);
  return c.contains('contractedTimes')?parts.filter(Boolean).join('*'):parts.join('');
 }
 const norm=t=>t.replace(/[–−]/g,'-').replace(/≤/g,'<=').replace(/≥/g,'>=').replace(/\s/g,'');
 const h=walk(q.querySelector('.secHdr')).replace(/[–−]/g,'-').replace(/\s+/g,' ').trim();
 return {header:h,rows:[...q.querySelectorAll('.piecewise-expressions-table tr')].map(r=>({expression:norm(walk(r.querySelector('.piecewise-expression'))),condition:norm(walk(r.querySelector('.piecewise-condition')))}))};
}'''
