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

const processedData = computed(() => {
    if (props.mimeType === 'text/csv') {
        const lines: string[] = props.data.split('\n'); 
        const header: string[] = lines[0].split(',');
        const values = lines.slice(1).map((line) => 
            line.split(',').reduce((combined, entry, index) => 
                ({[header[index]]: entry.trim(), ...combined}), {}))
        return {
            columns: header,
            values
        }
    }
    return props.data
})

</script>

<style lang="scss">


</style>
