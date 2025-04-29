export interface Route {
    name: string;
    path: string;
    component: string;
}

export type Routes = { [key: str]: Route }
