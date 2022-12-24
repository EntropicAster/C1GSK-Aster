import gamelib
import random
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
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.greedy_strategy(game_state)
        game_state.submit_turn()

    def greedy_strategy(self, game_state):
        '''
        Strategy that tries to make the best decision on each turn with no look-ahead

                Params:
                    game_state (game_state): current game state
        '''

        if game_state.turn_number == 0:

            self.opening(game_state)

        self.build_defences(game_state)
        gamelib.debug("Finished Defenses")

        self.build_attack(game_state)
        gamelib.debug("Finished Attack")
        
    def build_defenses(self, game_state):
        '''
        Places turrets to protect most vulnerable paths
        '''

        vulnerable_locations = []
        likely_starts = self.enemy_least_damage(game_state)

        for start in likely_starts:
            for location in game_state.find_path_to_edge(start):
                vulnerable_locations.append(location)

    # Finish this function later



    def get_edges(self, game_state, your_edges: bool = True):
        '''
        Function to get each player's edges

                Params:
                    self (self): self
                    game_state (game_state): current game state
                    your_edges (bool): bool that is true if you want your own edges and false if you want your opponent's

                Returns: List of edge coordinates
        '''

        if your_edges:
            edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        else:
            edges = game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        return edges

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
