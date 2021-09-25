from networking.io import Logger
from game import Game
from api import game_util
from model.position import Position
from model.decisions.move_decision import MoveDecision
from model.decisions.action_decision import ActionDecision
from model.decisions.buy_decision import BuyDecision
from model.decisions.harvest_decision import HarvestDecision
from model.decisions.plant_decision import PlantDecision
from model.decisions.do_nothing_decision import DoNothingDecision
from model.tile_type import TileType
from model.item_type import ItemType
from model.crop_type import CropType
from model.upgrade_type import UpgradeType
from model.game_state import GameState
from model.player import Player
from api.constants import Constants

import random

logger = Logger()
constants = Constants()


def crops_in_range(game_state, positions):
    for pos in positions:
        if game_state.tile_map.get_tile(pos.x, pos.y).crop.type:
            return True
    return False


def get_move_decision(game: Game, state) -> MoveDecision:
    """
    Returns a move decision for the turn given the current game state.
    This is part 1 of 2 of the turn.

    Remember, you can only sell crops once you get to a Green Grocer tile,
    and you can only harvest or plant within your harvest or plant radius.

    After moving (and submitting the move decision), you will be given a new
    game state with both players in their updated positions.

    :param: game The object that contains the game state and other related information
    :returns: MoveDecision A location for the bot to move to this turn
    """
    game_state: GameState = game.get_game_state()
    logger.debug(f"[Turn {game_state.turn}] Feedback received from engine: {game_state.feedback}")

    # Select your decision here!
    my_player: Player = game_state.get_my_player()
    pos: Position = my_player.position
    logger.info(f"Currently at {my_player.position}")
    harvestables = game_util.within_harvest_range(game_state, my_player.name)

    def move_towards(posit: Position) -> Position:
        dists = [(game_util.distance(move_pos, posit), move_pos)
                 for move_pos in game_util.within_move_range(game_state, my_player.name)]
        minim = min((dist for dist in dists), key=lambda x: x[0])[1]
        return minim

    # If we have something to sell that we harvested, then try to move towards the green grocer tiles
    if ((sum(my_player.seed_inventory.values()) == 0 and my_player.money >= 5) or
            len(my_player.harvested_inventory) > 0) and \
            not len(state['plants']):

        logger.debug("Moving towards green grocer")
        pos = min(move_towards(Position(13, 0)), move_towards(Position(17, 0)),
                  key=lambda x: game_util.distance(x, my_player.position))
    elif sum(my_player.seed_inventory.values()) > 0 and game_state.turn >= 21:
        pos = move_towards(Position(my_player.position.x, game_state.fband_mid_y + 1))
    else:
        if len(state['plants']) and state['plants'][0][1] <= game_state.turn and crops_in_range(game_state, [state['plants'][0][0]]):
            pos = move_towards(state['plants'][0][0])
            state['plants'].remove(state['plants'][0])
    decision = MoveDecision(move_towards(pos))

    logger.debug(f"[Turn {game_state.turn}] Sending MoveDecision: {decision}")
    return decision


def get_action_decision(game: Game, state) -> ActionDecision:
    """
    Returns an action decision for the turn given the current game state.
    This is part 2 of 2 of the turn.

    There are multiple action decisions that you can return here: BuyDecision,
    HarvestDecision, PlantDecision, or UseItemDecision.

    After this action, the next turn will begin.

    :param: game The object that contains the game state and other related information
    :returns: ActionDecision A decision for the bot to make this turn
    """
    game_state: GameState = game.get_game_state()
    logger.debug(f"[Turn {game_state.turn}] Feedback received from engine: {game_state.feedback}")
    # Select your decision here!
    my_player: Player = game_state.get_my_player()
    pos: Position = my_player.position
    # Focus on quads unless we have enough for golden corn
    crop = CropType.GOLDEN_CORN \
        if my_player.money >= 1000 else CropType.DUCHAM_FRUIT

    # Get a list of possible harvest locations for our harvest radius
    possible_harvest_locations = []
    harvest_radius = my_player.harvest_radius
    for harvest_pos in game_util.within_harvest_range(game_state, my_player.name):
        if game_state.tile_map.get_tile(harvest_pos.x, harvest_pos.y).crop.value > 0:
            possible_harvest_locations.append(harvest_pos)

    logger.debug(f"Possible harvest locations={[str(loc) for loc in possible_harvest_locations]}")
    # If we can harvest something, try to harvest it
    if len(possible_harvest_locations) and crops_in_range(game_state, possible_harvest_locations):
        decision = HarvestDecision(possible_harvest_locations)
        state['plants'] = [i for i in state['plants'] if i not in possible_harvest_locations]
    # If not but we have that seed, then try to plant it in a fertility band
    elif my_player.seed_inventory[crop] > 0 and \
            game_state.tile_map.get_tile(pos.x, pos.y).type != TileType.GREEN_GROCER and \
            pos.y == game_state.fband_mid_y + 1:
        logger.debug(f"Deciding to try to plant at position {pos}")
        # generate locations for 5 to left and right of player
        plant_pos = [Position(pos.x - i, pos.y + j) for i in range(1, 6) for j in range(0, 2)]
        plant_pos.extend([Position(pos.x + i, pos.y + j) for i in range(1, 6) for j in range(0, 2)])
        decision = PlantDecision([crop for i in range(len(plant_pos))], plant_pos)
        state['plants'].extend([(pos, game_state.turn + crop.get_growth_time()) for pos in plant_pos if pos.y == my_player.position.y])
    # If we don't have that seed, but we have the money to buy it, then move towards the
    # green grocer to buy it
    elif my_player.money >= crop.get_seed_price() * 3 and \
            game_state.tile_map.get_tile(pos.x, pos.y).type == TileType.GREEN_GROCER and \
            not game_util.distance(pos, Position(pos.x, game_state.fband_bot_y + 1)) > 40:
        buy_count = my_player.money // crop.get_seed_price()
        logger.debug(f"Buy {buy_count} of {crop}")
        decision = BuyDecision([crop], [buy_count])
    # If we can't do any of that, then just do nothing (move around some more)
    else:
        logger.debug(f"Couldn't find anything to do, waiting for move step")
        decision = DoNothingDecision()

    logger.debug(f"[Turn {game_state.turn}] Sending ActionDecision: {decision}")
    return decision


def main():
    """
    Competitor TODO: choose an item and upgrade for your bot
    """
    game = Game(ItemType.DELIVERY_DRONE, UpgradeType.SEED_A_PULT)
    state = {
        'action': "start",
        'plant_chill_time': 5,
        'plants': []
    }
    while (True):
        try:
            game.update_game()
        except IOError:
            exit(-1)
        game.send_move_decision(get_move_decision(game, state))

        try:
            game.update_game()
        except IOError:
            exit(-1)
        game.send_action_decision(get_action_decision(game, state))


if __name__ == "__main__":
    main()
