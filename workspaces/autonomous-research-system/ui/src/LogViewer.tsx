// Adapted from Astryx CodeBlockTerminal and CodeBlockScrollableBlock.
import React, {useMemo, useState} from 'react';
import {VStack, HStack} from '@astryxdesign/core/Layout';
import {Text} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {TextInput} from '@astryxdesign/core/TextInput';
import {CodeBlock} from '@astryxdesign/core/CodeBlock';
import {githubDark} from '@astryxdesign/core/theme/syntax';
import {Dialog, DialogHeader} from '@astryxdesign/core/Dialog';

type Props={text:string;title:string;metadata?:string;onRefresh?:()=>void;live?:boolean;onLiveChange?:(live:boolean)=>void};

export function LogViewer({text,title,metadata,onRefresh,live,onLiveChange}:Props) {
  const [query,setQuery]=useState(''),[wrapped,setWrapped]=useState(false),[fullscreen,setFullscreen]=useState(false);
  const lines=useMemo(()=>text ? text.split('\n') : [],[text]);
  const visible=useMemo(()=>query ? lines.filter(line=>line.toLocaleLowerCase().includes(query.toLocaleLowerCase())) : lines,[lines,query]);
  const code=visible.join('\n');
  const language=useMemo(()=>{
    const nonempty=visible.filter(line=>line.trim());
    return nonempty.length && nonempty.every(line=>{try{JSON.parse(line);return true}catch{return false}}) ? 'json' : 'plaintext';
  },[visible]);
  function body(expanded:boolean) {
    return <VStack gap={3} width="100%">
      <HStack gap={2} wrap="wrap" hAlign="between" vAlign="center">
        <TextInput label="搜索日志" type="search" size="sm" value={query} onChange={setQuery} placeholder="按关键词筛选当前日志" />
        <HStack gap={2} wrap="wrap">
          {onLiveChange && <Button size="sm" label={live?'暂停刷新':'恢复刷新'} onClick={()=>onLiveChange(!live)} />}
          {onRefresh && <Button size="sm" label="刷新" onClick={onRefresh} />}
          <Button size="sm" label={wrapped?'关闭换行':'自动换行'} onClick={()=>setWrapped(v=>!v)} />
          {!expanded && <Button size="sm" label="全屏查看" onClick={()=>setFullscreen(true)} />}
        </HStack>
      </HStack>
      <CodeBlock code={code || (query?'没有匹配的日志行。':'作业尚无控制台输出。')}
        title={title} language={language} syntaxTheme={githubDark} width="100%" size="sm"
        hasLineNumbers hasCopyButton isWrapped={wrapped} maxHeight={expanded?'65dvh':'26rem'} />
      <HStack gap={3} wrap="wrap" hAlign="between">
        <Text type="supporting">{metadata || '原始控制台输出'}{onLiveChange?` · ${live?'每5秒刷新':'刷新已暂停'}`:''}</Text>
        <Text type="supporting">{query?`筛选显示 ${visible.length} / ${lines.length} 行（行号与复制对应当前视图）`:`${lines.length.toLocaleString('zh-CN')} 行 · 可横向滚动查看长行`}</Text>
      </HStack>
    </VStack>;
  }
  return <>
    {body(false)}
    <Dialog isOpen={fullscreen} onOpenChange={setFullscreen} variant="fullscreen" padding={0}>
      <DialogHeader title={title} subtitle="程序日志" onOpenChange={setFullscreen} />
      <VStack padding={4}>{body(true)}</VStack>
    </Dialog>
  </>;
}
