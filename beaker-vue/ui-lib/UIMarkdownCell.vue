<template>
    <div class="markdown-cell">
        <div 
            class="code"
            :class="{'dark-mode': theme === 'dark'}"
        >
            <Codemirror
                v-model="cell.source"
                placeholder="Your markdown"
                :extensions="codeExtensions"
                :autofocus="true"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, inject, computed } from "vue";
import { Codemirror } from "vue-codemirror";
import { oneDark } from '@codemirror/theme-one-dark';

const props = defineProps([
    "cell"
]);

const cell = ref(props.cell);
const theme = inject('theme');

const codeExtensions = computed(() => {
    const ext = [];

    if (theme.value === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

</script>

<style lang="scss">

.markdown-cell {
    display: grid;

    grid-template-areas:
        "code code code exec";

    grid-template-columns: 1fr 1fr 1fr 3rem;
}

.code {
    grid-area: code;

    .cm-editor {
        border: 1px solid var(--surface-d);
    }
    .cm-focused {
        outline: none;
        border: 1px solid var(--purple-200);
        .cm-content {
            background-color: var(--surface-a);
        }
    }
    &.dark-mode {
        .cm-focused {
            border-color: #5b3c5b;
        }
    }
}

</style>
