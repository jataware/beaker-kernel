<template>
    <div class="chat-history-container" ref="chatHistoryRef" @scroll="handleScroll">
        <div v-for="(cell, index) in chatCells" 
             :key="cell.id || `chat-cell-${index}`" 
             class="chat-message"
            :cell-id="cell.id || `chat-cell-${index}`"
             :class="{
                'user-message': cell.cell_type === 'query',
                'agent-message': cell.type === 'thought' || cell.type === 'response',
                'agent-thinking': cell.status === 'busy',
                'has-code-cell-sibling': cell.code_cell_id
             }">
            <!-- User message -->
            <div v-if="cell.cell_type === 'query'" class="user-query"
                @click="executeCell(cell)"
            >
                <div class="message-content">{{ cell.source }}</div>
            </div>
            
            <!-- Agent thought message -->
            <div v-else-if="cell.type === 'thought'" 
            class="agent-thought"
            :parent-cell-id="cell.parent_cell_id"
            @click="scrollToCodeCell(cell.code_cell_id)"
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
    },
    selectCell: {
        type: Function,
        required: true,
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
    // console.log("queryCells", queryCells.map(cell => toRaw(cell)));
    
    for (const queryCell of queryCells) {
        // Add the query cell itself
        result.push(queryCell);
        
        // Add events from the query cell
        // console.log("queryCell events", toRaw(queryCell.events));
        if (queryCell.events) {
            for (const [index, event] of queryCell.events.entries()) {
                if (event.type === 'thought' || event.type === 'response') {
                    // TODO if the next event of the index, for thought events, is of type code_cell, 
                    // add the code cell id as a property to the event

                    try {
                        if(event.type === 'thought' && queryCell.events[index + 1]?.type === 'code_cell') {
                            // console.log("found thought event with code cell following it at index:", index);
                            // console.log("queryCell.events[index + 1]", toRaw(queryCell.events[index + 1]));
                            event.code_cell_id = queryCell.events[index + 1]?.content?.cell_id;
                            event.parent_cell_id = queryCell.id;
                        }
                    } catch(e) { // in case we went over index; ignore

                    }

                    result.push(event); // push the event, or the cell?
                }
            }
        }
    }

     console.log("result", result.map(event => toRaw(event)));
    
    return result;
});

// this works, although hacky for now
const executeCell = (cell) => {
    cell.execute(session);
}

const scrollToCodeCell = (cellId) => {
    props.selectCell(cellId);

    // In case the start of selectedcell isn't visible when selected->scrolled to it
    // scroll to the start of the cell
    setTimeout(() => {
        const cell = document.querySelector(`[cell-id="${cellId}"]`);
        if(cell) {
            cell.scrollIntoView({ behavior: 'smooth' });
        }
    }, 400);
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
    border-bottom: 1px solid var(--surface-d);
    
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

.has-code-cell-sibling {
    border: 1px solid;
    border-radius: var(--border-radius);
    border-color: #7254f366;
    cursor: pointer;
}
</style>