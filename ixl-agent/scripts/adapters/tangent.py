import re

import sympy as s
from ixl_agent.math_solver import expression

SKILL_PATH = '/math/calculus/find-tangent-lines-using-implicit-differentiation'
x, y = s.symbols('x y', real=True)
SYMBOLS = {'x': x, 'y': y}

READ_PROMPT = r"""root => {
  function walk(node) {
    if (node.nodeType === 3) return node.textContent;
    if (node.nodeType !== 1 || node.getAttribute('aria-hidden') === 'true') return '';
    const read = selector => {
      const parts = node.querySelectorAll(':scope > ' + selector);
      if (parts.length !== 1) throw new Error('Ambiguous math structure: ' + selector);
      return walk(parts[0]);
    };
    const classes = node.classList;
    if (classes.contains('wholeExp')) return '(' + read('.base') + ')^(' + read('.exponent') + ')';
    if (classes.contains('vFrac')) return '(' + read('.numerator') + ')/(' + read('.denominator') + ')';
    const parts = [...node.childNodes].map(walk).filter(v => v.trim());
    return parts.join(classes.contains('contractedTimes') ? '*' : '');
  }
  return walk(root).replace(/[–−]/g, '-');
}"""


def extract(question):
    candidates = question.locator('.secHdr, .math.section > .secContentPiece').filter(
        has_text=re.compile(r'^Find the (?:slope|equation) of the tangent line')
    )
    if candidates.count() != 1 or not candidates.is_visible():
        raise ValueError('Expected one visible tangent question')
    data = parse_prompt(candidates.evaluate(READ_PROMPT))
    if data['kind'] == 'equation' and question.locator('.yui3-sympadfiwidget-content').count() == 1:
        data['kind'] = 'full_equation'
    return data


def parse_prompt(prompt):
    match = re.fullmatch(
        r'Find\s+the\s+(slope|equation)\s+of\s+the\s+tangent\s+line\s+to\s+the\s+graph\s+of\s+'
        r'([^=]+)=([^=]+?)\s+at\s*\(([^,]+),([^,]+)\)\.',
        prompt.strip(),
    )
    if not match:
        raise ValueError('Expected a tangent question with one equation and one point')
    return dict(zip(('kind', 'lhs', 'rhs', 'x', 'y'), (re.sub(r'\s+', '', part) for part in match.groups())))


def curve(data):
    lhs = expression(data['lhs'], SYMBOLS)
    rhs = expression(data['rhs'], SYMBOLS)
    point = {var: expression(data[str(var)], {}) for var in (x, y)}
    if lhs.subs(point) != rhs.subs(point):
        raise ValueError('Extracted point is not on the curve')
    return lhs, rhs, point


def solve(data):
    lhs, rhs, point = curve(data)
    residual = lhs - rhs
    partial_y = residual.diff(y).subs(point)
    if partial_y == 0:
        raise ValueError('Cannot verify a finite tangent slope')
    slope = -residual.diff(x).subs(point) / partial_y
    if slope.is_Rational is not True:
        raise ValueError('Expected a rational slope')
    if data['kind'] == 'equation':
        return [str(point[y]), str(slope), str(point[x])]
    if data['kind'] == 'full_equation':
        intercept = point[y] - slope * point[x]
        term = f'{slope}*x' if slope != 0 else ''
        offset = f'+{intercept}' if term and intercept > 0 else str(intercept) if intercept or not term else ''
        return ['y=' + term + offset]
    return [str(slope)]


def verify(data, answer):
    lhs, rhs, point = curve(data)
    t = s.Dummy('t')
    if data['kind'] == 'equation':
        if len(answer) != 3:
            return False
        y0, slope, x0 = [expression(part, {}) for part in answer]
        if x0 != point[x] or y0 != point[y]:
            return False
    elif data['kind'] == 'full_equation':
        if len(answer) != 1 or not answer[0].startswith('y='):
            return False
        line = expression(answer[0][2:], SYMBOLS)
        if line.has(y) or line.diff(x, 2) != 0 or line.subs(x, point[x]) != point[y]:
            return False
        slope = line.diff(x)
    else:
        if len(answer) != 1:
            return False
        slope = expression(answer[0], {})
    residual = (lhs - rhs).subs({x: point[x] + t, y: point[y] + slope*t}, simultaneous=True)
    numerator, denominator = s.cancel(residual).as_numer_denom()
    return bool(denominator.subs(t, 0) != 0 and numerator.subs(t, 0) == 0
                and s.Poly(numerator, t).nth(1) == 0)


def widgets(question, count):
    items = question.locator('.yui3-sympadfiwidget-content')
    if items.count() != count or any(not item.is_visible() for item in items.all()):
        raise ValueError('Unexpected tangent answer controls')
    if count == 3:
        template = question.locator('.secContent').evaluate(
            r"""e => {const copy=e.cloneNode(true);
              copy.querySelectorAll('.yui3-sympadfiwidget').forEach(n=>n.replaceWith('#'));
              copy.querySelectorAll('.symPadArea').forEach(n=>n.remove());
              copy.querySelectorAll('.bigParen[aria-label]').forEach(n=>n.replaceWith(n.getAttribute('aria-label')));
              return copy.textContent.replace(/[–−]/g,'-').replace(/\s/g,'');
            }"""
        )
        if template != 'y-#=#(x-#)':
            raise ValueError(f'Unrecognized point-slope template: {template}')
    return items.all()


def fill(question, answer):
    for item, value in zip(widgets(question, len(answer)), answer):
        item.click()
        field = item.locator('input.proxy-input')
        if field.count() != 1 or not field.evaluate('e => e === document.activeElement'):
            raise ValueError('Tangent editor did not receive keyboard focus')
        field.press('Control+a')
        field.press('Backspace')
        in_fraction = False
        for char in value:
            if in_fraction and not char.isdigit():
                field.press('ArrowRight')
                in_fraction = False
            field.press({'/': 'Slash', '-': 'Minus', '+': 'Shift+Equal', '=': 'Equal', '*': 'Shift+Digit8'}.get(char, char))
            if char == '/':
                in_fraction = True


def read(question):
    items = widgets(question, 3 if extract(question)['kind'] == 'equation' else 1)
    return [item.evaluate(r"""root => {
      function walk(node) {
        if (node.nodeType === 3) return node.textContent;
        if (node.nodeType !== 1 || node.matches('.hidden,.secret,.sympad-instructions,.sympad-live-region,input,[id=symPadCursor]')) return '';
        if (node.classList.contains('vFrac')) {
          const n = node.querySelector(':scope > .numerator');
          const d = node.querySelector(':scope > .denominator');
          if (!n || !d) throw new Error('Missing fraction content');
          return '(' + walk(n) + ')/(' + walk(d) + ')';
        }
        return [...node.childNodes].map(walk).join('');
      }
      return walk(root).replace(/\s/g,'').replace(/[–−]/g,'-').replace(/[×⋅·]/g,'*');
    }""") for item in items]


def equivalent(data, answer, actual):
    if data['kind'] == 'full_equation':
        return len(actual) == 1 and verify(data, actual)
    return len(answer) == len(actual) and all(
        expression(a, {}) == expression(b, {}) for a, b in zip(answer, actual)
    )
