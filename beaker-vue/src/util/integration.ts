import { BeakerSession } from 'beaker-kernel';

export interface IntegrationResource {
    // names must be coherent with python resource class
    resource_type: string
    integration: string
    resource_id: string
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

export type IntegrationResourceMap = {
    [id in string]: IntegrationResource
}

export interface Integration {
    description: string
    source: string;
    slug: string
    name: string
    url: string
    provider: string
    // important: resources are loaded via a second API call and may not exist or be filled on the object
    resources?: IntegrationResourceMap;
}

export type IntegrationMap = {[key in string]: Integration};

export type IntegrationProviders = {
    [key in string]: {
        mutable: boolean
        integrations: Integration[]
    }
}

export interface IntegrationInterfaceState {
    selected: string | undefined
    integrations: IntegrationMap
    unsavedChanges: boolean
    selectedIntegrationResources: IntegrationResourceMap
}

export interface IntegrationAPIRouteDetails {
    sessionId: string,
    integrationId?: string,
    resourceType?: string,
    resourceId?: string,
}

const toRoute = (details: IntegrationAPIRouteDetails) =>
    [details.sessionId, details?.integrationId, details?.resourceType, details?.resourceId]
    .filter((x) => x)
    .join('/')

async function integrationApiWrapper<T>(
    method: "GET" | "POST",
    route: IntegrationAPIRouteDetails,
    body?: object
): Promise<T> {
    const path = `/beaker/integrations/${toRoute(route)}`
    console.log(`api request: ${path}`)
    const response = await fetch(path, {
        method,
        headers: {
            "Content-Type": "application/json"
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) })
    });
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    const json = await response.json() as T;
    return json
}

export const getIntegrationProviderType = (integration: Integration) => integration.provider.split(":")[0]

export const getIntegrationProviderSlug = (integration: Integration) => integration.provider.split(":")[1]

export const listIntegrations = async (sessionId: string): Promise<IntegrationMap> => {
    return (await integrationApiWrapper<{"integrations": IntegrationMap}>("GET", {sessionId})).integrations;
}

export const postIntegration = async (sessionId: string, integrationId: string, body: object): Promise<IntegrationMap> => {
    return await integrationApiWrapper<IntegrationMap>("POST", {sessionId, integrationId}, body);
}

export const getResourcesForIntegration = async (sessionId: string, integrationId: string) => {
    const routeDetails = {
        sessionId,
        integrationId,
        resourceType: "all"
    }
    return (await integrationApiWrapper<{"resources": IntegrationResourceMap}>("GET", routeDetails)).resources;
}

export function filterByResourceType<T>(resources: IntegrationResourceMap | undefined, resource_type: string): {[key in string]: T} {
    return Object.fromEntries(Object.entries(resources ?? {})
        .filter(([_, resource]) => resource.resource_type === resource_type)) as {[key in string]: T};
}
