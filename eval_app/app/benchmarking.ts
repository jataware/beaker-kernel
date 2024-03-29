import { promises as fs, Dirent } from 'fs';
import path from 'path';

type ResponseType = "code" | "text"

type Goal = {
  type: ResponseType;
  response: string;
};

type ScenarioStep = {
  prompt: string;
  evaluate: string;
  goals: Array<Goal>;
};

type Scenario = {
  title: string;
  language: string;
  contextInfo: Object;
  steps: Array<ScenarioStep>;
}

type Benchmarks = { [key: string]: Array<Scenario> }

async function get_benchmarks(eval_dir: string): Promise<Benchmarks> {
  const items = await fs.readdir(eval_dir, { withFileTypes: true });
  console.log(items)
  const isEvalFile = (item: Dirent) => {
    return !item.isDirectory() && item.name.slice(item.name.length - 5);
  }

  const benchmarks: Benchmarks = {};

  for (const file of items.filter(isEvalFile)) {
    console.log(file)
    const filePath = path.join(eval_dir, file.name);
    const contextName = file.name.slice(0, file.name.length - 5);

    const scenarios = JSON.parse(await fs.readFile(filePath, 'utf-8'));
    benchmarks[contextName] = scenarios;
  }

  return benchmarks;
}

export { get_benchmarks, Benchmarks, Scenario, ScenarioStep, Goal, ResponseType }
