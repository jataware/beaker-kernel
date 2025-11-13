"""
Async wrapper around CoScientist-LG for hypothesis generation with streaming support.
"""

import asyncio
import logging
import re
import io
import sys
import threading
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import asdict
from typing import Callable, Optional, Any
from pathlib import Path
from queue import Queue

logger = logging.getLogger(__name__)


# ============================================================================
# Default Configuration for Hypothesis Generation
# ============================================================================
# These are the single source of truth - modify here to change defaults
# All parameters can be overridden when creating a HypothesisGenerator instance

# Model Configuration
# -------------------
DEFAULT_MODEL_NAME = "gemini/gemini-2.5-flash"
# The LLM model to use for all agents (generation, review, evolution, etc.)
# Examples: "gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-20241022", "gemini/gemini-2.5-flash"
# Uses litellm format, so any litellm-supported model works
# Trade-off: Faster models (like gemini-flash) = lower cost/latency, slower models = higher quality

# Initial Generation
# ------------------
DEFAULT_HYPOTHESES_PER_GENERATION = 5
# Number of initial hypotheses to generate at the start of the workflow
# More hypotheses = more diverse starting pool, but slower and more expensive
# Recommended range: 3-10
# Note: With evolution_top_k < hypotheses_per_generation, lower-ranked hypotheses get discarded
# Example: If you generate 10 but only evolve top 3, the other 7 are dropped after initial ranking

# Refinement Iterations
# ---------------------
DEFAULT_MAX_ITERATIONS = 2
# Number of refinement cycles to run (meta-review → evolution → re-ranking → tournament → deduplication)
# Each iteration refines hypotheses based on feedback from previous reviews
# More iterations = higher quality final hypotheses, but much slower
# Recommended range: 1-3
# Cost scaling: Each iteration runs review/ranking/tournament on all evolved hypotheses
# Example: 1 iteration is good for quick exploration, 3 iterations for publication-quality hypotheses

# Evolution Selection
# -------------------
DEFAULT_EVOLUTION_TOP_K = 3
# Number of top-ranked hypotheses to evolve in each iteration
# Only the highest-ranked hypotheses are worth refining; lower ones are discarded
# Must be ≤ hypotheses_per_generation
# Recommended range: 1-3
# Trade-off: Higher values = more diverse final results but higher risk of duplicates
# WARNING: If evolution_top_k > 1, hypotheses may converge to duplicates because they
#          receive the same meta-review guidance. Consider setting to 2-3 only if
#          diversity is more important than avoiding duplicates.
# Example: evolution_top_k=1 gives you 1 highly-refined hypothesis
#          evolution_top_k=3 gives you 3 refined hypotheses (may have duplicates)

# ============================================================================
# Usage Examples
# ============================================================================
#
# Quick exploration (fast, low cost):
#   HypothesisGenerator(
#       hypotheses_per_generation=3,
#       max_iterations=1,
#       evolution_top_k=1
#   )
#   → Generates 3 hypotheses, evolves only #1, returns 1 refined hypothesis
#
# Balanced (moderate speed/cost):
#   HypothesisGenerator(
#       hypotheses_per_generation=5,
#       max_iterations=2,
#       evolution_top_k=2
#   )
#   → Generates 5 hypotheses, evolves top 2, runs 2 refinement cycles
#   → Risk of duplicates with evolution_top_k=2
#
# High quality (slow, expensive):
#   HypothesisGenerator(
#       hypotheses_per_generation=10,
#       max_iterations=3,
#       evolution_top_k=3,
#       model_name="gpt-4o"
#   )
#   → Generates 10 hypotheses, evolves top 3, runs 3 refinement cycles
#   → Best quality but highest risk of duplicates
# ============================================================================


class HypothesisGenerator:
    """
    Async wrapper for CoScientist-LG that provides streaming progress updates.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        hypotheses_per_generation: int = DEFAULT_HYPOTHESES_PER_GENERATION,
        evolution_top_k: int = DEFAULT_EVOLUTION_TOP_K,
        base_path: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the hypothesis generator.

        Args:
            model_name: LLM model to use for all agents (generation, review, evolution, etc.)
                       Examples: "gpt-4o-mini", "claude-3-5-sonnet-20241022", "gemini/gemini-2.5-flash"
                       Uses litellm format. Faster models = lower cost, slower models = higher quality.

            max_iterations: Number of refinement cycles to run. Each iteration includes:
                           meta-review → evolution → re-review → re-ranking → tournament → deduplication
                           Range: 1-3. More iterations = higher quality but much slower.

            hypotheses_per_generation: Number of initial hypotheses to generate.
                                      Range: 3-10. More = diverse pool but slower/more expensive.
                                      Note: Hypotheses not in top evolution_top_k are discarded.

            evolution_top_k: Number of top-ranked hypotheses to evolve each iteration.
                            Range: 1-3. Must be ≤ hypotheses_per_generation.
                            WARNING: Values > 1 may create duplicates (all receive same meta-review).
                            evolution_top_k=1 → 1 highly-refined hypothesis
                            evolution_top_k=3 → 3 refined hypotheses (potential duplicates)

            base_path: Directory path to save agent states and workflow logs.
                      Defaults to "./ai_coscientist_states"

            verbose: Enable detailed logging for debugging. Logs all agent interactions.
        """
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.hypotheses_per_generation = hypotheses_per_generation
        self.evolution_top_k = evolution_top_k
        self.base_path = base_path or "./ai_coscientist_states"
        self.verbose = verbose
        self._framework = None

    def _get_framework(self):
        """Lazy load the CoScientist-LG framework."""
        if self._framework is None:
            try:
                from coscientist_lg import HypothesisGenerator
                self._framework = HypothesisGenerator(
                    model_name=self.model_name,
                    max_iterations=self.max_iterations,
                    hypotheses_per_generation=self.hypotheses_per_generation,
                    evolution_top_k=self.evolution_top_k,
                    base_path=self.base_path,
                    verbose=self.verbose,
                )
            except ImportError as e:
                logger.error("CoScientist-LG not installed. Install with: pip install coscientist-lg")
                raise ImportError(
                    "CoScientist-LG is required for hypothesis generation. "
                    "Install with: pip install coscientist-lg"
                ) from e
        return self._framework

    async def generate_hypotheses(
        self,
        research_goal: str,
        progress_callback: Optional[Callable[[str, dict], None]] = None,
    ) -> dict:
        """
        Generate hypotheses with streaming progress updates.

        Args:
            research_goal: The research question or goal
            progress_callback: Async callback function for progress updates
                             Called with (phase_name, data) for each phase

        Returns:
            Dictionary with results including top hypotheses and metrics
        """

        async def emit_progress(phase: str, data: dict):
            """Helper to emit progress if callback is provided."""
            if progress_callback:
                try:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(phase, data)
                    else:
                        progress_callback(phase, data)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")

        try:
            logger.info("Starting hypothesis generation")
            framework = self._get_framework()

            # CoScientist-LG will emit all progress events through the callback
            # No need to emit manually here - just pass the callback through

            # NOTE: Lines below (210-332) define OLD AI-CoScientist agent callback system
            # This is no longer used with CoScientist-LG which uses phase-based callbacks
            loop = asyncio.get_event_loop()

            # Track agent completions for progress and phase detection
            agent_count = 0
            phase_state = {
                "current_phase": "initial_generation",
                "iteration": 0,
                "agent_counts": {},  # Track count per agent type
                "last_agent": None,
            }

            # Define callback that will be called by AI-CoScientist after each agent runs
            def sync_callback(agent_name: str, agent_output: str):
                """Synchronous callback called by AI-CoScientist - we'll schedule async emission"""
                nonlocal agent_count
                agent_count += 1

                # Track agent invocation counts
                if agent_name not in phase_state["agent_counts"]:
                    phase_state["agent_counts"][agent_name] = 0
                phase_state["agent_counts"][agent_name] += 1
                agent_num = phase_state["agent_counts"][agent_name]

                # Detect phase transitions and update state
                prev_phase = phase_state["current_phase"]

                # Initial generation phase
                if agent_name == "Supervisor":
                    phase_state["current_phase"] = "initial_generation"
                    message = "🎯 Analyzing research goal..."
                    progress = 5

                elif agent_name == "HypothesisGenerator":
                    message = f"✨ Generating {self.hypotheses_per_generation} initial hypotheses..."
                    progress = 15

                elif agent_name == "HypothesisReflector" and phase_state["current_phase"] == "initial_generation":
                    message = f"📝 Peer reviewing hypothesis {agent_num} of {self.hypotheses_per_generation}..."
                    progress = 20 + (agent_num * 40 // self.hypotheses_per_generation)

                elif agent_name == "HypothesisRanker" and phase_state["current_phase"] == "initial_generation":
                    phase_state["current_phase"] = "initial_ranking"
                    message = f"📊 Ranking {self.hypotheses_per_generation} hypotheses..."
                    progress = 65

                elif agent_name == "TournamentJudge":
                    if phase_state["current_phase"] != "tournament":
                        phase_state["current_phase"] = "tournament"
                        # Emit phase transition marker
                        asyncio.run_coroutine_threadsafe(
                            emit_progress("phase_marker", {
                                "message": "🏆 Tournament Selection Phase",
                                "phase": "tournament",
                                "description": "Comparing hypotheses head-to-head to refine rankings"
                            }),
                            loop
                        )
                    message = f"🏆 Tournament round {agent_num}..."
                    progress = 65 + min(10, agent_num // 3)

                elif agent_name == "MetaReviewer":
                    # MetaReviewer signals start of an iteration
                    phase_state["iteration"] += 1
                    phase_state["agent_counts"] = {}  # Reset agent counters for new iteration
                    phase_state["current_phase"] = f"iteration_{phase_state['iteration']}"
                    iter_num = phase_state["iteration"]
                    # Emit phase transition marker
                    asyncio.run_coroutine_threadsafe(
                        emit_progress("phase_marker", {
                            "message": f"🔄 Iteration {iter_num} of {self.max_iterations}",
                            "phase": f"iteration_{iter_num}",
                            "description": f"Refining hypotheses based on feedback (Iteration {iter_num}/{self.max_iterations})"
                        }),
                        loop
                    )
                    message = f"📚 Iteration {iter_num}: Meta review analysis..."
                    progress = 75 + ((iter_num - 1) * 20 // self.max_iterations)

                elif agent_name == "HypothesisEvolver":
                    iter_num = phase_state["iteration"]
                    evolver_count = phase_state["agent_counts"]["HypothesisEvolver"]
                    message = f"🧬 Iteration {iter_num}: Evolving hypothesis {evolver_count} of {self.evolution_top_k}..."
                    progress = 75 + ((iter_num - 1) * 20 // self.max_iterations) + 2

                elif agent_name == "HypothesisReflector" and phase_state["current_phase"].startswith("iteration"):
                    iter_num = phase_state["iteration"]
                    # Count reflectors in this iteration (reset logic would be needed for accuracy)
                    message = f"📝 Iteration {iter_num}: Re-reviewing evolved hypotheses..."
                    progress = 75 + ((iter_num - 1) * 20 // self.max_iterations) + 5

                elif agent_name == "HypothesisRanker" and phase_state["current_phase"].startswith("iteration"):
                    iter_num = phase_state["iteration"]
                    message = f"📊 Iteration {iter_num}: Re-ranking hypotheses..."
                    progress = 75 + ((iter_num - 1) * 20 // self.max_iterations) + 8

                elif agent_name == "ProximityAnalyzer":
                    iter_num = phase_state["iteration"]
                    message = f"🔍 Iteration {iter_num}: Analyzing hypothesis similarity..."
                    progress = 75 + ((iter_num - 1) * 20 // self.max_iterations) + 10

                else:
                    # Fallback for unknown agents
                    message = f"{agent_name} completed"
                    progress = min(95, 10 + agent_count * 3)

                # Detect if phase changed and emit transition marker
                if prev_phase != phase_state["current_phase"] and agent_name not in ["MetaReviewer", "TournamentJudge"]:
                    # Already handled phase markers above for specific transitions
                    pass

                # Schedule the async emit_progress to run in the event loop
                asyncio.run_coroutine_threadsafe(
                    emit_progress("agent_output", {
                        "message": message,
                        "agent_name": agent_name,
                        "agent_output": agent_output,
                        "progress": progress,
                        "iteration": phase_state["iteration"],  # Always send iteration number
                        "phase": phase_state["current_phase"]
                    }),
                    loop
                )

            # Run generation with callback
            # Note: CoScientist-LG uses phase-based callbacks (not agent-based)
            # Pass the progress_callback directly - CoScientist-LG emits proper phase events
            result = await framework.generate_hypotheses(
                research_goal,
                progress_callback=progress_callback
            )

            await emit_progress("complete", {
                "message": "✨ Hypothesis generation complete!",
                "progress": 100,
                "result": self._format_result(result)
            })

            return self._format_result(result)

        except Exception as e:
            logger.error(f"Error during hypothesis generation: {e}", exc_info=True)
            await emit_progress("error", {
                "message": f"Error: {str(e)}",
                "error": str(e)
            })
            raise

    async def generate_hypotheses_with_phases(
        self,
        research_goal: str,
        progress_callback: Optional[Callable[[str, dict], None]] = None,
    ) -> dict:
        """
        Generate hypotheses with detailed phase-by-phase streaming.

        This version intercepts the AI-CoScientist workflow to provide
        granular progress updates at each phase.

        Args:
            research_goal: The research question or goal
            progress_callback: Async callback for progress updates

        Returns:
            Dictionary with results
        """
        async def emit_progress(phase: str, data: dict):
            """Helper to emit progress if callback is provided."""
            if progress_callback:
                try:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(phase, data)
                    else:
                        progress_callback(phase, data)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")

        try:
            framework = self._get_framework()

            # Phase 1: Generation
            await emit_progress("generation_start", {
                "message": f"Generating {self.hypotheses_per_generation} initial hypotheses...",
                "progress": 5
            })

            # Run the full workflow - native async in CoScientist-LG
            result = await framework.generate_hypotheses(
                research_goal,
                progress_callback=progress_callback
            )

            await emit_progress("complete", {
                "message": "Hypothesis generation complete!",
                "progress": 100,
                "result": self._format_result(result)
            })

            return self._format_result(result)

        except Exception as e:
            logger.error(f"Error during hypothesis generation: {e}", exc_info=True)
            await emit_progress("error", {
                "message": f"Error: {str(e)}",
                "error": str(e)
            })
            raise

    async def generate_hypotheses_streaming(
        self,
        research_goal: str,
        progress_callback: Optional[Callable[[str, dict], None]] = None,
    ):
        """
        Generate hypotheses with streaming state updates after each node.

        This method yields intermediate state after each node completes,
        allowing real-time display of results as the workflow progresses.

        Args:
            research_goal: The research question or goal
            progress_callback: Async callback for progress updates

        Yields:
            Tuple of (node_name, formatted_state_dict) after each node completes
        """
        try:
            logger.info("Starting streaming hypothesis generation")
            framework = self._get_framework()

            # Stream results from CoScientist-LG
            async for node_name, state in framework.generate_hypotheses_streaming(
                research_goal=research_goal,
                progress_callback=progress_callback
            ):
                # Format the state for frontend consumption
                formatted_state = self._format_result(state)
                yield node_name, formatted_state

        except Exception as e:
            logger.error(f"Error during streaming hypothesis generation: {e}", exc_info=True)
            raise

    def _format_result(self, result: dict) -> dict:
        """
        Format result for frontend consumption.
        Handles both old AI-CoScientist format and new CoScientist-LG format.

        Args:
            result: Raw result from framework

        Returns:
            Formatted result dictionary
        """
        try:
            # Detect format: old uses "top_ranked_hypotheses", new uses "hypotheses"
            raw_hypotheses = result.get("hypotheses") or result.get("top_ranked_hypotheses", [])

            hypotheses = []
            for hyp_dict in raw_hypotheses:
                # CoScientist-LG already returns dicts from to_dict()
                # But handle Hypothesis objects for backwards compatibility
                if hasattr(hyp_dict, '__dict__') and hasattr(hyp_dict, 'to_dict'):
                    hyp_dict = hyp_dict.to_dict()
                elif hasattr(hyp_dict, '__dict__'):
                    hyp_dict = asdict(hyp_dict)

                hypotheses.append({
                    "text": hyp_dict.get("text", ""),
                    "score": hyp_dict.get("score", 0.0),
                    "elo_rating": hyp_dict.get("elo_rating", 1200),
                    "reviews": hyp_dict.get("reviews", []),
                    "similarity_cluster_id": hyp_dict.get("similarity_cluster_id"),
                    "evolution_history": hyp_dict.get("evolution_history", []),
                    "win_count": hyp_dict.get("win_count", 0),
                    "loss_count": hyp_dict.get("loss_count", 0),
                    "total_matches": hyp_dict.get("total_matches", 0),
                    "win_rate": hyp_dict.get("win_rate", 0.0),
                })

            # Handle different meta_review key names
            meta_review = result.get("meta_review") or result.get("meta_review_insights", {})

            # NEW: Handle research plan from supervisor
            research_plan = result.get("research_plan") or result.get("supervisor_guidance", {})

            # NEW: Handle tournament matchups
            tournament_matchups = result.get("tournament_matchups", [])

            # NEW: Handle evolution details
            evolution_details = result.get("evolution_details", [])

            # Handle different execution_time key names
            execution_time = result.get("execution_time") or result.get("total_workflow_time", 0)

            # Handle metrics (both formats have similar structure)
            metrics = result.get("metrics") or result.get("execution_metrics", {})

            return {
                "hypotheses": hypotheses,
                "meta_review": meta_review,
                "research_plan": research_plan,
                "tournament_matchups": tournament_matchups,
                "evolution_details": evolution_details,
                "similarity_clusters": result.get("similarity_clusters", []),
                "current_iteration": result.get("current_iteration", 0),
                "execution_time": execution_time,
                "metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Error formatting result: {e}")
            return {
                "hypotheses": [],
                "meta_review": {},
                "research_plan": {},
                "tournament_matchups": [],
                "evolution_details": [],
                "similarity_clusters": [],
                "current_iteration": 0,
                "execution_time": 0,
                "metrics": {},
                "error": str(e)
            }
