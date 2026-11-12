import json,importlib
import pytest
from ixl_agent.browser import IXLBrowser
from test_host_contract import URLS

@pytest.mark.parametrize('mode',['probability','chain','piecewise'])
def test_portable_adapter_local_submission(mode,tmp_path,monkeypatch):
 monkeypatch.chdir(tmp_path)
 config={'profile':str(tmp_path/'profile'),'url':'about:blank','question':'#question','score':'#score','input':'#answer','choices':'[role=radio]','submit':'#submit','feedback':'#feedback','complete':'#complete'}
 b=IXLBrowser(config)
 try:
  b.start(headless=True);page=b.page
  if mode=='probability':
   content='''<div class="secHdr">Does the table show the values of a valid probability function on the outcomes in a sample space?</div><table class="qTable"><tr class="colHeader"><td>Probability</td></tr><tr class="dataRow"><td>0.4</td></tr><tr class="dataRow"><td>0.6</td></tr></table><div role="radio" aria-label="yes" aria-checked="false" onclick="this.setAttribute('aria-checked','true')">yes</div><div role="radio" aria-label="no" aria-checked="false">no</div>'''
  elif mode=='chain':
   content='''<div class="secHdr">Values of f(x), g(x), and their derivatives are given in the tables below.</div><table class="qTable"><tr class="colHeader"><td>x</td><td>f(x)</td><td>f′(x)</td></tr><tr class="dataRow"><td>0</td><td>1</td><td>2</td></tr></table><table class="qTable"><tr class="colHeader"><td>x</td><td>g(x)</td><td>g′(x)</td></tr><tr class="dataRow"><td>1</td><td>3</td><td>4</td></tr></table><div class="secHdr">Find (g∘f)′(0).</div><input class="fillIn" id="answer">'''
  else:
   content='''<div class="secHdr">Find all values of k that make f(x) continuous at x=0.</div><table class="piecewise-expressions-table"><tr><td class="piecewise-expression">k</td><td class="piecewise-condition">if x≤0</td></tr><tr><td class="piecewise-expression">x+1</td><td class="piecewise-condition">if x&gt;0</td></tr></table><input class="fillIn" id="answer">'''
  page.set_content('<span id="score">0</span><div id="question">'+content+'</div><button id="submit">Submit</button><div id="feedback"></div><div id="complete" hidden></div><script>window.count=0;document.querySelector("#submit").onclick=()=>{window.count++;document.querySelector("#score").textContent="90";document.querySelector("#question td").textContent="new";};</script>')
  class PageFacade:
   url=URLS[mode]
   def __getattr__(self,name):return getattr(page,name)
  b.page=PageFacade()
  adapter=importlib.import_module(mode);adapter.run(b,target=90,max_seconds=5)
  result=json.loads((tmp_path/'reports'/mode/'result.json').read_text())
  assert result['target_verified'] is True
  assert result['final_score']==90 and len(result['rows'])==1
  assert page.evaluate('window.count')==1
  assert not page.is_closed()
 finally:b.close()
