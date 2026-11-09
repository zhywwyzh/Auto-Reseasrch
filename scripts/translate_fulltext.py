#!/usr/bin/env python3
"""Local, resumable paragraph translation; no agent tools or external API calls."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'translations/fulltext'
MODEL=ROOT/'.cache/translation-model'
REVISION='9a341cd1b679d3efd23b46e847b01745a71ed792'
PROMPT_REVISION='academic-en-zh-v2'
CACHE=BASE/'translation-cache.jsonl'
ORDER=['autosurvey','openscholar','surveyforge','co-scientist','ai-scientist-v2','paperbench','astabench','epoch','autoresearch']

def pieces(text,limit=700):
    # Split long paragraphs only for inference; rejoin them under their original ID.
    sentences=re.split(r'(?<=[.!?;])\s+(?=[A-Z0-9\[])|\n',text)
    out=[];buf=''
    for sentence in sentences:
        if not sentence.strip():continue
        if len(sentence)>limit:
            words=sentence.split();parts=[];part=''
            for w in words:
                if len(part)+len(w)>limit and part:parts.append(part);part=''
                part=(part+' '+w).strip()
            if part:parts.append(part)
        else:parts=[sentence]
        for part in parts:
            if buf and len(buf)+len(part)+1>limit:out.append(buf);buf=''
            buf=(buf+' '+part).strip()
    if buf:out.append(buf)
    return out or [text]

def protect(s):
    values=[]
    def replace(m):
        values.append(m.group())
        return f' ZXQ{len(values)-1}QXZ '
    protected=re.sub(r'\$[^$]+\$|https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',replace,s)
    return protected,values

def restore(s,values):
    missing=[]
    for i,v in enumerate(values):
        pattern=rf'Z\s*X\s*Q\s*{i}\s*Q\s*X\s*Z'
        s,n=re.subn(pattern,lambda _:v,s,flags=re.I)
        if not n:missing.append(v)
    return s,missing

def key(s):return hashlib.sha256((REVISION+'\n'+PROMPT_REVISION+'\n'+s).encode()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0);parser.add_argument('--batch-size',type=int,default=16);parser.add_argument('--assemble-only',action='store_true')
    args=parser.parse_args();BASE.mkdir(parents=True,exist_ok=True)
    cache={}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            if line.strip():
                entry=json.loads(line);cache[entry['key']]=entry
    documents=[];queue=[]
    for slug in ORDER:
        data=json.loads((BASE/slug/'units.json').read_text())
        frontmatter=True
        titles={'autosurvey':'AutoSurvey：大语言模型能够自动撰写综述','openscholar':'OpenScholar：利用检索增强语言模型综合科学文献','surveyforge':'SurveyForge：自动综述写作中的大纲启发式、记忆驱动生成与多维评价','co-scientist':'借助 Co-Scientist 加速科学发现','ai-scientist-v2':'AI Scientist-v2：通过智能体树搜索实现工作坊水平的自动科学发现','paperbench':'PaperBench：评价 AI 复现 AI 研究的能力','astabench':'AstaBench：利用科学研究任务套件严格评测 AI 智能体','epoch':'EPOCH：通过证据约束的搜索实现可靠发现'}
        title_done=False
        for u in data['units']:
            normalized=re.sub(r'\s+','',u['en']).lower()
            if normalized.startswith(('abstract','summary')) or (slug=='ai-scientist-v2' and u['en'].startswith('AI is increasingly')):frontmatter=False
            if frontmatter and slug!='autoresearch':
                u['translate']=False;u['kind']='frontmatter' if u['kind']!='page' else 'page'
                if not title_done and u['kind']!='page' and (slug.split('-')[0].lower() in normalized or slug=='co-scientist'):
                    u['manual_zh']=titles[slug];title_done=True
        documents.append((slug,data))
        for u in data['units']:
            if u['translate'] and u['kind']=='table':
                # Preserve every source row and number; translate textual labels
                # separately instead of allowing generation to transpose data.
                terms=re.findall(r'[A-Za-z][A-Za-z \t/()_-]{2,}',u['en'])
                u['table_terms']=list(dict.fromkeys(t.strip() for t in terms if t.strip() and len(t.strip())>2))
                u['pieces']=[p for t in u['table_terms'] for p in pieces(t)]
            else:u['pieces']=pieces(u['en']) if u['translate'] else []
            for s in u['pieces']:
                if key(s) not in cache:queue.append((slug,s))
    # Keep source order by document, sort nearby pieces by length to reduce padding.
    seen=set();queue=[(d,s) for d,s in queue if not (key(s) in seen or seen.add(key(s)))]
    queue=sorted(queue,key=lambda ds:(ORDER.index(ds[0]),len(ds[1])//120))
    if args.limit:queue=queue[:args.limit]
    if args.assemble_only:queue=[]
    print(json.dumps(dict(stage='prepared',pending_chunks=len(queue),cached_chunks=len(cache),model=str(MODEL),revision=REVISION)),flush=True)
    if queue:
        torch.set_num_threads(8)
        torch.cuda.set_per_process_memory_fraction(0.67)
        tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True,padding_side='left')
        model=AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='sdpa')
        model.eval();start=time.time();done=0;tokens=0
        with CACHE.open('a') as cachefile:
            for offset in range(0,len(queue),args.batch_size):
                batch=queue[offset:offset+args.batch_size]
                prompts=[];protected=[]
                for _,text in batch:
                    s,values=protect(text);protected.append(values)
                    terms='large language model / LLM = 大语言模型；agent = 智能体；hypothesis = 假设；rubric = 评分标准；retrieval = 检索。'
                    if slug in ['autosurvey','openscholar','surveyforge']:terms+='survey / surveys / survey paper = 文献综述；outline = 大纲。'
                    prompt='参考术语：'+terms+'\n将以下英文原文完整翻译成简体中文。只输出译文，不概括，不解释，保留数字、引用、专名和 ZXQ 标记：\n\n'+s
                    prompts.append(tokenizer.apply_chat_template([{'role':'user','content':prompt}],add_generation_prompt=True,tokenize=False))
                inputs=tokenizer(prompts,return_tensors='pt',padding=True).to('cuda')
                input_len=inputs['input_ids'].shape[-1]
                max_new=min(1400,max(160,int((input_len-70)*2.15)+70))
                try:
                    with torch.inference_mode():
                        outputs=model.generate(**inputs,max_new_tokens=max_new,do_sample=False,pad_token_id=tokenizer.pad_token_id,use_cache=True)
                except torch.cuda.OutOfMemoryError:
                    torch.cuda.empty_cache()
                    raise RuntimeError('GPU memory insufficient; resume using --batch-size 8')
                response_tokens=outputs[:,input_len:]
                answers=tokenizer.batch_decode(response_tokens,skip_special_tokens=True)
                for (slug,original),answer,values,ids in zip(batch,answers,protected,response_tokens):
                    answer=answer.strip()
                    answer=re.sub(r'^(?:译文|翻译|中文翻译)\s*[:：]\s*','',answer)
                    answer,missing=restore(answer,values)
                    if slug in ['autosurvey','openscholar','surveyforge']:
                        answer=answer.replace('调查问卷','文献综述').replace('调查研究','综述').replace('文献文献综述','文献综述')
                    if re.search(r'\bLLMs?\b|large language models?',original,re.I) and not re.search(r'\bagents?\b',original,re.I):
                        answer=answer.replace('智能体','大语言模型')
                    flags=[]
                    generated=int((ids!=tokenizer.pad_token_id).sum())
                    if generated>=max_new and ids[-1].item()!=tokenizer.eos_token_id:flags.append('generation_limit')
                    if missing:flags.append('formula_or_link_placeholder_missing')
                    if len(re.findall(r'[\u4e00-\u9fff]',answer))<2 and len(original.split())>8:flags.append('little_chinese')
                    if not answer:flags.append('empty_translation')
                    result=dict(key=key(original),en=original,zh=answer,flags=flags,missing_protected_values=missing,model='tencent/HY-MT2-1.8B',revision=REVISION,prompt_revision=PROMPT_REVISION)
                    cache[result['key']]=result;cachefile.write(json.dumps(result,ensure_ascii=False)+'\n')
                    tokens+=generated
                cachefile.flush();done+=len(batch)
                progress=dict(stage='translating',paper=batch[-1][0],done=done,total=len(queue),seconds=round(time.time()-start),output_tokens=tokens,tokens_per_second=round(tokens/max(1,time.time()-start),1))
                (BASE/'progress.json').write_text(json.dumps(progress))
                print(json.dumps(progress),flush=True)
    for slug,data in documents:
        complete=True;flags=0
        for u in data['units']:
            if not u['translate']:
                u['zh']=u.get('manual_zh',u['en']);u['status']='manual_title' if 'manual_zh' in u else 'retained_original';u['flags']=[]
                continue
            results=[cache.get(key(s)) for s in u['pieces']]
            if not all(results):complete=False;continue
            if 'table_terms' in u:
                translated=[]
                for term in u['table_terms']:
                    translated.append(term+' → '+' '.join(cache[key(p)]['zh'] for p in pieces(term)))
                u['zh']=u['en']+'\n\n表内文字对照（数值与原始行列保持不变）：\n'+'\n'.join(translated)
            else:u['zh']='\n'.join(r['zh'] for r in results)
            u['flags']=sorted({flag for r in results for flag in r['flags']})
            u['missing_protected_values']=[v for r in results for v in r['missing_protected_values']]
            u['status']='machine_draft_needs_review' if u['flags'] else 'machine_draft'
            flags+=bool(u['flags'])
        data['translation_status']='machine draft complete' if complete else 'translation in progress'
        data['translation_model']=dict(name='tencent/HY-MT2-1.8B',revision=REVISION,precision='bfloat16',decoding='greedy',review='assistant spot checks only; not human line-by-line proofreading')
        data['flagged_units']=flags
        (BASE/slug/'bilingual.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(paper=slug,complete=complete,flagged_units=flags)),flush=True)

if __name__=='__main__':main()
