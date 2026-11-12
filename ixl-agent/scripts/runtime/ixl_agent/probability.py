from fractions import Fraction
import sympy as s
from .math_solver import expression

def solve_distribution(data):
 expected='Does the table show the values of a valid probability function on the outcomes in a sample space?'
 if data['instruction']!=expected:raise ValueError('Unrecognized probability question')
 headers=data['headers']
 if headers.count('Probability')!=1:raise ValueError('Probability column not unique')
 col=headers.index('Probability');values=[]
 for row in data['rows']:
  if len(row)!=len(headers):raise ValueError('Incomplete row')
  v=expression(row[col])
  if v.free_symbols or not v.is_Rational:raise ValueError('Missing or inexact probability')
  values.append(v)
 if not values:raise ValueError('Empty probability table')
 total=sum(values);valid=all(0<=v<=1 for v in values) and total==1
 independent=[Fraction(int(v.p),int(v.q)) for v in values]
 check=all(Fraction(0)<=v<=Fraction(1) for v in independent) and sum(independent)==Fraction(1)
 if bool(valid)!=check:raise ValueError('Independent probability verification failed')
 return {'answer':'yes' if valid else 'no','probabilities':[str(v) for v in values],'sum':str(total),'bounds_valid':all(0<=v<=1 for v in values),'verification':'Exact SymPy rational and independent Fraction arithmetic agree'}

PROBABILITY_DOM=r'''q=>{
 function read(n){
  if(!n)throw new Error('Missing probability structure');if(n.nodeType===3)return n.textContent;
  if(n.nodeType!==1||n.getAttribute('aria-hidden')==='true')return '';
  if(n.classList.contains('vFrac'))return '('+read(n.querySelector(':scope > .numerator'))+')/('+read(n.querySelector(':scope > .denominator'))+')';
  return [...n.childNodes].map(read).join('');
 }
 const norm=t=>t.replace(/[–−]/g,'-').replace(/\s/g,'');
 const tables=q.querySelectorAll('table.qTable');if(tables.length!==1)throw new Error('Ambiguous probability tables');
 const t=tables[0];return {instruction:q.querySelector('.secHdr').innerText.replace(/\s+/g,' ').trim(),headers:[...t.querySelectorAll('tr.colHeader td')].map(c=>c.innerText.trim()),rows:[...t.querySelectorAll('tr.dataRow')].map(r=>[...r.querySelectorAll('td')].map(c=>norm(read(c))))};
}'''
