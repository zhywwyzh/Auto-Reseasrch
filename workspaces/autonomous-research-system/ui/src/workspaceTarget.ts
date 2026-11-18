export const workspacePath = "/workspaces/autonomous-research-system/runtime.html";

export function workspaceOrigin(input: string): string {
  const value = input.trim();
  if (!value) throw Error("请输入工作空间 IP 或地址");
  const url = new URL(value.includes("://") ? value : "http://" + value);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password ||
      url.search || url.hash || !["/", workspacePath].includes(url.pathname)) {
    throw Error("请填写 IP、IP:端口或 HTTP/HTTPS 地址，不要包含密码或查询参数");
  }
  // An IP alone uses the workbench port. Explicit URL schemes retain standard ports.
  if (!value.includes("://") && !url.port && !/:\d+$/.test(value)) url.port = "18767";
  return url.origin;
}

export function newCreationId(): string {
  // randomUUID requires HTTPS/localhost; getRandomValues also works over LAN HTTP.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
