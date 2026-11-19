"""Persistent local IXL practice host. No model service or credentials are bundled."""
import argparse,importlib,importlib.util,json,os,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'));sys.path.insert(0,str(HERE/'adapters'))
from ixl_agent.browser import IXLBrowser
MODES={
 '/math/algebra-2/identify-probability-distributions':'probability',
 '/math/calculus/chain-rule':'chain',
 '/math/calculus/make-a-piecewise-function-continuous':'piecewise',
 '/math/calculus/find-tangent-lines-using-implicit-differentiation':'tangent',
}
ADAPTIVE_MODES={'tangent'}
def valid_url(url):
 from urllib.parse import urlparse
 p=urlparse(url)
 if p.scheme!='https' or not(p.hostname=='ixl.com' or (p.hostname or '').endswith('.ixl.com')):raise ValueError('Use a public HTTPS IXL practice URL')
 if p.username or p.password:raise ValueError('Credentials must not appear in a URL')
 return p

def validate_practice(command,url):
 if command.get('submission_authorized') is not True or command.get('permitted_practice') is not True:raise ValueError('Explicit permitted-practice submission authorization required')
 mode=MODES.get(valid_url(url).path.rstrip('/'))
 if mode is None and 'adapter' not in command:raise ValueError('Unsupported skill format: inspect and prepare an adapter first')
 target=command.get('target_score');strict=command.get('strict',False);budget=command.get('max_seconds',180)
 if type(target) is not int or not 0<=target<=100 or (strict and target==100):raise ValueError('Invalid SmartScore target')
 if type(strict) is not bool or type(budget) not in (int,float) or not 0<budget<=3600:raise ValueError('Invalid comparison or time budget')
 return mode,target,strict,budget

def load_local_adapter(work, name, url):
 if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]*',name):
  raise ValueError('Use a local adapter module name')
 root=(work/'local_adapters').resolve()
 path=(root/(name+'.py')).resolve()
 if root.parent!=work or path.parent!=root or not path.is_file():
  raise ValueError('Adapter must be in this workspace’s local_adapters directory')
 spec=importlib.util.spec_from_file_location('ixl_local_'+name,path)
 module=importlib.util.module_from_spec(spec)
 # Read current source, including fixes made while this host stays alive.
 exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
 if getattr(module,'SKILL_PATH',None)!=valid_url(url).path.rstrip('/'):
  raise ValueError('Adapter does not match the current IXL skill')
 return module

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workspace',required=True);parser.add_argument('--url',required=True);parser.add_argument('--profile');parser.add_argument('--channel',default='chrome');parser.add_argument('--headless',action='store_true');args=parser.parse_args()
 valid_url(args.url)
 profile=Path(args.profile).resolve() if args.profile else None
 work=Path(args.workspace).resolve();work.mkdir(parents=True,exist_ok=True);os.chdir(work)
 cfg={'url':args.url,'profile':str(profile or work/'browser-profile'),'channel':args.channel,'question':'.question-component .ixl-practice-crate','score':'[data-cy=current-smartscore] .smartscore-text','input':'.question-component input.proxy-input','choices':'[role=radio]','submit':'.question-component button:has-text("Submit")','feedback':'.feedback','complete':'.practice-complete','codex':False}
 browser=IXLBrowser(cfg)
 try:
  browser.start(headless=args.headless);print(json.dumps({'status':'ready','url':browser.page.url,'workspace':str(work)}),flush=True)
  for line in sys.stdin:
   try:
    command=json.loads(line);action=command.get('action')
    if action=='close':break
    if action=='navigate':
     valid_url(command['url']);browser.page.goto(command['url'],wait_until='domcontentloaded');print(json.dumps({'status':'navigated','url':browser.page.url}),flush=True)
    elif action=='inspect':
     q=browser.page.locator(cfg['question']);q.wait_for(state='visible',timeout=15000)
     question=browser.one('question')
     result={'status':'inspected','url':browser.page.url,'score':browser.score(),'question':question.inner_text(),'bundled_adapter':MODES.get(valid_url(browser.page.url).path.rstrip('/'))}
     if command.get('capture') is True:
      capture=work/'reports'/'current-question'
      capture.mkdir(parents=True,exist_ok=True)
      markup=question.evaluate("""root => {
        const clone=root.cloneNode(true);
        const copies=clone.querySelectorAll('*');
        [...root.querySelectorAll('*')].forEach((el,i)=>{
          const copy=copies[i];
          if(copy && !el.getClientRects().length) copy.setAttribute('data-ixl-no-layout','');
        });
        clone.querySelectorAll('script,iframe,object,embed').forEach(el=>el.remove());
        return clone.outerHTML;
      }""")
      (capture/'question.html').write_text(markup,encoding='utf-8')
      question.screenshot(path=str(capture/'question.png'))
      result['capture']=str(capture)
     print(json.dumps(result,ensure_ascii=False),flush=True)
    elif action=='pause':(work/'STOP').touch();print('{"status":"paused"}',flush=True)
    elif action=='practice':
     from adaptive import UnconfirmedSubmission, run_local, pending_submission, reached
     url=browser.page.url
     mode,target,strict,budget=validate_practice(command,url)
     if pending_submission(work,url):raise UnconfirmedSubmission('Review the previous submission before retrying')
     if (work/'STOP').exists():
      if command.get('resume') is not True:raise RuntimeError('STOP is set; explicit user resume required')
      (work/'STOP').unlink()
     score=browser.score()
     if score is not None and reached(score,target,strict):
      print(json.dumps({'status':'target_reached','score':score,'submitted':0}),flush=True)
     elif 'adapter' in command or mode in ADAPTIVE_MODES:
      adapter=load_local_adapter(work,command['adapter'],url) if 'adapter' in command else importlib.import_module(mode)
      print(json.dumps(run_local(browser,adapter,work,target,strict,budget)),flush=True)
     else:
      adapter=importlib.import_module(mode);adapter.run(browser,target=target,strict=strict,max_seconds=budget)
    elif action=='verify_input':
     from adaptive import prepare
     url=browser.page.url
     if 'adapter' in command:
      adapter=load_local_adapter(work,command['adapter'],url)
     else:
      mode=MODES.get(valid_url(url).path.rstrip('/'))
      if mode not in ADAPTIVE_MODES:raise ValueError('Specify a workspace adapter name')
      adapter=importlib.import_module(mode)
     if (work/'STOP').exists() and command.get('resume') is not True:
      raise RuntimeError('STOP is set; explicit user resume required')
     plan=prepare(browser,adapter)
     print(json.dumps({'status':'input_verified','answer':str(plan[1]),'submitted':0}),flush=True)
    elif action=='review_submission':
     from adaptive import review_submission
     print(json.dumps(review_submission(browser,work)),flush=True)
    else:raise ValueError('Unknown host action')
   except Exception as exc:print(json.dumps({'error':type(exc).__name__+': '+str(exc),'browser_kept_open':True}),flush=True)
 finally:browser.close()
if __name__=='__main__':main()
