import gamelib
import random
import math
import warnings
from sys import maxsize
import json


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        global my_edges
        my_edges = []
        gamelib.debug_write("Setting up edges")
        for x in range(14):
            my_edges.append([int(x), int(13 - x)])
        for x in range(14):
            my_edges.append([int(14 + x), int(x)])

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.
        self.starter_strategy(game_state)
        gamelib.debug_write("Submitted Turn")
        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        This section is useful for deciding on which strategy to use (table of contents)
        """
        if(game_state.turn_number == 0):
            self.opening(game_state)
        self.build_defences(game_state)
        gamelib.debug_write("Finished Defenses")
        self.build_attack(game_state)

    def build_defences(self, game_state):

        self.GREEDt(game_state)
        '''
        while game_state.get_resource(SP) > 1:
            x = random.randint(0,28)
            y = random.randint(0, 14)
        #y = random.randint(0,14)
            if game_state.can_spawn(TURRET, [x,y]):
                game_state.attempt_spawn(TURRET,[x,y])
        '''

    def GREEDt(self, game_state):
        vuln_locations = []
        likely_starts = self.enemy_least_damage(game_state)
        gamelib.debug_write("adding  starts")
        for start in likely_starts:
            for location in game_state.find_path_to_edge(start):
                vuln_locations.append(location)
        open_locations = []
        necessary = []
        open_edges = []
        gamelib.debug_write("Filtering my_edges")
        for start in my_edges:
            if game_state.can_spawn(SCOUT, start):
                open_edges.append(start)
        gamelib.debug_write("Preventing blocking")
        for start in open_edges:
            for local in game_state.find_path_to_edge((self.least_damage_spawn_location(game_state, open_edges))):
                necessary.append(locals)
        gamelib.debug_write("Assembing my board")
        for x in range(28):
            for y in range(14):
                if game_state.can_spawn(TURRET, [x, y]):
                    if necessary.count([x,y]) == 0:
                        open_locations.append([x, y])
        damage_outputs = []
        gamelib.debug_write("Calculating damages")
        for location in open_locations:
            damage_outputs.append(0)
            for target in vuln_locations:
                if (self.is_in_range(location, target, 2.5)):
                    damage_outputs[len(damage_outputs) - 1] += 5
        gamelib.debug_write("Placing towers")
        while game_state.get_resource(SP) > 1 and len(open_locations) > 0:
            game_state.attempt_spawn(TURRET, open_locations[damage_outputs.index(max(damage_outputs))])
            damage_outputs.remove(max(damage_outputs))
            open_locations.pop(damage_outputs.index(max(damage_outputs)))
        gamelib.debug_write("Finished placement")

    def build_attack(self, game_state):
        open_edges = []
        gamelib.debug_write("Filtering my_edges")
        for start in my_edges:
            if game_state.can_spawn(SCOUT, start):
                open_edges.append(start)
        chosen_location = self.least_damage_spawn_location(game_state, open_edges)
        while game_state.get_resource(MP) > 0:
            game_state.attempt_spawn(SCOUT, chosen_location)

    def least_damage_spawn_location(self, game_state, location_options):
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = []
            if game_state.can_spawn(SCOUT, location):
                for location in game_state.find_path_to_edge(location):
                    path.append(location)
                damage = 0
                for path_location in path:
                        damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
                damages.append(damage)
        chosen = [[0, 2]]
        while (not chosen[-1] in enemy_edges) and len(damages) > 0:
            chosen = location_options[damages.index(min(damages))]
            location_options.pop(damages.index(min(damages)))
            damages.remove(min(damages))
        damage_taken = 0
        return [chosen, damage_taken]

    def is_in_range(self, l1, l2, rang):
        if (math.sqrt((l1[0] - l2[0]) * (l1[0] - l2[0]) + (l1[1] - l2[1]) * (l1[1] - l2[1])) < rang):
            return True
        return False

    def enemy_least_damage(self, game_state):
        damages = []
        possible_starts = []
        for start in enemy_edges:
            if not game_state.contains_stationary_unit(start):
                possible_starts.append(start)
        for location in possible_starts:
            path = game_state.find_path_to_edge(location)
            paticular_damage = 0
            for path_location in path:
                for attacker in game_state.get_attackers(path_location, 1):
                    if (attacker.attackRange == 2.5):
                        paticular_damage += 5
                    if (attacker.attackRange == 3.5):
                        paticular_damage += 15
            damages.append(paticular_damage)
        to_be_removed = []
        start = 0
        while (start < len(possible_starts)):
            if not damages[start] == min(damages):
                possible_starts.pop(start)
                damages.pop(start)
                start -= 1
            start += 1
        return possible_starts

    def opening(self, game_state):
        walls = [[0, 13], [1, 12], [2, 11], [3, 11], [4, 11], [5, 11], [6, 11], [7, 11], [8, 11], [9, 11], [10, 11], [27, 13], [26, 12], [25, 11], [24, 11], [23, 11], [22, 11], [21, 11], [20, 11], [19, 11], [18, 11], [17, 11]]
        for place in walls:
            game_state.attempt_spawn(WALL, place)
        turrets = [[9, 10], [10, 10], [13, 12], [14, 12], [17, 10], [18, 10]]
        for place in turrets:
            game_state.attempt_spawn(TURRET, place)


enemy_edges = [[0, 14], [1, 15], [2, 16], [3, 17], [4, 18], [5, 19], [6, 20], [7, 21], [8, 22], [9, 23], [10, 24],
               [11, 25], [12, 26], [13, 27], [14, 27], [15, 26], [16, 25], [17, 24], [18, 23], [19, 22], [20, 21],
               [21, 20], [22, 19], [23, 18], [24, 17], [25, 16], [26, 15], [27, 14]]

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()

