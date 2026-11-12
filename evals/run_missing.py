"""Run only cases not yet scored and merge successful case reports.

Example:
  python evals/run_missing.py --report eval_before.json --output-dir eval_before_parts
  python evals/run_missing.py --report eval_after.json --output-dir eval_after_parts
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def refresh_summary(report):
    cases = report['cases']
    scores = [c['grade']['score'] for c in cases if c['grade'].get('score') is not None]
    complete = len(scores) == len(cases) and bool(cases)
    report['summary'] = {
        'total_cases': len(cases),
        'scored_cases': len(scores),
        'unscored_cases': len(cases) - len(scores),
        'score_0_100': round(sum(scores) / len(scores), 2) if complete else None,
        'partial_mean_0_100': round(sum(scores) / len(scores), 2) if scores and not complete else None,
    }


def main():
    parser = argparse.ArgumentParser(description='Chạy case còn thiếu, hợp nhất case đã chấm.')
    parser.add_argument('--report', required=True, help='eval_before.json hoặc eval_after.json')
    parser.add_argument('--output-dir', required=True, help='Thư mục chứa báo cáo từng case')
    parser.add_argument('--provider', default='openrouter')
    parser.add_argument('--model', default='dots-studio/dots-3-note-preview:free')
    parser.add_argument('--judge-model', default='dots-studio/dots-3-note-preview:free')
    parser.add_argument('--version', choices=['baseline', 'improved'], default='improved')
    args = parser.parse_args()

    report_path = ROOT / args.report
    parts_dir = ROOT / args.output_dir
    parts_dir.mkdir(parents=True, exist_ok=True)
    report = json.loads(report_path.read_text(encoding='utf-8'))
    cases = {case['id']: case for case in report['cases']}
    report.setdefault('config', {}).update({
        'provider': args.provider, 'model': args.model,
        'judge_provider': args.provider, 'judge_model': args.judge_model,
    })

    try:
        for case_id in list(cases):
            if cases[case_id]['grade'].get('score') is not None:
                continue
            part_path = parts_dir / f'{case_id}.json'
            usable_part = False
            if part_path.exists():
                try:
                    saved = json.loads(part_path.read_text(encoding='utf-8'))
                    usable_part = (saved['config'].get('provider') == args.provider and
                                   saved['config'].get('model') == args.model and
                                   saved['config'].get('judge_model') == args.judge_model and
                                   saved['cases'][0]['grade'].get('score') is not None)
                except (OSError, ValueError, KeyError, IndexError):
                    usable_part = False
            if not usable_part:
                temp_path = parts_dir / f'{case_id}.attempt.json'
                cmd = [sys.executable, str(ROOT / 'evals' / 'run_evals.py'),
                       '--provider', args.provider, '--model', args.model,
                       '--judge-provider', args.provider, '--judge-model', args.judge_model,
                       '--case', case_id, '--output', str(temp_path)]
                child_env = None
                if args.version == 'baseline':
                    child_env = os.environ.copy()
                    child_env['AGENT_BASELINE'] = '1'
                completed = subprocess.run(cmd, cwd=ROOT, env=child_env)
                if completed.returncode != 0:
                    try:
                        failed = json.loads(temp_path.read_text(encoding='utf-8'))['cases'][0]
                        reason = failed['result'].get('error') or failed['grade'].get('reason')
                    except (OSError, ValueError, KeyError, IndexError):
                        reason = 'Không đọc được chi tiết lỗi.'
                    print(f'Dừng tại {case_id}: {reason}. Sửa nguyên nhân rồi chạy lại.')
                    break
                temp_path.replace(part_path)
            try:
                part = json.loads(part_path.read_text(encoding='utf-8'))
                case_result = part['cases'][0]
                if case_result['grade'].get('score') is not None:
                    cases[case_id] = case_result
                    report['cases'] = [cases[k] for k in cases]
                    refresh_summary(report)
                    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                    print(f"Đã hợp nhất {case_id}: {case_result['grade']['score']}/100")
                else:
                    print(f'{case_id} chưa được chấm; dừng để tránh lặp lỗi/quota.')
                    break
            except (OSError, ValueError, KeyError, IndexError) as exc:
                print(f'Không đọc được kết quả {case_id}: {exc}')
                break
    finally:
        pass

    refresh_summary(report)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Tổng hợp:', report['summary'])


if __name__ == '__main__':
    main()
