<template>
    <Button
        @click="handleAction"
        icon="pi pi-search"
        size="small"
        :disabled="busy"
        :loading="busy"
        :pt="{
            loadingIcon: {
                class: ['search-background']
            }
        }"
    >
    </Button>
</template>

<script lang="ts" setup>
import { ref, defineProps, withDefaults } from "vue";
import Button from "primevue/button";
import ProgressSpinner from 'primevue/progressspinner';

interface Props {
    action: () => Promise<any>;
}

const props = withDefaults(defineProps<Props>(), {
    async action() {
        console.log("no action defined");
    }
})

const busy = ref<boolean>(false);

const handleAction = async () => {
    busy.value = true;
    try {
        await props.action();
    }
    finally {
        busy.value = false;
    }
}

</script>

<style lang="scss">
    .search-background {
        &::after {
            content: "X";
        }
    }
</style>
