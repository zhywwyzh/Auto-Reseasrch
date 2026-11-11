"""Render the curated acceptance evidence; does not execute any experiment."""
import hashlib
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = (HERE / 'result-summary.json').read_bytes()
data = json.loads(raw)
escape = lambda x: html.escape(str(x))
last = data['runs'][-1]['result']
names = {
    'observation_shape': '观察尺寸80×80×3', 'two_players_25_actions': '两架无人机，每架25个动作',
    'environment_80_steps_finite': '80步环境输出、奖励、能量及数据量检查',
    'absolute_collection_jain_matches': '绝对采集量Jain公式与代码值一致（一次非零状态）',
    'environment_rng_disk_restore': 'Python环境与NumPy随机流落盘重放',
    'trainable_parameters_changed': '梯度更新确实改变网络参数',
    'all_global_variables_restored': '154个全局变量在新会话恢复一致',
    'fixed_batch_update_replayed': '同批次下一更新重放一致',
    'loss_log_finite': '各次更新损失有限', 'budget_exact': '生成、接纳、更新计数符合限定预算'}
checks = ''.join('<li><strong>'+escape(names.get(k,k))+'</strong>：'+
                 ('通过' if v['passed'] else '未通过/未完成')+
                 ('<small>'+escape(json.dumps(v['detail'],ensure_ascii=False))+'</small>' if v['detail'] is not None else '')+'</li>'
                 for k,v in last['checks'].items())
runs = ''.join('<tr><td>'+escape(r['run_id'])+'</td><td>'+escape(r['result']['status'])+
               '</td><td>'+format(r['manifest_wall_seconds'],'.2f')+'</td><td>'+format(r['result']['process_peak_rss_mib'],'.1f')+
               '</td><td>'+str(r['result']['environment_steps'])+'</td><td>'+str(r['result']['optimizer_calls'])+'</td></tr>' for r in data['runs'])
page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="source-sha256" content="HASH"><title>UCS-GenRL · 本机最小验证</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f6f2;color:#22332e;font:16px/1.8 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:32px 24px}a{color:#1c6853}nav{display:flex;gap:18px;flex-wrap:wrap;border-bottom:1px solid #d8e1da;padding:12px 0}section{padding:25px 0;border-bottom:1px solid #d8e1da}h1{font-size:30px}h2{font-size:23px}.notice{background:#e8f0e9;padding:18px;border-left:3px solid #1c6853}.facts{display:flex;gap:30px;flex-wrap:wrap}.facts strong{display:block;font-size:26px}small{display:block;color:#5b6a64;overflow-wrap:anywhere}li{margin:10px 0}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:10px;border-bottom:1px solid #d8e1da}.scroll{overflow:auto}code{overflow-wrap:anywhere}summary{cursor:pointer}button{padding:6px 14px;background:white;border:1px solid #d8e1da;color:#1c6853}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #b57b27}@media(max-width:600px){main{padding:20px 16px}h1{font-size:25px}}@media print{nav,button{display:none}body{background:white}main{max-width:none;padding:0}}
</style><main><a href="index.html">返回研究工作区</a><h1>本机最小验证：运行链路通过，正式实验仍有前置问题</h1>
<p>TR-001 · 2026-11-11 · 已执行的有界CPU测试。来源是候选开源代码，不是学位论文数值复现。</p>
<nav><a href="#result">结果</a><a href="#checks">验收</a><a href="#findings">发现</a><a href="#scope">边界与迁移</a><a href="#evidence">证据</a><button onclick="window.print()">打印</button></nav>
<section id="result"><h2>最小到可以先用CPU排查</h2><div class="notice">固定原候选环境与学习器；只缩减采样并发和批量。每次160次环境转移、5次梯度更新。没有执行课程优化、算法对照、LLM调用或服务器训练。</div>
<div class="facts"><p><strong>2核 / 3GiB</strong>容器资源上限</p><p><strong>RSS MiB</strong>最后一次Python进程峰值</p><p><strong>WALL 秒</strong>最后一次容器启动至退出</p><p><strong>0 GPU</strong>无GPU分配</p></div>
<p>原网络可训练参数 PARAMS 个。batch=1、unroll=20，60条新训练转移用于3次更新；另2次用同一固定批次验证恢复，接纳样本共100。80次随机环境检查与20次环境恢复重放计入160次总生成数。两种计数不相加。</p>
<div class="scroll"><table><thead><tr><th>运行记录（UTC）</th><th>状态</th><th>墙钟/秒</th><th>峰值RSS/MiB</th><th>转移</th><th>更新</th></tr></thead><tbody>RUNS</tbody></table></div>
<small>耗时不含下载、依赖安装和镜像构建。RSS是单Python进程峰值，不是整机或容器总峰值；未测GPU显存。全部运行均保留，没有按结果择优。第二轮用于依赖冻结及逐次非有限值停止检查后的验收，不是统计独立复验。</small></section>
<section id="checks"><h2>已通过的有限验收</h2><ul>CHECKS</ul><p>最后一次固定批次重放的最大绝对变量差为 ERROR；只证明本次CPU、固定数据和新会话条件下的恢复一致。</p></section>
<section id="findings"><h2>两个从静态疑点变成实际观察的问题</h2><ol><li><strong>重置后的指标非有限。</strong>尚未采集且没有能耗时，原代码的collection_fairness和efficiency出现未定义值。本轮仅记录，不把它们填成0、不改奖励。正式评价器需明确何时指标有定义及如何记录未定义状态。</li><li><strong>global_step不是环境交互计数。</strong>接纳20个样本时计数依次21、42、63；梯度更新与样本累加共用变量。正式实验需要独立账本，同时审查修正对学习率的影响。</li></ol>
<p>最初两次镜像构建失败：Gym/TFP的cloudpickle版本冲突，以及dm-tree源码构建缺少CMake。改用兼容Gym及dm-tree预编译版本后成功；这两次构建没有环境交互或梯度更新。</p></section>
<section id="scope"><h2>这次验证能支持怎样的迁移决定</h2><p><strong>可以准备服务器运行环境与下一阶段验收；尚不能直接认定正式实验已就绪。</strong>本机证明候选环境、原学习器的更新及有限恢复检查能在小资源下运行。</p>
<ul><li>继承原ResNetLSTM、V-trace、归一化、pixel control、RMSProp；原始源码只读且未修改。</li><li>同步单环境替代异步actor队列；batch从32降到1；动作按原logits分类分布使用NumPy RNG，不使用TensorFlow原采样随机流。学习率时域沿用候选源码75M。</li><li>环境为原开源配置16×16、E₀=30等，未强行改成学位原文。η、奖励、配置和评价口径对齐仍待处理。</li><li>环境/RNG与学习器变量分开验收，没有证明跨进程完整训练快照、异步队列或TF随机算子恢复。</li><li>服务器需要重新检查GPU依赖、batch32峰值、actor供数与队列、计数及完整快照；这里的CPU耗时不能用于推算正式GPU训练时长。</li></ul><p>当前停止在小规模验收。R1-P、B-CF与完整论文训练等待用户后续指令。</p></section>
<section id="evidence"><h2>可审查与可重跑的材料</h2><p><a href="validation/result-summary.json">结构化结果</a> · <a href="validation/protocol.json">执行合同</a> · <a href="validation/README.md">复跑说明</a> · <a href="validation/run_cpu_smoke.py">验收脚本</a> · <a href="validation/Dockerfile">容器定义</a></p>
<p>源码固定提交 <code>780e0b41d3fff54c8fa5ea0335979b3f1ec1f225</code>。原始结果、日志和检查点位于本课题被Git忽略的runs目录；结构化摘要保存源码/脚本哈希、镜像ID和全部运行记账。</p>
<details><summary>环境与来源</summary><p>TensorFlow1.15.5、Sonnet1.35、TFP0.8.0、Gym0.12.5、NumPy1.18.5。基础镜像digest固定、间接依赖版本冻结；没有对所有包另行归档wheel哈希。</p><p><a href="https://github.com/BIT-MCS/DRL-MTVCS">原代码</a> · <a href="https://www.tensorflow.org/install/docker">TensorFlow官方容器说明</a></p></details></section></main></html>'''
replacements = {'HASH': hashlib.sha256(raw).hexdigest(), 'RSS': format(last['process_peak_rss_mib'], '.1f'),
                'WALL': format(data['runs'][-1]['manifest_wall_seconds'], '.2f'), 'PARAMS': format(last['parameter_count'], ','),
                'RUNS': runs, 'CHECKS': checks, 'ERROR': escape(last['checks']['fixed_batch_update_replayed']['detail']['max_abs_error'])}
# Replace longer placeholders first; avoid rewriting the literal metric label RSS elsewhere.
page = page.replace('<strong>RSS MiB</strong>', '<strong>'+replacements.pop('RSS')+' MiB</strong>')
for key, value in replacements.items():
    page = page.replace(key, value)
(HERE.parent / 'local-validation.html').write_text(page)
