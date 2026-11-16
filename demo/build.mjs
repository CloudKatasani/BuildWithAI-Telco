// Inlines styles and scripts into one self-contained page (dist/datacrew-telco-studio.html)
// for hosting as a single file. Run: node demo/build.mjs
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const read = (f) => readFileSync(join(here, f), 'utf8');
let html = read('index.html');
const body = html.split('<!--ARTIFACT-START-->')[1].split('<!--ARTIFACT-END-->')[0]
  .replace('<!--HEAD-END-->\n</head>\n<body>', '')
  .replace('<link rel="stylesheet" href="styles.css">', `<style>\n${read('styles.css')}\n</style>`)
  .replace('<script src="data.js"></script>', `<script>\n${read('data.js')}\n</script>`)
  .replace('<script src="app.js"></script>', `<script>\n${read('app.js')}\n</script>`);
mkdirSync(join(here, 'dist'), { recursive: true });
writeFileSync(join(here, 'dist', 'datacrew-telco-studio.html'), body.trim() + '\n');
console.log('wrote dist/datacrew-telco-studio.html', body.length, 'bytes');
