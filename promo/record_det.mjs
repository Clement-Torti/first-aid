// deterministic: node record_det.mjs <url> <outdir>
import fs from 'fs';
import {spawn} from 'child_process';
const [url, out] = process.argv.slice(2);
const PORT = 9334, FPS = 30;
fs.rmSync(out, {recursive: true, force: true}); fs.mkdirSync(out + '/seq', {recursive: true});
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`,
  '--window-size=1080,1920', '--autoplay-policy=no-user-gesture-required', '--hide-scrollbars', '--force-device-scale-factor=1',
  `--user-data-dir=/tmp/promo-chrome-${Date.now()}`, 'about:blank'], {stdio: 'ignore'});
const sleep = ms => new Promise(r => setTimeout(r, ms));
let t;
for (let i = 0; i < 50; i++) { try { t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(url)}`, {method: 'PUT'})).json(); break; } catch { await sleep(200); } }
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const pend = {};
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({id: i, method, params})); });
ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend[m.id]) { pend[m.id](m.result || m.error); delete pend[m.id]; } };
await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', {width: 1080, height: 1920, deviceScaleFactor: 1, mobile: false});
await send('Page.navigate', {url});
await sleep(4000);
const dur = (await send('Runtime.evaluate', {expression: 'window.DURATION', returnByValue: true})).result.value;
const n = Math.round(dur * FPS); const T0 = Date.now();
for (let k = 0; k < n; k++) {
  const r = await send('Runtime.evaluate', {expression: `renderFrame(${(k / FPS).toFixed(5)})`, awaitPromise: true});
  if (r.exceptionDetails) console.log('ERR', k, JSON.stringify(r.exceptionDetails).slice(0, 300));
  const s = await send('Page.captureScreenshot', {format: 'jpeg', quality: 92});
  fs.writeFileSync(`${out}/seq/${String(k + 1).padStart(5, '0')}.jpg`, Buffer.from(s.data, 'base64'));
  if (k % 150 === 0) console.log('frame', k, ((Date.now() - T0) / 1000).toFixed(0) + 's');
}
ws.close(); chrome.kill();
console.log('done', n);
