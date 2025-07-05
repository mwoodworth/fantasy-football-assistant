"""
Mock NFL data generator for testing Fantasy Football Assistant

This module creates realistic mock data for teams, players, and statistics
to enable testing of all Phase 2 features without requiring real NFL data.
"""

import random
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.player import Player, PlayerStats, Team
from ..models.fantasy import League, FantasyTeam, Roster
from ..models.user import User

# NFL Teams data
NFL_TEAMS = [
    {"name": "Arizona Cardinals", "abbreviation": "ARI", "city": "Arizona", "division": "NFC West"},
    {"name": "Atlanta Falcons", "abbreviation": "ATL", "city": "Atlanta", "division": "NFC South"},
    {"name": "Baltimore Ravens", "abbreviation": "BAL", "city": "Baltimore", "division": "AFC North"},
    {"name": "Buffalo Bills", "abbreviation": "BUF", "city": "Buffalo", "division": "AFC East"},
    {"name": "Carolina Panthers", "abbreviation": "CAR", "city": "Carolina", "division": "NFC South"},
    {"name": "Chicago Bears", "abbreviation": "CHI", "city": "Chicago", "division": "NFC North"},
    {"name": "Cincinnati Bengals", "abbreviation": "CIN", "city": "Cincinnati", "division": "AFC North"},
    {"name": "Cleveland Browns", "abbreviation": "CLE", "city": "Cleveland", "division": "AFC North"},
    {"name": "Dallas Cowboys", "abbreviation": "DAL", "city": "Dallas", "division": "NFC East"},
    {"name": "Denver Broncos", "abbreviation": "DEN", "city": "Denver", "division": "AFC West"},
    {"name": "Detroit Lions", "abbreviation": "DET", "city": "Detroit", "division": "NFC North"},
    {"name": "Green Bay Packers", "abbreviation": "GB", "city": "Green Bay", "division": "NFC North"},
    {"name": "Houston Texans", "abbreviation": "HOU", "city": "Houston", "division": "AFC South"},
    {"name": "Indianapolis Colts", "abbreviation": "IND", "city": "Indianapolis", "division": "AFC South"},
    {"name": "Jacksonville Jaguars", "abbreviation": "JAX", "city": "Jacksonville", "division": "AFC South"},
    {"name": "Kansas City Chiefs", "abbreviation": "KC", "city": "Kansas City", "division": "AFC West"},
    {"name": "Las Vegas Raiders", "abbreviation": "LV", "city": "Las Vegas", "division": "AFC West"},
    {"name": "Los Angeles Chargers", "abbreviation": "LAC", "city": "Los Angeles", "division": "AFC West"},
    {"name": "Los Angeles Rams", "abbreviation": "LAR", "city": "Los Angeles", "division": "NFC West"},
    {"name": "Miami Dolphins", "abbreviation": "MIA", "city": "Miami", "division": "AFC East"},
    {"name": "Minnesota Vikings", "abbreviation": "MIN", "city": "Minnesota", "division": "NFC North"},
    {"name": "New England Patriots", "abbreviation": "NE", "city": "New England", "division": "AFC East"},
    {"name": "New Orleans Saints", "abbreviation": "NO", "city": "New Orleans", "division": "NFC South"},
    {"name": "New York Giants", "abbreviation": "NYG", "city": "New York", "division": "NFC East"},
    {"name": "New York Jets", "abbreviation": "NYJ", "city": "New York", "division": "AFC East"},
    {"name": "Philadelphia Eagles", "abbreviation": "PHI", "city": "Philadelphia", "division": "NFC East"},
    {"name": "Pittsburgh Steelers", "abbreviation": "PIT", "city": "Pittsburgh", "division": "AFC North"},
    {"name": "San Francisco 49ers", "abbreviation": "SF", "city": "San Francisco", "division": "NFC West"},
    {"name": "Seattle Seahawks", "abbreviation": "SEA", "city": "Seattle", "division": "NFC West"},
    {"name": "Tampa Bay Buccaneers", "abbreviation": "TB", "city": "Tampa Bay", "division": "NFC South"},
    {"name": "Tennessee Titans", "abbreviation": "TEN", "city": "Tennessee", "division": "AFC South"},
    {"name": "Washington Commanders", "abbreviation": "WAS", "city": "Washington", "division": "NFC East"}
]

# Mock player names by position
MOCK_PLAYERS = {
    "QB": [
        "Josh Allen", "Lamar Jackson", "Jalen Hurts", "Joe Burrow", "Justin Herbert",
        "Dak Prescott", "Tua Tagovailoa", "Kyler Murray", "Trevor Lawrence", "Daniel Jones",
        "Geno Smith", "Kirk Cousins", "Derek Carr", "Aaron Rodgers", "Russell Wilson",
        "Brock Purdy", "Jared Goff", "Justin Fields", "Anthony Richardson", "Bryce Young",
        "C.J. Stroud", "Jordan Love", "Mac Jones", "Sam Howell", "Desmond Ridder",
        "Kenny Pickett", "Zach Wilson", "Ryan Tannehill", "Jimmy Garoppolo", "Baker Mayfield",
        "Jacoby Brissett", "Carson Wentz"
    ],
    "RB": [
        "Christian McCaffrey", "Derrick Henry", "Dalvin Cook", "Alvin Kamara", "Ezekiel Elliott",
        "Aaron Jones", "Nick Chubb", "Joe Mixon", "Jonathan Taylor", "Austin Ekeler",
        "Saquon Barkley", "Josh Jacobs", "Kenneth Walker III", "Najee Harris", "Tony Pollard",
        "Miles Sanders", "Rhamondre Stevenson", "Dameon Pierce", "Breece Hall", "Travis Etienne",
        "James Cook", "Rachaad White", "Isiah Pacheco", "Kenneth Gainwell", "Cam Akers",
        "David Montgomery", "Kareem Hunt", "James Robinson", "Clyde Edwards-Helaire", "Antonio Gibson",
        "Devin Singletary", "Tyler Allgeier", "Brian Robinson", "Khalil Herbert", "Jerome Ford",
        "Gus Edwards", "Damien Harris", "Alexander Mattison", "Chuba Hubbard", "Samaje Perine"
    ],
    "WR": [
        "Cooper Kupp", "Davante Adams", "Tyreek Hill", "Stefon Diggs", "DeAndre Hopkins",
        "A.J. Brown", "Ja'Marr Chase", "CeeDee Lamb", "Mike Evans", "Keenan Allen",
        "Amari Cooper", "Tyler Lockett", "Jaylen Waddle", "Tee Higgins", "DK Metcalf",
        "Chris Godwin", "Amon-Ra St. Brown", "Garrett Wilson", "Calvin Ridley", "Diontae Johnson",
        "Terry McLaurin", "Courtland Sutton", "Jerry Jeudy", "Brandon Aiyuk", "Deebo Samuel",
        "Michael Pittman Jr.", "Drake London", "Chris Olave", "Jaylen Waddle", "Marquise Brown",
        "Christian Kirk", "Allen Robinson", "JuJu Smith-Schuster", "Elijah Moore", "Kadarius Toney",
        "Romeo Doubs", "Gabe Davis", "Curtis Samuel", "Jahan Dotson", "Skyy Moore"
    ],
    "TE": [
        "Travis Kelce", "Mark Andrews", "T.J. Hockenson", "Kyle Pitts", "Darren Waller",
        "George Kittle", "Dallas Goedert", "Pat Freiermuth", "Tyler Higbee", "Evan Engram",
        "David Njoku", "Gerald Everett", "Zach Ertz", "Hunter Henry", "Mike Gesicki",
        "Noah Fant", "Dawson Knox", "Cole Kmet", "Logan Thomas", "Robert Tonyan",
        "Hayden Hurst", "Tyler Conklin", "Irv Smith Jr.", "Albert Okwuegbunam", "Cade Otton",
        "Isaiah Likely", "Trey McBride", "Chigoziem Okonkwo", "Greg Dulcich", "Daniel Bellinger"
    ],
    "K": [
        "Justin Tucker", "Daniel Carlson", "Harrison Butker", "Tyler Bass", "Younghoe Koo",
        "Nick Folk", "Matt Gay", "Graham Gano", "Jason Sanders", "Evan McPherson",
        "Cairo Santos", "Mason Crosby", "Robbie Gould", "Chris Boswell", "Jake Elliott",
        "Brandon McManus", "Wil Lutz", "Ka'imi Fairbairn", "Ryan Succop", "Jason Myers",
        "Dustin Hopkins", "Matt Prater", "Cade York", "Riley Patterson", "Greg Zuerlein",
        "Michael Badgley", "Rodrigo Blankenship", "Matt Ammendola", "Tristan Vizcaino", "Joey Slye"
    ],
    "DEF": [
        "Bills", "49ers", "Cowboys", "Jets", "Eagles", "Steelers", "Ravens", "Broncos",
        "Saints", "Patriots", "Dolphins", "Chargers", "Browns", "Bengals", "Chiefs",
        "Colts", "Packers", "Cardinals", "Titans", "Jaguars", "Lions", "Vikings",
        "Falcons", "Panthers", "Bears", "Seahawks", "Rams", "Giants", "Commanders",
        "Buccaneers", "Raiders", "Texans"
    ]
}

# Injury statuses
INJURY_STATUSES = ["Healthy", "Healthy", "Healthy", "Healthy", "Probable", "Questionable", "Doubtful", "Out"]

# BYE weeks
BYE_WEEKS = {
    4: ["DAL", "NYG", "PIT", "SF"],
    5: ["MIA", "BUF", "CLE", "WAS"],
    6: ["KC", "LAC", "PHI", "TEN"],
    7: ["ARI", "CAR", "NYJ", "DEN"],
    8: ["BAL", "HOU", "IND", "NE"],
    9: ["CHI", "DET", "GB", "LV"],
    10: ["ATL", "CIN", "JAX", "NO"],
    11: ["LAR", "MIN", "SEA", "TB"],
    12: [],
    13: [],
    14: []
}


class MockDataGenerator:
    """Generate mock NFL data for testing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.current_season = 2024
        self.current_week = 8
    
    def generate_all_mock_data(self) -> Dict[str, Any]:
        """Generate complete mock dataset"""
        
        results = {
            "teams": self.create_teams(),
            "players": self.create_players(),
            "stats": self.create_player_stats(),
            "test_league": self.create_test_league(),
            "test_users": self.create_test_users()
        }
        
        self.db.commit()
        return results
    
    def create_teams(self) -> List[Team]:
        """Create NFL teams"""
        
        teams = []
        for team_data in NFL_TEAMS:
            team = Team(
                name=team_data["name"],
                abbreviation=team_data["abbreviation"],
                city=team_data["city"],
                division=team_data["division"],
                conference=team_data["division"].split()[0]  # AFC or NFC
            )
            self.db.add(team)
            teams.append(team)
        
        self.db.flush()
        return teams
    
    def create_players(self) -> List[Player]:
        """Create mock players for all positions"""
        
        players = []
        teams = self.db.query(Team).all()
        
        for position, names in MOCK_PLAYERS.items():
            for i, name in enumerate(names):
                team = random.choice(teams)
                
                # Generate realistic player attributes
                player = Player(
                    name=name,
                    position=position,
                    team_id=team.id,
                    jersey_number=random.randint(1, 99),
                    age=self._generate_age_for_position(position),
                    height=f"{self._generate_height_for_position(position)//12}'{self._generate_height_for_position(position)%12}\"",
                    weight=self._generate_weight_for_position(position),
                    years_pro=random.randint(0, 15),
                    college=self._generate_college(),
                    injury_status=random.choice(INJURY_STATUSES),
                    bye_week=self._get_bye_week_for_team(team.abbreviation)
                )
                
                self.db.add(player)
                players.append(player)
        
        self.db.flush()
        return players
    
    def create_player_stats(self) -> List[PlayerStats]:
        """Create mock player statistics for current season"""
        
        stats = []
        players = self.db.query(Player).all()
        
        for player in players:
            # Create stats for completed weeks
            for week in range(1, self.current_week + 1):
                # Skip bye weeks
                if week == player.bye_week:
                    continue
                
                stat = self._generate_weekly_stats(player, week)
                if stat:
                    self.db.add(stat)
                    stats.append(stat)
        
        self.db.flush()
        
        # Update season totals
        self._update_season_totals()
        
        return stats
    
    def _generate_weekly_stats(self, player: Player, week: int) -> Optional[PlayerStats]:
        """Generate realistic weekly stats for a player"""
        
        # Injury check - players don't play when injured
        if player.injury_status in ["Out", "IR"] and random.random() < 0.8:
            return None
        
        stat = PlayerStats(
            player_id=player.id,
            season=self.current_season,
            week=week
        )
        
        # Generate position-specific stats
        if player.position == "QB":
            self._generate_qb_stats(stat, player)
        elif player.position == "RB":
            self._generate_rb_stats(stat, player)
        elif player.position == "WR":
            self._generate_wr_stats(stat, player)
        elif player.position == "TE":
            self._generate_te_stats(stat, player)
        elif player.position == "K":
            self._generate_k_stats(stat, player)
        elif player.position == "DEF":
            self._generate_def_stats(stat, player)
        
        # Calculate fantasy points
        stat.fantasy_points_standard = self._calculate_fantasy_points(stat, "standard")
        stat.fantasy_points_ppr = self._calculate_fantasy_points(stat, "ppr")
        stat.fantasy_points_half_ppr = self._calculate_fantasy_points(stat, "half_ppr")
        
        return stat
    
    def _generate_qb_stats(self, stat: PlayerStats, player: Player):
        """Generate QB-specific stats"""
        
        # Base stats with some variance
        base_completions = random.randint(15, 35)
        base_attempts = base_completions + random.randint(5, 15)
        
        stat.pass_completions = base_completions
        stat.pass_attempts = base_attempts
        stat.pass_yards = random.randint(180, 400)
        stat.pass_touchdowns = random.choices([0, 1, 2, 3, 4], weights=[10, 30, 35, 20, 5])[0]
        stat.interceptions = random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0]
        
        # Rushing stats for mobile QBs
        stat.rush_attempts = random.randint(0, 8)
        stat.rush_yards = random.randint(0, 50)
        stat.rush_touchdowns = random.choices([0, 1], weights=[85, 15])[0]
        
        # Receiving stats (rare)
        stat.targets = 0
        stat.receptions = 0
        stat.receiving_yards = 0
        stat.receiving_touchdowns = 0
    
    def _generate_rb_stats(self, stat: PlayerStats, player: Player):
        """Generate RB-specific stats"""
        
        # Rushing stats
        stat.rush_attempts = random.randint(8, 25)
        stat.rush_yards = random.randint(30, 150)
        stat.rush_touchdowns = random.choices([0, 1, 2, 3], weights=[40, 40, 15, 5])[0]
        
        # Receiving stats
        stat.targets = random.randint(1, 8)
        stat.receptions = random.randint(0, stat.targets)
        stat.receiving_yards = random.randint(0, 80)
        stat.receiving_touchdowns = random.choices([0, 1], weights=[90, 10])[0]
        
        # Passing stats (rare)
        stat.pass_completions = 0
        stat.pass_attempts = 0
        stat.pass_yards = 0
        stat.pass_touchdowns = 0
        stat.interceptions = 0
    
    def _generate_wr_stats(self, stat: PlayerStats, player: Player):
        """Generate WR-specific stats"""
        
        # Receiving stats
        stat.targets = random.randint(3, 15)
        stat.receptions = random.randint(0, min(stat.targets, 12))
        stat.receiving_yards = random.randint(0, 150)
        stat.receiving_touchdowns = random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0]
        
        # Rushing stats (occasional)
        stat.rush_attempts = random.choices([0, 1, 2], weights=[80, 15, 5])[0]
        stat.rush_yards = random.randint(0, 20) if stat.rush_attempts > 0 else 0
        stat.rush_touchdowns = random.choices([0, 1], weights=[95, 5])[0]
        
        # Passing stats (rare)
        stat.pass_completions = 0
        stat.pass_attempts = 0
        stat.pass_yards = 0
        stat.pass_touchdowns = 0
        stat.interceptions = 0
    
    def _generate_te_stats(self, stat: PlayerStats, player: Player):
        """Generate TE-specific stats"""
        
        # Receiving stats
        stat.targets = random.randint(2, 10)
        stat.receptions = random.randint(0, min(stat.targets, 8))
        stat.receiving_yards = random.randint(0, 120)
        stat.receiving_touchdowns = random.choices([0, 1, 2], weights=[65, 30, 5])[0]
        
        # Rushing stats (rare)
        stat.rush_attempts = random.choices([0, 1], weights=[95, 5])[0]
        stat.rush_yards = random.randint(0, 10) if stat.rush_attempts > 0 else 0
        stat.rush_touchdowns = 0
        
        # Passing stats (very rare)
        stat.pass_completions = 0
        stat.pass_attempts = 0
        stat.pass_yards = 0
        stat.pass_touchdowns = 0
        stat.interceptions = 0
    
    def _generate_k_stats(self, stat: PlayerStats, player: Player):
        """Generate K-specific stats"""
        
        stat.field_goals_made = random.randint(0, 5)
        stat.field_goals_attempted = stat.field_goals_made + random.randint(0, 2)
        stat.extra_points_made = random.randint(0, 6)
        stat.extra_points_attempted = stat.extra_points_made + random.randint(0, 1)
        
        # All other stats are 0
        stat.pass_completions = 0
        stat.pass_attempts = 0
        stat.pass_yards = 0
        stat.pass_touchdowns = 0
        stat.interceptions = 0
        stat.rush_attempts = 0
        stat.rush_yards = 0
        stat.rush_touchdowns = 0
        stat.targets = 0
        stat.receptions = 0
        stat.receiving_yards = 0
        stat.receiving_touchdowns = 0
    
    def _generate_def_stats(self, stat: PlayerStats, player: Player):
        """Generate DEF-specific stats"""
        
        stat.sacks = random.randint(0, 6)
        stat.interceptions_def = random.randint(0, 3)
        stat.fumbles_recovered = random.randint(0, 2)
        stat.touchdowns_def = random.choices([0, 1, 2], weights=[80, 15, 5])[0]
        stat.safety = random.choices([0, 1], weights=[95, 5])[0]
        stat.points_allowed = random.randint(7, 35)
        stat.yards_allowed = random.randint(200, 500)
        
        # All other stats are 0
        stat.pass_completions = 0
        stat.pass_attempts = 0
        stat.pass_yards = 0
        stat.pass_touchdowns = 0
        stat.rush_attempts = 0
        stat.rush_yards = 0
        stat.rush_touchdowns = 0
        stat.targets = 0
        stat.receptions = 0
        stat.receiving_yards = 0
        stat.receiving_touchdowns = 0
        stat.field_goals_made = 0
        stat.field_goals_attempted = 0
        stat.extra_points_made = 0
        stat.extra_points_attempted = 0
    
    def _calculate_fantasy_points(self, stat: PlayerStats, scoring_type: str) -> float:
        """Calculate fantasy points for a stat line"""
        
        points = 0.0
        
        # Passing
        points += (stat.pass_yards or 0) * 0.04  # 1 point per 25 yards
        points += (stat.pass_touchdowns or 0) * 4  # 4 points per TD
        points -= (stat.interceptions or 0) * 2  # -2 points per INT
        
        # Rushing
        points += (stat.rush_yards or 0) * 0.1  # 1 point per 10 yards
        points += (stat.rush_touchdowns or 0) * 6  # 6 points per TD
        
        # Receiving
        points += (stat.receiving_yards or 0) * 0.1  # 1 point per 10 yards
        points += (stat.receiving_touchdowns or 0) * 6  # 6 points per TD
        
        # PPR scoring
        if scoring_type == "ppr":
            points += (stat.receptions or 0) * 1.0  # 1 point per reception
        elif scoring_type == "half_ppr":
            points += (stat.receptions or 0) * 0.5  # 0.5 points per reception
        
        # Kicking
        points += (stat.field_goals_made or 0) * 3  # 3 points per FG
        points += (stat.extra_points_made or 0) * 1  # 1 point per XP
        
        # Defense
        points += (stat.sacks or 0) * 1  # 1 point per sack
        points += (stat.interceptions_def or 0) * 2  # 2 points per INT
        points += (stat.fumbles_recovered or 0) * 2  # 2 points per fumble recovery
        points += (stat.touchdowns_def or 0) * 6  # 6 points per TD
        points += (stat.safety or 0) * 2  # 2 points per safety
        
        # Defense points allowed
        if stat.points_allowed is not None:
            if stat.points_allowed == 0:
                points += 10
            elif stat.points_allowed <= 6:
                points += 7
            elif stat.points_allowed <= 13:
                points += 4
            elif stat.points_allowed <= 20:
                points += 1
            elif stat.points_allowed <= 27:
                points += 0
            elif stat.points_allowed <= 34:
                points -= 1
            else:
                points -= 4
        
        return round(points, 2)
    
    def _update_season_totals(self):
        """Update season totals for all players"""
        
        players = self.db.query(Player).all()
        
        # Note: Player model doesn't have fantasy_points_season field
        # Fantasy points are calculated from individual stats as needed
        pass
    
    def create_test_league(self) -> League:
        """Create a test fantasy league"""
        
        league = League(
            name="Test League",
            platform="Mock",
            external_id="test-league-123",
            team_count=10,
            scoring_type="ppr",
            current_week=self.current_week,
            current_season=self.current_season,
            starting_qb=1,
            starting_rb=2,
            starting_wr=2,
            starting_te=1,
            starting_flex=1,
            starting_k=1,
            starting_def=1,
            bench_spots=6
        )
        
        self.db.add(league)
        self.db.flush()
        
        return league
    
    def create_test_users(self) -> List[User]:
        """Create test users for the league"""
        
        test_users = []
        
        # Create main test user
        main_user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            favorite_team="KC",
            is_active=True,
            preferred_scoring="ppr"
        )
        
        # Set password (would normally be hashed)
        main_user.hashed_password = "test_password_hash"
        
        self.db.add(main_user)
        test_users.append(main_user)
        
        # Create additional users for league
        for i in range(2, 11):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                first_name=f"User",
                last_name=f"{i}",
                favorite_team=random.choice([t["abbreviation"] for t in NFL_TEAMS]),
                is_active=True,
                hashed_password="test_password_hash",
                preferred_scoring="ppr"
            )
            
            self.db.add(user)
            test_users.append(user)
        
        self.db.flush()
        
        # Create fantasy teams for each user
        league = self.db.query(League).filter(League.name == "Test League").first()
        
        for i, user in enumerate(test_users):
            team = FantasyTeam(
                name=f"{user.first_name}'s Team",
                owner_id=user.id,
                league_id=league.id,
                wins=random.randint(0, 7),
                losses=random.randint(0, 7),
                ties=0,
                points_for=random.randint(800, 1200),
                points_against=random.randint(800, 1200)
            )
            
            self.db.add(team)
        
        self.db.flush()
        
        # Create some roster entries for the main user
        self._create_sample_roster()
        
        return test_users
    
    def _create_sample_roster(self):
        """Create a sample roster for the main test user"""
        
        main_user = self.db.query(User).filter(User.email == "test@example.com").first()
        main_team = self.db.query(FantasyTeam).filter(FantasyTeam.owner_id == main_user.id).first()
        
        # Get some top players at each position
        positions_needed = {
            "QB": 2,
            "RB": 4,
            "WR": 4,
            "TE": 2,
            "K": 1,
            "DEF": 1
        }
        
        for position, count in positions_needed.items():
            players = self.db.query(Player).filter(
                Player.position == position
            ).limit(count).all()
            
            for player in players:
                roster_entry = Roster(
                    fantasy_team_id=main_team.id,
                    player_id=player.id,
                    slot_type=position,
                    is_active=True,
                    acquisition_type="DRAFT"
                )
                
                self.db.add(roster_entry)
        
        self.db.flush()
    
    # Helper methods
    def _generate_age_for_position(self, position: str) -> int:
        """Generate realistic age for position"""
        age_ranges = {
            "QB": (22, 38),
            "RB": (21, 32),
            "WR": (22, 34),
            "TE": (23, 35),
            "K": (22, 42),
            "DEF": (22, 35)
        }
        
        min_age, max_age = age_ranges.get(position, (22, 35))
        return random.randint(min_age, max_age)
    
    def _generate_height_for_position(self, position: str) -> int:
        """Generate realistic height in inches"""
        height_ranges = {
            "QB": (70, 78),
            "RB": (66, 74),
            "WR": (68, 77),
            "TE": (74, 80),
            "K": (68, 74),
            "DEF": (70, 76)
        }
        
        min_height, max_height = height_ranges.get(position, (68, 76))
        return random.randint(min_height, max_height)
    
    def _generate_weight_for_position(self, position: str) -> int:
        """Generate realistic weight in pounds"""
        weight_ranges = {
            "QB": (205, 250),
            "RB": (190, 230),
            "WR": (170, 220),
            "TE": (230, 270),
            "K": (170, 200),
            "DEF": (200, 250)
        }
        
        min_weight, max_weight = weight_ranges.get(position, (180, 250))
        return random.randint(min_weight, max_weight)
    
    def _generate_college(self) -> str:
        """Generate random college"""
        colleges = [
            "Alabama", "Georgia", "Ohio State", "Clemson", "LSU", "Oklahoma",
            "Texas", "Florida", "Michigan", "Penn State", "Auburn", "Wisconsin",
            "Notre Dame", "USC", "Miami", "Oregon", "Washington", "Stanford",
            "North Carolina", "Tennessee", "Kentucky", "Arkansas", "Mississippi",
            "Texas A&M", "Florida State", "Virginia Tech", "Duke", "Wake Forest"
        ]
        
        return random.choice(colleges)
    
    def _get_bye_week_for_team(self, team_abbrev: str) -> int:
        """Get bye week for team"""
        for week, teams in BYE_WEEKS.items():
            if team_abbrev in teams:
                return week
        return random.randint(4, 11)
    
    def _generate_depth_position(self, position: str, index: int) -> int:
        """Generate depth chart position"""
        if position in ["QB", "K", "DEF"]:
            return (index % 3) + 1
        else:
            return (index % 4) + 1
    
    def _generate_salary(self, position: str, index: int) -> int:
        """Generate mock salary"""
        base_salaries = {
            "QB": 8000,
            "RB": 7000,
            "WR": 6500,
            "TE": 5500,
            "K": 4500,
            "DEF": 4000
        }
        
        base = base_salaries.get(position, 5000)
        variance = base * 0.3
        adjustment = (30 - index) * 100  # Better players cost more
        
        return int(base + adjustment + random.randint(-int(variance), int(variance)))


def seed_mock_data(db: Session) -> Dict[str, Any]:
    """Main function to seed database with mock data"""
    
    generator = MockDataGenerator(db)
    results = generator.generate_all_mock_data()
    
    print(f"Mock data generated successfully:")
    print(f"- {len(results['teams'])} teams")
    print(f"- {len(results['players'])} players")
    print(f"- {len(results['stats'])} player stats")
    print(f"- 1 test league with {len(results['test_users'])} users")
    
    return results