import { ContentsManager, Contents } from '@jupyterlab/services';

export type Example = {
    query: string,
    code: string,
    notes?: string
}

export type AttachedFile = {
    filepath: string,
    name: string
}

export type Datasource = {
    description: string,
    source: string,
    attached_files: AttachedFile[],
    examples: Example[],
    slug: string,
    name: string,
    url: string
}

export const formatExamples = (examples: Example[]): string => {
    if (examples.length === 0) {
        return "";
    }
    const newlineIndent = '\n    ';
    const reindentFollowingLines = str => str.replaceAll('\n', newlineIndent)
    const blockScalar = str => `|${newlineIndent}${reindentFollowingLines(str)}`
    return examples.map((example) =>
        [
            `- query: ${example.query}`,
            `code: ${blockScalar(example.code)}`,
            example?.notes ? `notes: ${blockScalar(example.notes)}` : '',
        ].join('\n  ')
    ).join('\n')
}

export const formatDatasource = (datasource: Datasource): string => {
    //const slug = slugWrapper.value;
    const indentLines = (text: string) => text
        .split('\n')
        .map(line => `\n    ${line}`)
        .join('')
        .trim()
    const indentedDescription = indentLines(datasource?.description ?? "")
    const indentedContents = indentLines(datasource?.source ?? "")
    const filePayload = (datasource?.attached_files ?? [])
        .map(attachment =>
            `${attachment.name}: !load_txt documentation/${attachment.filepath}\n`)
        .join('\n')

    const template = `
name: ${datasource.name}
slug: ${datasource.slug}
cache_key: api_assistant_${datasource.slug}
examples: !load_yaml documentation/examples.yaml

description: |
    ${indentedDescription}

${filePayload}

documentation: !fill |
    ${indentedContents}
`
    return template;
}

export const getDatasourceSlug = (datasource: Datasource): string =>
    datasource?.slug ?? datasource.name.toLowerCase().replaceAll(' ', '_');

export const getDatasourceFolder = (datasource: Datasource): string => {
    const url = datasource?.url;
    if (url === undefined || url === null || url === '') {
        return getDatasourceSlug(datasource);
    }
    else if (url.endsWith('api.yaml')) {
        return url.slice(0, -1 * ("/api.yaml".length))
    }
    return url
}

export const writeDatasource = async (
    folderRoot: string,
    datasource: Datasource,
    onerror: (e: any) => void
) => {
    const contentManager = new ContentsManager({});
    const formattedDatasource = formatDatasource(datasource)
    const basepath = `${folderRoot}/${getDatasourceFolder(datasource)}`

    const type = 'text/plain'
    const content = btoa(formattedDatasource);
    const format = 'base64';
    const fileObj: Partial<Contents.IModel> = {
        type,
        format,
        content,
    };

    // create examples if it doesn't exist, but don't fill it yet.
    const examplePath = `${basepath}/documentation/examples.yaml`;
    try {
        await contentManager.get(examplePath);
    }
    catch (e) {
        await contentManager.save(examplePath, {type, format, content: btoa("")});
    }

    try {
        await contentManager.save(`${basepath}/api.yaml`, fileObj);
        await contentManager.save(examplePath, {
            type,
            format,
            content: btoa(formatExamples(datasource?.examples ?? []))
        })
    }
    catch(e) {
        onerror(e)
        return;
    }
}

export const createFoldersForDatasource = async (folderRoot: string, datasource: Datasource) => {
    const contentManager = new ContentsManager({});
    const basepath = `${folderRoot}/${getDatasourceFolder(datasource)}`

    // is the datasource slug folder present?
    try {
        const targetDir = await contentManager.get(basepath);
        if (targetDir.type !== 'directory') {
            throw "Slug overlaps with existing non-directory file."
        }
    }
    catch (e) {
        const directory = await contentManager.newUntitled({
            path: folderRoot,
            type: 'directory'
        })
        await contentManager.rename(directory.path, basepath);
    }

    // what about documentation/?
    try {
        const targetDir = await contentManager.get(`${basepath}/documentation`);
        if (targetDir.type !== 'directory') {
            throw "slug/documentation overlaps with existing non-directory file. Is there a file named 'documentation' with no extension?"
        }
    }
    catch (e) {
        const subdirectory = await contentManager.newUntitled({
            path: basepath,
            type: 'directory'
        })
        await contentManager.rename(subdirectory.path, `${basepath}/documentation`)
    }
}

export const handleAddExampleMessage = async (
    msg,
    folderRoot: string,
    datasources: Datasource[],
    success: () => void,
    failure?: (error: string) => void
) => {
    const fail = (message: string) => {
        if (failure !== undefined) {
            failure(message)
        }
    }
    const content = msg?.content;
    if (content === undefined) {
        fail("Message content was undefined.")
        return;
    }

    const target = datasources?.find((integration) =>
        integration?.name === content?.integration);

    if (target === undefined) {
        fail(`Integration ${content?.integration} does not exist in integrations list.`)
        return;
    }

    if (target?.examples === undefined) {
        target.examples = []
    }

    target.examples.push(
        {
            code: content?.code ?? "",
            query: content?.query ?? "",
            notes: content?.notes ?? ""
        }
    )

    await writeDatasource(folderRoot, target, (e) => fail(e));
    success();
}

export const handleAddIntegrationMessage = async (
    msg,
    folderRoot: string,
    datasources: Datasource[],
    success: () => void,
    failure?: (error: string) => void
) => {
    const fail = (message: string) => {
        if (failure !== undefined) {
            failure(message)
        }
    }
    const content = msg?.content;
    if (content === undefined) {
        fail("Message content was undefined.")
        return;
    }

    const name = content.integration;
    const slug = name.toLowerCase().replaceAll(' ', '_');
    const description = content.description;

    const target = datasources?.find((integration) =>
        integration?.name === content?.integration);

    if (target !== undefined) {
        fail(`Integration ${content?.integration} already exists.`)
        return;
    }
    // unimplemented yet -- fetch schema and add base URL instructions based on the tool message contents
}
