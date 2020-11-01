from ge_modelingToolkit2 import *
import os
import glob
#from ModelToolkit2 import *

# os has operating system aware functions (provided by Derek)
# https://urldefense.com/v3/__https://www.geeksforgeeks.org/python-os-mkdir-method/__;!!PhOWcWs!nUjA_KItpfwobIwE_tQ_ogPwde2wU4O0EeqeEL0s7bv6kOvIMGkiWbnCzzMVIh3blQ$ 

# Time stamp to identify the simulation, and the directories where the data is stored
# Called in constructor of Partioning graph (used to be called in simulate() method
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#################################################################################
#####   Begin setting up model variables  #######################################
#################################################################################

# Global dictionary to store parameters (different for each study)
glob_dict = {}

gamma = 0.1# The expected time to recovery will be 1/gamma (days)
tau = 0.2#  The expected time to transmission by an ge will be 1/(weight*Tau) (days)

glob_dict['gamma'] = gamma
glob_dict['tau'] = tau

# Whether or not to save output files  <<<<<<<<<<<<<< Set to save directory
save_output = False
save_output = True
print("save_output= ", save_output)

glob_dict['save_output'] = save_output

#construct partitioner
enumerator = {i:i//5 for i in range(75)}
enumerator.update({i:15 for i in range(75,100)})
names = ["{}:{}".format(5 * i, 5 * (i + 1)) for i in range(15)]
partitioner = Partitioner('age', enumerator, names)

# denotes the fraction of people using masks
prevention_adoptions = {"household": {"masking": 0, "distancing": 0},
                          "school": {"masking": 0, "distancing": 0},
                          "workplace": {"masking": 0, "distancing": 0}}

glob_dict['enumerator'] = enumerator
glob_dict['prevention_adoptions'] = prevention_adoptions

#initialize populaceGraph
slim = False
slim = True
print("Running with slim= %d" % slim)

glob_dict['slim'] = slim

#construct netBuilder
#en_type_scalars is used to scale each weight, depending on the type of environment the edge will be placed in
env_type_scalars = {"household": 1, "school": 1.0, "workplace": 1.0}
#this dict is used to decide who is masking, and who is distancing
# 0.7 would represent the fraction of the population masking

# A value of 0 means that masks are not effective at all
# A value of 1 means that a mask wearer can neither infect or be infected. 
prevention_efficacies = {"masking": 0.0, "distancing": 0.0}  # I should get real I curves. Not extinction. I do. 
prevention_efficacies = {"masking": 0.3, "distancing": 0.3}  # I should get real I curves. Not extinction. I do. 

glob_dict['env_type_scalars'] = env_type_scalars
glob_dict['prevention_efficacies'] = prevention_efficacies

#################################################################################
#####   End setting up model variables  #######################################
#################################################################################

if save_output:
    dstdirname = os.path.join(".", "ge_simResults", timestamp, "src")
    os.makedirs(dstdirname)
    # Independent of OS
    os.system("cp *.py %s" % dstdirname)  # not OS independent
    #copyfile ('ge1_modelToolkit.py',os.path.join(dstdirname,'ge1_modelToolkit.py'))

model = PopulaceGraph(partitioner, prevention_adoptions, slim=slim, timestamp=timestamp)
model.resetVaccinated_Infected() # reset to default state (for safety)
mask_types = [0.25, 0.5, 0.25]  # Must sum to 1
model.differentiateMasks(mask_types)

glob_dict['mask_types'] = mask_types

# Reduction parameters
# Mask reduction is given by Normal(avg, cv*avg)
#avg_dict={"distancing": 0.4, "mask_eff": 0.4, "contact": 0.0}
# cv is the std / avg. The avg are the prevention_efficacies
cv_dict={"distancing": 0.2, "contact": 0.3, "masking": 0.4}
netBuilder = NetBuilder(env_type_scalars, prevention_efficacies, cv_dict=cv_dict)

vacc_perc = 0.0
infect_perc = 0.001
glob_dict['vacc_perc'] = vacc_perc
glob_dict['infect_perc'] = infect_perc

model.vaccinatePopulace(perc=vacc_perc)
model.infectPopulace(perc=infect_perc)
model.buildNetworks(netBuilder)
model.simulate(gamma, tau, title = "cv is None")
cv_vals = np.linspace(0., 1., 6) # Coefficient of variation (stdev/mean)
cv_vals = np.linspace(0.1, 1., 5) # Coefficient of variation (stdev/mean)
cv_vals = np.linspace(0., 0.6, 4) # Coefficient of variation (stdev/mean)

glob_dict['comments'] = """
Perform 5 simulations. 
Each simulation considers 10 values of the coefficient of variation (cv) [0-1]. 
There are no vaccinations. 
The simulations consider separately the effect of masks, contact matrices, and weights (social distancing). 
The graph structure is the same across all simulations, which is not quite correct when the contact 
  matrices are varied. 
In every simulation, a different set of people are infected or vaccinated (assuming that vacc_perc > 0)
What are prevention_efficacies? 
What are prevention_adoptions? 
What are env_type_scalars?
How are masked types used in the code? 
"""

"""
  for avg_efficacy in [0., 0.25, 0.5, 0.75]:
     for cv_key, cv_val in netBuilder.cv_dict.items():   
       for adopt in [0., 0.5, 1.]:  # masks and social distancing in schools and workplaes
         for val in cv_vals:
"""

def runGauntlet(count):
  glob_dict['simulation_index'] = count
  # All global variables are accessible

  for avg_efficacy in [0., 0.25, 0.5, 0.75]:
     # I should get real I curves. Not extinction. I do. 
     prevention_efficacies = {"masking": avg_efficacy, "distancing": avg_efficacy} 
     glob_dict['prevention_efficacies'] = prevention_efficacies

     for cv_key in netBuilder.cv_dict.keys():   
       if cv_key != 'masking': continue    ### FOR TESTING

       for adopt in [0., 0.5, 1.]:  # masks and social distancing in schools and workplaes
         prevention_adoptions["school"]     = {"masking": %f, "distancing": %f}
         prevention_adoptions["workplace"]  = {"masking": %f, "distancing": %f} 
         glob_dict['prevention_adoptions'] = prevention_adoptions

         for cv_val in cv_vals:
            model.resetVaccinated_Infected() # reset to default state (for safety)
            netBuilder.cv_dict[cv_key] = cv_val
            netBuilder.setModel(model)  # must occur before reweight
            pe = prevention_efficacies
            # Following two lines must occur before reweight
            # a,b of beta distribution hardcoded to 10,10
            # If nobody is wearing masks, this should have no effect
            model.setupMaskReduction(pe['masking'], cv_dict['masking'])
            model.setupSocialDistanceReduction(pe['distancing'], cv_dict['distancing'])
            # netBuilder has access to model, and model has access to netBuilder. Dangerous.
            model.reweight(netBuilder, prevention_adoptions)
            avg_key = cv_key
            avg_val = avg_dict[avg_key]
            model.infectPopulace(perc=infect_perc)
            model.vaccinatePopulace(perc=vacc_perc)
            title = "{} cv = {}".format(cv_key, cv_val)
    
            # variables to store 
            glob_dict['vacc_perc'] = vacc_perc
            glob_dict['infect_perc'] = infect_perc
            glob_dict['cv_key'] = cv_key
            glob_dict['cv_val'] = val
            glob_dict['avg_key'] = avg_key
            glob_dict['avg_val'] = avg_val

            model.simulate(gamma, tau, title=title, global_dict=glob_dict)

    netBuilder.cv_dict[cv_key] = cv_val
    print(model.getPeakPrevalences())


for count in range(3):
    print("--------- SIMULATION %d ----------------" % count)
    runGauntlet(count)

