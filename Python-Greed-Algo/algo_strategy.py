import gamelib
import random
import copy
import math
import warnings
from sys import maxsize
import json

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
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
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        game_map = gamelib.GameMap(self.config)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        self.greedy_strategy(game_state, game_map)
        game_state.submit_turn()

    def opening(self, game_state, game_map):
        not_furtherest_in_territory_edges = self.get_edges(game_state)
        not_furtherest_in_territory_edges.pop(0)
        not_furtherest_in_territory_edges.pop(game_map.HALF_ARENA - 1)
        for edge_location in not_furtherest_in_territory_edges:
            game_state.attempt_spawn(WALL, edge_location)

    def greedy_strategy(self, game_state, game_map):
        """
        Strategy that tries to make the best decision on each turn with no look-ahead

                Params:
                    game_state (game_state): current game state
        """

        if game_state.turn_number == 0:
            self.opening(game_state, game_map)

        self.build_defences(game_state, game_map)
        gamelib.debug_write("Finished Defenses")

        self.build_attack(game_state)
        gamelib.debug_write("Finished Attack")

    def build_defences(self, game_state, game_map):
        """
        Places turrets to protect most vulnerable paths
        """

        vulnerable_locations = []
        likely_starts, unaltered_damage = self.least_damage_spawn(game_state, myself=False)

        for start in likely_starts:
            for location in game_state.find_path_to_edge(start):
                vulnerable_locations.append(location)

        best_spawns, _ = self.least_damage_spawn(game_state)
        best_attack_path = game_state.find_path_to_edge(best_spawns[0])

        while game_state.get_resource(SP) >= 2:
            defensive_options = []
            for x in range(game_map.ARENA_SIZE):
                for y in range(game_map.HALF_ARENA):
                    if not [x, y] in best_attack_path:
                        for tower in [WALL, TURRET]:
                            if game_state.can_spawn(tower, [x, y]):
                                hypothetical_game_state = copy.deepcopy(game_state)
                                hypothetical_game_state.game_map.add_unit(tower, [x, y])
                                damage_added = self.get_path_damage(hypothetical_game_state, game_state.find_path_to_edge([x, y]), myself=False) - unaltered_damage
                                if tower == WALL:
                                    damage_added *= 2
                                defensive_options.append((damage_added, tower, [x, y]))
                                # gamelib.debug_write("Adding option " + tower)

                        if TURRET == game_state.game_map[x, y]:
                            hypothetical_game_state = copy.deepcopy(game_state)
                            hypothetical_game_state.game_map[x, y].upgrade()
                            damage_added = self.get_path_damage(hypothetical_game_state,
                                                                game_state.find_path_to_edge([x, y]),
                                                                myself=False) - unaltered_damage
                            defensive_options.append(damage_added, "upgrade", [x, y])
                            # gamelib.debug_write("Adding option")

            if not defensive_options:
                break
            best_option = max(defensive_options)

            if best_option == "upgrade":
                game_state.attempt_upgrade(best_option[2])
                gamelib.debug_write("upgrading")
            else:
                game_state.attempt_spawn(best_option[1], best_option[2])
                gamelib.debug_write("placing " + best_option[1])

    def build_attack(self, game_state):
        open_edges = []
        gamelib.debug_write("Filtering my_edges")
        for start in self.get_edges(game_state):
            if game_state.can_spawn(SCOUT, start):
                open_edges.append(start)

        chosen_locations, damage_taken = self.least_damage_spawn(game_state, open_edges)
        chosen_location = chosen_locations[0]
        scout_hp = 15
        if game_state.find_path_to_edge(chosen_location)[-1] in self.get_edges(game_state, myself=False):
            if int(game_state.get_resource(MP))*scout_hp > damage_taken:
                while game_state.get_resource(MP) >= 1:
                    game_state.attempt_spawn(SCOUT, chosen_location)
        else:
            while game_state.get_resource(MP) >= 3:
                game_state.attempt_spawn(DEMOLISHER, chosen_location)

    def least_damage_spawn(self, game_state, myself: bool = True):
        possible_starts = []
        for start in self.get_edges(game_state, myself=myself):
            if not game_state.contains_stationary_unit(start):
                possible_starts.append(start)

        damages = []
        for location in possible_starts:
            path = game_state.find_path_to_edge(location)
            if (path[-1][1] >= 14 and myself) or (path[-1][1] < 14 and not myself):
                particular_damage = self.get_path_damage(game_state, path, myself)
                damages.append((particular_damage, location))

        if len(damages) == 0:
            return [possible_starts[0]], -1
        min_damage = min(damages)[0]
        best_starts = []
        for pair in damages:
            if pair[0] == min_damage:
                best_starts.append(pair[1])

        return best_starts, min_damage

    def get_path_damage(self, game_state, path, myself: bool = True):
        particular_damage = 0
        for path_location in path:
            for attacker in game_state.get_attackers(path_location, not myself):
                if attacker.attackRange == 2.5:
                    particular_damage += 5
                if attacker.attackRange == 3.5:
                    particular_damage += 15
        return particular_damage

    def get_edges(self, game_state, myself: bool = True):
        """
        Function to get each player's edges

                Params:
                    self (self): self
                    game_state (game_state): current game state
                    your_edges (bool): bool that is true if you want your own edges and false if you want your opponent's

                Returns: List of edge coordinates
        """

        if myself:
            edges = game_state.game_map.get_edge_locations(
                game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(
                game_state.game_map.BOTTOM_RIGHT)
        else:
            edges = game_state.game_map.get_edge_locations(
                game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        return edges


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
