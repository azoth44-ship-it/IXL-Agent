def check_submit(start,budget):
 if Path('STOP').exists():raise RuntimeError('Canceled before submission')
 if time.perf_counter()-start>=budget:raise TimeoutError('Practice deadline reached before submission')

import json,time
from pathlib import Path
from ixl_agent.probability import solve_distribution,PROBABILITY_DOM
URL='https://www.ixl.com/math/algebra-2/identify-probability-distributions'
WAIT=r'''async ([qsel,ssel,old,previous,timeout])=>{
 const start=performance.now();let last=null,since=start;
 const visible=e=>{if(!e?.getClientRects().length)return false;for(let p=e;p;p=p.parentElement){const s=getComputedStyle(p);if(s.visibility==='hidden'||Number(s.opacity)===0)return false;}return true;};
 while(performance.now()-start<timeout){await new Promise(requestAnimationFrame);
  const q=document.querySelector(qsel),score=document.querySelector(ssel),raw=score?.innerText.trim();
  const value=/^\d{1,3}$/.test(raw)?Number(raw):null;
  const ready=visible(score)&&value!==null&&value<=100&&value!==previous&&(value<previous||(visible(q)&&q.innerText.trim()!==old));
  if(!ready){last=null;since=performance.now();continue;}
  if(last!==value){last=value;since=performance.now();}else if(performance.now()-since>=300)return value;
 }throw new Error('Feedback unknown; paused without another submission');
}'''
def inspect(b):
 root=Path('reports/probability90');root.mkdir(parents=True,exist_ok=True)
 if b.page.url!=URL:b.page.goto(URL,wait_until='domcontentloaded')
 b.page.locator(b.config['question']).wait_for(state='visible',timeout=15000);q=b.one('question')
 data={'url':b.page.url,'score':b.score(),'submit_count':b.page.locator(b.config['submit']).count(),'component_text':b.page.locator('.question-component').inner_text(),'text':q.inner_text(),'html':q.evaluate("e=>{const c=e.cloneNode(true);c.querySelectorAll('input[type=hidden]').forEach(n=>n.remove());return c.outerHTML}")}
 (root/'probe.json').write_text(json.dumps(data,indent=2));q.screenshot(path=str(root/'question.png'));print(json.dumps({k:v for k,v in data.items() if k!='html'}),flush=True)
def run(b,target=90,strict=False,max_seconds=180):
 root=Path('reports/probability');root.mkdir(parents=True,exist_ok=True);out={'target':target,'rows':[],'browser_restarts':0};start=time.perf_counter();seen=set()
 def save():out['elapsed_practice_seconds']=time.perf_counter()-start;(root/'result.json').write_text(json.dumps(out,indent=2))
 try:
  if b.page.url!=URL:raise ValueError('Wrong skill URL')
  score=b.score();out['starting_score']=score
  if score is None:raise ValueError('Score unknown')
  while not (score>target if strict else score>=target) and time.perf_counter()-start<max_seconds:
   if Path('STOP').exists():
    out['outcome']='Paused by user';save();return
   row={'score_before':score};t=time.perf_counter();q=b.one('question');data=q.evaluate(PROBABILITY_DOM);row.update(question=data,extraction_seconds=time.perf_counter()-t);key=json.dumps(data,sort_keys=True)
   if key in seen:raise ValueError('Question repeated; paused to prevent duplicate submission')
   t=time.perf_counter();solution=solve_distribution(data);row.update(solution=solution,solve_verify_seconds=time.perf_counter()-t)
   choice=q.get_by_role('radio',name=solution['answer'],exact=True)
   if choice.count()!=1:raise ValueError('Answer choice ambiguous')
   t=time.perf_counter();choice.click()
   if choice.get_attribute('aria-checked')!='true':raise ValueError('Selected answer readback mismatch')
   if q.evaluate(PROBABILITY_DOM)!=data:raise ValueError('Question changed')
   row['input_verify_seconds']=time.perf_counter()-t;signature=q.inner_text().strip();t=time.perf_counter();check_submit(start,max_seconds);b.one('submit').click();row['submission_seconds']=time.perf_counter()-t;seen.add(key);out['rows'].append(row);save()
   t=time.perf_counter();score=b.page.evaluate(WAIT,[b.config['question'],b.config['score'],signature,score,15000]);row.update(score_after=score,feedback_seconds=time.perf_counter()-t,positive_progress=score>row['score_before']);out['final_score']=score;save();print(json.dumps({'before':row['score_before'],'after':score,'answer':solution['answer']}),flush=True)
   if not row['positive_progress']:out['outcome']='Negative result; paused immediately';save();return
  out['target_verified']=(score>target if strict else score>=target);out['outcome']='Target reached; browser kept open' if (score>target if strict else score>=target) else 'Time budget ended; paused'
  b.page.locator(b.config['score']).screenshot(path=str(root/'final-score.png'));save();print(json.dumps({'outcome':out['outcome'],'starting_score':out['starting_score'],'final_score':score,'questions':len(out['rows']),'elapsed_practice_seconds':out['elapsed_practice_seconds']}),flush=True)
 except Exception as e:out.update(error=type(e).__name__+': '+str(e),outcome='Paused; browser kept open');save();print(json.dumps(out,indent=2),flush=True)
