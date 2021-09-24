from api.constants import Constants
from model.player import Player
from model.tile_map import TileMap
from typing import Dict


class GameState:
    def __init__(self, gamestate_dict: Dict) -> None:
        constants = Constants()
        self.turn = gamestate_dict['turn']
        self.player1 = Player(gamestate_dict['p1'])
        self.player2 = Player(gamestate_dict['p2'])
        self.tile_map = TileMap(gamestate_dict['tileMap'])
        self.player_num = gamestate_dict['playerNum']
        self.feedback = gamestate_dict['feedback']
        self.fband_bot_y = ((self.turn - 1) / 3) - 1
        self.fband_mid_y = self.fband_bot_y - constants.FBAND_INNER_HEIGHT - constants.FBAND_OUTER_HEIGHT

    def get_my_player(self) -> Player:
        if self.player_num == 1:
            return self.player1
        else:
            return self.player2

    def get_opponent_player(self) -> Player:
        if self.player_num == 1:
            return self.player2
        else:
            return self.player1
