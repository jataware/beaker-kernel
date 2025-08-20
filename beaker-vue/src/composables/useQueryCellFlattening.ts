import { ref, watch, nextTick } from 'vue';
import { BeakerMarkdownCell, BeakerCodeCell } from 'beaker-kernel';
import type { BeakerSessionComponentType } from '../components/session/BeakerSession.vue';

// TODO our approach was affected by disappearing cells, due to localStorage
// filling up without us noticing. We could refactor/simplify this now that we're
// aware of this...

export function useQueryCellFlattening(beakerSession: () => BeakerSessionComponentType) {
    const processedQueryEvents = ref<Map<string, Set<number>>>(new Map());

    const findCellByMetadata = (parentQueryId: string, eventIndex: number, cellType: 'thought' | 'response' | 'code' | 'user_question' | 'user_answer' | 'error' | 'abort' | 'question') => {
        const notebook = beakerSession().session.notebook;
        return notebook.cells.find(cell => 
            cell.metadata?.parent_query_cell === parentQueryId &&
            cell.metadata?.query_event_index === eventIndex &&
            cell.metadata?.beaker_cell_type === cellType
        );
    };
    
    // scan existing cells
    const initializeProcessedEvents = () => {
        const notebook = beakerSession()?.session?.notebook;
        if (!notebook) return;
        
        processedQueryEvents.value.clear();
        
        for (const cell of notebook.cells) {
            if (cell.metadata?.parent_query_cell && cell.metadata?.query_event_index !== undefined) {
                const parentQueryId = cell.metadata.parent_query_cell;
                const eventIndex = cell.metadata.query_event_index;
                
                if (!processedQueryEvents.value.has(parentQueryId)) {
                    processedQueryEvents.value.set(parentQueryId, new Set());
                }
                processedQueryEvents.value.get(parentQueryId).add(eventIndex);
            }
        }
    };
    
    // insert position after a query cell
    const findInsertionPosition = (queryCellId: string): number => {
        const notebook = beakerSession().session.notebook;
        const queryCellIndex = notebook.cells.findIndex(cell => cell.id === queryCellId);
        if (queryCellIndex === -1) return notebook.cells.length; // append at end if not found
        
        // last cell that's related the query
        let insertIndex = queryCellIndex + 1;
        while (insertIndex < notebook.cells.length && 
               notebook.cells[insertIndex].metadata?.parent_query_cell === queryCellId) {
            insertIndex++;
        }
        
        return insertIndex;
    };
    
    const createThoughtCell = (thoughtContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'thought')) {
            console.warn(`Thought cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        if(thoughtContent.length === 0 || thoughtContent === null || thoughtContent === "Thinking...") {
            console.warn(`Thought cell for query ${queryCellId}, event ${eventIndex} is practically empty, skipping`);
            return;
        }

        const metadata = {
            beaker_cell_type: 'thought',
            parent_query_cell: queryCellId,
            query_event_index: eventIndex
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
            parent_query_cell: queryCellId,
            query_event_index: eventIndex
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

        const metadata = {
            beaker_cell_type: 'code',
            parent_query_cell: queryCellId,
            query_event_index: eventIndex,
            source_cell_id: codeCellId // Keep track of the original child cell ID
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

    const createErrorCell = (errorContent: any, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'error')) {
            console.warn(`Error cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        let markdownContent = '';
        if (typeof errorContent === 'string') {
            markdownContent = `**Error:**\n\n${errorContent}`;
        } else if (errorContent && typeof errorContent === 'object') {
            if (errorContent.ename && errorContent.evalue) {
                markdownContent = `**Error:**\n\n**${errorContent.ename}:** ${errorContent.evalue}`;
                if (errorContent.traceback && errorContent.traceback.length > 0) {
                    markdownContent += `\n\n\`\`\`\n${errorContent.traceback.join('\n')}\n\`\`\``;
                }
            } else {
                markdownContent = `**Error:**\n\n\`\`\`json\n${JSON.stringify(errorContent, null, 2)}\n\`\`\``;
            }
        }

        const metadata = {
            beaker_cell_type: 'error',
            parent_query_cell: queryCellId,
            query_event_index: eventIndex
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

    const createAbortCell = (abortContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'abort')) {
            console.warn(`Abort cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        const markdownContent = `**Request Aborted:**\n\n${abortContent}`;

        const metadata = {
            beaker_cell_type: 'abort',
            parent_query_cell: queryCellId,
            query_event_index: eventIndex
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

    const createQuestionCell = (questionContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'question')) {
            console.warn(`Question cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return; // don't create duplicate
        }

        const markdownContent = `**Agent Question:**\n\n${questionContent}`;

        const metadata = {
            beaker_cell_type: 'question',
            parent_query_cell: queryCellId,
            query_event_index: eventIndex
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

    const updateQuestionCellWithReply = (replyContent: string, queryCellId: string, eventIndex: number) => {
        // the question should be in a previous event index
        let questionCell = null;
        let questionEventIndex = eventIndex - 1;
        
        // look backwards for the most recent question cell
        while (questionEventIndex >= 0 && !questionCell) {
            questionCell = findCellByMetadata(queryCellId, questionEventIndex, 'question');
            questionEventIndex--;
        }
        
        if (questionCell) {
            const currentContent = questionCell.source;
            const updatedContent = `${currentContent}\n\n**User Response:**\n\n${replyContent}`;
            questionCell.source = updatedContent;
            
            console.log(`updated question cell with reply for query ${queryCellId}, event ${eventIndex}`);
            return questionCell;
        } else {
            console.warn(`no question cell found for reply in query ${queryCellId}, creating standalone reply cell`);
            return createReplyCell(replyContent, queryCellId, eventIndex);
        }
    };

    const createReplyCell = (replyContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'user_answer')) {
            console.warn(`User answer cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        const markdownContent = `**User Response:**\n\n${replyContent}`;

        const metadata = {
            beaker_cell_type: 'user_answer',
            parent_query_cell: queryCellId,
            query_event_index: eventIndex
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
                                    } else if (event.type === 'error') {
                                        createErrorCell(event.content, cell.id, eventIndex);
                                    } else if (event.type === 'abort') {
                                        console.info("Not creating abort cells for now, as the abort state is shown on query cell.")
                                    //  createAbortCell(event.content, cell.id, eventIndex);
                                    } else if (event.type === 'user_question') {
                                        createQuestionCell(event.content, cell.id, eventIndex);
                                    } else if (event.type === 'user_answer') {
                                        updateQuestionCellWithReply(event.content, cell.id, eventIndex);
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
        // createErrorCell,
        // createAbortCell,
        // createQuestionCell,
        // createReplyCell,
        // createThoughtCell,
        // createResponseCell,
        // createCodeCell,
    };
}