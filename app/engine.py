import urllib3, json
import tqdm
import numpy
import itertools
from numba import jit

FILL_PENALTY = 500

def score(team_1, team_2):
    # First, compute the penalty from people being out of
    # their preferred positions.
    positions = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    _players  = team_1 + team_2
    penalty   = 0.
    for p_ix, player in enumerate(_players):
        assigned = positions[p_ix]
        affinity = int(player.config.positions[assigned])
        penalty += FILL_PENALTY * (5 - affinity)

    # Next, compute the penalty from each lane matchup.
    lane_penalty = []
    for p_ix in range(3):
        gap = numpy.abs(team_1[p_ix].mmr - team_2[p_ix].mmr)
        lane_penalty.append(gap)
    # Handle bot lane differently.
    bot_1_average = (team_1[3].mmr + team_1[4].mmr) / 2.
    bot_2_average = (team_2[3].mmr + team_2[4].mmr) / 2.
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
        return str([self.config.name, self.config.positions, self.mmr])

    def __hash__(self):
        return hash(self.config.name)

    def get_mmr(self):
        url_base = 'https://na.whatismymmr.com/api/v1/summoner'
        http = urllib3.PoolManager()
        response = http.request(
             'GET', url_base, fields={"name" : self.config.name}
        )
        decoded = response.data.decode('UTF-8')
        res = json.loads(decoded)
        norm_mmr = res["normal"]["avg"]
        rank_mmr = res["ranked"]["avg"]
        try:
            aram_mmr = res["aram"]["avg"] - 100
        except:
            aram_mmr = 0
        if norm_mmr is None:
            norm_mmr = 1000
        if rank_mmr is None:
            rank_mmr = 1000
        if aram_mmr is None:
            aram_mmr = 1000
        mmr = max(norm_mmr, rank_mmr)
        return mmr

class Match(object):

    def __init__(self, players_p):
        self.players_p   = set(players_p)
        self.Np          = len(players_p)
        self._best_score = 1e12
        self._best_teams = None
        assert self.Np == 10, self.Np

    def order_teams(self, team_1, team_2):
        best = 1e12
        _order1, _order2 = None, None
        for order1 in itertools.permutations(range(5)):
            for order2 in itertools.permutations(range(5)):
                team_1_order = [team_1[i] for i in order1]
                team_2_order = [team_2[i] for i in order2]
                _score, _ = score(team_1_order, team_2_order)
                if _score < best:
                    best = _score
                    _order1, _order2 = team_1_order, team_2_order
        return best, _order1, _order2

    def compute_matchings(self):
        for comb in tqdm.tqdm(itertools.combinations(self.players_p, self.Np // 2), total=252):
            team_1 = list(comb)
            team_2 = list(self.players_p - set(comb))

            _score, _order1, _order2 = self.order_teams(team_1, team_2)
            if _score < self._best_score:
                self._best_score = _score
                self._best_teams = (_order1, _order2)
        return self._best_teams, self._best_score

def parse_text(fpath):
    with open(fpath, 'r') as f:
        lines = f.readlines()
        lines = [line.strip().split(": ") for line in lines]
        names, prefs = zip(*lines)
        prefs = [[int(i) for i in pref] for pref in prefs]
    players = []
    for name, pref in zip(names, prefs):
        config = Config(name, pref)
        players.append(Player(config))
    from pprint import pprint
    pprint(players)
    match = Match(players)
    teams, score = match.compute_matchings()
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

if __name__ == "__main__":
    parse_text('./sample.txt')
