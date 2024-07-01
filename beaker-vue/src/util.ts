/**
 *
 **/
export function capitalize(s: string) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 *
 **/
export function getDateTime() {
    const t = new Date();
    // convert the local time zone offset from minutes to milliseconds
    const z = t.getTimezoneOffset() * 60 * 1000;
    // subtract the offset from t
    const tLocalNumber = Number(t) - z;
    // create shifted Date object
    const tLocal = new Date(tLocalNumber);
    // convert to ISO format string
    let iso = tLocal.toISOString();
    // drop the milliseconds and zone
    iso = iso.split(".")[0];
    // replace the T with _, and : with , (: aren't allowed on filenames)
    iso = iso.replace('T', '_').replace(/:/g,',');
    return iso;
}

/**
 *
 **/
export function downloadFileDOM(data: string, filename: string, mimeType: string) {
    const rawData = null;
    const blob = new Blob([data], {type: mimeType});

    const nav = (window.navigator as any);

    if (nav.msSaveOrOpenBlob) {
        nav.msSaveBlob(blob, filename);
    }
    else {
        const elem = window.document.createElement('a');
        elem.href = window.URL.createObjectURL(blob);
        elem.download = filename;
        document.body.appendChild(elem);
        elem.click();
        document.body.removeChild(elem);
    }
}
