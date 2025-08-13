import { ref, watch, nextTick } from 'vue';
import { BeakerMarkdownCell, BeakerCodeCell } from 'beaker-kernel';
import type { BeakerSessionComponentType } from '../components/session/BeakerSession.vue';

// TODO our approach was affected by disappearing cells, due to localStorage
// filling up without us noticing. We could refactor/simplify this now that we're
// aware of this...

export function useQueryCellFlattening(beakerSession: () => BeakerSessionComponentType) {
    const processedQueryEvents = ref<Map<string, Set<number>>>(new Map());
    
    const findCellByMetadata = (parentQueryId: string, eventIndex: number, cellType: 'thought' | 'response' | 'code') => {
        const notebook = beakerSession().session.notebook;
        return notebook.cells.find(cell => 
            cell.metadata?.beaker_parent_query === parentQueryId &&
            cell.metadata?.beaker_event_index === eventIndex &&
            cell.metadata?.beaker_cell_type === cellType
        );
    };
    
    // scan existing cells
    const initializeProcessedEvents = () => {
        const notebook = beakerSession()?.session?.notebook;
        if (!notebook) return;
        
        processedQueryEvents.value.clear();
        
        for (const cell of notebook.cells) {
            if (cell.metadata?.beaker_parent_query && cell.metadata?.beaker_event_index !== undefined) {
                const parentQueryId = cell.metadata.beaker_parent_query;
                const eventIndex = cell.metadata.beaker_event_index;
                
                if (!processedQueryEvents.value.has(parentQueryId)) {
                    processedQueryEvents.value.set(parentQueryId, new Set());
                }
                processedQueryEvents.value.get(parentQueryId).add(eventIndex);
                // console.log(`marking event ${eventIndex} as processed, query: ${parentQueryId}`);
            }
        }
    };
    
    // insert position after a query cell
    const findInsertionPosition = (queryCellId: string): number => {
        const notebook = beakerSession().session.notebook;
        const queryCellIndex = notebook.cells.findIndex(cell => cell.id === queryCellId);
        if (queryCellIndex === -1) return notebook.cells.length; // Append at end if not found
        
        // last cell that's related the query
        let insertIndex = queryCellIndex + 1;
        while (insertIndex < notebook.cells.length && 
               notebook.cells[insertIndex].metadata?.beaker_parent_query === queryCellId) {
            insertIndex++;
        }
        
        return insertIndex;
    };
    
    const createThoughtCell = (thoughtContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'thought')) {
            console.warn(`Thought cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        const metadata = {
            beaker_cell_type: 'thought',
            beaker_parent_query: queryCellId,
            beaker_event_index: eventIndex
        };

        const markdownCell = new BeakerMarkdownCell({
            cell_type: "markdown",
            source: `**Agent Thought:**\n\n${thoughtContent}`,
            metadata
        });
        
        const insertPosition = findInsertionPosition(queryCellId);
        
        beakerSession().session.notebook.insertCell(markdownCell, insertPosition);
        
        return markdownCell;
    };
    
    const createResponseCell = (responseContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'response')) {
            console.warn(`Response cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        let markdownContent = '';
        if (typeof responseContent === 'string') {
            markdownContent = `**Agent Response:**\n\n${responseContent}`;
        } else if (responseContent && typeof responseContent === 'object') {
            markdownContent = `**Agent Response:**\n\n\`\`\`json\n${JSON.stringify(responseContent, null, 2)}\n\`\`\``;
        }

        const metadata = {
            beaker_cell_type: 'response',
            beaker_parent_query: queryCellId,
            beaker_event_index: eventIndex
        };

        const markdownCell = new BeakerMarkdownCell({
            cell_type: "markdown",
            source: markdownContent,
            metadata
        });
        
        const insertPosition = findInsertionPosition(queryCellId);
        beakerSession().session.notebook.insertCell(markdownCell, insertPosition);
        
        return markdownCell;
    };
    
    const createCodeCell = (codeCellId: string, queryCell: any, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'code')) {
            console.warn(`Code cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        // console.log(`creating code cell for query ${queryCellId}, event ${eventIndex}`);

        const childCell = queryCell.children?.find(child => child.id === codeCellId);
        if (!childCell) {
            console.warn(`Code cell ${codeCellId} not found in query cell children`);
            return;
        }

        // TODO rename these fields for clarity
        const metadata = {
            beaker_cell_type: 'code',
            beaker_parent_query: queryCellId,
            beaker_event_index: eventIndex,
            beaker_original_id: codeCellId // Keep track of the original child cell ID
        };

        const newCodeCell = new BeakerCodeCell({
            cell_type: "code",
            source: childCell.source,
            metadata,
            outputs: childCell.outputs || []
        });
        
        newCodeCell.execution_count = childCell.execution_count;
        
        const insertPosition = findInsertionPosition(queryCellId);
        
        beakerSession().session.notebook.insertCell(newCodeCell, insertPosition);
        
        return newCodeCell;
    };
    
    const setupQueryCellFlattening = (cells: () => any[]) => {
        watch(
            cells,
            (cellsArray) => {
                if (!cellsArray) return;
                
                if (processedQueryEvents.value.size === 0) {
                    initializeProcessedEvents();
                }
                
                for (const cell of cellsArray) {
                    if (cell.cell_type === 'query') {
                        if (!processedQueryEvents.value.has(cell.id)) {
                            processedQueryEvents.value.set(cell.id, new Set());
                        }
                        
                        watch(
                            () => cell.events,
                            (events) => {
                                if (!events || events.length === 0) return;
                                
                                const processedEvents = processedQueryEvents.value.get(cell.id);
                                
                                const isCompleted = events.length > 0 && 
                                    ['response', 'error', 'abort'].includes(events[events.length - 1].type);
                                    
                                if (isCompleted && processedEvents.size === events.length) {
                                    console.log(`Query ${cell.id} is completed and all events processed, skipping`);
                                    return;
                                }
                                
                                events.forEach((event, eventIndex) => {
                                    if (processedEvents.has(eventIndex)) {
                                        return; // already processed
                                    }
                                    
                                    console.log(`Processing new event ${eventIndex} of type ${event.type}`);
                                    
                                    processedEvents.add(eventIndex);
                                    
                                    if (event.type === 'thought' && event.content?.thought) {
                                        createThoughtCell(event.content.thought, cell.id, eventIndex);
                                    } else if (event.type === 'code_cell' && event.content?.cell_id) {
                                        nextTick(() => {
                                            createCodeCell(event.content.cell_id, cell, cell.id, eventIndex);
                                        });
                                    } else if (event.type === 'response') {
                                        createResponseCell(event.content, cell.id, eventIndex);
                                    }
                                });
                            },
                            { deep: true, immediate: true }
                        );
                    }
                }
            },
            { deep: true, immediate: true }
        );
    };
    
    const resetProcessedEvents = () => {
        processedQueryEvents.value.clear();
    };
    
    return {
        processedQueryEvents,
        setupQueryCellFlattening,
        resetProcessedEvents,
        initializeProcessedEvents,
    };
}