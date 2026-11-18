import {ExecutionObservation} from "./ExecutionObservation";
import {ResearchConsole} from "./ResearchConsole";
import {ResearchQueue} from "./ResearchQueue";
import {StatusPill} from "./StatusPill";
import {ModelRoutingFields, emptyModelPolicy} from "./ModelRouting";
import {ModelUsage} from "./ModelUsage";
import {WorkspaceAddress, type Connection} from "./WorkspaceAddress";
import {newCreationId} from "./workspaceTarget";
// Adapted from Astryx dashboard-progress: Section padding 6, block padding 10,
// content gap 6 and responsive three-column workstream layout.
import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import "@astryxdesign/core/reset.css";
import "@astryxdesign/core/astryx.css";
import "@fontsource-variable/noto-sans-sc";
import { Collapsible } from "@astryxdesign/core/Collapsible";
import { Theme } from "@astryxdesign/core/theme";
import { themes, defaultThemeSlug } from "./astryx-themes";
import { AppShell } from "@astryxdesign/core/AppShell";
import { TopNav, TopNavHeading } from "@astryxdesign/core/TopNav";
import {
  SideNav,
  SideNavItem,
  SideNavSection,
} from "@astryxdesign/core/SideNav";
import { VStack, HStack } from "@astryxdesign/core/Layout";
import { Grid } from "@astryxdesign/core/Grid";
import { Section } from "@astryxdesign/core/Section";
import { Text, Heading } from "@astryxdesign/core/Text";
import { Card } from "@astryxdesign/core/Card";
import { Button } from "@astryxdesign/core/Button";
import { StatusDot } from "@astryxdesign/core/StatusDot";
import { Icon } from "@astryxdesign/core/Icon";
import { ProgressBar } from "@astryxdesign/core/ProgressBar";
import { Table } from "@astryxdesign/core/Table";
import { TextInput } from "@astryxdesign/core/TextInput";
import { TextArea } from "@astryxdesign/core/TextArea";
import { Selector } from "@astryxdesign/core/Selector";
import { TabList, Tab } from "@astryxdesign/core/TabList";

type Data = Record<string, any>;
const names: Record<string, string> = {
  RUNNING: "运行中",
  READY: "已就绪",
  COMPLETED: "已完成",
  PENDING: "待执行",
  FAILED: "失败",
  UNKNOWN: "执行结果未确认",
  BLOCKED: "待处理",
  WAITING_EXTERNAL: "等待条件",
  STOPPED_USER: "已停止",
  STOPPED_BUDGET: "达到额度",
  NEEDS_RECONCILIATION: "执行结果未确认",
  REVISION_REQUIRED: "待修订",
  NOT_CREATED: "尚未开始",
  running: "进行中",
  pending: "待执行",
  completed: "执行结束",
  failed: "失败",
  unknown: "执行结果未确认",
  succeeded: "返回成功",
};
const phases: Record<string, string> = {
  resolve: "定义与协议",
  implement: "代码实现",
  validate: "运行验收",
  pilot: "先导实验",
  experiment: "正式实验",
  analyze: "证据分析",
  write: "论文与PDF",
  paper_review: "全文终审",
  plan: "研究计划",
  code_repair: "自动修复",
};
const routes = [
  ["overview", "研究总览"],
  ["experiments", "实验进度"],
  ["results", "成果与论文"],
  ["usage", "任务与模型用量"],
  ["system", "系统管理"],
  ["guide", "使用说明"],
];
const date = (x: any) =>
  x ? new Date(x).toLocaleString("zh-CN", { hour12: false }) : "暂无记录";
const num = (x: any) =>
  typeof x === "number" ? x.toLocaleString("zh-CN") : "未知";
const status = (x: string) => names[x] || x || "未知";
function Rows({
  rows,
  columns,
}: {
  rows: Data[];
  columns: [string, string][];
}) {
  return (
    <Table
      data={rows}
      columns={columns.map(([key, header]) => ({
        key,
        header,
        renderCell: (r: Data) => (
          <Text>
            {typeof r[key] === "object"
              ? JSON.stringify(r[key])
              : String(r[key] ?? "—")}
          </Text>
        ),
      }))}
      textOverflow="wrap"
      hasHover
    />
  );
}
function Block({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <VStack gap={4}>
      <Heading level={3}>{title}</Heading>
      {children}
    </VStack>
  );
}
function Notes({ items }: { items: any[] }) {
  return (
    <VStack gap={3} maxWidth="56rem">
      {items.filter(Boolean).map((x, i) => (
        <Text key={i} color="secondary">
          {typeof x === "string" ? x : JSON.stringify(x)}
        </Text>
      ))}
    </VStack>
  );
}
function Metric({ label, value }: { label: string; value: any }) {
  return (
    <Card padding={6}>
      <VStack gap={2}>
        <Text type="supporting">{label}</Text>
        <Heading level={2}>{value}</Heading>
      </VStack>
    </Card>
  );
}
function Progress({
  label,
  done,
  total,
  stepStatus,
}: {
  label: string;
  done: any;
  total: any;
  stepStatus?: string;
}) {
  return typeof done === "number" && typeof total === "number" && total > 0 ? (
    <ProgressBar
      label={label}
      value={done}
      max={total}
      hasValueLabel
      formatValueLabel={(v, m) =>
        `${num(v)} / ${num(m)} · ${((v / m) * 100).toFixed(1)}%${v >= m && stepStatus && stepStatus !== "completed" ? "（计数已满，步骤未结束）" : ""}`
      }
    />
  ) : (
    <Text type="supporting">
      {total
        ? `计划 ${num(total)} 项，等待实测计数`
        : "分母尚未确定，不估算完成比例"}
    </Text>
  );
}
function ResearchProgress({s, detailed = false}: {s: Data; detailed?: boolean}) {
  const p = s.progress || {}, e = s.experiment_progress || {}, d = e.dashboard || {};
  const stages: Data[] = p.stages || [];
  const current = stages.find((r) => r.status === "RUNNING") || stages.find((r) => r.phase === p.current_task?.phase) || stages.find((r) => r.status !== "COMPLETED");
  const index = current ? stages.indexOf(current) : -1;
  const completed = stages.filter((r) => r.status === "COMPLETED");
  const upcoming = stages.filter((r, i) => i > index && r.status !== "COMPLETED");
  const stopped = s.status?.startsWith("STOPPED_");
  const latest = [...(s.tasks || [])].reverse().find((t: Data) => t.status === "COMPLETED" && t.summary);
  const series = [...(e.series || [])].sort((a: Data,b: Data) => (b.rank || 0) - (a.rank || 0))[0];
  const missing = ["awaiting_design", "invalid"].includes(d.mode);
  const summary = missing ? e.summary : d.summary || e.summary;
  const blocker = d.blocker || (s.status === "NEEDS_RECONCILIATION" ? "执行调用最终回执缺失；具体证据与处理项见上方。" : p.blocking_error);
  const next = missing ? (p.current_task?.title ? `核对并继续“${p.current_task.title}”，接入本轮训练计数。` : p.next_action) : d.next_action || p.next_action;
  return <VStack gap={4}>
    <VStack gap={2}>
      <Text type="supporting">{stopped ? "停止前进展" : "当前研究进展"}{index >= 0 ? ` · 第 ${index + 1} / ${stages.length} 阶段` : ""}</Text>
      <Heading level={detailed ? 2 : 3}>{current?.label || (s.status === "COMPLETED" ? "本轮研究流程已结束" : "阶段尚未登记")}</Heading>
      {p.current_task?.title && <Text>具体工作：{p.current_task.title}</Text>}
    </VStack>
    {stages.length > 0 && <VStack gap={2}>
      <Text weight="semibold">阶段验收：{completed.length} / {stages.length} 个阶段已通过</Text>
      {completed.length > 0 && <Text type="supporting">已通过：{completed.map((r) => r.label).join(" → ")}</Text>}
      {upcoming.length > 0 && <Text type="supporting">后续：{upcoming.map((r) => r.label).join(" → ")}</Text>}
    </VStack>}
    <VStack gap={2}>
      <Text weight="semibold">实验推进到哪里</Text>
      {!!d.steps?.length && <Text>本轮工作项：{d.steps.filter((r: Data) => r.status === "completed").length} / {d.steps.length} 项已完成{d.current_step ? ` · 当前：${d.steps.find((r: Data) => r.id === d.current_step)?.label || d.current_step}` : ""}。工作项状态不代表完整实验已通过。</Text>}
      {series && !series.planned_only && Number.isFinite(series.counts?.terminal) && series.counts?.total > 0 ? <>
        <Progress label={series.label + (stopped || series.snapshot_stale ? " · 最近快照" : "")} done={series.counts.terminal} total={series.counts.total} />
        <Text type="supporting">还剩 {num(Math.max(0, series.counts.total - series.counts.terminal))} 回合未记录终态；结束数包含失败，不等于实验验收通过。</Text>
      </> : <Text>{summary || "尚无实验计数记录。"}</Text>}
      {missing && <Text type="supporting">{d.mode === "invalid" ? "本轮进度未通过核对" : "本轮进度未接入"}；已有历史批次记录如上，不能据此推算当前完成比例。</Text>}
      <Text type="supporting">数据截至 {date(d.updated_at || series?.source_at || e.source_at || p.updated_at)}{stopped ? " · 停止前记录，非实时状态" : d.mode === "stale" ? " · 执行说明待更新，以下保留最近记录" : ""}</Text>
    </VStack>
    {latest && <VStack gap={1}><Text weight="semibold">最近完成的工作</Text><Text type="supporting">{latest.title} · 完成时记录</Text><Text>{latest.summary}</Text></VStack>}
    <VStack gap={1}>
      <Text><strong>{stopped ? "暂停原因：" : "当前阻碍："}</strong>{blocker || (stopped ? "任务已停止，后续步骤尚未继续。" : "当前未登记具体阻碍。")}</Text>
      {next && <Text><strong>{stopped ? "恢复后下一步：" : "下一步："}</strong>{next}</Text>}
    </VStack>
    {detailed && stages.length > 0 && <VStack gap={4}>
      <Heading level={3}>研究阶段路线</Heading>
      <Grid columns={{minWidth: 180, max: 3}} gap={4}>
        {stages.map((r, i) => {
          const label = r.status === "RUNNING" && stopped ? "停在此阶段" : status(r.status);
          return <HStack key={r.phase} gap={3} vAlign="start">
            <StatusDot variant={r.status === "COMPLETED" ? "success" : r.status === "RUNNING" ? "accent" : "neutral"} label={label} />
            <VStack gap={1}><Text weight={r.phase === current?.phase ? "semibold" : "normal"}>{i + 1}. {r.label}</Text><Text type="supporting">{label}</Text></VStack>
          </HStack>;
        })}
      </Grid>
    </VStack>}
  </VStack>;
}
function Experiments({ s }: { s: Data }) {
  const p = s.experiment_progress,
    d = p?.dashboard;
  return (
    <VStack gap={6}>
      <Block title="实验计数与作业明细">
        {d?.objective && <Text color="secondary">{d.objective}</Text>}
        <Text type="supporting">{s.status?.startsWith("STOPPED_") ? "以下为停止前采样与回执。" : "页面自动读取采样与回执。"} 采样时间与每条记录的执行状态分别保留。</Text>
      </Block>
      <Grid columns={{ minWidth: 280, max: 3 }} gap={4}>
        {(d?.steps || []).map((r: Data) => (
          <Card key={r.id} padding={6}>
            <VStack gap={4}>
              <HStack hAlign="between">
                <Heading level={4}>{r.label}</Heading>
                <Text type="supporting">{status(r.status)}</Text>
              </HStack>
              <Progress
                label={r.label}
                done={
                  r.terminal ??
                  (Number.isInteger(r.completed) && Number.isInteger(r.failed)
                    ? r.completed + r.failed
                    : null)
                }
                total={r.total}
                stepStatus={r.status}
              />
              <Text>{r.detail}</Text>
              <Text type="supporting">{r.target_basis}</Text>
              {r.failed != null && (
                <Text type="supporting">
                  失败 {num(r.failed)} · 完成 {num(r.completed)}
                </Text>
              )}
            </VStack>
          </Card>
        ))}
      </Grid>
      {!!p?.series?.length && (
        <Block title="实验轮次">
          <Grid columns={{ minWidth: 280, max: 3 }} gap={4}>
            {p.series.map((r: Data, i: number) => (
              <Card key={i} padding={6}>
                <VStack gap={4}>
                  <Heading level={4}>{r.label}</Heading>
                  <Progress
                    label={r.label}
                    total={r.counts?.total}
                    done={r.planned_only ? null : r.counts?.terminal}
                  />
                  <Text type="supporting">
                    {r.note || "执行比例包含失败；科学结论另行验收。"}
                  </Text>
                </VStack>
              </Card>
            ))}
          </Grid>
        </Block>
      )}
      {!!d?.jobs?.length && (
        <Block title="作业观察">
          <Rows
            rows={d.jobs.map((j: Data) => ({
              ...j,
              status: status(j.status),
              observed_at: date(j.observed_at),
              elapsed_seconds:
                j.elapsed_seconds == null
                  ? "未知"
                  : Math.round(j.elapsed_seconds) + " 秒",
            }))}
            columns={[
              ["kind", "作业类别"],
              ["status", "状态"],
              ["elapsed_seconds", "运行时长"],
              ["observed_at", "最近观察"],
            ]}
          />
        </Block>
      )}
      {!!d?.timeline?.length && (
        <Block title="进展与处理记录">
          <Rows
            rows={d.timeline.map((r: Data) => ({
              ...r,
              updated_at: date(r.updated_at),
            }))}
            columns={[
              ["updated_at", "时间"],
              ["summary", "进展"],
              ["blocker", "阻碍"],
              ["next_action", "下一步"],
            ]}
          />
        </Block>
      )}
      <Notes
        items={[
          ...(p?.warnings || []),
          ...(d?.warnings || []),
          p?.overall_note,
        ]}
      />
    </VStack>
  );
}
function Results({ s }: { s: Data }) {
  const d = s.delivery;
  return (
    <VStack gap={6}>
      {!!s.drafts?.length && <Block title="阶段草稿与写作修订">
        <Text type="supporting">草稿独立展示；正式实验、论文完成与评分仍以各阶段核验记录为准。</Text>
        {s.drafts.map((draft:Data,i:number)=><VStack key={i} gap={2}><Button label={draft.label} href={draft.url} /><Text type="supporting">{draft.note}</Text></VStack>)}
      </Block>}
      <Block title={d?.label || "成果与论文"}>
        <Text type="supporting">{s.topic} / {s.id} · {d?.execution_label || names[s.status] || s.status}</Text>
        <Text>{d?.summary || "当前还没有已核验的交付产物。"}</Text>
        <HStack gap={3} wrap="wrap">
          {(d?.links || []).map((l: Data, i: number) => (
            <Button
              key={i}
              label={l.label || l.title || "查看产物"}
              href={l.href || l.url}
            />
          ))}
        </HStack>
      </Block>
      {d?.score && (
        <Metric label="内部评审评分" value={`${d.score.overall} / 10`} />
      )}
      {d?.review_assessment && <Block title="本轮全文复评">
        <Text type="supporting">{d.review_assessment.scale}</Text>
        <Text>{d.review_assessment.reviewer?.kind || "内部评审"}；评审记录绑定本轮稿件与 PDF。</Text>
        <Table data={d.review_assessment.dimensions} textOverflow="wrap" columns={[
          {key: "label", header: "维度"},
          {key: "score", header: "分项评分", renderCell: (row: Data) => <Text>{row.score ?? "未评分"}</Text>},
          {key: "reason", header: "依据与限制"},
        ]} />
        <Text>{d.review_assessment.overall == null ? "未给总评" : `总评：${d.review_assessment.overall}`}：{d.review_assessment.overall_reason}</Text>
      </Block>}
      <Notes
        items={[
          ...(d?.findings || []),
          ...(d?.pending || []),
          ...(d?.warnings || []),
        ]}
      />
      {!!d?.figures?.length && (
        <Block title="实验图表">
          <HStack gap={3} wrap="wrap">
            {d.figures.map((f: Data, i: number) => (
              <Button key={i} label={f.label || "实验图表"} href={f.url} />
            ))}
          </HStack>
        </Block>
      )}
      <Notes items={[d?.scope, d?.source_note]} />
      <Block title="本轮执行报告">
        <VStack gap={4} maxWidth="56rem">
          {String(s.report || "等待执行报告")
            .split(/\n\s*\n/)
            .map((paragraph, i) => (
              <Text
                key={i}
                as="p"
                style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
              >
                {paragraph}
              </Text>
            ))}
        </VStack>
      </Block>
    </VStack>
  );
}
function ReferenceLibrary() {
  const [file, setFile] = useState("usage.html"),
    [blocks, setBlocks] = useState<{ tag: string; text: string }[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    const abort = new AbortController();
    fetch("/workspaces/autonomous-research-system/" + file + "?legacy=1", {
      signal: abort.signal,
    })
      .then((r) => {
        if (!r.ok) throw Error("说明加载失败");
        return r.text();
      })
      .then((html) => {
        const doc = new DOMParser().parseFromString(html, "text/html");
        doc
          .querySelectorAll("script,style,nav,form,button")
          .forEach((n) => n.remove());
        setBlocks(
          Array.from(doc.querySelectorAll("h1,h2,h3,p,li,table,pre"))
            .filter((n) => !n.parentElement?.closest("li,table,pre"))
            .map((n) => ({
              tag: n.tagName,
              text: (n.textContent || "").trim(),
            }))
            .filter((n) => n.text),
        );
        setError("");
      })
      .catch((e) => {
        if (!abort.signal.aborted) setError(String(e));
      });
    return () => abort.abort();
  }, [file]);
  return (
    <Block title="平台参考资料">
      <Selector
        label="参考文档"
        value={file}
        onChange={setFile}
        options={[
          { value: "usage.html", label: "完整使用说明" },
          { value: "index.html", label: "系统设计与架构" },
          { value: "research-goals.html", label: "研究目标模板" },
          { value: "journal-review.html", label: "期刊样例与阶段预审" },
        ]}
      />
      {error && <Text role="alert">{error}</Text>}
      {blocks.map((b, i) =>
        /^H/.test(b.tag) ? (
          <Heading key={i} level={3}>
            {b.text}
          </Heading>
        ) : (
          <Text key={i} as="p" style={{ whiteSpace: "pre-wrap" }}>
            {b.text}
          </Text>
        ),
      )}
    </Block>
  );
}
function App() {
  const [connection, setConnection] = useState<Connection | null>(null);
  const initial = new URLSearchParams(location.hash.slice(1));
  const [page, setPage] = useState(
    initial.get("page") ||
      (initial.get("run")
        ? "experiments"
        : {
            "system.html": "system",
            "usage.html": "guide",
            "index.html": "guide",
            "journal-review.html": "guide",
            "research-goals.html": "guide",
          }[location.pathname.split("/").pop() || ""] || "overview"),
  );
  const [selected, setSelected] = useState(initial.get("run") || "");
  const [rows, setRows] = useState<Data[]>([]),
    [states, setStates] = useState<Record<string, Data>>({}),
    [options, setOptions] = useState<Data>({}),
    [system, setSystem] = useState<Data>({});
  const [showDemo, setShowDemo] = useState(false);
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState("all"),
    [creating, setCreating] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [synced, setSynced] = useState("");
  const [mode, setMode] = useState<"light" | "dark">(() =>
    localStorage.getItem("ars-theme") === "dark" ? "dark" : "light",
  );
  const token = useRef(""),
    loading = useRef(false);
  const [goal, setGoal] = useState(""),
    [topic, setTopic] = useState(""),
    [createMode, setCreateMode] = useState("new"),
    [topicTitle, setTopicTitle] = useState(""),
    [materials, setMaterials] = useState(""),
    [creationId, setCreationId] = useState(newCreationId),
    [backend, setBackend] = useState("codex"),
    [workflow, setWorkflow] = useState("paper"),
    [target, setTarget] = useState("none"),
    [targetName, setTargetName] = useState(""),
    [model, setModel] = useState(""),
    [modelPolicy, setModelPolicy] = useState<Data>(emptyModelPolicy),
    [limits, setLimits] = useState<Record<string, string>>({
      max_calls: "0",
      max_seconds: "0",
      max_tokens: "0",
      task_timeout: "0",
    }),
    [budget, setBudget] = useState("2");
  async function api(path: string, data?: Data) {
    const res = await fetch("/api/agent/" + path, {
      ...(data
        ? {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-ARS-Token": token.current,
            },
            body: JSON.stringify(data),
          }
        : {}),
      signal: AbortSignal.timeout(15000),
    });
    const out = await res.json();
    if (!res.ok) {
      if (res.status === 401) void loadConnection();
      throw Error(out.error || String(res.status));
    }
    return out;
  }
  async function loadConnection() {
    try {
      const response = await fetch("/api/agent/connection", {signal: AbortSignal.timeout(10000)});
      const info = await response.json();
      if (!response.ok) throw Error(info.error || "无法连接工作空间");
      setConnection(info);
      setError("");
    } catch (e) { setError("工作空间连接失败：" + String(e)); }
  }
  async function refresh() {
    if (loading.current) return;
    loading.current = true;
    try {
      const [list, opt, sys] = await Promise.all([
        api("campaigns"),
        api("options"),
        api("system"),
      ]);
      token.current = list.token;
      setRows(list.campaigns);
      setOptions(opt);
      setSystem(sys);
      const values = await Promise.allSettled(
        list.campaigns.map(async (c: Data) => {
          const state = await api("state?key=" + encodeURIComponent(c.key));
          setStates((prev) => ({...prev, [c.key]: state}));
        }),
      );
      setError(
        values.some((r) => r.status === "rejected")
          ? "部分任务详情未能同步，保留上次数据。"
          : "",
      );
      setSynced(new Date().toLocaleTimeString("zh-CN"));
    } catch (e) {
      setError(String(e));
    } finally {
      loading.current = false;
    }
  }
  useEffect(() => {
    void loadConnection();
  }, []);
  useEffect(() => {
    if (!connection?.authenticated) return;
    refresh();
    const id = setInterval(refresh, 2000);
    const hash = () => {
      const p = new URLSearchParams(location.hash.slice(1));
      setPage(p.get("page") || (p.get("run") ? "experiments" : "overview"));
      setSelected(p.get("run") || "");
    };
    window.addEventListener("hashchange", hash);
    return () => {
      clearInterval(id);
      window.removeEventListener("hashchange", hash);
    };
  }, [connection?.authenticated]);
  function navigate(p: string, key = selected) {
    setPage(p);
    setSelected(key);
    location.hash = new URLSearchParams({
      page: p,
      ...(key ? { run: key } : {}),
    }).toString();
  }
  async function act(action: string, data: Data = {}) {
    if (busy) return;
    setBusy(true);
    setNotice("正在提交…");
    try {
      const out = await api(action, data);
      setNotice("操作已提交，执行结果以最新回执为准。");
      if (["create", "create-research"].includes(action)) {
        setCreating(false);
        navigate("experiments", out.key);
        if(action === "create-research"){setCreationId(newCreationId());setTopicTitle("");setGoal("");setMaterials("");setNotice(`独立课题已创建：${out.topic.id} · ${out.topic.title}，尚未启动。`)}
      }
      await refresh();
    } catch (e) {
      setNotice(String(e));
    } finally {
      setBusy(false);
    }
  }
  const real = rows.filter(
      (c) => showDemo || c.topic !== "ARS-DEMO" || c.key === selected,
    ),
    visible = real.filter(
      (c) =>
        (filter === "all" || c.status === filter) &&
        [c.topic, c.id, c.goal]
          .join(" ")
          .toLowerCase()
          .includes(query.toLowerCase()),
    );
  const key =
      selected || real.find((c) => c.status === "RUNNING")?.key || real[0]?.key,
    s = states[key];
  const section = routes.find((r) => r[0] === page)?.[1] || "研究总览";
  const active = real.filter((c) => c.status === "RUNNING").length;
  const currentRun = real.find((c) => c.key === key);
  const groups = [
    {title: "正在运行", rows: visible.filter((c) => c.status === "RUNNING")},
    {title: "各课题最近一次运行 · 当前未运行", rows: visible.filter((c) => c.is_latest_run && c.status !== "RUNNING")},
  ];
  const history = visible.filter((c) => !c.is_latest_run && c.status !== "RUNNING");
  return (
    <Theme theme={themes[defaultThemeSlug]} mode={mode}>
      <AppShell
        variant="elevated"
        topNav={
          <TopNav
            label="平台导航"
            heading={
              <TopNavHeading heading="ARS" subheading="自主研究工作台" />
            }
            endContent={
              <HStack gap={3} vAlign="center">
                <Text type="supporting">
                  {synced ? "同步于 " + synced : "连接中"}
                </Text>
                <Button
                  label={mode === "light" ? "深色模式" : "浅色模式"}
                  variant="ghost"
                  onClick={() => {
                    const next = mode === "light" ? "dark" : "light";
                    setMode(next);
                    localStorage.setItem("ars-theme", next);
                  }}
                />
                <Button
                  label="新建研究"
                  variant="primary"
                  isDisabled={!connection?.authenticated}
                  onClick={() => {
                    setCreating(true);
                    navigate("overview", "");
                  }}
                />
              </HStack>
            }
          />
        }
        sideNav={
          <SideNav
            topContent={
              <Section variant="transparent" padding={4}>
                <VStack gap={3}><HStack gap={2} vAlign="center"><Icon icon="viewColumns" color="accent" /><Text weight="semibold">研究工作空间</Text></HStack><Text type="supporting">目标 · 实验 · 证据</Text><WorkspaceAddress connection={connection} onConnected={loadConnection} /></VStack>
              </Section>
            }
            footer={
              <Section variant="transparent">
                <Text type="supporting">研究资料与实验仅保留本地</Text>
              </Section>
            }
          >
            <SideNavSection title="工作空间">
              {routes.map(([id, label]) => (
                <SideNavItem
                  key={id}
                  label={label}
                  icon={<Icon icon={id==='overview'?'viewColumns':id==='experiments'?'clock':id==='results'?'checkDouble':id==='usage'?'arrowsUpDown':id==='system'?'wrench':'info'} size="sm" />}
                  isSelected={page === id}
                  href={"#page=" + id}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(id, ["overview", "usage"].includes(id) ? "" : selected);
                  }}
                />
              ))}
            </SideNavSection>
            {[{title: "正在运行", items: real.filter((c) => c.status === "RUNNING")},
              {title: "最近运行", items: real.filter((c) => c.is_latest_run && c.status !== "RUNNING")},
              {title: "历史运行", items: real.filter((c) => !c.is_latest_run && c.status !== "RUNNING")}
            ].map((group) => <SideNavSection key={group.title} title={group.title}>
              {group.items.map((c) => <SideNavItem
                key={c.key}
                label={`${c.topic} · ${c.last_started_at ? new Date(c.last_started_at).toLocaleString("zh-CN", {month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false}) : "尚未启动"}`}
                endContent={<Text type="supporting">{status(c.status)}</Text>}
                isSelected={key === c.key && page !== "overview"}
                onClick={() => navigate("experiments", c.key)}
              />)}
            </SideNavSection>)}
          </SideNav>
        }
      >
        <Section variant="transparent" padding={6}>
          <VStack gap={4} maxWidth="88rem" style={{ marginInline: "auto" }}>
            <HStack hAlign="between" vAlign="center" wrap="wrap">
              <VStack gap={3} maxWidth="56rem">
                <Text type="supporting">ARS / {section}</Text>
                <Heading level={1}>{section}</Heading>
                <Text color="secondary">
                  {page === "overview"
                    ? "从研究目标到实验、证据与论文，持续掌握每一步。"
                    : s && ["experiments", "results"].includes(page)
                      ? (options.topics?.find((t: Data) => t.id === s.topic)
                          ?.title || s.topic) +
                        " · " + s.id
                      : "研究执行、系统治理与可追溯记录。"}
                </Text>
              </VStack>
              <Button label="立即刷新" onClick={connection?.authenticated ? refresh : loadConnection} />
            </HStack>
            {s && ["results"].includes(page) && (
              <Collapsible
                trigger="查看完整研究目标与执行约定"
                defaultIsOpen={false}
              >
                <VStack gap={4} paddingBlock={4} maxWidth="56rem">
                  {String(s.goal || "")
                    .split(/\n+/)
                    .filter(Boolean)
                    .map((paragraph, i) => (
                      <Text key={i} as="p" style={{ overflowWrap: "anywhere" }}>
                        {paragraph}
                      </Text>
                    ))}
                </VStack>
              </Collapsible>
            )}
            {error && <Text role="alert">{error}</Text>}
            {notice && <Text role="status">{notice}</Text>}
          </VStack>
        </Section>
        {connection?.authenticated && <Section variant="transparent" padding={6}>
          <VStack gap={5} maxWidth="88rem" style={{ marginInline: "auto" }}>
            {creating && (
              <Card padding={6}>
                <VStack gap={4}>
                  <HStack hAlign="between">
                    <Heading level={2}>{createMode === "new" ? "新建独立研究课题" : "已有课题新增运行"}</Heading>
                    <Button
                      label="收起"
                      variant="ghost"
                      onClick={() => setCreating(false)}
                    />
                  </HStack>
                  <HStack gap={3} wrap="wrap">
                    <Button label="新建独立课题" variant={createMode === "new" ? "primary" : "secondary"} isDisabled={busy} onClick={()=>setCreateMode("new")} />
                    <Button label="已有课题新增运行" variant={createMode === "existing" ? "primary" : "secondary"} isDisabled={busy} onClick={()=>setCreateMode("existing")} />
                  </HStack>
                  {createMode === "new" && <VStack gap={3}>
                    <Text>创建全新的研究对象，自动分配编号、独立工作区和首个运行。后续任务、资料、实验进度和模型用量均归入新课题。</Text>
                    <TextInput label="新课题名称" placeholder="输入你要开展的新研究名称" isDisabled={busy} value={topicTitle} onChange={setTopicTitle} />
                  </VStack>}
                  <Grid columns={{ minWidth: 260, max: 2 }} gap={4}>
                    {createMode === "existing" && <Selector
                      label="选择已有课题"
                      options={(options.topics || []).map((t: Data) => ({
                        value: t.id,
                        label: t.id + " · " + t.title,
                      }))}
                      value={topic}
                      onChange={setTopic}
                    />}
                    <Selector
                      label="执行器"
                      options={[
                        { value: "codex", label: "Codex · 真实执行" },
                        { value: "mock", label: "模拟 · 程序验证" },
                      ]}
                      value={backend}
                      onChange={setBackend}
                    />
                    {createMode === "existing" && <Selector
                      label="研究流程"
                      options={[
                        { value: "readonly", label: "只读审查" },
                        {
                          value: "paper",
                          label: "实现、实验到论文",
                          disabled:
                            backend !== "codex" ||
                            !(options.paper_topics || []).includes(topic),
                        },
                      ]}
                      value={workflow}
                      onChange={setWorkflow}
                    />}
                    <Selector
                      label="投稿目标"
                      options={(options.submission_targets || []).map(
                        (t: Data) => ({ value: t.id, label: t.label }),
                      )}
                      value={target}
                      onChange={setTarget}
                    />
                  </Grid>
                  {target === "custom" && (
                    <TextInput
                      label="自定义目标名称"
                      value={targetName}
                      onChange={setTargetName}
                    />
                  )}
                  <TextArea
                    label="研究目标"
                    isDisabled={busy}
                    value={goal}
                    onChange={setGoal}
                    rows={4}
                  />
                  {createMode === "new" && <VStack gap={3}>
                    <TextArea label="初始资料与约束（选填）" placeholder="已有论文、数据、本地资料路径、参考链接、研究范围及约束。可以留空。" isDisabled={busy} value={materials} onChange={setMaterials} rows={4} />
                    <Text type="supporting">首个运行从研究规划与资料分析开始。实验设备、数据使用和实验执行权限在该课题内单独配置。</Text>
                  </VStack>}
                  <ModelRoutingFields policy={modelPolicy} onChange={setModelPolicy} defaultModel={model} onDefault={setModel} options={options.model_routing} disabled={busy} />
                  <Grid columns={{ minWidth: 180, max: 4 }} gap={4}>
                    {Object.entries(limits).map(([k, v]) => (
                      <TextInput
                        key={k}
                        label={
                          (
                            {
                              max_calls: "调用上限",
                              max_seconds: "累计秒数",
                              max_tokens: "Token 阈值",
                              task_timeout: "单任务秒数",
                            } as Data
                          )[k]
                        }
                        value={v}
                        onChange={(x) => setLimits({ ...limits, [k]: x })}
                        inputMode="numeric"
                      />
                    ))}
                  </Grid>
                  <Text type="supporting">
                    额度填 0 表示不限制。创建后由你启动。
                  </Text>
                  <Button
                    label={createMode === "new" ? "创建独立研究" : "创建新运行"}
                    variant="primary"
                    isDisabled={
                      busy ||
                      (createMode === "new" ? !topicTitle.trim() || topicTitle.length>160 : !topic) ||
                      goal.length>10000 || materials.length>10000 || !goal.trim() ||
                      Object.values(limits).some((v) => !/^\d+$/.test(v))
                    }
                    onClick={() =>
                      act(createMode === "new" ? "create-research" : "create", {
                        ...(createMode === "new" ? {title:topicTitle,materials,creation_id:creationId} : {topic,import_history:true,workflow:backend === "codex" && (options.paper_topics || []).includes(topic) ? workflow : "readonly"}),
                        goal,
                        backend,
                        model,
                        model_policy: modelPolicy,
                        submission_target: target,
                        submission_target_name: targetName,
                        ...Object.fromEntries(
                          Object.entries(limits).map(([k, v]) => [
                            k,
                            Number(v),
                          ]),
                        ),
                      })
                    }
                  />
                </VStack>
              </Card>
            )}
            {page === "overview" && (
              <>
                <HStack gap={6} wrap="wrap">
                  <Text>研究课题 <strong>{new Set(real.map((c) => c.topic)).size}</strong></Text>
                  <Text>正在运行 <strong>{active}</strong></Text>
                  <Text type="supporting">本机监督器：{system.supervisor_alive ? "在线" : "待核对"}</Text>
                </HStack>
                <HStack gap={4} wrap="wrap">
                  <Button
                    label={showDemo ? "隐藏模拟任务" : "显示模拟任务"}
                    onClick={() => setShowDemo(!showDemo)}
                  />
                  <TextInput
                    label="搜索研究"
                    placeholder="课题、目标或运行编号"
                    value={query}
                    onChange={setQuery}
                  />
                  <Selector
                    label="任务状态"
                    value={filter}
                    onChange={setFilter}
                    options={[
                      { value: "all", label: "全部状态" },
                      ...[
                        "RUNNING",
                        "READY",
                        "WAITING_EXTERNAL",
                        "COMPLETED",
                        "STOPPED_USER",
                        "STOPPED_BUDGET",
                        "NEEDS_RECONCILIATION",
                      ].map((v) => ({ value: v, label: status(v) })),
                    ]}
                  />
                </HStack>

                <ResearchQueue groups={groups} history={history} states={states} topics={options.topics || []}
                  onOpen={run=>navigate("experiments",run)} onResults={run=>navigate("results",run)} status={status} />
                {!visible.length && <Text>没有符合筛选条件的研究任务。</Text>}
              </>
            )}
            {["experiments", "results"].includes(page) &&
              (s ? (
                <>
                  <HStack hAlign="between" wrap="wrap" gap={4}>
                    <Selector
                      label="当前研究"
                      options={real.map((c) => ({
                        value: c.key,
                        label: `${c.topic} / ${c.id}${c.is_latest_run ? " · 最近运行" : " · 历史运行"}`,
                      }))}
                      value={key}
                      onChange={(v) => navigate(page, v)}
                    />
                    <HStack gap={2} wrap="wrap">
                      <StatusPill state={s.status} label={status(s.status)} />
                      {page === "experiments" && <Button label="查看本轮成果" onClick={() => navigate("results", key)} />}
                      <Button
                        label="启动"
                        isDisabled={
                          busy || !["READY", "RUNNING"].includes(s.status)
                        }
                        onClick={() => act("start", { key })}
                      />
                      <Button
                        label="继续 / 恢复"
                        isDisabled={
                          busy || ["RUNNING", "READY"].includes(s.status)
                        }
                        onClick={() => act("resume", { key })}
                      />
                      <Button
                        label="停止"
                        variant="destructive"
                        isDisabled={
                          busy ||
                          ["STOPPED_USER", "COMPLETED"].includes(s.status)
                        }
                        onClick={() => act("stop", { key })}
                      />
                    </HStack>
                  </HStack>
                  <HStack gap={5} wrap="wrap">
                    <Text type="supporting">最近启动：{currentRun?.last_started_at ? date(currentRun.last_started_at) : "尚无启动记录"}</Text>
                    {currentRun?.stopped_at && <Text type="supporting">停止：{date(currentRun.stopped_at)}</Text>}
                  </HStack>
                  {page === "experiments" && <ResearchConsole key={key} s={s} runKey={key} options={options}
                    invoke={async(action,data)=>{const out=await api(action,data);void refresh();return out}}
                    onUsage={()=>navigate("usage",key)} progress={<><ResearchProgress s={s} /><Experiments s={s} /></>} />}
                  {page === "results" && <Results s={s} />}
                </>
              ) : (
                <Text>请选择研究任务，或先创建一个研究任务。</Text>
              ))}
            {page === "usage" && <ModelUsage key={selected || "all"} runs={rows} initialScope={selected || "all"} />}
            {page === "system" && (
              <>
                <Grid columns={{ minWidth: 220, max: 3 }} gap={4}>
                  <Metric
                    label="持续监督器"
                    value={system.supervisor_alive ? "运行中" : "待核对"}
                  />
                  <Metric
                    label="策略版本"
                    value={system.evolution?.versions?.length || 0}
                  />
                  <Metric
                    label="系统优化调用"
                    value={
                      system.evolution
                        ? `${system.evolution.calls} / ${system.evolution.config.max_calls}`
                        : "未初始化"
                    }
                  />
                </Grid>
                <Block title="系统策略管理">
                  <HStack gap={3} wrap="wrap">
                    <TextInput
                      label="调用额度"
                      value={budget}
                      onChange={setBudget}
                      inputMode="numeric"
                    />
                    {!system.evolution ? (
                      <Button
                        label="初始化系统"
                        isDisabled={busy || !/^\d+$/.test(budget)}
                        onClick={() =>
                          act("system-init", { max_calls: Number(budget) })
                        }
                      />
                    ) : (
                      <>
                        <Button
                          label="执行一次优化"
                          variant="primary"
                          isDisabled={
                            busy ||
                            system.evolution.config.stopped ||
                            system.evolution.calls >=
                              system.evolution.config.max_calls ||
                            system.evolution.operations?.some((o: Data) =>
                              ["RUNNING", "RESERVED", "UNKNOWN"].includes(
                                o.state,
                              ),
                            )
                          }
                          onClick={() => act("system-optimize")}
                        />
                        <Button
                          label="停止优化"
                          isDisabled={busy}
                          onClick={() => act("system-stop")}
                        />
                        <Button
                          label="回滚策略"
                          isDisabled={busy}
                          onClick={() => act("system-rollback")}
                        />
                        <Button
                          label="增加额度"
                          isDisabled={
                            busy ||
                            !/^\d+$/.test(budget) ||
                            Number(budget) < 1 ||
                            Number(budget) > 20
                          }
                          onClick={() =>
                            act("system-budget", {
                              additional_calls: Number(budget),
                            })
                          }
                        />
                      </>
                    )}
                  </HStack>
                  <Text type="supporting">
                    系统优化使用模型额度；研究任务的预算分别保存。
                  </Text>
                </Block>
                <Rows
                  rows={(system.supervisor?.campaigns || []).map((r: Data) => ({
                    ...r,
                    status: status(r.status),
                  }))}
                  columns={[
                    ["topic", "课题"],
                    ["id", "运行"],
                    ["status", "状态"],
                    ["action", "监督动作"],
                    ["reason", "原因"],
                  ]}
                />
                <Block title="策略版本档案">
                  <Rows
                    rows={(system.evolution?.versions || []).map((v: Data) => ({
                      ...v,
                      viable: v.viable ? "通过" : "未通过",
                    }))}
                    columns={[
                      ["id", "版本"],
                      ["origin", "来源"],
                      ["viable", "评测"],
                      ["hypothesis", "改进假设"],
                    ]}
                  />
                </Block>
                <Block title="优化操作记录">
                  <Rows
                    rows={system.evolution?.operations || []}
                    columns={[
                      ["id", "操作"],
                      ["state", "状态"],
                      ["receipt", "回执"],
                    ]}
                  />
                </Block>
              </>
            )}
            {page === "guide" && (
              <>
                <Heading level={2}>让研究过程持续可见</Heading>
                <Grid columns={{ minWidth: 280, max: 3 }} gap={4}>
                  {[
                    [
                      "01 · 目标与授权",
                      "创建任务时明确研究目标、执行器、研究流程和资源上限。任务材料按课题隔离，仅保存在本地。",
                    ],
                    [
                      "02 · 实验与进度",
                      "智能体在实验开始前设计工作项，运行中更新当前动作、真实计数、失败与下一步。未知分母和过期采样会明确标记。",
                    ],
                    [
                      "03 · 证据与交付",
                      "实验终态与科学验收分别核对。成果页查看论文、PDF、图表和报告，用量页查看各模型与任务的实际消耗。",
                    ],
                  ].map(([t, b]) => (
                    <Card key={t} padding={6}>
                      <VStack gap={4}>
                        <Heading level={3}>{t}</Heading>
                        <Text>{b}</Text>
                      </VStack>
                    </Card>
                  ))}
                </Grid>
                <Block title="自动执行与修复">
                  <Text>
                    任务失败后，平台保留原始报错，调用执行智能体修复，再由控制器独立复验并继续原任务。UNKNOWN
                    状态先核对回执，避免重复提交。
                  </Text>
                  <Text>
                    停止按钮用于明确终止当前任务；恢复依据账本中的待执行和待核对工作继续。浏览页面不会启动实验。
                  </Text>
                </Block>
                <ReferenceLibrary />
                <Block title="访问与数据范围">
                  <Text>
                    左侧“工作空间地址”默认连接本机，也可填写其他设备的 IP 或地址直接切换。目标设备需要运行工作台服务并开放网络监听，首次远程连接需输入连接码。任务、模型配置与文件都属于当前连接的设备；研究内容仍保存在该设备的本地忽略目录。
                  </Text>
                </Block>
              </>
            )}
          </VStack>
        </Section>}
      </AppShell>
    </Theme>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
