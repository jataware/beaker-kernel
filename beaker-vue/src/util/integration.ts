import { BeakerSession } from 'beaker-kernel';

export class Example {
    query: string
    code: string
    notes?: string
}

export class AttachedFile {
    filepath: string
    name: string
    content?: string
}

export class Integration {
    description: string;
    source: string;
    attached_files: AttachedFile[];
    examples: Example[]
    slug: string
    name: string
    url: string
}

export type IntegrationProviders = {
    [key in string]: {
        mutable: boolean
        integrations: Integration[]
    }
}

export const handleAddExampleMessage = async (
    msg,
    integrations: Integration[],
    session: BeakerSession,
) => {
    const content = msg?.content;
    if (content === undefined) {
        throw "Message content was undefined."
    }

    const target = integrations?.find((integration) =>
        integration?.slug === content?.integration
        || integration?.name === content?.integration
    );

    if (target === undefined) {
        throw `Integration ${content?.integration} does not exist in integrations list.`
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
    //session.executeAction('add_example', target);
}

export const handleAddIntegrationMessage = async (
    msg,
    integrations: Integration[],
    session: BeakerSession,
) => {
    const content = msg?.content;
    if (content === undefined) {
        throw "Message content was undefined."
    }

    const name = content.integration;
    const slug = name.toLowerCase().replaceAll(' ', '_');
    const description = content.description;
    const baseUrl = content.base_url;
    const schema = content.schema;

    const target = integrations?.find((integration) =>
        integration?.name === content?.integration);
    if (target !== undefined) {
        throw `Integration ${content?.integration} already exists.`
    }

    const integration: Integration = {
        description,
        source: `
The base URL for the service is '${baseUrl}'
Below is the OpenAPI schema for the desired service.

{schema}`,
        attached_files: [
            {
                name: 'schema',
                filepath: 'schema.yaml',
                content: schema
            }
        ],
        examples: [],
        slug,
        name,
        url: ''
    }
    integrations.push(integration);
    //session.executeAction('save_integration', integration);
}

