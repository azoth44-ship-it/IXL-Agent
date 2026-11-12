from pathlib import Path
import hashlib
import re
from playwright.sync_api import sync_playwright

def extract_score(text):
    m=re.fullmatch(r'(?:SmartScore\s*:?\s*)?(\d{1,3})',text.strip(),re.I)
    return int(m[1]) if m and 0<=int(m[1])<=100 else None

class IXLBrowser:
    def __init__(self, config):
        self.config=config; self.context=None; self._pw=None; self.images={}
    def start(self, headless=False, url=None):
        if self.context is not None:
            if self.page.is_closed(): raise RuntimeError('Practice tab closed; inspect browser before restarting')
            return self
        self._pw=sync_playwright().start()
        options=dict(headless=headless)
        if self.config.get('channel'): options['channel']=self.config['channel']
        self.context=self._pw.chromium.launch_persistent_context(str(Path(self.config['profile']).resolve()),**options)
        self.page=self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(10000)
        self.page.set_default_navigation_timeout(30000)
        self.page.goto(url or self.config['url'],wait_until='domcontentloaded')
        return self
    def one(self,key):
        loc=self.page.locator(self.config[key])
        if loc.count()!=1 or not loc.is_visible(): raise ValueError('Cannot uniquely identify '+key)
        return loc
    def score(self):
        try: return extract_score(self.one('score').inner_text())
        except Exception: return None
    def question(self):
        self.page.locator(self.config['question']).wait_for(state='visible',timeout=15000)
        q=self.one('question'); text=q.inner_text().strip()
        if q.locator('.secHdr').count()==1 and 'Find the derivative of' in text:
            text=q.locator('.secHdr').evaluate(DERIVATIVE_DOM)
        if not text: raise ValueError('Question is empty')
        visual=not text.startswith('Differentiate: ') and q.locator('svg,canvas,img').count()>0
        fingerprint=hashlib.sha256(text.encode()).hexdigest()
        image=None
        if visual:
            if fingerprint not in self.images:
                Path('screenshots').mkdir(exist_ok=True)
                path=str(Path('screenshots',fingerprint+'.png').resolve()); q.screenshot(path=path); self.images[fingerprint]=path
            image=self.images[fingerprint]
        return text,fingerprint,image
    def submit(self,answer,fingerprint):
        if self.question()[1]!=fingerprint: raise ValueError('Question changed before submission')
        choices=self.page.locator(self.config['choices'])
        if choices.count():
            matches=[choices.nth(i) for i in range(choices.count()) if choices.nth(i).inner_text().strip()==answer]
            if len(matches)!=1: raise ValueError('Ambiguous answer format/choice')
            matches[0].click()
        else:
            if ',' in answer or ' + C' in answer: raise ValueError('Multiple roots/integral require manual formatting')
            field=self.one('input')
            if 'proxy-input' in (field.get_attribute('class') or ''):
                self.fill_math_answer(answer)
            else: field.fill(answer)
        q=self.one('question')
        self._submitted_text=(q.locator('.secHdr').inner_text() if q.locator('.secHdr').count()==1 else q.inner_text()).strip()
        self.one('submit').click()
    def wait_result(self,previous_score,timeout=10000):
        displayed=self.page.evaluate(r"""async ([q,s,old,completeSelector,previous,timeout])=>{
          const start=performance.now();let candidate=null,since=start;
          while(performance.now()-start<timeout){
            await new Promise(requestAnimationFrame);
            const question=document.querySelector(q),score=document.querySelector(s),complete=document.querySelector(completeSelector);
            const changed=question && question.getClientRects().length && (question.querySelector('.secHdr') || question).innerText.trim()!==old;

            const raw=score?.innerText.trim(),value=/^\d{1,3}$/.test(raw)?Number(raw):null;
            const visible=e=>{
              if(!e || !e.getClientRects().length)return false;
              for(let n=e;n;n=n.parentElement){const st=getComputedStyle(n);if(st.visibility==='hidden' || Number(st.opacity)===0)return false;}
              return true;
            };
            const incorrect=value!==null && previous!==null && value<previous;
            const ready=visible(score) && value!==null && value<=100 && (previous===null || value!==previous) && (incorrect || (changed && visible(question)) || visible(complete));
            if(!ready){candidate=null;since=performance.now();continue;}
            if(candidate!==value){candidate=value;since=performance.now();}
            else if(performance.now()-since>=300)return value;
          }
          throw new Error('No stable platform result; submission remains paused');
        }""",[self.config['question'],self.config['score'],self._submitted_text,self.config['complete'],previous_score,timeout])
        self.last_result_score=displayed
        feedback=self.feedback()
        if feedback is None and displayed is not None and previous_score is not None:
            # Explicit inference from platform progress, not model self-assessment.
            if displayed>previous_score: return True
            if displayed<previous_score: return False
        return feedback

    def fill_math_answer(self,answer):
        from .math_solver import expression
        import sympy as s
        field=self.one('input'); field.click(); field.press('ControlOrMeta+A')
        for token in re.split(r'(\*\*-?\d+)',answer):
            if not token: continue
            if token.startswith('**'):
                field.press_sequentially('^'+token[2:],delay=15); field.press('ArrowRight')
            else: field.press_sequentially(token,delay=15)
        actual=field.locator('xpath=../..').evaluate(EDITOR_DOM)
        if s.cancel(expression(actual)-expression(answer))!=0:
            raise ValueError('Rendered editor expression differs from intended answer; submission blocked')
        return actual

    def feedback(self):
        try:
            value=self.one('feedback').inner_text().strip().lower()
            if value in ('correct','correct!'): return True
            if value in ('incorrect','incorrect!'): return False
        except Exception: pass
        return None
    def close(self):
        try:
            if self.context: self.context.close()
        finally:
            if self._pw: self._pw.stop()

DERIVATIVE_DOM = r"""e => {
 function walk(n) {
  if(!n) throw new Error('Missing math structure');
  if(n.nodeType===3) return n.textContent;
  if(n.nodeType!==1 || n.getAttribute('aria-hidden')==='true') return '';
  const cl=n.classList;
  if(cl.contains('vFrac')) return '('+walk(n.querySelector(':scope > .numerator'))+')/('+walk(n.querySelector(':scope > .denominator'))+')';
  if(cl.contains('wholeExp')) return '('+walk(n.querySelector(':scope > .base'))+')^('+walk(n.querySelector(':scope > .exponent'))+')';
  const parts=[...n.childNodes].map(walk);
  if(cl.contains('contractedTimes')) return parts.filter(Boolean).join('*');
  return parts.join('');
 }
 const raw=walk(e).replace(/[–−]/g,'-').trim();
 const m=raw.match(/^Find the derivative of f\(x\)=(.+)\.$/);
 if(!m) throw new Error('Unsupported derivative layout');
 return 'Differentiate: '+m[1];
}"""


EDITOR_DOM = r"""root => {
 function read(n) {
  if(n.nodeType===3) return n.textContent;
  if(n.nodeType!==1) return '';
  if(n.classList.contains('hidden') || n.classList.contains('secret') || n.id==='symPadCursor') return '';
  if(n.classList.contains('exponentAIT')) return '^('+read(n.querySelector('.exponentAITExponentContent'))+')';
  return [...n.childNodes].map(read).join('');
 }
 return read(root).replace(/\s/g,'').replace(/[–−]/g,'-');
}"""
