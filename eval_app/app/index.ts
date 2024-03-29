import { BeakerSession } from 'beaker-ts';

import { get_benchmarks, Scenario } from './benchmarking.js'


function createSession(baseUrl:string): BeakerSession {
  // TODO: Expose settings instead of baseUrl
  const settings = {
    baseUrl: baseUrl,
    appUrl: baseUrl,
    wsUrl: baseUrl.replace("http", "ws"),
    token: "89f73481102c46c0bc13b2998f9a4fce",
  };  
  return new BeakerSession(
    {
      settings,
      name: "Benchmarking",
      kernelName: "beaker_kernel",
      sessionId: "dev_session",
      rendererOptions: {renderers: []}
    }
  );
}


async function setScenarioContext (contextName: string, scenario: Scenario, baseUrl: string) {

    const session = createSession("localhost:8080")
    const result = await session.sendBeakerMessage(
        "context_setup_request",
        {
          contextName,
          language: scenario.language, 
          contextInfo: scenario.contextInfo
        }
    );

    const startSuccess = ['error', 'abort'].indexOf(result?.content?.status) === -1  
    return startSuccess
}




get_benchmarks("./evaluations")
  .then(console.log);

