"""
Fantasy Software Engineer League - Scoring Engine

A flexible, configurable scoring system where metrics can be
defined and weighted based on league preferences.

IMPORTANT: The actual metrics are intentionally left as placeholders.
Configure your league's scoring by defining metrics in the
ScoringConfiguration class.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

from models import WeeklyScore, LeagueSettings


class MetricType(Enum):
    """Types of metrics that can be tracked."""
    COUNT = "count"           # Simple count (commits, PRs, etc.)
    PERCENTAGE = "percentage"  # Percentage-based (test coverage, etc.)
    BOOLEAN = "boolean"        # Yes/no achievements
    RATIO = "ratio"           # Calculated ratios
    DURATION = "duration"      # Time-based metrics


@dataclass
class ScoringMetric:
    """
    Definition of a single scoring metric.

    This is the building block for the scoring system. Each metric
    defines what to measure and how to score it.
    """
    # Identifier
    name: str
    display_name: str
    description: str

    # Scoring configuration
    metric_type: MetricType
    points_per_unit: float = 1.0

    # Bounds (optional)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    max_points: Optional[float] = None  # Cap on points from this metric

    # Bonus thresholds (optional)
    bonus_threshold: Optional[float] = None
    bonus_points: float = 0.0

    # Penalty configuration (optional)
    penalty_threshold: Optional[float] = None
    penalty_points: float = 0.0

    # Is this metric enabled?
    is_active: bool = True

    def calculate_points(self, raw_value: float) -> tuple[float, float, float]:
        """
        Calculate points from a raw metric value.

        Returns: (base_points, bonus_points, penalty_points)
        """
        if not self.is_active:
            return (0.0, 0.0, 0.0)

        # Apply bounds
        value = raw_value
        if self.min_value is not None:
            value = max(value, self.min_value)
        if self.max_value is not None:
            value = min(value, self.max_value)

        # Calculate base points
        base_points = value * self.points_per_unit

        # Apply max points cap
        if self.max_points is not None:
            base_points = min(base_points, self.max_points)

        # Calculate bonus
        bonus = 0.0
        if self.bonus_threshold is not None and raw_value >= self.bonus_threshold:
            bonus = self.bonus_points

        # Calculate penalty
        penalty = 0.0
        if self.penalty_threshold is not None and raw_value <= self.penalty_threshold:
            penalty = self.penalty_points

        return (base_points, bonus, penalty)


@dataclass
class ScoringConfiguration:
    """
    Complete scoring configuration for a league.

    This is where you define all the metrics your league will use.
    Modify this to customize your league's scoring system.
    """
    metrics: list[ScoringMetric] = field(default_factory=list)

    # Global multipliers
    weekly_multiplier: float = 1.0
    playoff_multiplier: float = 1.5

    @classmethod
    def create_default(cls) -> "ScoringConfiguration":
        """
        Create a default configuration with placeholder metrics.

        CUSTOMIZE THIS for your league!
        """
        return cls(
            metrics=[
                # ============================================
                # PLACEHOLDER METRICS - CONFIGURE THESE!
                # ============================================
                #
                # Below are example metrics. Uncomment and modify
                # based on what your league wants to track.
                #
                # Example: Code Production Metrics
                # ScoringMetric(
                #     name="commits",
                #     display_name="Commits",
                #     description="Number of commits merged",
                #     metric_type=MetricType.COUNT,
                #     points_per_unit=0.5,
                #     max_points=10.0,
                # ),
                # ScoringMetric(
                #     name="prs_merged",
                #     display_name="PRs Merged",
                #     description="Number of pull requests merged",
                #     metric_type=MetricType.COUNT,
                #     points_per_unit=3.0,
                # ),
                #
                # Example: Code Quality Metrics
                # ScoringMetric(
                #     name="code_reviews",
                #     display_name="Code Reviews",
                #     description="Number of code reviews completed",
                #     metric_type=MetricType.COUNT,
                #     points_per_unit=2.0,
                # ),
                # ScoringMetric(
                #     name="test_coverage",
                #     display_name="Test Coverage %",
                #     description="Test coverage percentage",
                #     metric_type=MetricType.PERCENTAGE,
                #     points_per_unit=0.1,
                #     bonus_threshold=90.0,
                #     bonus_points=5.0,
                # ),
                #
                # Example: Bug/Issue Metrics
                # ScoringMetric(
                #     name="bugs_fixed",
                #     display_name="Bugs Fixed",
                #     description="Number of bugs fixed",
                #     metric_type=MetricType.COUNT,
                #     points_per_unit=4.0,
                # ),
                # ScoringMetric(
                #     name="bugs_introduced",
                #     display_name="Bugs Introduced",
                #     description="Number of bugs introduced (penalty)",
                #     metric_type=MetricType.COUNT,
                #     points_per_unit=-3.0,  # Negative for penalty
                # ),
                #
                # Add your metrics here!
            ]
        )

    def add_metric(self, metric: ScoringMetric) -> None:
        """Add a metric to the configuration."""
        self.metrics.append(metric)

    def remove_metric(self, metric_name: str) -> bool:
        """Remove a metric by name."""
        for i, m in enumerate(self.metrics):
            if m.name == metric_name:
                self.metrics.pop(i)
                return True
        return False

    def get_metric(self, metric_name: str) -> Optional[ScoringMetric]:
        """Get a metric by name."""
        for m in self.metrics:
            if m.name == metric_name:
                return m
        return None

    def get_active_metrics(self) -> list[ScoringMetric]:
        """Get all active metrics."""
        return [m for m in self.metrics if m.is_active]


@dataclass
class ScoringEngine:
    """
    Engine that calculates scores based on configured metrics.

    This engine takes raw metric data and produces fantasy points.
    """
    config: ScoringConfiguration

    def calculate_score(
        self,
        raw_metrics: dict[str, float],
        is_playoff: bool = False,
    ) -> WeeklyScore:
        """
        Calculate a complete weekly score from raw metrics.

        Args:
            raw_metrics: Dict mapping metric names to raw values
            is_playoff: Whether this is a playoff week (applies multiplier)

        Returns:
            WeeklyScore with all calculated values
        """
        score = WeeklyScore(raw_metrics=raw_metrics)

        total_base = 0.0
        total_bonus = 0.0
        total_penalty = 0.0

        for metric in self.config.get_active_metrics():
            if metric.name in raw_metrics:
                raw_value = raw_metrics[metric.name]
                base, bonus, penalty = metric.calculate_points(raw_value)

                score.category_points[metric.name] = base
                total_base += base
                total_bonus += bonus
                total_penalty += penalty

        # Apply multipliers
        multiplier = self.config.weekly_multiplier
        if is_playoff:
            multiplier *= self.config.playoff_multiplier

        score.bonus_points = total_bonus * multiplier
        score.penalty_points = total_penalty * multiplier
        score.total_points = (total_base + total_bonus - total_penalty) * multiplier
        score.calculated_at = datetime.now()

        return score

    def get_scoring_breakdown(self, score: WeeklyScore) -> dict:
        """
        Get a detailed breakdown of a score for display.
        """
        breakdown = {
            "metrics": {},
            "subtotals": {
                "base_points": sum(score.category_points.values()),
                "bonus_points": score.bonus_points,
                "penalty_points": score.penalty_points,
            },
            "total": score.total_points,
        }

        for metric in self.config.get_active_metrics():
            if metric.name in score.raw_metrics:
                breakdown["metrics"][metric.display_name] = {
                    "raw_value": score.raw_metrics[metric.name],
                    "points": score.category_points.get(metric.name, 0.0),
                }

        return breakdown


# ============================================
# METRIC PRESETS
# ============================================
# These are example preset configurations that can be used
# as starting points for your league.

def create_github_focused_config() -> ScoringConfiguration:
    """
    Preset focused on GitHub activity metrics.

    Good for teams that want to track code contributions.
    """
    config = ScoringConfiguration()

    config.add_metric(ScoringMetric(
        name="commits",
        display_name="Commits",
        description="Number of commits merged to main branches",
        metric_type=MetricType.COUNT,
        points_per_unit=0.5,
        max_points=15.0,
    ))

    config.add_metric(ScoringMetric(
        name="prs_merged",
        display_name="PRs Merged",
        description="Pull requests merged",
        metric_type=MetricType.COUNT,
        points_per_unit=3.0,
    ))

    config.add_metric(ScoringMetric(
        name="prs_reviewed",
        display_name="PRs Reviewed",
        description="Pull requests reviewed",
        metric_type=MetricType.COUNT,
        points_per_unit=2.0,
    ))

    config.add_metric(ScoringMetric(
        name="issues_closed",
        display_name="Issues Closed",
        description="Issues closed",
        metric_type=MetricType.COUNT,
        points_per_unit=2.5,
    ))

    config.add_metric(ScoringMetric(
        name="review_comments",
        display_name="Review Comments",
        description="Meaningful comments on code reviews",
        metric_type=MetricType.COUNT,
        points_per_unit=0.5,
        max_points=10.0,
    ))

    return config


def create_agile_focused_config() -> ScoringConfiguration:
    """
    Preset focused on Agile/Sprint metrics.

    Good for teams using Jira, Linear, or similar tools.
    """
    config = ScoringConfiguration()

    config.add_metric(ScoringMetric(
        name="story_points_completed",
        display_name="Story Points",
        description="Story points completed in the sprint",
        metric_type=MetricType.COUNT,
        points_per_unit=2.0,
    ))

    config.add_metric(ScoringMetric(
        name="tickets_completed",
        display_name="Tickets Completed",
        description="Number of tickets moved to done",
        metric_type=MetricType.COUNT,
        points_per_unit=3.0,
    ))

    config.add_metric(ScoringMetric(
        name="bugs_fixed",
        display_name="Bugs Fixed",
        description="Bug tickets resolved",
        metric_type=MetricType.COUNT,
        points_per_unit=4.0,
        bonus_threshold=5.0,
        bonus_points=5.0,
    ))

    config.add_metric(ScoringMetric(
        name="sprint_commitment_met",
        display_name="Sprint Commitment",
        description="Percentage of sprint commitment met",
        metric_type=MetricType.PERCENTAGE,
        points_per_unit=0.1,
        bonus_threshold=100.0,
        bonus_points=10.0,
    ))

    return config


def create_quality_focused_config() -> ScoringConfiguration:
    """
    Preset focused on code quality metrics.

    Good for teams emphasizing quality over quantity.
    """
    config = ScoringConfiguration()

    config.add_metric(ScoringMetric(
        name="test_coverage_delta",
        display_name="Test Coverage Change",
        description="Change in test coverage percentage",
        metric_type=MetricType.PERCENTAGE,
        points_per_unit=1.0,
        penalty_threshold=-5.0,
        penalty_points=10.0,
    ))

    config.add_metric(ScoringMetric(
        name="code_review_approvals",
        display_name="Review Approvals",
        description="Code reviews approved",
        metric_type=MetricType.COUNT,
        points_per_unit=2.0,
    ))

    config.add_metric(ScoringMetric(
        name="documentation_added",
        display_name="Documentation",
        description="Documentation pages/sections added or updated",
        metric_type=MetricType.COUNT,
        points_per_unit=3.0,
    ))

    config.add_metric(ScoringMetric(
        name="tech_debt_resolved",
        display_name="Tech Debt Resolved",
        description="Tech debt items addressed",
        metric_type=MetricType.COUNT,
        points_per_unit=4.0,
    ))

    config.add_metric(ScoringMetric(
        name="build_failures_caused",
        display_name="Build Failures",
        description="Build failures caused (penalty)",
        metric_type=MetricType.COUNT,
        points_per_unit=-5.0,
    ))

    return config


# ============================================
# EXAMPLE USAGE
# ============================================
"""
# Creating a custom scoring configuration:

config = ScoringConfiguration()

# Add your metrics
config.add_metric(ScoringMetric(
    name="my_metric",
    display_name="My Custom Metric",
    description="Description of what this measures",
    metric_type=MetricType.COUNT,
    points_per_unit=2.0,
))

# Create scoring engine
engine = ScoringEngine(config)

# Calculate score from raw data
raw_data = {
    "my_metric": 15,
}
score = engine.calculate_score(raw_data)
print(f"Total points: {score.total_points}")

# Or use a preset:
github_config = create_github_focused_config()
agile_config = create_agile_focused_config()
quality_config = create_quality_focused_config()
"""
