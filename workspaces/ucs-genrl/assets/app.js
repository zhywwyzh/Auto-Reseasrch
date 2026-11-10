'use strict';
const pages = [...document.querySelectorAll('.page')];
const navLinks = [...document.querySelectorAll('nav a')];
function showPage() {
  const requested = location.hash.slice(1);
  const selected = pages.some(p => p.id === requested) ? requested : 'overview';
  pages.forEach(p => { p.hidden = p.id !== selected; });
  navLinks.forEach(a => {
    if (a.hash === '#' + selected) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  document.title = document.getElementById(selected).querySelector('h1').textContent.replace(/\s+/g, ' ') + ' · UCS-GenRL';
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', showPage);
showPage();
document.getElementById('print').addEventListener('click', () => window.print());
function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
const data = window.RESEARCH_DESIGN;
function renderExperiments() {
  const list = document.getElementById('experiment-list');
  const filter = document.getElementById('experiment-filter').value;
  list.replaceChildren();
  data.experiments.filter(x => filter === '全部' || x.stage === filter).forEach(x => {
    const article = el('article', undefined, 'experiment');
    const header = el('div', undefined, 'exp-heading');
    header.append(el('h3', x.id + ' · ' + x.title), el('span', x.stage, 'tag'));
    const dl = el('dl');
    [['研究判断', x.claim], ['对照设计', x.control], ['观察指标', x.measure], ['可推翻条件', x.failure], ['预算边界', x.budget]].forEach(([k,v]) => dl.append(el('dt', k), el('dd', v)));
    article.append(header, dl); list.append(article);
  });
}
document.getElementById('experiment-filter').addEventListener('change', renderExperiments);
renderExperiments();
const contracts = document.getElementById('contract-list');
data.contracts.forEach(x => {
  const detail = el('details');
  detail.append(el('summary', x.name + ' — ' + x.role));
  [['输入', x.input], ['输出', x.output], ['必须保持', x.invariant]].forEach(([k,v]) => {
    const p = el('p'); p.append(el('strong', k + '：'), document.createTextNode(v)); detail.append(p);
  });
  contracts.append(detail);
});
function readNumber(id) {
  const input = document.getElementById(id);
  if (input.value === '' || !input.checkValidity()) return NaN;
  return Number(input.value);
}
const countFormat = new Intl.NumberFormat('zh-CN');
function updateBound() {
  const k = readNumber('bound-k'), n = readNumber('bound-n');
  const delta = readNumber('bound-delta'), eps = readNumber('bound-eps');
  const out = document.getElementById('bound-radius'), needed = document.getElementById('bound-required');
  const message = document.getElementById('bound-message');
  if (![k,n,delta,eps].every(Number.isFinite) || !Number.isInteger(k) || !Number.isInteger(n)) {
    out.textContent = '—'; needed.textContent = '—'; message.textContent = '请输入范围内的数值；候选数和评价数须为整数。'; return;
  }
  const radius = Math.sqrt(2 * Math.log(2*k/delta)/n);
  out.textContent = radius.toFixed(3);
  needed.textContent = countFormat.format(Math.ceil(2*Math.log(2*k/delta)/(eps*eps)));
  message.textContent = radius >= 1 ? '当前界半径不小于最大可能改善1，无法据此确认正迁移；这不等于方法没有效果。' : '若要求真实改善至少τ，观察到的平均差需不小于τ+' + radius.toFixed(3) + '。这里只覆盖独立确认评价误差，不覆盖训练随机性与短长期漂移。';
}
['bound-k','bound-n','bound-delta','bound-eps'].forEach(id => document.getElementById(id).addEventListener('input', updateBound));
updateBound();
function updateBudget() {
  const methods=readNumber('budget-methods'), seeds=readNumber('budget-seeds'), steps=readNumber('budget-steps'), suites=readNumber('budget-suites');
  const valid=[methods,seeds,steps,suites].every(Number.isFinite) && [methods,seeds,suites].every(Number.isInteger);
  document.getElementById('budget-total').textContent=valid ? countFormat.format(Math.round(methods*seeds*steps*suites*1e6)) + ' 步' : '请输入有效数值';
  document.getElementById('budget-runs').textContent=valid ? countFormat.format(methods*seeds*suites) : '—';
}
['budget-methods','budget-seeds','budget-steps','budget-suites'].forEach(id => document.getElementById(id).addEventListener('input', updateBudget));
updateBudget();
const notes=document.getElementById('review-notes'), status=document.getElementById('note-status');
const storageKey='ucs-genrl-review-v1';
try { notes.value=localStorage.getItem(storageKey)||''; if(notes.value) status.textContent='已恢复当前浏览器保存的笔记；未写回仓库。'; }
catch { status.textContent='浏览器存储不可用；可编辑后下载，关闭页面前请导出。'; }
notes.addEventListener('input',()=>{
  try {localStorage.setItem(storageKey,notes.value);status.textContent='已保存到当前浏览器；未写回仓库。';}
  catch {status.textContent='本地自动保存不可用，请下载记录保留。';}
});
document.getElementById('download-notes').addEventListener('click',()=>{
  const record={workspace:'UCS-GenRL',document_version:'2026-11-10-draft-3',exported_at:new Date().toISOString(),status:'用户讨论笔记；不自动构成实施批准',notes:notes.value};
  const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)+'\n'],{type:'application/json;charset=utf-8'}));
  const a=el('a');a.href=url;a.download='ucs-genrl-review-notes.json';document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
