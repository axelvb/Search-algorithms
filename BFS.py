import argparse
from queue import PriorityQueue
import random
import sys
from typing import Iterable
from itertools import count
import wumpus as wws

from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any=field(compare=False)


class BFSPlayer(wws.OfflinePlayer):
    

    def findNeighbours(self, pos: tuple, world_info:dict):
            left = (pos[0]-1, pos[1])
            right = (pos[0]+1, pos[1])
            up = (pos[0], pos[1]+1)
            down = (pos[0], pos[1]-1)
            
            possible_neighbours = [left, right, up, down]
            neighbours = []
            
            for position in possible_neighbours:
                if position[0] < 0 or position[1] < 0 or position[0] > world_info['Size'][0] or position[1] > world_info['Size'][1]:
                    continue
                if position in world_info['Pits']:
                    continue 
                neighbours.append(position)

            return neighbours


    def doesPathExist(self, world_info: dict):
        # Does a DFS to determine if there exists a possible path from agent to gold
        # Returns true if path exists and false if not

        start = world_info['Hunter'][0]
        
        if (world_info['Gold'] == start):
            return True
        
        visited = [start]

        stack = [] #nodes to be visited
        start_neighbours = self.findNeighbours(start, world_info)

        for neighbour in start_neighbours:
            stack.append(neighbour)

        while len(stack) > 0:
            current = stack.pop()
            if current == world_info['Gold'][0]:
                return True
            neighbours = self.findNeighbours(current, world_info)
            for neighbour in neighbours:
                if not neighbour in visited:
                    stack.append(neighbour)
            visited.append(current)
        return False


    def start_episode(self, world: wws.WumpusWorld) -> Iterable[wws.Hunter.Actions]:
        """Print the description of the world before starting."""

        world_info = {k: [] for k in ('Hunter', 'Pits', 'Wumpus', 'Gold', 'Exits')}
        world_info['Size'] = (world.size.x, world.size.y)
        world_info['Blocks'] = [(c.x, c.y) for c in world.blocks]

        for obj in world.objects:
            if isinstance(obj, wws.Hunter):
                world_info['Hunter'].append((obj.location.x, obj.location.y))
                all_actions = list(obj.Actions)
            elif isinstance(obj, wws.Pit):
                world_info['Pits'].append((obj.location.x, obj.location.y))
            elif isinstance(obj, wws.Wumpus):
                world_info['Wumpus'].append((obj.location.x, obj.location.y))
            elif isinstance(obj, wws.Exit):
                world_info['Exits'].append((obj.location.x, obj.location.y))
            elif isinstance(obj, wws.Gold):
                world_info['Gold'].append((obj.location.x, obj.location.y))

        print('World details:')
        for k in ('Size', 'Pits', 'Wumpus', 'Gold', 'Exits', 'Blocks'):
            print('  {}: {}'.format(k, world_info.get(k, None)))      

        move = all_actions[0]
        right = all_actions[1]
        left = all_actions[2]
        shoot = all_actions[3]
        grab = all_actions[4]
        climb = all_actions[5]
        #Grabing and leaving if gold is in start square
        if world_info['Gold'][0] == (0,0):
            return [grab, climb]
        
        # Checking if path exists before doing heavy computation
        if not self.doesPathExist(world_info):
            return [climb]
        
        
        
        frontier = PriorityQueue()                       
        #Structure of states: [Arrow used, Wumpus dead, direction, player pos, actions taken to get to state]
        start_state = [False, False, 'N', (0,0), []]

        frontier.put(PrioritizedItem(0, start_state))   #Priority of actions taken

        reached_gold = False     # When the gold is reached the best journey back will always be the way you came, so no need to compute that as well
        
        while not frontier.empty() and (not reached_gold):
    
            parent = frontier.get()
            parent = (parent.priority, parent.item)
            parent_state = parent[1]
            
            for action in all_actions:     #Looping through Left, right, shoot and move and adding resulting states to frontier. Grab and climb are handled once the gold is reached
                legal_move = True
                if action == left:
                    actions = list(parent_state[4])
                    actions.append(left)
                    # Finding new direction after turn
                    if parent_state[2] == 'E':
                        new_direction = 'N'
                    elif parent_state[2] == 'N':
                        new_direction = 'W'
                    elif parent_state[2] == 'W':
                        new_direction = 'S'
                    else:
                        new_direction = 'E'
                    
                    new_state = [parent_state[0], parent_state[1], new_direction, parent_state[3], actions]
                    
                elif action == right:
                    actions = list(parent_state[4])
                    actions.append(right)
                    # Finding new direction after turn
                    if parent_state[2] == 'E':
                        new_direction = 'S'
                    elif parent_state[2] == 'N':
                        new_direction = 'E'
                    elif parent_state[2] == 'W':
                        new_direction = 'N'
                    else:
                        new_direction = 'W'
                    
                    new_state = [parent_state[0], parent_state[1], new_direction, parent_state[3], actions]
                    
                        
                elif action == move:
                    current_pos = parent_state[3]
                    current_dir = parent_state[2]                    
                    
                    # Calculating new position
                    if current_dir == 'E':
                        new_x = current_pos[0] + 1
                        new_y = current_pos[1]
                    elif current_dir == 'N':
                        new_x = current_pos[0]
                        new_y = current_pos[1] + 1
                    elif current_dir == 'W':
                        new_x = current_pos[0] - 1
                        new_y = current_pos[1]
                    else:
                        new_x = current_pos[0]
                        new_y = current_pos[1] - 1
                    
                    new_pos = (new_x, new_y)
                    # Checking if new position is legal and also not suicide
                    if new_pos in world_info['Pits'] or new_pos in world_info['Wumpus']:
                        legal_move = False
                    
                    if new_pos[0] < 0 or new_pos[0] >= world_info['Size'][0] or new_pos[1] < 0 or new_pos[1] >= world_info['Size'][1]:
                        legal_move = False
                        
                    if legal_move:
                        actions = list(parent_state[4])
                        actions.append(move)
                        
                        new_state = [parent_state[0], parent_state[1], parent_state[2], new_pos, actions]
                        # Checking if gold is reached and saving the state if it is
                        if new_pos == world_info['Gold'][0]:
                            reached_gold = True
                            gold_state = new_state
                            break
                        
                
                
                elif action == shoot:
                    actions = list(parent_state[4])
                    actions.append(shoot)
                    
                    current_pos = parent_state[3]
                    current_dir = parent_state[2]
                    wumpus_pos = world_info['Wumpus'][0]
                    wumpus_dead = parent_state[1]
                    arrow_used = parent_state[0]
                    
                    if arrow_used:   #Cant shoot without a arrow, so no need to add new state
                        legal_move = False
                        continue
                    # Checking if the wumpus is hit by the arrow
                    if current_dir == 'N':
                        if wumpus_pos[0] == current_pos[0] and wumpus_pos[1] > current_pos[1]:
                            wumpus_dead = True
                    elif current_dir == 'E':
                        if wumpus_pos[1] == current_pos[1] and wumpus_pos[0] > current_pos[0]:
                            wumpus_dead = True
                    elif current_dir == 'S':
                        if wumpus_pos[0] == current_pos[0] and wumpus_pos[1] < current_pos[1]:
                            wumpus_dead = True
                    elif current_dir == 'W':
                        if wumpus_pos[1] == current_pos[1] and wumpus_pos[0] < current_pos[0]:
                            wumpus_dead = True
                            
                    arrow_used = True
                    
                    new_state = [arrow_used, wumpus_dead, current_dir, current_pos, actions]                
                    
                # Adding the new state to the frontier with cost +1 from parent
                if legal_move:
                    #print(f'Added new state {next(counter)}')
                    moveTest = PrioritizedItem(parent[0]+1, new_state) 
                    frontier.put(moveTest)
                        
        #Now the gold is reached and the state is saved
        #We have to find the way back as well
        actions_to_gold = gold_state[4]
        all_actions = list(actions_to_gold)

        #Taking the gold and turning around
        all_actions.append(grab)
        all_actions.append(left)
        all_actions.append(left)

        #Reversing our actions, no need to consider shoot
        for action in list(actions_to_gold[::-1]):
            if action == left:
                all_actions.append(right)
            if action == right:
                all_actions.append(left)
            if action == move:
                all_actions.append(move)
                
        if all_actions[-1] != move:
            all_actions = all_actions[:-1]    #If the last move is a turn (left or right) we can remove it
            
        all_actions.append(climb)
        print(all_actions)
        return all_actions
        


def classic(size: int = 0):
    """Play the classic version of the wumpus."""
    # create the world
    world = wws.WumpusWorld.classic(size=size if size > 3 else random.randint(4, 8))

    # Run a player without any knowledge about the world
    wws.run_episode(world, wws.UserPlayer())


def classic_offline(size: int = 0):
    """Play the classic version of the wumpus with a player knowing the world and the agent."""
    # create the world
    world = wws.WumpusWorld.classic(size=size if size > 3 else random.randint(4, 8))

    # Run a player with knowledge about the world
    wws.run_episode(world, BFSPlayer())


WUMPUS_WORLD = '''
    {
        "id": "simple wumpus world",
        "size": [7, 7],
        "hunters": [[0, 0]],
        "pits": [[4, 0], [3, 1], [2, 2], [6, 2], [4, 4], [3, 5], [4, 6], [5, 6]],
        "wumpuses": [[1, 2]],
        "exits": [[0, 0]],
        "golds": [[6, 3]],
        "blocks": []
    }
'''


def fixed_offline(world_json: str = WUMPUS_WORLD):
    """Play on a given world described in JSON format."""
    # create the world
    world = wws.WumpusWorld.from_JSON(world_json)

    # Run a player with knowledge about the world
    wws.run_episode(world, BFSPlayer())


def real_deal(size: int = 0):
    """Play the classic version of the wumpus without being able to see the actual layout, that is as the actual software agent will do."""
    # create the world
    world = wws.WumpusWorld.classic(size=size if size > 3 else random.randint(4, 8))

    # Run a player without any knowledge about the world
    wws.run_episode(world, wws.UserPlayer(), show=False)


EXAMPLES = (classic, classic_offline, fixed_offline, real_deal)


def main(*cargs):
    """Demonstrate the use of the wumpus API on selected worlds"""
    ex_names = {ex.__name__.lower(): ex for ex in EXAMPLES}
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('example', nargs='?', help='select one of the available example', choices=list(ex_names.keys()))
    args = parser.parse_args(cargs)
    
    if args.example:
        ex = ex_names[args.example.lower()]
    else:
        # Randomly play one of the examples
        ex = random.choice(EXAMPLES)

    print('Example {}:'.format(ex.__name__))
    print('  ' + ex.__doc__)
    ex()

    return 0


if __name__ == "__main__":
    sys.exit(main('fixed_offline'))
    
        





