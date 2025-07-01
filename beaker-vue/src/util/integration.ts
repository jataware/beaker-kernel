import { BeakerSession } from 'beaker-kernel';

// todo -- removeold examples below

export interface Example { // todo
    query: string
    code: string
    notes?: string
}

export interface AttachedFile { // todo
    filepath: string
    name: string
    content?: string
}

// todo remove old examples above

export interface IntegrationResource {
    type: string
    integration?: string
}

export interface IntegrationExample extends IntegrationResource {
    type: "example";
    query: string
    code: string
    notes?: string
}

export interface IntegrationAttachedFile extends IntegrationResource {
    type: "file";
    filepath: string
    name: string
    content?: string
}

export type IntegrationResources = {
    [id in string]: IntegrationResource
}

export interface Integration {
    description: string;
    source: string;
    slug: string
    name: string
    url: string
    resources?: IntegrationResources;
    // remove below fields
    attached_files: AttachedFile[]; // remove
    examples: Example[]  // remove
}

export type IntegrationProviders = {
    [key in string]: {
        mutable: boolean
        integrations: Integration[]
    }
}

// export const handleAddExampleMessage = async (
//     msg,
//     integrations: Integration[],
//     session: BeakerSession,
// ) => {
//     const content = msg?.content;
//     if (content === undefined) {
//         throw "Message content was undefined."
//     }

//     const target = integrations?.find((integration) =>
//         integration?.slug === content?.integration
//         || integration?.name === content?.integration
//     );

//     if (target === undefined) {
//         throw `Integration ${content?.integration} does not exist in integrations list.`
//     }

//     if (target?.examples === undefined || target?.examples === null) {
//         target.examples = []
//     }

//     target.examples.push(
//         {
//             code: content?.code ?? "",
//             query: content?.query ?? "",
//             notes: content?.notes ?? ""
//         }
//     )
//     //session.executeAction('add_example', target);
// }

// export const handleAddIntegrationMessage = async (
//     msg,
//     integrations: Integration[],
//     session: BeakerSession,
// ) => {
//     const content = msg?.content;
//     if (content === undefined) {
//         throw "Message content was undefined."
//     }

//     const name = content.integration;
//     const slug = name.toLowerCase().replaceAll(' ', '_');
//     const description = content.description;
//     const baseUrl = content.base_url;
//     const schema = content.schema;

//     const target = integrations?.find((integration) =>
//         integration?.name === content?.integration);
//     if (target !== undefined) {
//         throw `Integration ${content?.integration} already exists.`
//     }

//     const integration: Integration = {
//         description,
//         source: `
// The base URL for the service is '${baseUrl}'
// Below is the OpenAPI schema for the desired service.

// {schema}`,
//         attached_files: [
//             {
//                 name: 'schema',
//                 filepath: 'schema.yaml',
//                 content: schema
//             }
//         ],
//         examples: [],
//         slug,
//         name,
//         url: ''
//     }
//     integrations.push(integration);
//     //session.executeAction('save_integration', integration);
// }

