"""
Action handlers for hypothesis generation.

This module provides a mixin class that can be added to any BeakerContext
to enable hypothesis generation capabilities.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from beaker_kernel.lib.utils import action
from beaker_kernel.lib.hypothesis.generator import (
    HypothesisGenerator,
    DEFAULT_MODEL_NAME,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_HYPOTHESES_PER_GENERATION,
    DEFAULT_EVOLUTION_TOP_K,
)

logger = logging.getLogger(__name__)


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object to ensure it's JSON-serializable.

    This handles common issues like:
    - Unescaped quotes in strings
    - Invalid unicode characters
    - Non-serializable types
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, str):
        # Ensure string is valid by encoding/decoding
        try:
            # Test if it's JSON-serializable
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # If not, try to clean it
            return obj.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    elif isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    else:
        # For other types, convert to string
        return str(obj)


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
        """Lazy load the hypothesis generator with defaults from generator.py."""
        if self._hypothesis_generator is None:
            self._hypothesis_generator = HypothesisGenerator(
                model_name=DEFAULT_MODEL_NAME,
                max_iterations=DEFAULT_MAX_ITERATIONS,
                hypotheses_per_generation=DEFAULT_HYPOTHESES_PER_GENERATION,
                evolution_top_k=DEFAULT_EVOLUTION_TOP_K,
                verbose=False,  # Set to False to reduce log noise
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

            # Run generation with streaming results
            print("About to call generator.generate_hypotheses_streaming...")
            print(f"Progress callback: {progress_callback}")

            last_state = None
            async for node_name, state in generator.generate_hypotheses_streaming(
                research_goal=research_goal,
                progress_callback=progress_callback
            ):
                print(f"Node completed: {node_name}")
                print(f"State has {len(state.get('hypotheses', []))} hypotheses")
                last_state = state

                try:
                    sanitized_state = sanitize_for_json(state)

                    # Emit hypothesis_update for the hypothesis list
                    self.send_response(
                        stream="iopub",
                        msg_or_type="hypothesis_update",
                        content={
                            "task_id": task_id,
                            "node_name": node_name,
                            "state": sanitized_state
                        },
                        parent_header=parent_header
                    )

                    # ALSO emit rich agent-style output for hierarchical display
                    # Some nodes emit MULTIPLE outputs (one per hypothesis/matchup)
                    agent_outputs = self._format_agent_output(node_name, sanitized_state)
                    if agent_outputs:
                        # agent_outputs is now a LIST of outputs
                        for agent_output in agent_outputs:
                            await progress_callback("agent_output", {
                                "message": agent_output["message"],
                                "agent_name": agent_output["agent_name"],
                                "agent_output": agent_output["output"],
                                "progress": agent_output.get("progress", 50),
                                "phase": agent_output.get("phase"),
                                "iteration": agent_output.get("iteration")
                            })

                    print(f"Node {node_name} output sent successfully")
                except Exception as e:
                    print(f"ERROR sending node output: {e}")
                    logger.error(f"Error sending node output: {e}", exc_info=True)

            print("generator.generate_hypotheses_streaming completed")

            # Send final complete message with last state
            self.send_response(
                stream="iopub",
                msg_or_type="hypothesis_complete",
                content={
                    "task_id": task_id,
                    "result": sanitize_for_json(last_state) if last_state else {}
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

    def _format_agent_output(self, node_name: str, state: dict) -> list:
        """
        Format node output to match the agent output format expected by frontend.

        Maps CoScientist-LG node names to agent display format with rich output.
        Returns a LIST of outputs (some nodes produce multiple outputs).
        Frontend expects agent_output as a JSON STRING (it will JSON.parse it).
        """
        import json

        # Determine phase and iteration from state
        current_iteration = state.get("current_iteration", 0)

        # Check if we're in a refinement iteration
        # Nodes that ONLY appear in iterations (never in initial phase)
        is_iteration_only_node = node_name in ["meta_review", "evolve", "proximity"]

        # Check if we've started iterations by looking for iteration-specific data
        # similarity_clusters is only set by proximity node, which only runs in iterations
        similarity_clusters = state.get("similarity_clusters", [])
        has_run_proximity = len(similarity_clusters) > 0

        # evolution_details is only set by evolve node, which only runs in iterations
        evolution_details = state.get("evolution_details", [])
        has_evolution = len(evolution_details) > 0

        # meta_review is only set by meta_review node, which only runs in iterations
        # Check if it has any actual data (not just an empty dict)
        meta_review_data = state.get("meta_review", {})
        has_meta_review = bool(meta_review_data and len(meta_review_data) > 0)

        # The most reliable indicator: if current_iteration > 0, we've completed at least one iteration
        # (proximity increments it at the end of each iteration)
        has_completed_iteration = current_iteration > 0

        # If we've seen meta_review, proximity, evolution, or if this IS an iteration-only node, or if we've completed an iteration
        in_refinement = is_iteration_only_node or has_run_proximity or has_evolution or has_meta_review or has_completed_iteration

        # Initial phase: supervisor, generate, review, rank, tournament (before any iterations)
        # Iteration phases: meta_review, evolve, review, rank, tournament, proximity
        # Note: current_iteration is 0-indexed internally, but we display as 1-indexed
        # Special case: proximity node increments current_iteration BEFORE emitting, so we see the incremented value
        if node_name in ["supervisor", "generate"]:
            phase = "initial_generation"
            iteration = None
        elif not in_refinement:
            # Initial review/rank/tournament (before first iteration starts)
            phase = "initial_generation"
            iteration = None
        else:
            # In a refinement iteration - display as 1-indexed
            # For proximity node, current_iteration is already incremented, so don't add 1
            if node_name == "proximity":
                display_iteration = current_iteration
            else:
                display_iteration = current_iteration + 1
            phase = f"iteration_{display_iteration}"
            iteration = display_iteration

        if node_name == "supervisor":
            research_plan = state.get("research_plan", {})
            return [{
                "agent_name": "Supervisor",
                "message": "🎯 Research plan created",
                "output": json.dumps(research_plan, indent=2),
                "progress": 10,
                "phase": phase,
                "iteration": iteration
            }]

        elif node_name == "generate":
            hypotheses = state.get("hypotheses", [])
            return [{
                "agent_name": "HypothesisGenerator",
                "message": f"✨ Generated {len(hypotheses)} initial hypotheses",
                "output": json.dumps({
                    "hypotheses": [{"text": h["text"]} for h in hypotheses]
                }, indent=2),
                "progress": 20,
                "phase": phase,
                "iteration": iteration
            }]

        elif node_name == "review":
            # Emit ONE output per hypothesis review
            hypotheses = state.get("hypotheses", [])
            outputs = []
            for i, h in enumerate(hypotheses, 1):
                if h.get("reviews"):
                    review = h["reviews"][-1]  # Latest review
                    outputs.append({
                        "agent_name": "HypothesisReflector",
                        "message": f"📝 Review {i}/{len(hypotheses)}",
                        "output": json.dumps({
                            "hypothesis_text": h["text"],
                            "review_summary": review.get("review_summary", ""),
                            "overall_score": review.get("overall_score", 0),
                            "scores": review.get("scores", {}),
                            "detailed_feedback": review.get("detailed_feedback", {}),
                            "constructive_feedback": review.get("constructive_feedback", ""),
                            "safety_ethical_concerns": review.get("safety_ethical_concerns", "")
                        }, indent=2),
                        "progress": 25 + (i * 15 // len(hypotheses)),
                        "phase": phase,
                        "iteration": iteration
                    })
            return outputs if outputs else None

        elif node_name == "rank":
            hypotheses = state.get("hypotheses", [])
            return [{
                "agent_name": "HypothesisRanker",
                "message": f"📊 Ranked {len(hypotheses)} hypotheses",
                "output": json.dumps({
                    "ranked_hypotheses": [
                        {
                            "text": h["text"],
                            "overall_score": h["score"] / 10  # Normalize to 0-1 for component display
                        }
                        for h in hypotheses
                    ]
                }, indent=2),
                "progress": 60,
                "phase": phase,
                "iteration": iteration
            }]

        elif node_name == "tournament":
            # Emit ONE output per tournament matchup
            matchups = state.get("tournament_matchups", [])
            outputs = []
            for i, matchup in enumerate(matchups, 1):
                outputs.append({
                    "agent_name": "TournamentJudge",
                    "message": f"🏆 Matchup {i}/{len(matchups)}",
                    "output": json.dumps({
                        "winner": matchup.get("winner", "a"),
                        "hypothesis_a": matchup.get("hypothesis_a", ""),
                        "hypothesis_b": matchup.get("hypothesis_b", ""),
                        "decision_summary": matchup.get("reasoning", ""),
                        "confidence": matchup.get("confidence", "Unknown")
                    }, indent=2),
                    "progress": 65 + (i * 10 // len(matchups)) if matchups else 65,
                    "phase": phase,
                    "iteration": iteration
                })
            return outputs if outputs else None

        elif node_name == "meta_review":
            meta_review = state.get("meta_review", {})
            return [{
                "agent_name": "MetaReviewer",
                "message": "📚 Meta-review analysis complete",
                "output": json.dumps(meta_review, indent=2),
                "progress": 80,
                "phase": phase,
                "iteration": iteration
            }]

        elif node_name == "evolve":
            # Emit ONE output per evolved hypothesis
            evolution_details = state.get("evolution_details", [])
            outputs = []
            for i, detail in enumerate(evolution_details, 1):
                outputs.append({
                    "agent_name": "HypothesisEvolver",
                    "message": f"🧬 Evolution {i}/{len(evolution_details)}",
                    "output": json.dumps({
                        "original_hypothesis_text": detail.get("original", ""),
                        "refined_hypothesis_text": detail.get("evolved", ""),
                        "refinement_summary": detail.get("rationale", ""),
                        "specific_refinements": detail.get("changes", [])
                    }, indent=2),
                    "progress": 85,
                    "phase": phase,
                    "iteration": iteration
                })
            return outputs if outputs else None

        elif node_name == "proximity":
            similarity_clusters = state.get("similarity_clusters", [])
            hypotheses = state.get("hypotheses", [])
            return [{
                "agent_name": "ProximityAnalyzer",
                "message": f"🔍 Deduplication complete: {len(hypotheses)} unique hypotheses",
                "output": json.dumps({
                    "similarity_clusters": similarity_clusters,
                    "diversity_assessment": f"Identified {len(similarity_clusters)} distinct clusters of similar hypotheses"
                }, indent=2),
                "progress": 90,
                "phase": phase,
                "iteration": iteration
            }]

        return None

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
