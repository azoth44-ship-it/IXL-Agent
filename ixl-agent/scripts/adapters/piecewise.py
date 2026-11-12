from pathlib import Path
def check_submit(start,budget):
 if Path('STOP').exists():raise RuntimeError('Canceled before submission')
 if time.perf_counter()-start>=budget:raise TimeoutError('Practice deadline reached before submission')

import json,time
from ixl_agent.piecewise import solve_continuity,PIECEWISE_DOM

WAIT=r'''async ([qsel,ssel,old,previous,timeout])=>{
 const start=performance.now();let last=null,since=start;
 const visible=e=>{if(!e?.getClientRects().length)return false;for(let p=e;p;p=p.parentElement){const s=getComputedStyle(p);if(s.visibility==='hidden'||Number(s.opacity)===0)return false;}return true;};
 while(performance.now()-start<timeout){
  await new Promise(requestAnimationFrame);
  const q=document.querySelector(qsel),score=document.querySelector(ssel),raw=score?.innerText.trim();
  const value=/^\d{1,3}$/.test(raw)?Number(raw):null;
  const signature=q?(q.querySelector('.secHdr')?.innerText+'|'+q.querySelector('.piecewise-expressions-table')?.innerText):'';
  const ready=visible(score)&&value!==null&&value<=100&&value!==previous&&(value<previous||(visible(q)&&signature!==old));
  if(!ready){last=null;since=performance.now();continue;}
  if(last!==value){last=value;since=performance.now();}
  else if(performance.now()-since>=300)return value;
 }
 throw new Error('Feedback unknown; paused without another submission');
}'''

def run(b,target=90,strict=False,max_seconds=180):
 root=Path('reports/piecewise');root.mkdir(parents=True,exist_ok=True)
 out={'target':target,'rows':[],'browser_restarts':0};start=time.perf_counter();seen=set()
 def save():
  out['elapsed_practice_seconds']=time.perf_counter()-start
  (root/'result.json').write_text(json.dumps(out,indent=2))
 try:
  score=b.score();out['starting_score']=score
  if score is None:raise ValueError('Score unknown')
  while not (score>target if strict else score>=target) and time.perf_counter()-start<max_seconds:
   if Path('STOP').exists():
    out['outcome']='Paused by user';save();return
   b.page.locator(b.config['question']).wait_for(state='visible',timeout=15000)
   row={'score_before':score};t=time.perf_counter();q=b.one('question');data=q.evaluate(PIECEWISE_DOM)
   row.update(question=data,extraction_seconds=time.perf_counter()-t);key=json.dumps(data,sort_keys=True)
   if key in seen:raise ValueError('Question not changed; stopped to prevent duplicate submission')
   t=time.perf_counter();solution=solve_continuity(data);row.update(solution=solution,reasoning_verification_seconds=time.perf_counter()-t)
   field=q.locator('input.fillIn')
   if field.count()!=1 or not field.is_visible():raise ValueError('Expected one visible value-list input')
   t=time.perf_counter();field.fill(solution['answer'])
   if field.input_value()!=solution['answer']:raise ValueError('Answer readback mismatch')
   if q.evaluate(PIECEWISE_DOM)!=data:raise ValueError('Question changed before submission')
   signature=q.evaluate("q=>q.querySelector('.secHdr').innerText+'|'+q.querySelector('.piecewise-expressions-table').innerText")
   row['input_readback_seconds']=time.perf_counter()-t
   t=time.perf_counter();check_submit(start,max_seconds);b.one('submit').click();row['submission_seconds']=time.perf_counter()-t;seen.add(key);out['rows'].append(row);save()
   t=time.perf_counter();score=b.page.evaluate(WAIT,[b.config['question'],b.config['score'],signature,score,15000]);row.update(feedback_seconds=time.perf_counter()-t,score_after=score,positive_progress=score>row['score_before'])
   print(json.dumps({'before':row['score_before'],'after':score,'answer':solution['answer']}),flush=True);out['final_score']=score;save()
   if not row['positive_progress']:
    out['outcome']='Negative platform result; paused immediately';save();return
  out['target_verified']=(score>target if strict else score>=target);out['outcome']='Target reached; browser kept open' if (score>target if strict else score>=target) else 'Time budget ended; paused'
  b.page.locator(b.config['score']).screenshot(path=str(root/'final-score.png'))
  save()
  print(json.dumps(out,indent=2),flush=True)
 except Exception as e:
  out.update(error=type(e).__name__+': '+str(e),outcome='Paused; browser kept open');save();print(json.dumps(out,indent=2),flush=True)
