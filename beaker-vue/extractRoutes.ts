const fs = require('fs');
const path = require('path');

console.log("Extracting routes...")

// Generate just enough mock `window` to allow router to work.
globalThis.window = <any>{
    location: {
        "href":"about:blank",
        "origin":"",
        "protocol":"about:",
        "host":"blank",
        "hostname":"blank",
        "port":"",
        "pathname":"",
        "search":"",
        "hash":""
    },
    history: {
        length: 0,
        scrollRestoration: "auto",
        state: {},
    },
    addEventListener() {},
    removeEventListener() {},

};
globalThis.location = globalThis.window.location;

const router = (await import('./src/router'))?.default;
const routes = router.getRoutes();

const output = Object.fromEntries(routes.map((route) => [route.path, {path: route.path, name: route.name, component: route.components?.default}]))

const routeJson = JSON.stringify(output, undefined, 2);

console.log("Writing route json files...");
console.log("  dist/routes.json");
fs.writeFileSync(path.resolve('dist/routes.json'), routeJson);
console.log("  dist/html/routes.json");
fs.writeFileSync(path.resolve('dist/html/routes.json'), routeJson);
console.log("Done.")
