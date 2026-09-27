// node record.mjs <url> <outdir> : records a page at 1080x1920 via CDP screencast, resampled to 30 fps
import fs from 'fs';
import {spawn} from 'child_process';
const [url, out] = process.argv.slice(2);
const PORT = 9333, FPS = 30;
fs.rmSync(out, {recursive: true, force: true}); fs.mkdirSync(out + '/raw', {recursive: true}); fs.mkdirSync(out + '/seq');
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`,
  '--window-size=1080,1920', '--autoplay-policy=no-user-gesture-required', '--hide-scrollbars', '--force-device-scale-factor=1',
  `--user-data-dir=/tmp/promo-chrome-${Date.now()}`, '--enable-gpu-rasterization', 'about:blank'], {stdio: 'ignore'});
const sleep = ms => new Promise(r => setTimeout(r, ms));
let t;
for (let i = 0; i < 50; i++) { try { t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(url)}`, {method: 'PUT'})).json(); break; } catch { await sleep(200); } }
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const pend = {}; const frames = [];
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({id: i, method, params})); });
ws.onmessage = ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pend[m.id]) { pend[m.id](m.result); delete pend[m.id]; }
  if (m.method === 'Page.screencastFrame') {
    const f = `${out}/raw/${String(frames.length).padStart(5, '0')}.jpg`;
    fs.writeFileSync(f, Buffer.from(m.params.data, 'base64'));
    frames.push({f, ts: m.params.metadata.timestamp});
    send('Page.screencastFrameAck', {sessionId: m.params.sessionId});
  }
};
await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', {width: 1080, height: 1920, deviceScaleFactor: 1, mobile: false});
await send('Page.navigate', {url});
await sleep(3500);
const dur = (await send('Runtime.evaluate', {expression: 'window.DURATION', returnByValue: true})).result.value;
await send('Page.startScreencast', {format: 'jpeg', quality: 92, maxWidth: 1080, maxHeight: 1920, everyNthFrame: 1});
await sleep(400);
const t0 = Date.now() / 1000;
await send('Runtime.evaluate', {expression: 'start()'});
await sleep(dur * 1000 + 300);
await send('Page.stopScreencast');
ws.close(); chrome.kill();
// resample
const n = Math.round(dur * FPS); let j = 0, used = 0;
for (let k = 0; k < n; k++) {
  const tt = t0 + k / FPS;
  while (j + 1 < frames.length && frames[j + 1].ts <= tt) j++;
  fs.copyFileSync(frames[j].f, `${out}/seq/${String(k + 1).padStart(5, '0')}.jpg`);
}
const inWin = frames.filter(f => f.ts >= t0).length;
console.log(JSON.stringify({captured: frames.length, inWindow: inWin, effFps: +(inWin / dur).toFixed(1), out: n}));
