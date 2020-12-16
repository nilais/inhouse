import dload
import numpy
import tqdm
import itertools

FILL_PENALTY = 300

def score(team_1, team_2):
    # First, compute the penalty from people being out of
    # their preferred positions.
    positions = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    _players  = team_1 + team_2
    penalty   = 0.
    for p_ix, player in enumerate(_players):
        assigned = positions[p_ix]
        print(assigned, player.config.positions)
        affinity = int(player.config.positions[assigned])
        penalty += FILL_PENALTY * (5 - affinity)

    # Next, compute the penalty from each lane matchup.
    lane_penalty = []
    for p_ix in range(3):
        gap = numpy.abs(team_1[p_ix].mmr - team_2[p_ix].mmr)
        lane_penalty.append(gap)
    # Handle bot lane differently.
    bot_1_average = team_1[3].mmr + team_1[4].mmr
    bot_2_average = team_2[3].mmr + team_2[4].mmr
    gap = numpy.abs(bot_1_average - bot_2_average)
    lane_penalty.append(gap)
    return penalty + max(lane_penalty), max(lane_penalty)

class Config(object):

    def __init__(self, name, positions):
        self.name      = name
        self.positions = positions

class Player(object):

    def __init__(self, config):
        self.config = config
        self.mmr    = self.get_mmr()

    def __repr__(self):
        return(self.config.name)

    def __hash__(self):
        return hash(self.config.name)

    def get_mmr(self):
        url_base = 'https://na.whatismymmr.com/api/v1/summoner?name='
        url = url_base + "+".join(self.config.name.split())
        res = dload.json(url)
        if not res["normal"]["warn"]:
            mmr = res["normal"]["avg"]
        elif not res["ranked"]["warn"]:
            mmr = res["ranked"]["avg"]
        else:
            mmr = 1100
        return mmr

class Match(object):

    def __init__(self, players_p):
        self.players_p   = set(players_p)
        self.Np          = len(players_p)
        self._best_score = 1e12
        self._best_teams = None
        assert self.Np == 10, self.Np

    def compute_matchings(self):
        for comb in tqdm.tqdm(itertools.combinations(self.players_p, self.Np // 2)):
            team_1 = list(comb)
            team_2 = list(self.players_p - set(comb))
            _score = score(team_1, team_2)
            if _score < self._best_score:
                self._best_score = _score
                self._best_teams = (team_1, team_2)
        return self._best_teams, self._best_score

def parse_text(fpath):
    with open(fpath, 'r') as f:
        lines = f.readlines()
        lines = [line.strip().split(": ") for line in lines]
        names, prefs = zip(*lines)
        print(prefs)
        prefs = [[int(i) for i in pref] for pref in prefs]
    players = []
    for name, pref in zip(names, prefs):
        config = Config(name, pref)
        players.append(Player(config))
    match = Match(players)
    teams, score = match.compute_matchings()
    from pprint import pprint
    pprint(teams)
    print(score)

def process_matches(users):
    names = [user.username for user in users]
    prefs = [list(user.preferences) for user in users]

    players = []
    for name, pref in zip(names, prefs):
        config = Config(name, pref)
        players.append(Player(config))
    match = Match(players)
    teams, score = match.compute_matchings()
    return teams, score
