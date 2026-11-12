"""Persistent local IXL practice host. No model service or credentials are bundled."""
import argparse,importlib,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'));sys.path.insert(0,str(HERE/'adapters'))
from ixl_agent.browser import IXLBrowser
MODES={
 '/math/algebra-2/identify-probability-distributions':'probability',
 '/math/calculus/chain-rule':'chain',
 '/math/calculus/make-a-piecewise-function-continuous':'piecewise',
}
def valid_url(url):
 from urllib.parse import urlparse
 p=urlparse(url)
 if p.scheme!='https' or not(p.hostname=='ixl.com' or (p.hostname or '').endswith('.ixl.com')):raise ValueError('Use a public HTTPS IXL practice URL')
 if p.username or p.password:raise ValueError('Credentials must not appear in a URL')
 return p

def validate_practice(command,url):
 if command.get('submission_authorized') is not True or command.get('permitted_practice') is not True:raise ValueError('Explicit permitted-practice submission authorization required')
 mode=MODES.get(valid_url(url).path.rstrip('/'))
 if mode is None:raise ValueError('Unsupported skill format: inspect and prepare an adapter first')
 target=command.get('target_score');strict=command.get('strict',False);budget=command.get('max_seconds',180)
 if type(target) is not int or not 0<=target<=100 or (strict and target==100):raise ValueError('Invalid SmartScore target')
 if type(strict) is not bool or type(budget) not in (int,float) or not 0<budget<=3600:raise ValueError('Invalid comparison or time budget')
 return mode,target,strict,budget

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workspace',required=True);parser.add_argument('--url',required=True);parser.add_argument('--profile');parser.add_argument('--channel',default='chrome');parser.add_argument('--headless',action='store_true');args=parser.parse_args()
 valid_url(args.url)
 work=Path(args.workspace).resolve();work.mkdir(parents=True,exist_ok=True);os.chdir(work)
 cfg={'url':args.url,'profile':str(Path(args.profile).resolve()) if args.profile else str(work/'browser-profile'),'channel':args.channel,'question':'.question-component .ixl-practice-crate','score':'[data-cy=current-smartscore] .smartscore-text','input':'.question-component input.proxy-input','choices':'[role=radio]','submit':'.question-component button:has-text("Submit")','feedback':'.feedback','complete':'.practice-complete','codex':False}
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
     print(json.dumps({'url':browser.page.url,'score':browser.score(),'question':browser.one('question').inner_text()},ensure_ascii=False),flush=True)
    elif action=='pause':(work/'STOP').touch();print('{"status":"paused"}',flush=True)
    elif action=='practice':
     mode,target,strict,budget=validate_practice(command,browser.page.url)
     if (work/'STOP').exists():
      if command.get('resume') is not True:raise RuntimeError('STOP is set; explicit user resume required')
      (work/'STOP').unlink()
     adapter=importlib.import_module(mode);adapter.run(browser,target=target,strict=strict,max_seconds=budget)
    else:raise ValueError('Unknown host action')
   except Exception as exc:print(json.dumps({'error':type(exc).__name__+': '+str(exc),'browser_kept_open':True}),flush=True)
 finally:browser.close()
if __name__=='__main__':main()
