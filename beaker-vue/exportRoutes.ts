import { Plugin } from 'vite';
import fs from 'fs';
import path from 'path';

export function ExportRoutesPlugin(): Plugin {
  return {
    name: 'export-routes-plugin',
    apply: 'build', // Only during build
    async writeBundle(bundle) {
      const srcPath = path.resolve('src/router/routes.json');
      const outputPath = path.resolve('dist/routes.json');
      fs.copyFileSync(srcPath, path.resolve('dist/routes.json'));
      fs.copyFileSync(srcPath, path.resolve('dist/html/routes.json'));
      console.log(`✅ Routes exported to ${outputPath}`);
    },
  }
}
