"""
Async wrapper around AI-CoScientist for hypothesis generation with streaming support.
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


class HypothesisGenerator:
    """
    Async wrapper for AI-CoScientist that provides streaming progress updates.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        max_iterations: int = 3,
        hypotheses_per_generation: int = 10,
        evolution_top_k: int = 3,
        tournament_size: int = 8,
        base_path: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the hypothesis generator.

        Args:
            model_name: LLM model to use (e.g., "gpt-4o-mini", "claude-3-sonnet-20240229")
            max_iterations: Number of refinement iterations
            hypotheses_per_generation: Initial hypothesis count
            evolution_top_k: Number of top hypotheses to evolve
            tournament_size: Tournament rounds
            base_path: Path to save agent states
            verbose: Enable detailed logging
        """
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.hypotheses_per_generation = hypotheses_per_generation
        self.evolution_top_k = evolution_top_k
        self.tournament_size = tournament_size
        self.base_path = base_path or "./ai_coscientist_states"
        self.verbose = verbose
        self._framework = None

    def _get_framework(self):
        """Lazy load the AI-CoScientist framework."""
        if self._framework is None:
            try:
                from ai_coscientist import AIScientistFramework
                self._framework = AIScientistFramework(
                    model_name=self.model_name,
                    max_iterations=self.max_iterations,
                    hypotheses_per_generation=self.hypotheses_per_generation,
                    evolution_top_k=self.evolution_top_k,
                    tournament_size=self.tournament_size,
                    base_path=self.base_path,
                    verbose=self.verbose,
                )
            except ImportError as e:
                logger.error("AI-CoScientist not installed. Install with: pip install ai-coscientist")
                raise ImportError(
                    "AI-CoScientist is required for hypothesis generation. "
                    "Install with: pip install ai-coscientist"
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

            # Phase 1: Initial Generation
            logger.info("Emitting generation_start progress")
            await emit_progress("generation_start", {
                "message": f"Generating {self.hypotheses_per_generation} initial hypotheses...",
                "progress": 0
            })
            logger.info("generation_start progress emitted")

            # Use AI-CoScientist's callback system to stream agent outputs
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
                        "iteration": phase_state["iteration"] if phase_state["current_phase"].startswith("iteration") else None,
                        "phase": phase_state["current_phase"]
                    }),
                    loop
                )

            # Run generation with callback
            result = await loop.run_in_executor(
                None,
                framework.run_research_workflow,
                research_goal,
                sync_callback
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
            loop = asyncio.get_event_loop()

            # Phase 1: Generation
            await emit_progress("generation_start", {
                "message": f"Generating {self.hypotheses_per_generation} initial hypotheses...",
                "progress": 5
            })

            # Run the full workflow in executor
            # TODO: Future enhancement - break into individual phase calls
            result = await loop.run_in_executor(
                None,
                framework.run_research_workflow,
                research_goal
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

    def _format_result(self, result: dict) -> dict:
        """
        Format AI-CoScientist result for frontend consumption.

        Args:
            result: Raw result from AI-CoScientist

        Returns:
            Formatted result dictionary
        """
        try:
            hypotheses = []
            for hyp_dict in result.get("top_ranked_hypotheses", []):
                # Handle both dict and Hypothesis object
                if hasattr(hyp_dict, '__dict__'):
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
                })

            return {
                "hypotheses": hypotheses,
                "meta_review": result.get("meta_review_insights", {}),
                "execution_time": result.get("total_workflow_time", 0),
                "metrics": result.get("execution_metrics", {}),
            }
        except Exception as e:
            logger.error(f"Error formatting result: {e}")
            return {
                "hypotheses": [],
                "meta_review": {},
                "execution_time": 0,
                "metrics": {},
                "error": str(e)
            }
