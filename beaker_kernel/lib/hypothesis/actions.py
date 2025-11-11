"""
Action handlers for hypothesis generation.

This module provides a mixin class that can be added to any BeakerContext
to enable hypothesis generation capabilities.
"""

import asyncio
import logging
from typing import Optional

from beaker_kernel.lib.utils import action
from beaker_kernel.lib.hypothesis.generator import HypothesisGenerator

logger = logging.getLogger(__name__)


class HypothesisGenerationMixin:
    """
    Mixin to add hypothesis generation actions to a BeakerContext.

    This provides the backend action handlers for:
    - generate_hypotheses: Start a new hypothesis generation task
    - cancel_hypothesis_generation: Cancel a running task
    - get_hypothesis_status: Check the status of a generation task
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hypothesis_generator: Optional[HypothesisGenerator] = None
        self._hypothesis_task: Optional[asyncio.Task] = None
        self._hypothesis_task_id: Optional[str] = None

    def _get_hypothesis_generator(self) -> HypothesisGenerator:
        """Lazy load the hypothesis generator."""
        if self._hypothesis_generator is None:
            # TODO: Get these from config
            self._hypothesis_generator = HypothesisGenerator(
                model_name="gpt-4o-mini",
                max_iterations=3,
                hypotheses_per_generation=10,
                evolution_top_k=3,
                tournament_size=8,
                verbose=True,
            )
        return self._hypothesis_generator

    @action(
        action_name="generate_hypotheses",
        default_payload='{"research_goal": "Your research question here", "config": {}}'
    )
    async def generate_hypotheses_action(self, message):
        """
        Start a hypothesis generation task.

        Payload:
            research_goal (str): The research question or goal
            config (dict): Optional configuration overrides
                - model_name (str): LLM model to use
                - max_iterations (int): Refinement iterations
                - hypotheses_per_generation (int): Initial count
                - evolution_top_k (int): Top K to evolve
                - tournament_size (int): Tournament rounds

        Returns:
            Status dict with task_id
        """
        print("=" * 80)
        print("GENERATE_HYPOTHESES_ACTION CALLED!!!")
        print("=" * 80)
        logger.info("GENERATE_HYPOTHESES_ACTION CALLED")
        content = message.content
        research_goal = content.get("research_goal")
        print(f"Research goal: {research_goal}")
        logger.info(f"Research goal: {research_goal}")

        if not research_goal:
            return {
                "status": "error",
                "error": "research_goal is required"
            }

        # Check if a task is already running
        if self._hypothesis_task and not self._hypothesis_task.done():
            return {
                "status": "error",
                "error": "A hypothesis generation task is already running"
            }

        # Apply config overrides if provided
        config = content.get("config", {})
        if config:
            self._hypothesis_generator = HypothesisGenerator(**config)

        # Generate a task ID
        import uuid
        task_id = str(uuid.uuid4())
        self._hypothesis_task_id = task_id

        print(f"Creating background task with ID: {task_id}")
        logger.info(f"Creating background task with ID: {task_id}")

        # Start the background task
        self._hypothesis_task = asyncio.create_task(
            self._run_hypothesis_generation(research_goal, message.header, task_id)
        )

        print(f"Background task created: {self._hypothesis_task}")
        logger.info(f"Background task created: {self._hypothesis_task}")

        return {
            "status": "started",
            "task_id": task_id,
            "research_goal": research_goal
        }

    async def _run_hypothesis_generation(self, research_goal: str, parent_header: dict, task_id: str):
        """
        Run hypothesis generation in the background with progress streaming.

        Args:
            research_goal: The research question
            parent_header: Message header for iopub routing
            task_id: Unique task identifier
        """
        print("=" * 80)
        print("_RUN_HYPOTHESIS_GENERATION STARTED")
        print(f"Task ID: {task_id}")
        print(f"Research goal: {research_goal}")
        print("=" * 80)
        logger.info(f"_run_hypothesis_generation started for task {task_id}")

        try:
            print("Getting hypothesis generator...")
            generator = self._get_hypothesis_generator()
            print("Got hypothesis generator")

            async def progress_callback(phase: str, data: dict):
                """Stream progress updates to frontend via iopub."""
                print("=" * 80)
                print(f"PROGRESS_CALLBACK CALLED: phase={phase}")
                print(f"Data: {data}")
                print(f"Task ID: {task_id}")
                print(f"Parent header: {parent_header}")
                print("=" * 80)
                logger.info(f"Sending progress update: phase={phase}, data={data}")

                content = {
                    "task_id": task_id,
                    "phase": phase,
                    **data
                }
                # print(f"Message content: {content}")  # Commented out - too verbose

                try:
                    self.send_response(
                        stream="iopub",
                        msg_or_type="hypothesis_progress",
                        content=content,
                        parent_header=parent_header
                    )
                    print("send_response() completed successfully")
                    logger.info("Progress update sent")
                except Exception as e:
                    print(f"ERROR in send_response: {e}")
                    logger.error(f"Error sending progress: {e}", exc_info=True)

            # Run generation with streaming progress
            print("About to call generator.generate_hypotheses...")
            print(f"Progress callback: {progress_callback}")
            result = await generator.generate_hypotheses(
                research_goal=research_goal,
                progress_callback=progress_callback
            )
            print("generator.generate_hypotheses completed")

            # Send final complete message
            self.send_response(
                stream="iopub",
                msg_or_type="hypothesis_complete",
                content={
                    "task_id": task_id,
                    "result": result
                },
                parent_header=parent_header
            )

        except asyncio.CancelledError:
            logger.info(f"Hypothesis generation task {task_id} was cancelled")
            self.send_response(
                stream="iopub",
                msg_or_type="hypothesis_cancelled",
                content={
                    "task_id": task_id,
                    "message": "Task was cancelled"
                },
                parent_header=parent_header
            )
        except Exception as e:
            logger.error(f"Error in hypothesis generation: {e}", exc_info=True)
            self.send_response(
                stream="iopub",
                msg_or_type="hypothesis_error",
                content={
                    "task_id": task_id,
                    "error": str(e),
                    "message": f"An error occurred: {str(e)}"
                },
                parent_header=parent_header
            )

    @action(
        action_name="cancel_hypothesis_generation",
        default_payload='{"task_id": ""}'
    )
    async def cancel_hypothesis_generation_action(self, message):
        """
        Cancel a running hypothesis generation task.

        Payload:
            task_id (str): The task ID to cancel

        Returns:
            Status dict
        """
        content = message.content
        task_id = content.get("task_id")

        if not task_id:
            return {"status": "error", "error": "task_id is required"}

        if task_id != self._hypothesis_task_id:
            return {"status": "error", "error": "Invalid task_id"}

        if self._hypothesis_task and not self._hypothesis_task.done():
            self._hypothesis_task.cancel()
            return {"status": "cancelled", "task_id": task_id}
        else:
            return {"status": "error", "error": "No task is running"}

    @action(
        action_name="get_hypothesis_status",
        default_payload='{"task_id": ""}'
    )
    async def get_hypothesis_status_action(self, message):
        """
        Get the status of a hypothesis generation task.

        Payload:
            task_id (str): The task ID to check

        Returns:
            Status dict with task info
        """
        content = message.content
        task_id = content.get("task_id")

        if not task_id:
            return {"status": "error", "error": "task_id is required"}

        if task_id != self._hypothesis_task_id:
            return {"status": "unknown", "task_id": task_id}

        if not self._hypothesis_task:
            return {"status": "not_found", "task_id": task_id}

        if self._hypothesis_task.done():
            if self._hypothesis_task.cancelled():
                return {"status": "cancelled", "task_id": task_id}
            elif self._hypothesis_task.exception():
                return {
                    "status": "error",
                    "task_id": task_id,
                    "error": str(self._hypothesis_task.exception())
                }
            else:
                return {"status": "completed", "task_id": task_id}
        else:
            return {"status": "running", "task_id": task_id}
