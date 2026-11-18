"""Manifest-bound preliminary drafts; never substitutes for stage acceptance."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

VERSION='preliminary-drafts-v1'


def entries(directory,state):
    root=Path(directory).resolve();manifest=root/'artifacts/drafts.json'
    if not manifest.exists():return []
    if manifest.is_symlink() or not manifest.resolve().is_relative_to(root):raise ValueError('草稿登记路径无效')
    data=json.loads(manifest.read_text())
    if data.get('version')!=VERSION or data.get('topic')!=state['topic'] or data.get('run_id')!=state['id']:
        raise ValueError('草稿登记运行身份不匹配')
    artifacts=data.get('artifacts',[])
    if not isinstance(artifacts,list) or len(artifacts)>100:raise ValueError('草稿登记列表无效')
    return artifacts


def artifact_bytes(directory,state,index,digest):
    root=Path(directory).resolve();artifacts=entries(root,state)
    if type(index) is not int or not 0<=index<len(artifacts):raise ValueError('没有此草稿')
    entry=artifacts[index];relative=Path(entry['path'])
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('草稿必须位于本运行内')
    path=root/relative
    if not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in [path,*path.parents] if p!=root and p.is_relative_to(root)):
        raise ValueError('拒绝草稿路径越界或符号链接')
    if path.suffix not in ('.pdf','.tex','.json','.md','.html'):raise ValueError('不支持的草稿格式')
    body=path.read_bytes()
    if not body or digest!=entry['sha256'] or hashlib.sha256(body).hexdigest()!=digest:raise ValueError('草稿版本校验失败')
    return {'path':path,'sha256':digest},body


def describe(directory,state):
    result=[]
    try:
        for i,entry in enumerate(entries(directory,state)):
            artifact_bytes(directory,state,i,entry['sha256'])
            result.append(dict(label=entry['label'],note=entry.get('note','阶段草稿，未表示研究已完成'),
                sha256=entry['sha256'],url='/api/agent/artifact?'+urlencode(dict(key=state['topic']+'/'+state['id'],stage='draft',index=i,sha256=entry['sha256']))))
    except (OSError,ValueError,TypeError,KeyError):
        return []
    return result
