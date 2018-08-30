from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random
class TerranAgent(base_agent.BaseAgent):
    def __init__(self):
        super(TerranAgent, self).__init__()

        self.attack_coordinates = None
        self.action_args = []
        self.actions = []
        self.overlord_eggs = 0
        self.unintMap={}
    ####### Agent Unit #######
    def unit_type_is_selected(self, obs, unit_type):
        if (len(obs.observation.single_select) > 0 an
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
    ####### Agent Action #######
    def can_do(self, obs, action):
        return action in obs.observation.available_actions

    def mining(self, *args):
        self.action_args = list(args)
        self.actions = [actions.FUNCTIONS.select_point, actions.FUNCTIONS.Smart_screen]

    def constructing(self, act_to_build,num, *args):
        tmpArgs=list(args);tmpAct=[actions.FUNCTIONS.select_point, act_to_build]
        for i in num:
            self.action_args.append(tmpArgs)
            self.action_args.append((random.randint(0, 83), random.randint(0, 83)))
            self.actions.append(tmpAct)

    def producing(self, act_to_unit,num, *args):
        tmpArgs=list(args);tmpAct=[actions.FUNCTIONS.select_point, act_to_unit]
        for i in num:
            self.action_args.append(tmpArgs)
            self.actions.append(tmpAct)

    def attack(self, *args):
        self.action_args = list(args)
        self.actions = [actions.FUNCTIONS.select_army, actions.FUNCTIONS.Attack_minimap]


    ####### Agent Strategy #######
    def step(self,obs):
        super(TerranAgent, self).step(obs)
        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative ==
                                    features.PlayerRelative.SELF).nonzero()
            xmean = player_x.mean()
            ymean = player_y.mean()

            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16)
        Reaper_All=self.get_all_units_by_type(obs, units.Terran.Reaper)
        '''
        set a number,then attack
        10 Supply Depot (and throughout)
        12 Barracks
        13 Refinery
        @ 100% BarracksOrbital Command
        Marine
        @ 100% MarineTech Lab
        17 Refinery
        @ 100 % Tech LabReaper
        Research Nitro Pack Upgrade
        20 Add two extra Barracks (3 total)
        ~35 Add two extra Barracks (5 total)
        ~50 Command Center
        '''
        if len(self.actions) == 0:
            mineral = obs.observation.player.minerals
            scv_All=self.get_all_units_by_type(obs, units.Terran.SCV)
            supply_depot_All=self.get_all_units_by_type(obs,units.Terran.SupplyDepot)
            barracks_All=self.get_all_units_by_type(obs,units.Terran.Barracks)
            refinery_All=self.get_all_units_by_type(obs,units.Terran.Refinery)
            reaper_All=self.get_all_units_by_type(obs,units.Terran.Reaper)
            orbitalCommand_All=self.get_all_units_by_type(obs,units.Terran.OrbitalCommand)
            if mineral>300:
                if self.can_do(obs,actions.FUNCTIONS.Morph_OrbitalCommand_quick.id)
                    return actions.FUNCTIONS.Morph_OrbitalCommand_quick("now")
            if mineral>200:
                if len(scv_All)<10:
                    self.producing(actions.FUNCTIONS.Train_SCV_quick,units.Terran.SCV,None)
                elif len(scv_All)==50:
                    self.constructing(action.FUNCTIONS.Build_CommandCenter_screen,1,units.Terran.SCV)
                elif len(scv_All)==35:
                    self.constructing(action.FUNCTIONS.Build_Barracks_screen,2,units.Terran.SCV)
                elif len(scv_All)==20:
                    self.constructing(action.FUNCTIONS.Build_Barracks_screen,2,units.Terran.SCV)
                elif len(scv_All)==17:
                    self.constructing(action.FUNCTIONS.Build_Refinery_screen,1,units.Terran.SCV)
                elif len(scv_All)==13:
                    self.constructing(action.FUNCTIONS.Build_Refinery_screen,1,units.Terran.SCV)
                elif len(scv_All)>=12:
                    self.constructing(action.FUNCTIONS.Build_Barracks_screen,1,units.Terran.SCV)
                elif len(scv_All)>=10:
                    self.constructing(action.FUNCTIONS.Build_SupplyDepot_screen,1,units.Terran.SCV)
                if len(orbitalCommand_All)>0 and len(barracks_All)>0:
                    self.producing(actions.FUNCTIONS.Train_Zergling_quick, 1,units.Zerg.Larva)
            if mineral<150:
                self.mining(units.Terran.SCV)
            if len(reaper_All)>0:
                self.attack()


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
            elif action.id == actions.FUNCTIONS.Train_SCV_quick.id:
                return action("now")
            elif action.id == actions.FUNCTIONS.Train_Zergling_quick.id:
                return action("now")
            else:
                pass
            return actions.FUNCTIONS.no_op()
        return actions.FUNCTIONS.no_op()

def main(unused_argv):
  agent = TerranAgent()
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