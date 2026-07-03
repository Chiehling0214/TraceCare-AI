import { useState } from "react";

import type { DeviceState } from "../types/device";
import { formatDateTime } from "../format";
import { reconnectDevice } from "../api/device";

const stateLabels: Record<string, string> = {
  NORMAL: "正常",
  WARNING: "待確認",
  CRITICAL: "高風險",
  ACKNOWLEDGED: "已確認未結案"
};

const ledLabels: Record<string, string> = {
  GREEN_SOLID: "綠燈恆亮",
  YELLOW_BLINKING: "黃燈閃爍",
  YELLOW_SOLID: "黃燈恆亮",
  RED_BLINKING: "紅燈閃爍"
};

const buzzerLabels: Record<string, string> = {
  OFF: "關閉",
  SHORT_BEEP: "短音提示",
  INTERMITTENT: "間歇提示"
};

const connectionLabels: Record<string, string> = {
  CONNECTED: "已連線",
  DISCONNECTED: "未連線",
  RECONNECTING: "重新連線中",
  OFFLINE: "離線"
};

export function DeviceStateCard({ device, onReconnect }: { device: DeviceState | null; onReconnect?: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleReconnect() {
    setBusy(true);
    setError(null);
    try {
      await reconnectDevice();
      await onReconnect?.();
    } catch {
      setError("設備重新連線失敗；筆電警示仍可使用。");
    } finally {
      setBusy(false);
    }
  }

  if (!device) return <section className="panel">正在載入設備狀態…</section>;
  return (
    <section className="panel device-panel">
      <div className="section-title">
        <div>
          <h2>設備狀態</h2>
          <p className="muted">非醫療設備；硬體離線時使用筆電警示 fallback。</p>
        </div>
        <span className={`device-dot device-${device.state}`} />
      </div>
      {device.fallback_active && (
        <div className="message warning">硬體目前不可用，Dashboard 與筆電警示 fallback 仍會依後端狀態運作。</div>
      )}
      {error && <div className="message error">{error}</div>}
      <dl className="device-grid">
        <div>
          <dt>狀態</dt>
          <dd>{stateLabels[device.state]} ({device.state})</dd>
        </div>
        <div>
          <dt>Adapter</dt>
          <dd>{device.adapter_mode}</dd>
        </div>
        <div>
          <dt>連線狀態</dt>
          <dd>{connectionLabels[device.connection_status] ?? device.connection_status}</dd>
        </div>
        <div>
          <dt>LED</dt>
          <dd>{ledLabels[device.led] ?? device.led}</dd>
        </div>
        <div>
          <dt>蜂鳴器</dt>
          <dd>{buzzerLabels[device.buzzer] ?? device.buzzer}</dd>
        </div>
        <div>
          <dt>連線</dt>
          <dd>{device.connection}</dd>
        </div>
        <div>
          <dt>Heartbeat</dt>
          <dd>{formatDateTime(device.last_heartbeat_at)}</dd>
        </div>
        <div>
          <dt>Fallback</dt>
          <dd>{device.fallback_active ? "啟用" : "未啟用"}</dd>
        </div>
      </dl>
      {device.last_error && <p className="muted">設備錯誤：{device.last_error}</p>}
      <div className="actions">
        <button className="button secondary" disabled={busy} onClick={handleReconnect}>
          {busy ? "重新連線中…" : "重新連線設備"}
        </button>
      </div>
      <p className="muted">更新時間：{formatDateTime(device.updated_at)}</p>
    </section>
  );
}
