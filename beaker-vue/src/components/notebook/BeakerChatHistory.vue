<template>
    <div class="chat-history-container" ref="chatHistoryRef" @scroll="handleScroll">
        <div v-for="(cell, index) in chatCells" 
             :key="cell.id || `chat-cell-${index}`" 
             class="chat-message"
             :class="{
                'user-message': cell.cell_type === 'query',
                'agent-message': cell.type === 'thought' || cell.type === 'response',
                'agent-thinking': cell.status === 'busy'
             }">
            <!-- User message -->
            <div v-if="cell.cell_type === 'query'" class="user-query"
                @click="executeCell(cell)"
            >
                <div class="message-content">{{ cell.source }}</div>
            </div>
            
            <!-- Agent thought message -->
            <div v-else-if="cell.type === 'thought'" class="agent-thought"
            @click="scrollToCodeCell(cell)"
            >
                <div class="message-content">
                    <span class="thought-icon"><BrainIcon /></span>
                    {{ cell.content?.thought || cell.content }}
                </div>
            </div>
            
            <!-- Agent response message -->
            <div v-else-if="cell.type === 'response'" class="agent-response">
                <div class="message-content">{{ cell.content }}</div>
            </div>
        </div>

        <!-- Thinking indicator (when agent is processing) -->
        <div v-if="isAgentThinking" class="agent-thinking-indicator">
            <span class="thought-icon"><BrainIcon /></span>
            <span>Thinking</span>
            <span class="thinking-animation"></span>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, inject, computed, onMounted, watch, defineProps, defineEmits, defineExpose, toRaw } from 'vue';
import { BeakerSession } from 'beaker-kernel/src';
import { type BeakerNotebookComponentType } from './BeakerNotebook.vue';
import BrainIcon from '../../assets/icon-components/BrainIcon.vue';

const props = defineProps({
    codeCellsContainer: {
        type: Object,
        required: false,
        default: null
    },
    beakerNotebookRef: {
        type: Object,
        required: false,
        default: null
    }
});

const emit = defineEmits(['scroll']);

const session = inject<BeakerSession>('session', null);
const notebook = inject<BeakerNotebookComponentType>("notebook", null);
const chatHistoryRef = ref<HTMLElement | null>(null);

// Get all chat-related cells (query cells, thought events, and response events)
const chatCells = computed(() => {
    if (!session?.notebook?.cells) return [];

    const result = [];
    
    // Add top-level query cells
    const queryCells = session.notebook.cells.filter(cell => cell.cell_type === 'query');
    console.log("queryCells", queryCells);
    
    for (const queryCell of queryCells) {
        // Add the query cell itself
        result.push(queryCell);
        
        // Add events from the query cell
        if (queryCell.events) {
            for (const event of queryCell.events) {
                if (event.type === 'thought' || event.type === 'response') {
                    result.push(event); // push the event, or the cell?
                }
            }
        }
    }
    
    return result;
});

const executeCell = (cell) => {
    // console.log("executeCell", toRaw(cell));
    // console.log("beakerNotebookRef", props.beakerNotebookRef);
    // props.beakerNotebookRef.value?.executeCell(cellId);
    // console.log("notebook", notebook);
    // console.log("cell.execute", cell.execute);
    // console.log("session", session);
    cell.execute(session);
}

const scrollToCodeCell = (cell) => {
    console.log("scrollToCodeCell", toRaw(cell));
    console.log("beakerNotebookRef raw", toRaw(props.beakerNotebookRef));
    // console.log("codeCellsContainer", toRaw(props.codeCellsContainer));
    // console.log("", toRaw(props.codeCellsContainerRef));
    console.log("beakernotebookref", props?.beakerNotebookRef?.value);

    // props.beakerNotebookRef.value?.scrollToCell(cell.id);
}


// Check if agent is currently thinking
const isAgentThinking = computed(() => {
    if (!session?.notebook?.cells) return false;
    return session.notebook.cells.some(cell => cell.status === 'busy');
});

// Scroll to bottom when new messages arrive
watch(() => chatCells.value.length, () => {
    setTimeout(() => {
        scrollToBottom();
    }, 100);
});

// Scroll to bottom on mount
onMounted(() => {
    scrollToBottom();
});

// Function to scroll to bottom of chat
const scrollToBottom = () => {
    if (chatHistoryRef.value) {
        chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
    }
};

// Emit scroll event to parent component
const handleScroll = (event) => {
    emit('scroll', event);
};

defineExpose({
    scrollToBottom,
    chatHistoryEl: chatHistoryRef
});
</script>

<style lang="scss">
.chat-history-container {
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    
    .chat-message {
        margin-bottom: 0.5rem;
        
        &.user-message {
            align-self: flex-end;
            max-width: 80%;
        }
        
        &.agent-message {
            align-self: flex-start;
            max-width: 80%;
        }
    }
    
    .user-query {
        background-color: var(--surface-d);
        border-radius: var(--border-radius);
        padding: 0.75rem 1rem;
        
        .message-content {
            white-space: pre-wrap;
        }
    }
    
    .agent-thought, .agent-response {
        background-color: var(--surface-c);
        border-radius: var(--border-radius);
        padding: 0.75rem 1rem;
        
        .message-content {
            white-space: pre-wrap;
        }
    }
    
    .thought-icon {
        display: inline-block;
        height: 1rem;
        margin-right: 0.5rem;
        vertical-align: middle;
        
        svg {
            fill: currentColor;
            stroke: currentColor;
            width: 1rem;
            margin: 0;
        }
    }
    
    .agent-thinking-indicator {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin-top: 0.5rem;
        opacity: 0.7;
    }
    
    .thinking-animation:after {
        overflow: hidden;
        display: inline-block;
        vertical-align: bottom;
        position: relative;
        animation: thinking-ellipsis 2000ms steps(48, end) infinite;
        content: "\2026\2026\2026\2026"; /* ascii code for the ellipsis character */
        width: 4em;
    }
}

@keyframes thinking-ellipsis {
    from {
        right: 4em;
    }
    to {
        right: -4em;
    }
}
</style>