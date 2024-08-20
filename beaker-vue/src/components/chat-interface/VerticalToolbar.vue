<template>
    <Toolbar class="vertical-toolbar">
        <template #start>
            <slot name="start">
                <slot name="start-extra"></slot>
            </slot>
        </template>
        <template #center>
            <slot name="center">
                <slot name="center-extra"></slot>
            </slot>
        </template>
        <template #end>
            <slot name="end">
                <slot name="end-extra"></slot>
            </slot>
        </template>
    </Toolbar>
</template>

<script setup lang="tsx">
import Toolbar from "primevue/toolbar";
</script>

<style lang="scss">
.vertical-toolbar.p-toolbar {
    flex-direction: column;
    padding: 0.5rem;
    background: none;
    border: none;
}
.vertical-toolbar.p-toolbar div {
    flex-direction: column;
}
.vertical-toolbar-divider {
    background-color: var(--surface-200);
    height: 1px;
    width: 80%
}

.vertical-toolbar .p-toolbar-group-center {
    width: 80%;
}

</style>