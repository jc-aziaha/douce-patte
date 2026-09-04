// Minifie les fichiers statiques (JS via esbuild, CSS via Lightning CSS) dans dist/,
// en conservant la même arborescence que le code source pour ne rien changer aux
// chemins référencés par les pages HTML.
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const DIST = path.join(ROOT, 'dist');

function reset(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
}

function copyStaticFiles() {
  const entries = fs.readdirSync(ROOT, { withFileTypes: true });
  for (const entry of entries) {
    if (['css', 'js', 'node_modules', 'dist', 'package.json', 'package-lock.json', 'build.js'].includes(entry.name)) continue;
    const src = path.join(ROOT, entry.name);
    const dest = path.join(DIST, entry.name);
    fs.cpSync(src, dest, { recursive: true });
  }
}

const esbuildBin = require('esbuild').ESBUILD_BINARY_PATH || path.join(ROOT, 'node_modules', '@esbuild', `${process.platform}-${process.arch}`, process.platform === 'win32' ? 'esbuild.exe' : 'bin/esbuild');
const lightningcssBin = path.join(ROOT, 'node_modules', 'lightningcss-cli', process.platform === 'win32' ? 'lightningcss.exe' : 'lightningcss');
const run = (cmd, args) => execFileSync(cmd, args, { stdio: 'inherit' });

function buildJs() {
  const jsDir = path.join(ROOT, 'js');
  const outDir = path.join(DIST, 'js');
  fs.mkdirSync(outDir, { recursive: true });
  for (const file of fs.readdirSync(jsDir)) {
    run(esbuildBin, [
      path.join(jsDir, file),
      '--minify',
      '--target=es2019',
      `--outfile=${path.join(outDir, file)}`
    ]);
  }
}

function buildCss() {
  const cssDir = path.join(ROOT, 'css');
  const outDir = path.join(DIST, 'css');
  fs.mkdirSync(outDir, { recursive: true });
  for (const file of fs.readdirSync(cssDir)) {
    run(lightningcssBin, [
      '--minify',
      '--browserslist',
      path.join(cssDir, file),
      '-o', path.join(outDir, file)
    ]);
  }
}

reset(DIST);
copyStaticFiles();
buildJs();
buildCss();
console.log('Build terminé dans dist/');
