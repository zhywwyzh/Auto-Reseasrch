#!/usr/bin/env python3
"""Fetch source-reading checkouts; never install or run upstream code.

Run without flags to regenerate index.html from sources.json.
Use --fetch to restore missing checkouts at their recorded commits, or record
the upstream HEAD on the first download. Existing checkouts are not updated.
Untracked files, model weights, data archives and submodules are not fetched.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'sources.json'


def git(*args):
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE='1', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', *map(str, args)], env=env, text=True,
                            capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-900:])
    return result.stdout.strip()


def acquire(project):
    p = dict(project)
    folder = ROOT / 'upstream' / p['id']
    try:
        if folder.exists():
            if not (folder / '.git').is_dir():
                raise RuntimeError('目标已存在且非独立 Git 副本，未修改')
            remote = git('-C', folder, 'remote', 'get-url', 'origin')
            if remote.casefold().removesuffix('.git') != p['repository'].casefold().removesuffix('.git'):
                raise RuntimeError('现有副本来源不匹配，未修改')
        else:
            folder.parent.mkdir(parents=True, exist_ok=True)
            git('clone', '--depth=1', '--filter=blob:none', '--no-checkout',
                p['repository'], folder)
            git('-C', folder, 'sparse-checkout', 'set', '--no-cone', '/*',
                '!/data/', '!/datasets/', '!/checkpoints/', '!/model_weights/')
            if p.get('commit'):
                git('-C', folder, 'fetch', '--depth=1', 'origin', p['commit'])
                git('-C', folder, 'checkout', '--detach', p['commit'])
            else:
                git('-C', folder, 'checkout', '--detach', 'HEAD')
        actual = git('-C', folder, 'rev-parse', 'HEAD')
        if p.get('commit') and actual != p['commit']:
            raise RuntimeError('现有副本与记录版本不同，未更新版本记录')
        p.update(commit=actual, status='downloaded', local_directory='upstream/' + p['id'])
        p.pop('error', None)
        p['license_files'] = sorted(x.name for x in folder.iterdir()
                                    if x.is_file() and x.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE')))
    except Exception as e:
        p.update(status='failed', error=str(e))
    return p


def render(data):
    e = lambda value: html.escape(str(value), quote=True)
    rows = []
    for p in data['projects']:
        local = p.get('local_directory')
        name = f'<a href="{e(local)}/">{e(p["name"])}</a>' if local else e(p['name'])
        rows.append('<tr>' + ''.join(f'<td>{v}</td>' for v in [
            name, e(p['kind']), e(p.get('status', 'pending')),
            e(p.get('commit') or '未下载'), e(p['license_note']),
            f'<a href="{e(p["repository"].removesuffix(".git"))}">官方仓库</a>'
        ]) + '</tr>')
    not_cloned = ''.join(f'<li><b>{e(x["name"])}</b>：{e(x["reason"])}</li>' for x in data['not_cloned'])
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>论文评价 AI 方案库</title><style>
body{max-width:1300px;margin:36px auto;padding:0 24px;font:16px/1.8 system-ui,sans-serif;color:#263a31;background:#f7f8f5}h1{font-size:28px}h2{font-size:22px;margin-top:32px}a{color:#21684c}table{border-collapse:collapse;width:100%;background:white;font-size:14px}th,td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #d8dfda}td:nth-child(4){font-family:monospace;overflow-wrap:anywhere;max-width:190px}.scroll{overflow:auto}.note{padding:18px;background:#e8f0e9}code{overflow-wrap:anywhere}small{color:#57675f}</style></head><body><small>归档日期：''' + e(data['collected_on']) + '''</small><h1>论文评价 AI 方案库</h1><p>''' + e(data['purpose']) + '''</p><p><a href="../docs/research/ai-paper-review/index.html">完整检索报告与写作建议</a> · <a href="../thesis-reference/related-papers/ai-paper-review/index.html">本地论文目录（从本地文件打开）</a> · <a href="sources.json">来源与固定版本</a></p><div class="note"><b>目录规则</b><br>''' + e(data['checkout_policy']) + '''<br>本页、清单及收集脚本可以由 Git 跟踪；论文原文和上游副本不上传。公开源码与权重、开源许可范围分别记录。</div><h2>已收纳来源</h2><div class="scroll"><table><thead><tr><th>方案 / 本地副本</th><th>类别</th><th>下载状态</th><th>Git commit</th><th>许可证说明</th><th>来源</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div><h2>恢复与使用边界</h2><p>重新克隆本仓库后，可运行 <code>python3 paper-review-ai/fetch_sources.py --fetch</code> 恢复记录版本的阅读副本。普通运行仅重建本页。现有副本不会被自动更新或重置。</p><p>尚未安装依赖、下载独立模型权重、执行研究实验或付费评审；源码下载不是效果复现。</p><h2>只保存论文 / 报告、未归类为已开源实现</h2><ul>''' + not_cloned + '''</ul></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    data = json.loads(MANIFEST.read_text())
    failed = False
    if args.fetch:
        by_id = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            jobs = [pool.submit(acquire, p) for p in data['projects']]
            for future in as_completed(jobs):
                p = future.result()
                by_id[p['id']] = p
                print(p['id'], p['status'], p.get('error', p.get('commit')), flush=True)
                failed |= p['status'] != 'downloaded'
        data['projects'] = [by_id[p['id']] for p in data['projects']]
        MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'index.html').write_text(render(data), encoding='utf-8')
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
