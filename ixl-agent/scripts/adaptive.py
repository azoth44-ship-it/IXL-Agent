"""Shared submission loop for question formats prepared in the workspace."""
import hashlib
import json
from time import perf_counter
from urllib.parse import urlsplit


class UnconfirmedSubmission(RuntimeError):
    pass


def reached(score, target, strict):
    return score > target if strict else score >= target


def pending_submission(work, url):
    return pending_path(work, url).exists()


def pending_path(work, url):
    path = urlsplit(url).path.rstrip('/')
    key = hashlib.sha256(path.encode()).hexdigest()
    return work / 'reports' / 'adaptive' / key / 'pending.json'


def prepare(browser, adapter):
    question = browser.one('question')
    data = adapter.extract(question)
    answer = adapter.solve(data)
    if adapter.verify(data, answer) is not True:
        raise ValueError('Independent mathematical check failed')
    adapter.fill(question, answer)
    actual = adapter.read(question)
    if adapter.equivalent(data, answer, actual) is not True:
        raise ValueError('Editor readback does not match the verified answer')
    if adapter.extract(browser.one('question')) != data:
        raise ValueError('Question changed during input verification')
    return data, answer, actual


def review_submission(browser, work):
    pending = pending_path(work, browser.page.url)
    if not pending.exists():
        raise ValueError('No pending adaptive submission')
    record = json.loads(pending.read_text(encoding='utf-8'))
    if record.get('incorrect'):
        raise UnconfirmedSubmission('Incorrect feedback was recorded; remain paused')
    browser._submitted_text = record['header']
    correct = browser.wait_result(record['before'], timeout=5000)
    score = browser.last_result_score
    if correct is not True or score is None or score <= record['before']:
        raise UnconfirmedSubmission('The earlier answer has no confirmed positive result')
    pending.unlink()
    return {'status': 'submission_confirmed', 'score': score, 'submitted': 0}


def run_local(browser, adapter, work, target, strict, budget):
    url = browser.page.url
    pending = pending_path(work, url)
    root = pending.parent
    root.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    score = browser.score()
    report = {'url': url, 'starting_score': score, 'target': target, 'strict': strict, 'rows': []}
    seen = set()

    def save():
        report.update(elapsed_seconds=perf_counter() - start, final_score=score)
        (root / 'result.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding='utf-8')

    try:
        if pending.exists():
            raise UnconfirmedSubmission('Review the previous submission before retrying')
        if score is None:
            raise ValueError('SmartScore is unreadable')
        while not reached(score, target, strict):
            if (work / 'STOP').exists() or perf_counter() - start >= budget:
                report['status'] = 'paused'
                return report
            before = perf_counter()
            data, answer, actual = prepare(browser, adapter)
            identity = json.dumps(data, sort_keys=True, ensure_ascii=False)
            if identity in seen or browser.page.url != url or browser.score() != score:
                raise ValueError('Question, URL or score no longer matches the active attempt')
            question = browser.one('question')
            header = question.locator('.secHdr')
            browser._submitted_text = (header.inner_text() if header.count() == 1 else question.inner_text()).strip()
            submit = browser.one('submit')
            if (work / 'STOP').exists() or perf_counter() - start >= budget:
                report['status'] = 'paused'
                return report
            row = {'question': data, 'answer': str(answer), 'readback': str(actual),
                   'before': score, 'prepare_seconds': perf_counter() - before}
            report['rows'].append(row)
            record = {'before': score, 'header': browser._submitted_text}
            pending.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
            submitted = perf_counter()
            submit.click()
            result = browser.wait_result(score, timeout=15000)
            after = browser.last_result_score
            row.update(after=after, feedback_seconds=perf_counter() - submitted)
            if after is not None:
                row['score_changed'] = after != score
            if result is not True or after is None or after <= score:
                report['status'] = 'incorrect' if result is False or (after is not None and after < score) else 'unknown_feedback'
                if report['status'] == 'incorrect':
                    record['incorrect'] = True
                    pending.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
                score = after
                return report
            score = after
            seen.add(identity)
            save()
            pending.unlink()
        report['status'] = 'target_reached'
        browser.one('score').screenshot(path=str(root / 'final-score.png'))
        return report
    except Exception as exc:
        report.update(status='unknown_feedback' if pending.exists() else 'pre_submit_blocked',
                      error=f'{type(exc).__name__}: {exc}')
        return report
    finally:
        save()
