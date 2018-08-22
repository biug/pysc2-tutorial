from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random

class ZergAgent(base_agent.BaseAgent):
  def __init__(self):
    super(ZergAgent, self).__init__()
    
    self.attack_coordinates = None
    self.action_args = []
    self.actions = []
    self.overlord_eggs = 0

  def unit_type_is_selected(self, obs, unit_type):
    if (len(obs.observation.single_select) > 0 and
        obs.observation.single_select[0].unit_type == unit_type):
      return True
    
    if (len(obs.observation.multi_select) > 0 and
        obs.observation.multi_select[0].unit_type == unit_type):
      return True
    
    return False

  def get_units_by_type(self, obs, unit_type):
    return [unit for unit in obs.observation.feature_units
            if unit.unit_type == unit_type]

  def get_all_units_by_type(self, obs, unit_type):
    return [unit for unit in obs.observation.raw_units
            if unit.unit_type == unit_type]

  def get_all_complete_units_by_type(self, obs, unit_type):
    return [unit for unit in obs.observation.raw_units
            if unit.unit_type == unit_type and int(unit.build_progress) == 100]

  def get_unit_counts(self, obs, unit_type):
    for unit in obs.observation.unit_counts:
      if unit[0] == unit_type:
        return unit[1]
    return 0
  
  def can_do(self, obs, action):
    return action in obs.observation.available_actions

  def mining(self, *args):
    self.action_args = list(args)
    self.actions = [actions.FUNCTIONS.select_point, actions.FUNCTIONS.Smart_screen]

  def constructing(self, building, *args):
    self.action_args = list(args)
    self.actions = [actions.FUNCTIONS.select_point, building]

  def producing(self, unit, *args):
    self.action_args = list(args)
    self.actions = [actions.FUNCTIONS.select_point, unit]

  def attack(self, *args):
    self.action_args = list(args)
    self.actions = [actions.FUNCTIONS.select_army, actions.FUNCTIONS.Attack_minimap]

  def egg_type(self, obs):
    last_actions = obs.observation.last_actions
    if len(last_actions) > 0:
      last_action = last_actions[0]
      if last_action == actions.FUNCTIONS.Train_Overlord_quick:
        return units.Zerg.Overlord
    return 0

  def future_food(self, obs):
    hatcheries = len(self.get_all_units_by_type(obs, units.Zerg.Hatchery))
    lairs = len(self.get_all_units_by_type(obs, units.Zerg.Lair))
    hives = len(self.get_all_units_by_type(obs, units.Zerg.Hive))
    overseers = len(self.get_all_units_by_type(obs, units.Zerg.Overseer))
    if len(obs.observation.last_actions) > 0:
      if obs.observation.last_actions[0] == actions.FUNCTIONS.Train_Overlord_quick.id:
        self.overlord_eggs += 1
    overlords = 1 + self.overlord_eggs
    return 6 * (hatcheries + lairs + hives) + 8 * (overlords + overseers)

  def step(self, obs):
    super(ZergAgent, self).step(obs)
    
    if obs.first():
      player_y, player_x = (obs.observation.feature_minimap.player_relative ==
                            features.PlayerRelative.SELF).nonzero()
      xmean = player_x.mean()
      ymean = player_y.mean()
      
      if xmean <= 31 and ymean <= 31:
        self.attack_coordinates = (49, 49)
      else:
        self.attack_coordinates = (12, 16)

    zerglings = self.get_all_units_by_type(obs, units.Zerg.Zergling)
    if len(zerglings) >= 8:
      if self.unit_type_is_selected(obs, units.Zerg.Zergling):
        if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
          return actions.FUNCTIONS.Attack_minimap("now",
                                                  self.attack_coordinates)

      if self.can_do(obs, actions.FUNCTIONS.select_army.id):
        return actions.FUNCTIONS.select_army("select")

    if len(self.actions) == 0:
      mineral = obs.observation.player.minerals
      food = self.future_food(obs) - obs.observation.player.food_used
      spawning_pools = self.get_all_units_by_type(obs, units.Zerg.SpawningPool)
      completed_spawning_pools = self.get_all_complete_units_by_type(obs, units.Zerg.SpawningPool)
      larvae = self.get_units_by_type(obs, units.Zerg.Larva)
      if mineral > 200 and len(spawning_pools) == 0:
        self.constructing(actions.FUNCTIONS.Build_SpawningPool_screen, units.Zerg.Drone, (random.randint(0, 83), random.randint(0, 83)))
      if mineral > 150 and food < 10:
        self.producing(actions.FUNCTIONS.Train_Overlord_quick, units.Zerg.Larva, None)
      if mineral > 50 and food > 0 and len(completed_spawning_pools) > 0 and len(larvae) > 0:
        self.producing(actions.FUNCTIONS.Train_Zergling_quick, units.Zerg.Larva, None)

    if len(obs.observation.last_actions) > 0:
      print("last action = %s" % repr(obs.observation.last_actions[0]))
    if len(self.actions) > 0:
      action = self.actions.pop(0)
      arg = self.action_args.pop(0)
      if not self.can_do(obs, action.id):
        return actions.FUNCTIONS.no_op()
      if action.id == actions.FUNCTIONS.Attack_minimap.id:
        return action("now", self.attack_coordinates)
      elif action.id == actions.FUNCTIONS.select_point.id:
        units_ = self.get_units_by_type(obs, arg)
        if len(units_) > 0:
          unit_ = random.choice(units_)
          return action("select", (unit_.x, unit_.y))
      elif action.id == actions.FUNCTIONS.select_army.id:
        return action("select")
      elif action.id == actions.FUNCTIONS.Smart_screen.id:
        return action("now", arg)
      elif action.id == actions.FUNCTIONS.Build_SpawningPool_screen.id:
        return action("now", arg)
      elif action.id == actions.FUNCTIONS.Train_Overlord_quick.id:
        return action("now")
      elif action.id == actions.FUNCTIONS.Train_Zergling_quick.id:
        return action("now")
      else:
        pass
      return actions.FUNCTIONS.no_op()
    
    return actions.FUNCTIONS.no_op()

def main(unused_argv):
  agent = ZergAgent()
  try:
    while True:
      with sc2_env.SC2Env(
          map_name="AbyssalReef",
          players=[sc2_env.Agent(sc2_env.Race.zerg),
                   sc2_env.Bot(sc2_env.Race.terran,
                               sc2_env.Difficulty.very_easy)],
          agent_interface_format=features.AgentInterfaceFormat(
              feature_dimensions=features.Dimensions(screen=84, minimap=64),
              use_feature_units=True, use_raw_units=True, use_unit_counts=True),
          step_mul=4,
          game_steps_per_episode=0,
          visualize=True) as env:
          
        agent.setup(env.observation_spec(), env.action_spec())
        
        timesteps = env.reset()
        agent.reset()
        
        while True:
          step_actions = [agent.step(timesteps[0])]
          if timesteps[0].last():
            break
          timesteps = env.step(step_actions)
      
  except KeyboardInterrupt:
    pass
  
if __name__ == "__main__":
  app.run(main)
