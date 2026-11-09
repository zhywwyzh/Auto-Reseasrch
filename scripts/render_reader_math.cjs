// Offline, server-side math rendering. No formula is sent to a model or API.
const fs = require('fs');
const path = require('path');
const katex = require(path.join(__dirname, '../.cache/reader-tools/node_modules/katex'));
const items = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = {};
for (const tex of items) {
  try {
    output[tex] = {html: katex.renderToString(tex, {
      throwOnError: true, strict: 'ignore', trust: false, output: 'htmlAndMathml',
    })};
  } catch (error) {
    output[tex] = {error: String(error.message)};
  }
}
process.stdout.write(JSON.stringify(output));
