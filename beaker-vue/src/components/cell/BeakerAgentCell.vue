<template>
    <div class="agent-cell">
        <div class="agent-cell-header">
            <div class="agent-cell-title">
                <div v-if="useBrainIcon" 
                     class="agent-cell-icon brain-icon" 
                     >
                     <BrainIconSvg />
                </div>
                <i v-else 
                   :class="headerIconClass" 
                   class="agent-cell-icon">
                </i>
                <span class="agent-cell-label">{{ cellTypeLabel }}</span>
            </div>
            <div class="agent-cell-actions">
                <Button v-if="showMoreDetailsButton" 
                        @click="showMoreDetails" 
                        size="small" 
                        severity="secondary"
                        text>
                    More Details
                </Button>
            </div>
        </div>
        
        <div class="agent-cell-content" v-html="renderedMarkdown"></div>
    </div>
</template>

<script setup lang="ts">
import { ref, inject, computed, nextTick, onBeforeMount, getCurrentInstance, onBeforeUnmount} from "vue";
import { marked } from 'marked';
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
// import type { BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';
import Button from 'primevue/button';
import BrainIconSvg from '../../assets/icon-components/BrainIcon.vue';

const props = defineProps([
    "cell"
]);

const instance = getCurrentInstance();
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const cell = ref(props.cell);

const agentCellType = computed(() => props.cell?.metadata?.beaker_cell_type);

const cellTypeLabel = computed(() => {
    const labels = {
        'thought': 'Assistant',
        'response': 'Assistant',
        'user_question': 'Assistant',
        'error': 'Error',
        'abort': 'Aborted'
    };
    return labels[agentCellType.value] || 'Assistant';
});

const headerIconClass = computed(() => {
    const iconClasses = {
        'thought': 'pi pi-sparkles',
        'response': 'pi pi-sparkles',
        'user_question': 'pi pi-question-circle',
        'error': 'pi pi-times-circle',
        'abort': 'pi pi-ban'
    };
    return iconClasses[agentCellType.value] || 'pi pi-comment';
});

// Not using for now
const useBrainIcon = computed(() => {
    return false;
    return ['thought', 'response'].includes(agentCellType.value);
});

const showMoreDetailsButton = computed(() => {
    return false;
    // TODO add to provide info to users on LLM work done
    return ["thought", "response", "user_question"].includes(agentCellType.value);
});

const renderedMarkdown = computed(() => {
    if (typeof props.cell === 'object' && props.cell) {
        const { source } = props.cell;
        const cellSource = Array.isArray(source) ? source.join("") : source;
        
        const cleanedSource = cellSource
            .replace(/^\*\*[^*]+\*\*\n\n/, '');
            
        return marked.parse(cleanedSource);
    }
    return "";
});

const showMoreDetails = () => {
    // TODO implement
    console.log('Show more details for cell:', props.cell.id);
};

const execute = () => {
}

const enter = (position?: "start" | "end" | number) => {
}

const clear = () => {
}

const exit = () => {
}

defineExpose({
    execute,
    enter,
    exit,
    clear,
    model: cell,
});

onBeforeMount(() => {
    marked.setOptions({
     });
    beakerSession.cellRegistry[cell.value.id] = instance.vnode;
})

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<script lang="ts">
import { BeakerMarkdownCell } from "beaker-kernel";
export default {
    modelClass: BeakerMarkdownCell,
    icon: "pi pi-pencil",
};
</script>

<style lang="scss">

.agent-cell {
    margin-bottom: 0.25rem;
}

.agent-cell-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 1.95rem;
}

.agent-cell-title {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-weight: 600;
    color: var(--p-primary-500);
}

.agent-cell-actions {
    display: flex;
}

.agent-cell-content {
    padding-right: 2rem;
    
    img {
        max-width: 100%;
    }
     p {
        margin-block-start: 0.25rem;
        margin-block-end: 0rem;
     }
}

.brain-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    
    svg {
        width: 1.2em;
        height: 1.2em;
    }
}

.brain-icon {
    .brain-svg-path {
        fill: var(--p-primary-500);
    }
}

</style>
