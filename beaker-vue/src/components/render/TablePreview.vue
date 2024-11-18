<template>
    <div class="table-renderer">
        <DataTable 
            :value="processedData.values"
            paginator 
            :rows="20" 
            :rowsPerPageOptions="[10, 20, 50]"
        >
            <Column 
                v-for="column in processedData.columns"
                :field="column"
                :header="column"
                :key="column"
            >
            
            </Column>
        </DataTable>
    </div>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ColumnGroup from 'primevue/columngroup';   // optional
import Row from 'primevue/row';                   // optional


const props = defineProps([
    "data",
    "mimeType"
]);

const processSeparatedValues = (rowSeparator, valueSeparator): 
    {columns: string[], values: object[]} => 
{
    const rows: string[] = props.data.split(rowSeparator); 
    const header: string[] = rows[0].split(valueSeparator);
    const values = rows.slice(1).map((row) => 
        row.split(',').reduce((combined, entry, index) => 
            ({[header[index]]: entry.trim(), ...combined}), {}))
    return {
        columns: header,
        values,
    }
}

const processedData = computed(() => {
    if (props.mimeType === 'text/csv') {
        return processSeparatedValues('\n', ',');
    }
    if (props.mimeType === 'text/tsv') {
        return processSeparatedValues('\t', ',');
    }
    return props.data
})

</script>

<style lang="scss">


</style>
