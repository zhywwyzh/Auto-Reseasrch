import React, {useState} from "react";
import {VStack, HStack} from "@astryxdesign/core/Layout";
import {Text} from "@astryxdesign/core/Text";
import {Button} from "@astryxdesign/core/Button";
import {Selector} from "@astryxdesign/core/Selector";
import {TextInput} from "@astryxdesign/core/TextInput";
import {Dialog, DialogHeader} from "@astryxdesign/core/Dialog";
import {workspaceOrigin, workspacePath} from "./workspaceTarget";

export type Connection = {
  authenticated: boolean;
  local: boolean;
  remote_enabled: boolean;
  address: string;
  access_key?: string;
  addresses?: string[];
};

function savedAddresses(): string[] {
  try {
    const data = JSON.parse(localStorage.getItem("ars-workspace-addresses") || "[]");
    return Array.isArray(data) ? [...new Set(data.filter(x => typeof x === "string").map(workspaceOrigin))].slice(0, 8) : [];
  } catch { return []; }
}

export function WorkspaceAddress({connection, onConnected}: {connection: Connection | null; onConnected: () => Promise<void>}) {
  const [open, setOpen] = useState(false);
  const local = ["127.0.0.1", "localhost", "[::1]"].includes(location.hostname);
  const localOrigin = `http://127.0.0.1:${location.port || "18767"}`;
  const [choice, setChoice] = useState(local ? "local" : location.origin);
  const [address, setAddress] = useState("");
  const [history] = useState(savedAddresses);
  const [error, setError] = useState("");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const origins = [...new Set([...(local ? [] : [location.origin]), ...history])].filter(x => x !== localOrigin);
  function switchWorkspace() {
    setError("");
    try {
      const target = choice === "local" ? localOrigin : workspaceOrigin(choice === "other" ? address : choice);
      localStorage.setItem("ars-workspace-addresses", JSON.stringify([...new Set([target, ...history])].slice(0, 8)));
      if (target === location.origin) { setOpen(false); return; }
      // Reload the entire workspace: all API calls, documents and actions share
      // the destination origin. Never carry a run ID, token or task data across.
      location.assign(target + workspacePath);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  async function unlock() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/agent/connect", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({access_key: key.trim()}), signal: AbortSignal.timeout(10000),
      });
      const out = await response.json();
      if (!response.ok) throw Error(out.error || "连接失败");
      setKey(""); await onConnected();
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  const needsKey = connection && !connection.authenticated;
  return <VStack gap={2}>
    <Text type="supporting" style={{overflowWrap: "anywhere"}}>工作空间地址：{local ? "本机" : location.host}</Text>
    <Button label="切换工作空间地址" variant="secondary" onClick={() => {setError(""); setOpen(true);}} />
    <Dialog isOpen={open || !!needsKey} onOpenChange={setOpen} purpose={needsKey ? "required" : "form"} width="32rem">
      <DialogHeader title="工作空间地址" onOpenChange={setOpen} />
      <VStack padding={6} gap={4}>
        {needsKey && <VStack gap={3}>
          <Text weight="semibold">连接此工作空间：{location.host}</Text>
          <Text type="supporting">向目标设备的所有者获取连接码。验证后可访问该设备的研究与操作。</Text>
          <TextInput label="工作空间连接码" type="password" autoComplete="current-password" value={key} onChange={setKey} onEnter={unlock} />
          <Button label={busy ? "正在连接…" : "连接工作空间"} onClick={unlock} isDisabled={busy || !key.trim()} />
        </VStack>}
        <Text type="supporting">默认连接本机；填写其他设备的 IP，可直接打开它部署的工作台，无需 SSH 隧道。</Text>
        <Selector label="连接到" value={choice} onChange={setChoice} options={[
          {value:"local",label:"本机（默认）"},
          ...origins.map(x => ({value:x,label:x})),
          {value:"other",label:"其他设备 IP / 地址"},
        ]} width="100%" />
        {choice === "other" && <TextInput label="目标设备 IP / 地址" value={address} onChange={setAddress} placeholder="例如 192.168.1.20 或 192.168.1.20:18767" description="仅填写 IP 时使用端口 18767，也支持完整 HTTP/HTTPS 地址。" onEnter={switchWorkspace} />}
        <Text type="supporting">当前连接：{location.origin}。切换后显示目标设备自己的任务、文件和模型配置。</Text>
        {connection?.local && <VStack gap={3}>
          <Text weight="semibold">从其他设备访问本工作空间</Text>
          {connection.remote_enabled ? <>
            {(connection.addresses || []).map(x => <Text key={x} style={{overflowWrap:"anywhere"}}>{x}</Text>)}
            <TextInput label="本工作空间连接码" type={showKey ? "text" : "password"} value={connection.access_key || ""} isReadOnly description="仅在本机显示，分享给需要访问此工作空间的人。" />
            <Button label={showKey ? "隐藏连接码" : "显示连接码"} variant="ghost" onClick={() => setShowKey(!showKey)} />
          </> : <Text type="supporting">本工作空间尚未开放网络监听，服务启动时添加 --host 0.0.0.0 即可开放。</Text>}
          <Text type="supporting">目标设备必须运行工作台服务，且双方网络可达。HTTP 地址适用于可信内网；公网部署需配置 HTTPS。</Text>
        </VStack>}
        {error && <Text role="alert">{error}</Text>}
        <HStack gap={3} hAlign="end" wrap="wrap">
          <Button label="取消" onClick={() => setOpen(false)} />
          <Button label="打开工作空间" variant="primary" onClick={switchWorkspace} />
        </HStack>
      </VStack>
    </Dialog>
  </VStack>;
}
