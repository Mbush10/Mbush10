"""
Fantasy Software Engineer League - Example Usage

This script demonstrates how to set up and run a fantasy league.
"""

from src.models import Engineer, LeagueSettings
from src.league_manager import LeagueManager
from src.scoring_engine import (
    ScoringEngine,
    ScoringConfiguration,
    ScoringMetric,
    MetricType,
    create_github_focused_config,
)


def main():
    # ================================================
    # 1. Initialize the League Manager
    # ================================================
    manager = LeagueManager()

    # ================================================
    # 2. Create a League
    # ================================================
    settings = LeagueSettings(
        roster_size=5,
        starter_slots=3,
        flex_slots=1,
        bench_slots=1,
        regular_season_weeks=10,
        playoff_weeks=2,
        playoff_teams=4,
    )

    league = manager.create_league(
        name="Tech Giants Fantasy League",
        commissioner_email="commissioner@example.com",
        settings=settings,
        max_teams=8,
    )
    print(f"Created league: {league.name} (ID: {league.id})")

    # ================================================
    # 3. Add Engineers to the Pool
    # ================================================
    engineers = [
        Engineer(name="Alice Chen", position="Backend", years_experience=5),
        Engineer(name="Bob Smith", position="Frontend", years_experience=3),
        Engineer(name="Carol Jones", position="Fullstack", years_experience=7),
        Engineer(name="David Lee", position="DevOps", years_experience=4),
        Engineer(name="Eve Wilson", position="Backend", years_experience=6),
        Engineer(name="Frank Brown", position="Frontend", years_experience=2),
        Engineer(name="Grace Kim", position="Fullstack", years_experience=8),
        Engineer(name="Henry Davis", position="DevOps", years_experience=5),
        # Add more engineers for a full draft pool...
    ]

    for eng in engineers:
        manager.add_engineer_to_pool(eng)

    print(f"Added {len(engineers)} engineers to the pool")

    # ================================================
    # 4. Create Fantasy Teams
    # ================================================
    teams_data = [
        ("Code Crushers", "Manager A", "managera@example.com"),
        ("Bug Busters", "Manager B", "managerb@example.com"),
        ("Merge Masters", "Manager C", "managerc@example.com"),
        ("Deploy Devils", "Manager D", "managerd@example.com"),
    ]

    teams = []
    for name, mgr_name, mgr_email in teams_data:
        team = manager.create_team(
            league_id=league.id,
            team_name=name,
            manager_name=mgr_name,
            manager_email=mgr_email,
        )
        teams.append(team)
        print(f"Created team: {team.name}")

    # ================================================
    # 5. Set Up and Run the Draft
    # ================================================
    manager.setup_draft(league.id, randomize_order=True)
    print(f"\nDraft order set. League status: {league.status}")

    # Simulate draft picks (in a real app, this would be interactive)
    available = manager.get_available_engineers()
    for team in teams:
        for _ in range(settings.roster_size):
            if available:
                eng = available.pop(0)
                manager.make_draft_pick(league.id, team.id, eng.id)
                print(f"  {team.name} drafts {eng.name}")

    print(f"\nDraft complete. League status: {league.status}")

    # ================================================
    # 6. Set Starting Lineups
    # ================================================
    for team in teams:
        team = manager.get_team(team.id)  # Refresh
        starters = team.roster[:settings.starter_slots + settings.flex_slots]
        manager.set_starting_lineup(team.id, starters)
        print(f"{team.name} lineup set with {len(starters)} starters")

    # ================================================
    # 7. Configure Scoring
    # ================================================
    # Use a preset or create custom config
    scoring_config = create_github_focused_config()

    # Or add custom metrics:
    scoring_config.add_metric(ScoringMetric(
        name="oncall_incidents_resolved",
        display_name="On-Call Incidents",
        description="Incidents resolved during on-call",
        metric_type=MetricType.COUNT,
        points_per_unit=5.0,
    ))

    engine = ScoringEngine(scoring_config)
    print(f"\nScoring configured with {len(scoring_config.get_active_metrics())} metrics")

    # ================================================
    # 8. Generate Week 1 Matchups
    # ================================================
    week1_matchups = manager.generate_weekly_matchups(league.id, week=1)
    print(f"\nWeek 1 Matchups:")
    for m in week1_matchups:
        team_a = manager.get_team(m.team_a_id)
        team_b = manager.get_team(m.team_b_id)
        print(f"  {team_a.name} vs {team_b.name}")

    # ================================================
    # 9. Simulate Weekly Scores (would come from real data)
    # ================================================
    print("\nSimulating Week 1 scores...")

    for team in teams:
        team = manager.get_team(team.id)
        for eng_id in team.starting_lineup:
            eng = manager.get_engineer(eng_id)

            # Simulated raw metrics (would come from GitHub API, Jira, etc.)
            raw_metrics = {
                "commits": 12,
                "prs_merged": 3,
                "prs_reviewed": 5,
                "issues_closed": 2,
                "review_comments": 8,
                "oncall_incidents_resolved": 1,
            }

            # Calculate and record score
            score = engine.calculate_score(raw_metrics)
            score.engineer_id = eng_id
            score.league_id = league.id
            score.week = 1
            manager.weekly_scores[score.id] = score

            print(f"  {eng.name}: {score.total_points:.1f} pts")

    # ================================================
    # 10. Calculate Team Scores and Finalize Matchups
    # ================================================
    print("\nWeek 1 Results:")
    for matchup in week1_matchups:
        matchup.team_a_score = manager.calculate_team_weekly_score(matchup.team_a_id, 1)
        matchup.team_b_score = manager.calculate_team_weekly_score(matchup.team_b_id, 1)

        manager.finalize_matchup(matchup.id)

        team_a = manager.get_team(matchup.team_a_id)
        team_b = manager.get_team(matchup.team_b_id)

        winner = manager.get_team(matchup.winner_id) if matchup.winner_id else None
        winner_name = winner.name if winner else "TIE"

        print(f"  {team_a.name} ({matchup.team_a_score:.1f}) vs "
              f"{team_b.name} ({matchup.team_b_score:.1f}) - Winner: {winner_name}")

    # ================================================
    # 11. Display Standings
    # ================================================
    print("\nLeague Standings:")
    standings = manager.get_standings(league.id)
    for i, team in enumerate(standings, 1):
        print(f"  {i}. {team.name} ({team.record}) - {team.total_points:.1f} pts")

    print("\n" + "=" * 50)
    print("League is ready for Week 2!")
    print("=" * 50)


if __name__ == "__main__":
    main()
