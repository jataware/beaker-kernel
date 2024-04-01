import { promises as fs, Dirent } from 'fs';
import path from 'path';
import { BeakerSession } from 'beaker-kernel';

import { baseUrl, token } from './settings.json'


async function evalNotebook(contextName: string, benchmark: any) {
  const settings = {
    baseUrl,
    appUrl: baseUrl,
    wsUrl: baseUrl.replace("http", "ws"),
    token,
  };  
  const session = new BeakerSession(
    {
      settings,
      name: "Benchmarking",
      kernelName: "beaker_kernel",
      sessionId: "dev_session",
      rendererOptions: {renderers: []}
    }
  );

  session.notebook.loadFromIPynb(benchmark);
  const contextInfo = JSON.parse(session.notebook.cells[0].source.join("\n"));
  const setupResult = session.sendBeakerMessage(
      "context_setup_request",
      {
        contextName,
        contextInfo: contextInfo
      }
  );
  const startSuccess = ['error', 'abort'].indexOf(setupResult?.content?.status) === -1;
  if (!startSuccess) {
    throw new Error("Failed to start session");
  };

  for (let cell of session.notebook.cells){
    if (cell != null){
      await cell.execute(session);
    }
  }

  const resultingNotebook = session.notebook.toIPynb();
  await session.kernel.shutdown(); // TODO: Refactor when beaker-ts is updated
  return resultingNotebook;

}


async function getBenchmarks(evalDir: string, resultDir: string) {
  const items = await fs.readdir(evalDir, { withFileTypes: true });
  const contexts = items.filter((item: Dirent) => item.isDirectory());
  await fs.mkdir(resultDir);
  contexts.map(async (context:Dirent)=>{
    const resultPath = path.join(resultDir, context.name);
    await fs.mkdir(resultPath);

    const contextPath = path.join(evalDir, context.name);
    const unfilterFiles = await fs.readdir(contextPath, { withFileTypes: true });
    const files = unfilterFiles.filter(file => file.name.length <= 6 || file.name.slice(0, file.name.length - 6) !== ".ipynb")

    files.map( async (file) => {
      const filePath = path.join(contextPath, file.name);
      const notebook = JSON.parse(await fs.readFile(filePath, 'utf-8'));
      const result = evalNotebook(context.name, notebook)
      const fileContents = JSON.stringify(result);
      await fs.writeFile(path.join(resultPath, file.name), fileContents);
    })
    
  });
  await Promise.all(contexts)
}

getBenchmarks("./evaluations", "./result")

