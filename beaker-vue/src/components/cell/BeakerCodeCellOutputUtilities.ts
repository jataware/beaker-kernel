// general behaviors for how to handle user representation of outputs

type OutputType = "stream" | "error" | "execute_result" | "display_data";

const formatStream = (output, shortened: boolean): string => {
    return shortened ? output.name : `Text (stream: ${output.name})`;
}

const formatError = (output, shortened: boolean): string => {
    return shortened ? output?.ename : `${output?.ename}: ${output?.evalue}`;
}

const formatExecuteResult = (output, shortened: boolean): string => {
    const values = Object.keys(output?.data || {});
    const userFacingNames = {
        "text/plain": "Text",
        "image/png": "Image"
    };
    const result = values.sort().map(
        (format) => Object.keys(userFacingNames)
            .includes(format) ? userFacingNames[format] : format)
            .join(", ");
    return shortened ? result.split(",")[0] : result;
}

export const formatOutputs = (
    outputs: {output_type: OutputType} & {[key: string]: any}[], 
    shorten: OutputType[]
): string => {
    const formatters: {[key in OutputType]: (output: object, shortened: boolean) => string} = {
        "stream": formatStream,
        "error": formatError,
        "execute_result": formatExecuteResult,
        "display_data": formatExecuteResult
    };
    if (outputs[0] === undefined) {
        return '';
    }
    // collapse multiple contiguous stream outputs into one 
    if (outputs.every(output => output?.output_type === 'stream')) {
        return formatters['stream'](outputs[0], shorten.includes(outputs[0]?.output_type))
    }
    const headers: string[] = outputs.map(output =>
        formatters[output?.output_type](output, shorten.includes(output?.output_type)));
    return headers.join(", ");
}

// get the most meaningful icon for an execute_result; e.g. plaintext is less than image/png
const executeResultIcon = (output) => {
    const outputTypeIconMap = {
        "image/png": "pi pi-chart-bar",
        "text/html": "pi pi-table",
        "text/plain": "pi pi-align-left",
        "": "pi pi-code",
    };
    const precedenceList = ["image/png", "text/html", "text/plain"];
    const values = Object.keys(output?.data || {});
    for (const desiredType of precedenceList) {
        if (values.includes(desiredType)) {
            return outputTypeIconMap[desiredType];
        }
    }
    return ""
};

export const chooseOutputIcon = (outputs: {output_type: OutputType}[]) => {
    const outputTypes = outputs.map(output => output.output_type);

    const result = outputs.find(output =>
        output.output_type === "execute_result"
        || output.output_type === "display_data");
    if (result !== undefined) {
        return executeResultIcon(result);
    }

    if (outputTypes.includes("error")) {
        return "pi pi-times-circle"
    }

    return "pi pi-pen-to-square"
}
