"""Restricted expression grammar: never eval/sympify untrusted text."""
import ast
import re
from dataclasses import dataclass, asdict
import sympy as s

x = s.Symbol('x', real=True)

def expression(text, symbols=None, functions=None):
    functions = {} if functions is None else functions
    symbols = {"x":x} if symbols is None else symbols
    tree = ast.parse(text.replace('^','**'), mode='eval')
    def visit(n):
        if isinstance(n, ast.Constant) and type(n.value) in (int,float):
            if len(str(n.value)) > 32: raise ValueError('Number too large')
            return s.Rational(str(n.value))
        if isinstance(n, ast.Name) and n.id in symbols: return symbols[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):
            return -visit(n.operand) if isinstance(n.op,ast.USub) else visit(n.operand)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in functions and len(n.args)==1 and not n.keywords:
            return functions[n.func.id](visit(n.args[0]))
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add): return a+b
            if isinstance(n.op,ast.Sub): return a-b
            if isinstance(n.op,ast.Mult): return a*b
            if isinstance(n.op,ast.Div) and b != 0: return a/b
            if isinstance(n.op,ast.Pow) and b.is_Integer and abs(b)<=12: return a**b
        raise ValueError('Unsupported expression')
    if len(text)>200 or sum(1 for _ in ast.walk(tree))>80: raise ValueError('Expression too large')
    result=visit(tree.body)
    if result.has(s.zoo,s.nan,s.oo,-s.oo): raise ValueError('Nonfinite expression')
    return result

@dataclass
class Solution:
    question_type: str = 'unknown'
    interpreted_question: str = ''
    answer: str = ''
    explanation: str = 'Needs interpretation or visual information'
    confidence: float = 0
    verification_status: str = 'unverified'
    reasoning_engine: str = 'sympy'
    def dict(self): return asdict(self)

def solve(text):
    r=Solution(interpreted_question=text)
    try:
        m=re.fullmatch(r'(Calculate|Simplify|Solve|Factor|Differentiate|Integrate)\s*:?\s*(.+?)[.?]?\s*',text,re.I)
        if not m: return r
        op,body=m[1].lower(),m[2]
        if op=='solve':
            left,right=body.split('='); residual=expression(left)-expression(right)
            if s.degree(residual,x) not in (1,2): return r
            roots=s.solve(residual,x)
            if not roots or not all(s.simplify(residual.subs(x,v))==0 for v in roots): return r
            ans=', '.join(str(v) for v in roots); kind='equation'
        else:
            e=expression(body)
            if op=='differentiate':
                value=s.diff(e,x)
                numerator,denominator=s.fraction(s.cancel(e))
                def pd(poly):
                    return sum(c*k*x**(k-1) for (k,),c in s.Poly(poly,x).terms() if k)
                expected=(pd(numerator)*denominator-numerator*pd(denominator))/denominator**2
                ok=s.cancel(value-expected)==0
            elif op=='integrate': value=s.integrate(e,x); ok=s.simplify(s.diff(value,x)-e)==0
            elif op=='factor': value=s.factor(e); ok=s.expand(value-e)==0
            else:
                value=s.cancel(e); ok=s.simplify(value-e)==0
                if e.free_symbols: return r
            if not ok: return r
            ans=str(value)+(' + C' if op=='integrate' else ''); kind=op
        return Solution(kind,text,ans,'Checked symbolically; equations by substitution',0.99,'verified','sympy')
    except (ValueError,SyntaxError,TypeError,NotImplementedError,s.PolynomialError,ZeroDivisionError): return r
