import type { DeviceState } from "../types/device";
import { formatDateTime } from "../format";

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

export function DeviceStateCard({ device }: { device: DeviceState | null }) {
  if (!device) return <section className="panel">正在載入模擬設備狀態…</section>;
  return (
    <section className="panel device-panel">
      <div className="section-title">
        <h2>模擬設備狀態</h2>
        <span className={`device-dot device-${device.state}`} />
      </div>
      <dl className="device-grid">
        <div>
          <dt>狀態</dt>
          <dd>{stateLabels[device.state]} ({device.state})</dd>
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
      </dl>
      <p className="muted">更新時間：{formatDateTime(device.updated_at)}</p>
    </section>
  );
}
