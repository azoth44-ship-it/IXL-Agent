import importlib,json,sys,io
from pathlib import Path
import pytest
import session

URLS={v:'https://www.ixl.com'+k for k,v in session.MODES.items()}
@pytest.mark.parametrize('url',['https://ixl.com.evil.example/math','http://www.ixl.com/math','https://user:pass@www.ixl.com/math'])
def test_reject_nonpublic_ixl(url):
 with pytest.raises(ValueError):session.valid_url(url)

def test_submission_authorization():
 with pytest.raises(ValueError):session.validate_practice({'target_score':90},URLS['probability'])
 with pytest.raises(ValueError):session.validate_practice({'target_score':90,'submission_authorized':True,'permitted_practice':True},'https://www.ixl.com/math/calculus/unknown')

def test_target_comparison():
 command={'target_score':80,'strict':True,'submission_authorized':True,'permitted_practice':True}
 assert session.validate_practice(command,URLS['chain'])[1:3]==(80,True)
 command['target_score']=100
 with pytest.raises(ValueError):session.validate_practice(command,URLS['chain'])

class Locator:
 def screenshot(self,path):Path(path).write_bytes(b'local-test-placeholder')
class Page:
 def __init__(self,url):self.url=url
 def locator(self,_):return Locator()
class Browser:
 def __init__(self,mode,score):self.page=Page(URLS[mode]);self.config={'score':'#score'};self.value=score
 def score(self):return self.value

@pytest.mark.parametrize('mode',['chain','probability','piecewise'])
def test_reached_goal_never_submits(mode,tmp_path,monkeypatch):
 monkeypatch.chdir(tmp_path);adapter=importlib.import_module(mode)
 adapter.run(Browser(mode,91),target=90,strict=True,max_seconds=1)
 result=json.loads((tmp_path/'reports'/mode/'result.json').read_text())
 assert result['target_verified'] is True and result['rows']==[]

@pytest.mark.parametrize('mode',['chain','probability','piecewise'])
def test_cancellation_blocks_pending_submission(mode,tmp_path,monkeypatch):
 monkeypatch.chdir(tmp_path);(tmp_path/'STOP').touch();adapter=importlib.import_module(mode)
 adapter.run(Browser(mode,20),target=90,max_seconds=1)
 result=json.loads((tmp_path/'reports'/mode/'result.json').read_text())
 assert result['outcome']=='Paused by user' and result['rows']==[]


def test_host_reuses_browser_and_does_not_submit_on_packaging(tmp_path,monkeypatch):
 counts={'start':0,'close':0}
 class HostBrowser:
  def __init__(self,cfg):self.page=Page(cfg['url'])
  def start(self,**kwargs):counts['start']+=1
  def close(self):counts['close']+=1
 monkeypatch.setattr(session,'IXLBrowser',HostBrowser)
 monkeypatch.setattr(sys,'argv',['session.py','--workspace',str(tmp_path),'--url',URLS['probability']])
 monkeypatch.setattr(sys,'stdin',io.StringIO('{"action":"practice","target_score":90}\n{"action":"close"}\n'))
 monkeypatch.chdir(tmp_path)
 session.main()
 assert counts=={'start':1,'close':1}
