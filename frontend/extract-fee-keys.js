const fs = require('fs');
const c = fs.readFileSync('src/views/admin/FeeManagement.vue', 'utf8');
const keys = [...new Set([...c.matchAll(/t\('fee\.(\w+)'/g)].map(m => m[1]))].sort();
console.log(keys.join('\n'));
console.log('\nTotal:', keys.length);