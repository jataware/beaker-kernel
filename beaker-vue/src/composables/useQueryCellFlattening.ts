import { ref, watch, nextTick } from 'vue';
import type { BeakerSessionComponentType } from '../components/session/BeakerSession.vue';
import brainIconSvg from '../assets/brain.svg?raw';

export function useQueryCellFlattening(beakerSession: () => BeakerSessionComponentType) {
    const processedQueryEvents = ref<Map<string, Set<number>>>(new Map());

    const createIconPrefix = (cellType: string) => {
        const iconHtml = brainIconSvg.replace('<svg', '<svg style="width: 1em; height: 1em; vertical-align: middle; margin-right: 0.25em;"');
        return `${iconHtml}`;
    };

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

    const createCellMetadata = (cellType: string, queryCellId: string, eventIndex: number, additionalMetadata = {}) => {
        return {
            beaker_cell_type: cellType,
            parent_query_cell: queryCellId,
            query_event_index: eventIndex,
            ...additionalMetadata
        };
    };

    function moveCellToPosition(currentIndex: number, insertPosition: number) {
        if (currentIndex !== insertPosition) {
            beakerSession().session.notebook.moveCell(currentIndex, insertPosition);
        }
    }

    const createAndPositionMarkdownCell = (source: string, queryCellId: string, metadata: any) => {
        const insertPosition = findInsertionPosition(queryCellId);
        const markdownCell = beakerSession().session.addMarkdownCell(source, metadata);

        moveCellToPosition(beakerSession().session.notebook.cells.length - 1, insertPosition);
        return markdownCell;
    };

    const createAndPositionCodeCell = (source: string, queryCellId: string, metadata: any, outputs: any[] = []) => {
        const insertPosition = findInsertionPosition(queryCellId);
        const codeCell = beakerSession().session.addCodeCell(source, metadata, outputs);

        moveCellToPosition(beakerSession().session.notebook.cells.length - 1, insertPosition);
        return codeCell;
    };
    
    const createThoughtCell = (thoughtContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'thought')) {
            console.warn(`Thought cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        if(thoughtContent.length === 0 || thoughtContent === null || thoughtContent === "Thinking...") {
            console.warn(`Thought cell for query ${queryCellId}, event ${eventIndex} is practically empty, skipping`);
            return;
        }

        const metadata = createCellMetadata('thought', queryCellId, eventIndex);
        const iconPrefix = createIconPrefix('thought');
        const source = `${iconPrefix}**Agent Thought:**\n\n${thoughtContent}`;
        
        return createAndPositionMarkdownCell(source, queryCellId, metadata);
    };
    
    const createResponseCell = (responseContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'response')) {
            console.warn(`Response cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        let markdownContent = '';
        if (typeof responseContent === 'string') {
            markdownContent = `${createIconPrefix('response')}**Agent Response:**\n\n${responseContent}`;
        } else if (responseContent && typeof responseContent === 'object') {
            markdownContent = `${createIconPrefix('response')}**Agent Response:**\n\n\`\`\`json\n${JSON.stringify(responseContent, null, 2)}\n\`\`\``;
        }

        const metadata = createCellMetadata('response', queryCellId, eventIndex);
        
        return createAndPositionMarkdownCell(markdownContent, queryCellId, metadata);
    };
    
    const createCodeCell = (codeCellId: string, queryCell: any, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'code')) {
            console.warn(`Code cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        const childCell = queryCell.children?.find(child => child.id === codeCellId);
        if (!childCell) {
            console.warn(`Code cell ${codeCellId} not found in query cell children`);
            return;
        }

        const metadata = createCellMetadata('code', queryCellId, eventIndex, {
            source_cell_id: codeCellId
        });

        const newCodeCell = createAndPositionCodeCell(
            childCell.source, 
            queryCellId, 
            metadata, 
            childCell.outputs || []
        );
        
        newCodeCell.execution_count = childCell.execution_count;
        if (childCell.last_execution) {
            newCodeCell.last_execution = {
                ...childCell.last_execution,
                status: 'ok' // or ... childCell.last_execution.status ...
            };
        } else if (childCell.outputs && childCell.outputs.length > 0) {
            // outputs with no execution state => assume it was executed successfully
            // since this is added by the agent
            newCodeCell.last_execution = {
                status: 'ok',
                checkpoint_index: undefined // TODO
            };
        }
        
        return newCodeCell;
    };

    const createErrorCell = (errorContent: any, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'error')) {
            console.warn(`Error cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        let markdownContent = '';
        if (typeof errorContent === 'string') {
            markdownContent = `${createIconPrefix('error')}**Error:**\n\n${errorContent}`;
        } else if (errorContent && typeof errorContent === 'object') {
            if (errorContent.ename && errorContent.evalue) {
                markdownContent = `${createIconPrefix('error')}**Error:**\n\n**${errorContent.ename}:** ${errorContent.evalue}`;
                if (errorContent.traceback && errorContent.traceback.length > 0) {
                    markdownContent += `\n\n\`\`\`\n${errorContent.traceback.join('\n')}\n\`\`\``;
                }
            } else {
                markdownContent = `${createIconPrefix('error')}**Error:**\n\n\`\`\`json\n${JSON.stringify(errorContent, null, 2)}\n\`\`\``;
            }
        }

        const metadata = createCellMetadata('error', queryCellId, eventIndex);
        
        return createAndPositionMarkdownCell(markdownContent, queryCellId, metadata);
    };

    const createAbortCell = (abortContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'abort')) {
            console.warn(`Abort cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        const markdownContent = `${createIconPrefix('abort')}**Request Aborted:**\n\n${abortContent}`;
        const metadata = createCellMetadata('abort', queryCellId, eventIndex);
        
        return createAndPositionMarkdownCell(markdownContent, queryCellId, metadata);
    };

    const createQuestionCell = (questionContent: string, queryCellId: string, eventIndex: number) => {
        if (findCellByMetadata(queryCellId, eventIndex, 'question')) {
            console.warn(`Question cell for query ${queryCellId}, event ${eventIndex} exists, skipping`);
            return;
        }

        const markdownContent = `${createIconPrefix('question')}**Agent Question:**\n\n${questionContent}`;
        const metadata = createCellMetadata('question', queryCellId, eventIndex);
        
        return createAndPositionMarkdownCell(markdownContent, queryCellId, metadata);
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

        const markdownContent = `${createIconPrefix('user_answer')}**User Response:**\n\n${replyContent}`;
        const metadata = createCellMetadata('user_answer', queryCellId, eventIndex);
        
        return createAndPositionMarkdownCell(markdownContent, queryCellId, metadata);
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
                                        return;
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