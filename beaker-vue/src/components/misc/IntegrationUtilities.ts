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

export type Integration = {
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
            `- query: "${example.query}"`,
            `code: ${blockScalar(example.code)}`,
            example?.notes ? `notes: ${blockScalar(example.notes)}` : '',
        ].join('\n  ')
    ).join('\n')
}

export const formatIntegration = (integration: Integration): string => {
    //const slug = slugWrapper.value;
    const indentLines = (text: string) => text
        .split('\n')
        .map(line => `\n    ${line}`)
        .join('')
        .trim()
    const indentedDescription = indentLines(integration?.description ?? "")
    const indentedContents = indentLines(integration?.source ?? "")
    const filePayload = (integration?.attached_files ?? [])
        .map(attachment =>
            `${attachment.name}: !load_txt documentation/${attachment.filepath}\n`)
        .join('\n')

    const template = `
name: ${integration.name}
slug: ${integration.slug}
cache_key: api_assistant_${integration.slug}
examples: !load_yaml documentation/examples.yaml

description: |
    ${indentedDescription}

${filePayload}

documentation: !fill |
    ${indentedContents}
`
    return template;
}

export const getIntegrationSlug = (integration: Integration): string =>
    integration?.slug ?? integration.name.toLowerCase().replaceAll(' ', '_');

export const getIntegrationFolder = (integration: Integration): string => {
    const url = integration?.url;
    if (url === undefined || url === null || url === '') {
        return getIntegrationSlug(integration);
    }
    else if (url.endsWith('api.yaml')) {
        return url.slice(0, -1 * ("/api.yaml".length))
    }
    return url
}

export const writeIntegration = async (
    folderRoot: string,
    integration: Integration,
    onerror: (e: any) => void
) => {
    const contentManager = new ContentsManager({});
    const formattedDatasource = formatIntegration(integration)
    const basepath = `${folderRoot}/${getIntegrationFolder(integration)}`

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
            content: btoa(formatExamples(integration?.examples ?? []))
        })
    }
    catch(e) {
        if (onerror !== undefined) {
            onerror(e)
        }
    }
}

export const createFoldersForIntegration = async (folderRoot: string, integration: Integration) => {
    const contentManager = new ContentsManager({});
    const basepath = `${folderRoot}/${getIntegrationFolder(integration)}`

    // is the integration slug folder present?
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
    integrations: Integration[],
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

    const target = integrations?.find((integration) =>
        integration?.name === content?.integration);

    if (target === undefined) {
        fail(`Integration ${content?.integration} does not exist in integrations list.`)
        return;
    }

    if (target?.examples === undefined || target?.examples === null) {
        target.examples = []
    }

    target.examples.push(
        {
            code: content?.code ?? "",
            query: content?.query ?? "",
            notes: content?.notes ?? ""
        }
    )

    await writeIntegration(folderRoot, target, (e) => fail(e));
    success();
}

export const handleAddIntegrationMessage = async (
    msg,
    folderRoot: string,
    integrations: Integration[],
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
    const baseUrl = content.base_url;
    const schema = content.schema;

    const target = integrations?.find((integration) =>
        integration?.name === content?.integration);
    if (target !== undefined) {
        fail(`Integration ${content?.integration} already exists.`)
        return;
    }

    const integration: Integration = {
        description,
        source: '',
        attached_files: [
            {
                name: 'schema',
                filepath: 'schema.yaml'
            }
        ],
        examples: [],
        slug,
        name,
        url: ''
    }
    await createFoldersForIntegration(folderRoot, integration);
    const basepath = `${folderRoot}/${getIntegrationFolder(integration)}`
    const schemaFile: Partial<Contents.IModel> = {
        type: 'text/plain',
        format: 'base64',
        content: btoa(schema),
    };
    const examplePath = `${basepath}/documentation/schema.yaml`;
    const contentManager = new ContentsManager({});
    await contentManager.save(examplePath, schemaFile);

    const openAPIWrapper = `
The base URL for the service is '${baseUrl}'
Below is the OpenAPI schema for the desired service.

{schema}`
    integration.source = openAPIWrapper;
    integrations.push(integration);
    await writeIntegration(folderRoot, integration, failure);
    success();
}

