from types import SimpleNamespace

import pytest

from adaptive import pending_submission, prepare, review_submission, run_local
from session import load_local_adapter


URL = 'https://www.ixl.com/math/calculus/new-format'


class Browser:
    def __init__(self):
        self.page = SimpleNamespace(url=URL)
        self.value = 79
        self.clicks = 0
        self.current = 'first question'
        self.field = ''
        self.timeout = False

    def score(self):
        return self.value

    def one(self, key):
        if key == 'submit':
            return SimpleNamespace(click=self.click)
        if key == 'score':
            return SimpleNamespace(screenshot=lambda **kwargs: None)
        return self

    def locator(self, _):
        return SimpleNamespace(count=lambda: 0)

    def inner_text(self):
        return self.current

    def click(self):
        self.clicks += 1

    def wait_result(self, before, timeout):
        if self.timeout:
            raise TimeoutError('Feedback still loading')
        self.last_result_score = self.value = before + 1
        self.current = f'question at {self.value}'
        return True


@pytest.fixture
def adapter(tmp_path):
    folder = tmp_path / 'local_adapters'
    folder.mkdir()
    (folder / 'fixture.py').write_text(
        "SKILL_PATH = '/math/calculus/new-format'\n"
        "def extract(q): return {'prompt': q.inner_text()}\n"
        "def solve(data): return 2 + 2\n"
        "def verify(data, answer): return answer - 2 == 2\n"
        "def fill(q, answer): q.field = str(answer)\n"
        "def read(q): return q.field\n"
        "def equivalent(data, answer, actual): return str(answer) == actual\n",
        encoding='utf-8',
    )
    return load_local_adapter(tmp_path, 'fixture', URL)


def test_verify_input_then_stop_above_goal(tmp_path, adapter):
    browser = Browser()
    assert prepare(browser, adapter)[2] == '4'
    assert browser.clicks == 0
    result = run_local(browser, adapter, tmp_path, 80, True, 5)
    assert result['status'] == 'target_reached'
    assert result['final_score'] == 81
    assert browser.clicks == 2


def test_readback_mismatch_blocks_submission(tmp_path, adapter):
    browser = Browser()
    adapter.read = lambda q: '5'
    result = run_local(browser, adapter, tmp_path, 90, False, 5)
    assert result['status'] == 'pre_submit_blocked'
    assert not pending_submission(tmp_path, URL)
    assert browser.clicks == 0


def test_delayed_feedback_requires_review_before_another_click(tmp_path, adapter):
    browser = Browser()
    browser.timeout = True
    result = run_local(browser, adapter, tmp_path, 80, False, 5)
    assert result['status'] == 'unknown_feedback'
    assert pending_submission(tmp_path, URL)
    run_local(browser, adapter, tmp_path, 80, False, 5)
    assert browser.clicks == 1
    browser.timeout = False
    assert review_submission(browser, tmp_path)['score'] == 80
    assert not pending_submission(tmp_path, URL)
    assert run_local(browser, adapter, tmp_path, 80, False, 5)['status'] == 'target_reached'
    assert browser.clicks == 1
