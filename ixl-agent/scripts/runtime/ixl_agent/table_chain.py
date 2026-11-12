import re
import sympy as s
from .math_solver import expression,x

def constant(text):
 v=expression(text)
 if v.free_symbols or not v.is_Rational:raise ValueError('Unknown table value')
 return v

def solve_table_chain(data):
 tables={}
 for table in data['tables']:
  h=table['header'];m=re.fullmatch(r'([fg])\(x\)',h[1]) if len(h)==3 else None
  if not m or h[0]!='x' or h[2]!=m[1]+"'(x)":raise ValueError('Ambiguous table columns')
  name=m[1]
  if name in tables:raise ValueError('Duplicate function table')
  rows={}
  for row in table['rows']:
   if len(row)!=3:raise ValueError('Incomplete table row')
   a,b,c=map(constant,row)
   if a in rows:raise ValueError('Duplicate table argument')
   rows[a]=(b,c)
  tables[name]=rows
 m=re.fullmatch(r"Find\(([fg])∘([fg])\)'\(([^)]+)\)\.",data['target'])
 if not m:raise ValueError('Unrecognized chain-rule request')
 outer,inner=m[1],m[2];point=constant(m[3])
 inner_value,inner_derivative=tables[inner][point]
 outer_value,outer_derivative=tables[outer][inner_value]
 answer=outer_derivative*inner_derivative
 # Independently build value-and-derivative interpolants and differentiate composition.
 def hermite(rows):
  poly=0
  for a,(value,derivative) in rows.items():
   L=s.prod((x-b)/(a-b) for b in rows if b!=a)
   poly+=value*(1-2*s.diff(L,x).subs(x,a)*(x-a))*L**2+derivative*(x-a)*L**2
  return s.expand(poly)
 polynomials={n:hermite(rows) for n,rows in tables.items()}
 for n,rows in tables.items():
  for a,(v,d) in rows.items():
   if polynomials[n].subs(x,a)!=v or s.diff(polynomials[n],x).subs(x,a)!=d:raise ValueError('Interpolant verification failed')
 composed=polynomials[outer].subs(x,polynomials[inner])
 if s.diff(composed,x).subs(x,point)!=answer:raise ValueError('Independent composition derivative mismatch')
 return {'answer':str(answer),'outer':outer,'inner':inner,'point':str(point),'inner_value':str(inner_value),'inner_derivative':str(inner_derivative),'outer_derivative':str(outer_derivative),'verification':'Table lookup checked against automatic differentiation of Hermite-interpolated composition'}

TABLE_DOM=r'''q=>{
 const norm=t=>t.replace(/[–−]/g,'-').replace(/′/g,"'").replace(/\s/g,'');
 const tables=[...q.querySelectorAll('table.qTable')].map(t=>({header:[...t.querySelectorAll('tr.colHeader td')].map(c=>norm(c.innerText)),rows:[...t.querySelectorAll('tr.dataRow')].map(r=>[...r.querySelectorAll('td')].map(c=>norm(c.innerText)))}));
 const headers=[...q.querySelectorAll('.secHdr')];
 return {tables:tables,target:norm(headers[headers.length-1].innerText)};
}'''
