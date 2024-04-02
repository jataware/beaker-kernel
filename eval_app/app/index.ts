import fs = require("fs");
import path = require('path');
import beaker = require('beaker-kernel');
import settings =  require('./settings.json');


async function evalNotebook(contextName: string, benchmark: any) {
  const config = {
    baseUrl: settings.baseUrl,
    appUrl: settings.baseUrl,
    wsUrl: settings.baseUrl.replace("http", "ws"),
    token: settings.token,
  };  
  const session = new beaker.BeakerSession(
    {
      settings: config,
      name: "Benchmarking",
      kernelName: "beaker_kernel",
      sessionId: "dev_session",
      rendererOptions: {renderers: []}
    }
  );

  session.notebook.loadFromIPynb(benchmark);
  const rawContextInfo = session.notebook.cells[0].source; 
  const contextInfo = JSON.parse(
    typeof rawContextInfo === "string" ? rawContextInfo : rawContextInfo.join("\n")
  );
  const startMsg = session.sendBeakerMessage(
      "context_setup_request",
      {
        contextName,
        contextInfo: contextInfo
      }
  );
  const setupResult = await startMsg.done
  const startSuccess = 'status' in setupResult.content && ['error', 'abort'].indexOf(setupResult.content.status) === -1;
  if (!startSuccess) {
      throw new Error("Failed to start session");
  };

  for (let cell of session.notebook.cells){
    if ('execute' in cell && typeof cell.execute === 'function'){
      cell.execute(session);
    }
  }

  const resultingNotebook = session.notebook.toIPynb();
  await session.kernel.shutdown(); // TODO: Refactor when beaker-ts is updated
  return resultingNotebook;

}


async function getBenchmarks(evalDir: string, resultDir: string) {
  const items = await fs.promises.readdir(evalDir, { withFileTypes: true });
  const contexts = items.filter((item: fs.Dirent) => item.isDirectory());
  await fs.promises.mkdir(resultDir);
  contexts.map(async (context:fs.Dirent)=>{
    const resultPath = path.join(resultDir, context.name);
    await fs.promises.mkdir(resultPath);

    const contextPath = path.join(evalDir, context.name);
    const unfilterFiles = await fs.promises.readdir(contextPath, { withFileTypes: true });
    const files = unfilterFiles.filter(file => file.name.length <= 6 || file.name.slice(0, file.name.length - 6) !== ".ipynb")

    files.map( async (file) => {
      const filePath = path.join(contextPath, file.name);
      const notebook = JSON.parse(await fs.promises.readFile(filePath, 'utf-8'));
      const result = evalNotebook(context.name, notebook)
      const fileContents = JSON.stringify(result);
      await fs.promises.writeFile(path.join(resultPath, file.name), fileContents);
    })
    
  });
  await Promise.all(contexts)
}

getBenchmarks("./evaluations", "./result")

