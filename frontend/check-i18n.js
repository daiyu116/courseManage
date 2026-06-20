const fs = require('fs');

const zh = JSON.parse(fs.readFileSync('src/locales/zh-CN.json', 'utf8'));
const en = JSON.parse(fs.readFileSync('src/locales/en.json', 'utf8'));

function getAllKeys(obj, prefix = '') {
  let keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      keys = keys.concat(getAllKeys(v, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

const zhKeys = getAllKeys(zh);
const enKeys = getAllKeys(en);

const zhSet = new Set(zhKeys);
const enSet = new Set(enKeys);

console.log('=== Key Count ===');
console.log('zh-CN keys:', zhKeys.length);
console.log('en keys:', enKeys.length);

console.log('\n=== Duplicates in zh-CN ===');
const zhSeen = new Set();
const zhDups = [];
zhKeys.forEach(k => { if (zhSeen.has(k)) zhDups.push(k); zhSeen.add(k); });
console.log(zhDups.length ? zhDups.join(', ') : 'None');

console.log('\n=== Duplicates in en ===');
const enSeen = new Set();
const enDups = [];
enKeys.forEach(k => { if (enSeen.has(k)) enDups.push(k); enSeen.add(k); });
console.log(enDups.length ? enDups.join(', ') : 'None');

console.log('\n=== Missing in en (present in zh-CN) ===');
const missingEn = zhKeys.filter(k => !enSet.has(k));
console.log(missingEn.length ? missingEn.join('\n') : 'None');

console.log('\n=== Missing in zh-CN (present in en) ===');
const missingZh = enKeys.filter(k => !zhSet.has(k));
console.log(missingZh.length ? missingZh.join('\n') : 'None');