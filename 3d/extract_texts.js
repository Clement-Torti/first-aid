// writes 3d/texts.json: {lang: [{f, t}]}; {N} kept for the TTS normalizer
const fs = require('fs');
global.navigator = {languages: []}; global.location = {search: ''}; global.localStorage = {getItem: () => null};
eval(fs.readFileSync(__dirname + '/../i18n.js', 'utf8') + ';global.LANGS=LANGS');
const out = {};
for (const [lg, L] of Object.entries(LANGS)) {
  const a = out[lg] = [];
  for (const [id, [, , steps]] of Object.entries(L.p)) steps.forEach((s, i) => a.push({f: `${id}_${i}`, t: s[0] + '. ' + s[1]}));
  a.push({f: 'done', t: L.ui.stay + '. ' + L.ui.stay2.replace(/<br>/g, ' ')});
  a.push({f: 'late', t: L.ui.late});
}
fs.writeFileSync(__dirname + '/texts.json', JSON.stringify(out, null, 1));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])));
