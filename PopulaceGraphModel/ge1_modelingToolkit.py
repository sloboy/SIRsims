import random
from os import mkdir
import EoN
import networkx as nx
import itertools
import pickle
from datetime import datetime
import time
import matplotlib.pyplot as plt
import numpy as np
import math
from scipy.interpolate import interp1d



#----------------------------------------------------------------------
class Partitioner:
    """
    Objects of this class can be used to split a list of people into disjoint sets
    """

    def __init__(self, attribute, enumerator, labels=None):
        """
        :param attribute: string
        The attribute by which to partition must match one of the attributes in 'populace'

        :param enumerator: dict
        The enumerator should map each possible values for the given attribute to the index of a partition set

        :param labels: list
        A list of names for plotting with partitioned sets
        """

        self.enumerator = enumerator
        self.attribute = attribute
        self.names = labels
        self.attribute_values = dict.fromkeys(set(enumerator.values()))
        self.num_sets = (len(np.unique(list(enumerator.values()))))

    def partitionGroup(self, members, populace):
        """
        :param members: list
        An list of indexes for the peaple to partition
        :param populace:
        A dict associating people to a list of their attributes is required for applying the enumerator

        :return: dict

        """
        partitioned_members = {i: [] for i in range(self.num_sets)}
        for person in members:
            #determine the number for which group the person belongs in, depending on their attribute
            group = self.enumerator[populace[person][self.attribute]]
            #add person to  to dict in group
            partitioned_members[group].append(person)
        return partitioned_members

#----------------------------------------------------------------------
#was a thought, but I never used it
class memberedPartition:
    def __init__(self, members, populace, enumerator, attribute, names = None):
        super.__init__()
        self.partitioned_members = super.partitionGroup(members, populace)

#----------------------------------------------------------------------
class Environment:
    """
    Objects to the carry details of every home, workplace, and school
    Each environment is an individual school, workplace, or home 
    """
    def __init__(self, index, members, type, preventions = None):
        """
        :param index: int
        an identifier
        :param members: list
        a list of people who attend the environment
        :param type: string
        either 'household', 'school', or 'workplace'
        :param preventions: dict
        keys should be 'household', 'school', or 'workplace'. Each should map to another dict,
        with keys for 'masking', and 'distancing', which should map to an int in range[0:1] that represents
            #environment.drawSelfDistance(self.env_edges[environment.index])  # Is this needed?
        the prevelance of the prevention strategy in the environment
        """

        self.index = index
        self.members = members
        self.type = type
        self.preventions = None
        self.population = len(members)
       # self.distancing = distancing

    #def drawSelfDistance(self, env_edges):
    def drawSelfDistance(self):
        '''
        In each environment, I want to choose a fraction of edges that are social distancing
        and for which there will be a reduction due to social distancing. 
        How to do that? 

        :param type: list of edge pairs [(v1,v2),(v3,v4),...] of environment index
        List of edges in the graph of environment with index env_index
        :return: void
        '''

        # I should collect all the edges of the environment, and assign 1 or zero regarding whether there 
        # is social distancing. 

        num_edges = len(self.edges)
        #print("drawSelfDistance, num_edges= ", num_edges)

        if self.preventions == None:
            num_social = 0
        else:
            num_social = int(num_edges * self.preventions["distancing"])

        distancing_status = [1] * num_social + [0] * (num_edges - num_social)
        random.shuffle(distancing_status)
        # class Environment
        self.distancing_status = dict(zip(self.edges, distancing_status))
        #print("self= ", self, ", distancing_status= ", self.distancing_status)

    def drawMasks(self):
        '''
        creates a dict linking each member of the environment with a mask
        :return: void
        '''

        # assign masks
        if self.preventions == None:
            num_masks = 0
        else:
            num_masks = int(self.population * self.preventions["masking"])

        mask_status = [1] * num_masks + [0] * (self.population - num_masks)
        random.shuffle(mask_status)
        # class Environment
        self.mask_status = dict(zip(self.members, mask_status))


#----------------------------------------------------------------------
class PartitionedEnvironment(Environment):
    """
    being partitioned, it also holds a contact matrix and a partitioner
    """

    def __init__(self, index, members, type, populace, contact_matrix, partitioner, preventions = None):
        """
        :param index: int
        an identifier
        :param members: list
        a list of people who attend the environment
        :param type: string
        either 'household', 'school', or 'workplace'
        :param preventions: dict
        keys should be 'household', 'school', or 'workplace'. Each should map to another dict,
        with keys for 'masking', and 'distancing', which should map to an int in range[0:1] that represents
        the prevelance of the prevention strategy in the environment
        :param populace: dict
        :param contact_matrix: 2d array
        :param partitioner: Partitioner
        for creating a partition
        """
        super().__init__(index,members, type, preventions)
        self.partitioner = partitioner
        self.contact_matrix = contact_matrix
        self.id_to_partition = dict.fromkeys(members)

        #self.total_matrix_contact = contact_matrix.sum()
        self.partition = partitioner.partitionGroup(members, populace)
        for set in self.partition:
            for person in self.partition[set]:
                self.id_to_partition[person] = (set)

    def returnReciprocatedCM(self):
        '''
        :return: this function  averages to returs a modified version of the contact matrix where
        CM_[i,j]*N[i]= CM_[j,i]*N[j]
        '''

        cm = self.contact_matrix
        dim = cm.shape
        rm = np.zeros(dim)
        set_sizes = [len(self.partition[i]) for i in self.partition]

        for i in range(dim[0]):
            for j in range(dim[1]):
                if set_sizes[i] != 0:
                    rm[i,j] = (cm[i,j]*set_sizes[i]+cm[j,i]*set_sizes[j])/(2*set_sizes[i])
        return rm
        def __str__(self):
            print("{}population: {}".type)


#----------------------------------------------------------------------
class TransmissionWeighter:
    """
    a transmission weighter object carries all parameters and functions that involve calculating weight for edges in the graph
    """
    def __init__(self, env_type_scalars, prevention_reductions):#, loc_masking):
        """                        
        :param env_type_scalars: dict
        must map to a scalar for each environment type, for scaling weights

        :param prevention_reductions: dict
        must map prevention names, currently either 'masking' or 'distancing' to scalars
        """

        self.prevention_reductions = prevention_reductions
        self.env_scalars           = env_type_scalars
        self.global_weight         = 1

        #self.loc_masking = loc_masking
        #self.age_scalars = age_scalars

    def setEnvScalars(self, env_scalars):
        self.env_scalars = env_scalars

    def setPreventions(self, preventions):
        self.preventions = preventions

    def setPreventionReductions(self, prevention_reductions):
        self.prevention_reductions = prevention_reductions

    def getWeight(self, personA, personB, environment):
        start_time = time.time()
        """
        In class TransmissionWeighter
        Uses the environments type and preventions to deternmine weight
        :param personA: int
        currently unused
        :param personB: int
        currently unused
        :param environment: environment
         the shared environment of two nodes for the weight
        :return:
        """

        """
        This function is called for a single person 
        self.env_scalars = default_env_scalars   = {"school": 0.3, "workplace": 0.3, "household": 1}
        1. If no preventions, weight = w_global * 0.3 (global_weight = 1. When is it not 1?)
        2. If there are preventions, there is randomness. Let r1 and r2 be two random numbers
            p1 = 
        """

        #print(personA, personB)  # 30 29
        #print(environment.distancing_status)
        #wv = environment.distancing_status[(personA, personB)]

        weight = self.global_weight * self.env_scalars[environment.type]
        #including the effect of masks
        if environment.preventions != None:
            # I like this: a mask_status per person. We also need mask_reduction per person
            n_masks = (environment.mask_status[personA] + environment.mask_status[personB])
            # self.prevnetion_reductions becomes a string!!! HOW!!!
            # If two people do not wear masks, the weight is not affected
            weight = weight*(1.-self.prevention_reductions["masking"])**n_masks
            #weight = weight*(1-(1-self.prevention_reductions["distancing"]) * environment.preventions["distancing"])
            # Fixed by Gordon
            weight = weight*(1-self.prevention_reductions["distancing"])

        return weight


#-----------------------------------------------------
class PopulaceGraph:
    """
    A list of people, environments, and functions need to track a weighted graph 
        to represent contacts between members of the populace
    """

    #-----------------
    def setup_households(self):
        households = self.pops_by_category["sp_hh_id"]

        for index in households:
            houseObject              = Environment(index, households[index], "household", 0)
            self.environments[index] = (houseObject)

    #-----------------
    def setup_workplaces(self, partition):
        workplaces = self.pops_by_category["work_id"]
        with open("../ContactMatrices/Leon/ContactMatrixWorkplaces.pkl", 'rb') as file:
            work_matrices = pickle.load(file)

        for index in workplaces:
            if index == None: continue
            workplace = PartitionedEnvironment(index, workplaces[index], "workplace", 
                                               self.populace, work_matrices[index], partition)
            self.environments[index] = (workplace)

    #-----------------
    def setup_schools(self, partition):
        schools = self.pops_by_category["school_id"]
        with open("../ContactMatrices/Leon/ContactMatrixSchools.pkl", 'rb') as file:
            school_matrices = pickle.load(file)
        for index in schools:
            if index == None: continue
            school = PartitionedEnvironment(index, schools[index], "school", self.populace, 
                                            school_matrices[index], partition )
            self.environments[index] = (school)
           
    #----------------
    def printEnvironments(self):
        keys = list(self.environments.keys())
        envs = set()
        for k in keys:
            envs.add(self.environments[k].type)

        # Environment type can be "household", "workplace", "school"
        #print("envs= ", envs)
        # attributers of environments[keys[1]]: "index', 'members', 'population', 'preventions', 'type'"
        #print(dir(self.environments[keys[1]]))
        for k in range(25000,25200):
            print("-----------------")
            print(self.environments[keys[k]].members)  # list of one element [12]. Meaning? 
            print(self.environments[keys[k]].population)  # 1  (nb of members)
            print(self.environments[keys[k]].preventions)  # None (or a list?
            print(self.environments[keys[k]].type)  # list of one element [12]. Meaning? 

    #-------------------------------
    def __init__(self, partition, timestamp, graph = None, populace = None, 
                 attributes = ['sp_hh_id', 'work_id', 'school_id', 'race', 'age'], slim = False):
        """        
        :param partition: Partitioner
        needed to build schools and workplaces into partitioned environments         
        :param timestamp
        Time stamp that corresponds to a collection of simulations
        :param graph: nx.Graph 
         a weighted graph to represent contact and hence chances of infection between people
        :param populace: dict
        maps a persons index to a list of their attributes
        :param pops_by_category:         
        :param attributes:
        names for the characteristics each person has
        :param slim: bool
        will filter 90% of people from the object to speed debugging
        """

        # Graphs are not yet set up in the constructor

        # Timestamp call only once per partitioning
        self.stamp = timestamp
        #self.stamp = datetime.now().strftime("%m_%d_%H_%M_%S")

        self.isBuilt = False
        #self.record = Record()
        self.sims = []
        self.contactMatrix = None
        self.total_weight = 0
        self.record = Record()
        self.total_edges = 0
        self.total_weight = 0
        self.environments_added = 0
        #self.edge_envs = {}  # keep track of the environment associated with each edge

        # What is this for? 
        if partition != None:
            self.hasPartition = True
        else:
            self.hasPartition = False

        if graph == None:
            self.graph = nx.Graph()

        #load populace from file if necessary
        if populace == None:
        # for loading people objects from file
            with open("people_list_serialized.pkl", 'rb') as file:
                x = pickle.load(file)

            # return represented by dict of dicts
        #renames = {"sp_hh_id": "household", "work_id": "work", "school_id": "school"} maybe later...

        if slim == True:
            print("WARNING! slim = True, 90% of people are filtered out")
            self.populace = {}
            for key in x:
                if random.random()>0.9:
                    self.populace[key] = (vars(x[key]))
        else:
            self.populace = ({key: (vars(x[key])) for key in x})  # .transpose()
        self.population = len(self.populace)
        keys = list(self.populace.keys())

        # print(self.populace[keys[1]])
        # {'sp_id': 164082714, 'sp_hh_id': 58565423, 'age': 64, 'sex': 0, 'race': 1, 'relate': 0, 
        #   'school_id': None, 'work_id': 505089288, 'comorbidities': {'Hypertension': False, 
        #   'Obesity': False, 'Lung disease': False, 'Diabetes': False, 'Heart disease': False, 
        #   'MaskUsage': False, 'Other': False}}

        # for sorting people into categories
        # takes a dict of dicts to rep resent populace and returns a list of dicts of lists to represent groups of people with the same
        # attributes

        # pops_by_category: for each category, a dictionary
        # attributes:  ['sp_hh_id', 'work_id', 'school_id', 'race', 'age']

        #print("attributes: ", attributes)
        pops_by_category = {category: {} for category in attributes}

        for person in self.populace:
            for category in attributes:
                try:
                    # Append to list of persons
                    # I am not sure of the meaning of self.populace[person][category]: it is a key
                    pops_by_category[category][self.populace[person][category]].append(person)
                except:
                    # Initialize dictionary value to a list
                    pops_by_category[category][self.populace[person][category]] = [person]

        #print(list(pops_by_category["age"].keys())); 
        #print(list(pops_by_category["race"].keys())); 
        #print(list(pops_by_category["school_id"].keys())); quit()

        pops_by_category["age_groups"] = {}
        #print("keys: ", pops_by_category["age"])
        #print("keys: ", list(pops_by_category["age"]))


        for bracket in range(0,20):
            #print(bracket)
            pops_by_category["age_groups"][bracket] = []
            for i in range(0,5):
                try:   # easier than conditionals. I divided all ages into groups of 5
                    pops_by_category["age_groups"][bracket].extend(pops_by_category["age"][5*bracket+i])
                except:
                    break
            #print("bracket: %d, size: %d" % (bracket, len(pops_by_category["age_groups"][bracket])))

        self.pops_by_category = pops_by_category
        #print("pops_by_category['race']", pops_by_category['race'])  # just a list of numbers

        # env_name_alternate = {"household": "sp_hh_id", "work": "work_id", "school": "school_id"} outdated
        #adding households to environment list
        self.environments = {}
        self.setup_households()
        self.setup_workplaces(partition)
        self.setup_schools(partition)

    #-------------------------------
    def zeroWeights(self, env):
        # GE: How to turn off a school without reconstructing the school graph? 
        # NOT USED
        # Run through the edges and set the weight to zero
        start_time = time.time()
        G = self.graph
        for e in G.edges():
            environment = self.environments[self.graph.adj[e[0]][e[1]]['environment']]
            print("env, envi= ", env, environment.type)
            if env == environment.type:
                self.graph.adj[e[0]][e[1]]['transmission_weight'] = 0
        print("zeroWeights[%s]: %f sec" % (env, time.time() - start_time))
    #---------------------------------
    def printWeights(self):
        G = self.graph
        for e in G.edges():
            w = G[e[0]][e[1]]['transmission_weight']
            env = self.environments[G[e[0]][e[1]]['environment']]
            print("weight(e): ", e, " => ", w, env.type)
    #---------------------------------
    def envEdges(self):
        # Added by Gordon Erlebacher, class PopulaceGraph
        # Construct a dictionary for each environment, of its edges. This will be used
        # to assign edge properties per environment. 
        env_edges= {}
        for ix in self.environments:
            env_edges[ix] = []   # list of edges

        for edge in self.graph.edges():
            #get environment
            env = self.environments[self.graph.adj[edge[0]][edge[1]]['environment']]
            # env is an environment object
            env_edges[env.index].append((edge[0], edge[1]))  ### ERROR

        # attach edge list to the environment
        for ix in self.environments:
            env = self.environments[ix]
            env.edges = env_edges[ix]

    #------------------------------------
    def build(self, weighter, preventions, env_degrees, alg = None):
        """
        constructs a graph for the objects populace
        this model is built to use 
        :param weighter: TransmissionWeighter
        will be used to determine the graphs weights
        :param preventions: dict
        :param env_degrees:
        :param alg:
        :return:
        """

        start_time = time.time()
        #None is default so old scripts can still run. self not defined in signature
        if alg == None:
            alg = self.clusterPartitionedStrogatz

        self.trans_weighter = weighter
        self.preventions = preventions
        self.environment_degrees = env_degrees

        # For Debugging and record keeping
        #self.record.print('\n')
        #self.record.print("building populace into graphs with the {} clustering algorithm".format(clusteringAlg.__name__))
        #start = time.time()

        # Create empty graph
        self.graph = nx.Graph()

        #self.printEnvironments()  # for debugging and understanding


        # loop through all schools, workplaces, households (3 environments)
        # Keeping prevents for each environment separately, allows different schools to have 
        # different preventions
        #for env in self.environments:
            #print("env= ", env) # integers
        for index in self.environments:
            #print("indexx= ", index)
            env = self.environments[index] # environment
            #print("env= ", env)
            self.addEnvironment(env, alg)
            # GE: WHY ARE THESE LINES NO LONGER REQUIRED?
            #env.preventions = preventions[env.type]  # how are preventions used in the model? 
            #self.constructGraphFromCM(env, alg)

        # Graphs are done


        self.isBuilt = True
        finish_time = time.time()
        print("build took {} seconds to finish".format(finish_time-start_time))

        # we are in class PopulaceGraph
        # Create edge list for each environment keyed by the environment index
        # It would be better if each environment had a set of edges
        
        # Attach list of edges to each environment
        self.envEdges()

    #----------------------------------
    def reweight(self, weighter, preventions, alg = None):
        """
        In class PopulaceGraph
        Recomputes the weights on each edge using with, presumably new, arguments

        :param weighter:
        :param preventions:
        :param env_degrees:
        :param alg:
        :return:
        """
        start_time          = time.time()
        self.trans_weighter = weighter
        self.preventions    = preventions

        #update new prevention strategies on each environment
        for index in self.environments:
            environment = self.environments[index]
            environment.drawMasks()
            #environment.drawSelfDistance(self.env_edges[environment.index])
            environment.drawSelfDistance()
            # GE: WHY IS THIS NOT USED in ModelToolkit.py?
            environment.preventions = preventions[environment.type]

        #pick and replace weights for each environment
        # There is no easy way to collect the edges for a given environment unless one does 
        # a pass on the graph once it has been created. I will do that. 

        for edge in self.graph.edges():
            #get environment
            environment = self.environments[self.graph.adj[edge[0]][edge[1]]['environment']]
            new_weight = weighter.getWeight(edge[0], edge[1], environment)
            self.graph.adj[edge[0]][edge[1]]['transmission_weight'] = new_weight
        finish_time = time.time()
        print("graph has been reweighted in {} seconds".format(finish_time-start_time))

    #------------------------------------------[
    #-------------------
    def addEdge(self, nodeA, nodeB, environment, weight_scalar = 1):
        '''
        fThis helper function  not only makes it easier to track
        variables like total weight and edges for the whole graph, each time
        a graph is added, it can be useful for debugging
        :param nodeA: int
         The node for one side of the edge
        :param nodeB: int
        The noden for the other side
        :param environment: Environment
         needed to get weight
        :param weight_scalar: double
        may be used if one wants to scale the edgesweight bigger/smaller than the trasmission_weighter would regurarly predict

        '''
        weight = self.trans_weighter.getWeight(nodeA, nodeB, environment)*weight_scalar
        self.total_weight += weight
        self.total_edges += 1
        self.graph.add_edge(nodeA, nodeB, transmission_weight = weight, environment = environment.index)
        #print("nodes: ", nodeA, nodeB)
        #self.edge_envs[(nodeA, nodeB)] = environment

    #merge environments, written for plotting and exploration
    #-------------------
    def returnMultiEnvironment(self, env_indexes, partition):
        members = []
        for index in env_indexes:
            members.extend(self.environments[index].members)
        return PartitionedEnvironment(None, members, 'multiEnvironment', self.populace, None, partition)

    #-------------------
    def clusterDense(self, environment, subgroup = None, weight_scalar = 1):
        """
        This function will add every edge possible for the group. Thats n*(n-1)/2 edges

        :param environment: Environment
        The environment to add edges to
        :param subgroup: list
        may be used if one intends to only add edgse for members of the environments subgroup
        :param weight_scalar: double
         may be used if one wants the weights scaled larger/smaller than normal
        """
        """
                      
        :param environment:
        :param subgroup:
        :param weight_scalar:
        :return:
        """
        if subgroup == None:
            members = environment.members
        else:
            members = subgroup
        type = environment.type
        member_count = len(members)
        #memberWeightScalar = np.sqrt(memberCount)
        for i in range(member_count):
            for j in range(i):
                self.addEdge(members[i], members[j], environment, weight_scalar)


    #-------------------
    def constructGraphFromCM(self, environment, alg):
        """
        This function iterates over the models list of environments and networks them one by one
        by calling clusterDense. Every edge in everyhousehold will be added to the model. However,
        the edges for the other, partitioned environments, alg, which must a function, must
        be able to determine how to build the network, and along with the environment, the alg will also be passed a value
        which specify what avg node degree it should produce

        :param environment: Environment
        the environment that needs to be added
        :param alg: function
        The algorithm to be used for networking the PartitionedEnvironments
        :return:
        """

        if environment.type == 'household':
            self.clusterDense(environment)
        else:
            # the graph is computed according to contact matrix of environment
            # self.clusterPartitionedStrogatz(environment, self.environment_degrees[environment.type])
            alg(environment, self.environment_degrees[environment.type])

    #---------------------
    def addEnvironment(self, environment, alg):
        """
        THE DESCRIPTION DOES NOT SEEM RIGHT. THERE IS NO ITERATION

        Class PopulaceGraph
        This function iterates over the models list of environment and networks them one by one
        by calling clusterDense, every edge in every household will be added to the model. However,
        the edges for the other, partitioned environments, alg, which must a function, must
        be able to determine how to build he network, and along with the environment, the alg will also be passed a value
        which specify what avg node degree it should produce

        :param environment: Environment
        the environment that needs to be added
        :param alg: function
        The algorithm to be used for networking the PartitionedEnvironments
        :return:
        """

        if environment.type == 'household':
            self.clusterDense(environment)
        else:
            # the graph is computed according to contact matrix of environment
            # self.clusterPartitionedStrogatz(environment, self.environment_degrees[environment.type])
            preventions = self.preventions[environment.type]
            environment.preventions = preventions
            environment.drawMasks()
            alg(environment, self.environment_degrees[environment.type])


    #-------------------
    def clusterStrogatz(self, environment,  num_edges, weight_scalar = 1, subgroup = None, rewire_p = 0.2):
        """
         clusterStrogatz

         :param environment:  environment which needs to be added
         :param num_edges:
         :param weight_scalar:
         :param subgroup:
         :param rewire_p:
         :return:
        """

        if subgroup == None:
            members = environment.members
        else:
            members = subgroup

        #unpack params
        # if only one person, don't bother
        member_count = len(members)
        if member_count == 1:
            return

        local_k = math.floor(num_edges/member_count)*2
        remainder = num_edges - local_k*member_count/2
        if local_k >= member_count:
            self.clusterDense(environment, weight_scalar = weight_scalar)
            return

        for i in range(member_count):
            nodeA = members[i]
            for j in range(1, local_k // 2+1):
                rewireRoll = random.uniform(0, 1)
                if rewireRoll < rewire_p:
                    nodeB = members[(i + random.choice(range(member_count - 1))) % member_count]
                else:
                    nodeB = members[(i + j) % member_count]
                self.addEdge(nodeA, nodeB, environment, weight_scalar)
        edgeList = self.genRandEdgeList(members, members, remainder)
        for edge in edgeList: self.addEdge(edge[0], edge[1], environment)


    #-------------------
    def clusterBipartite(self, environment, members_A, members_B, edge_count, weight_scalar = 1, p_random = 0.2):
        #reorder groups by size
        A = min(members_A, members_B, key = len)
        if A == members_A:
            B = members_B
        else:
            B = members_A

        size_A = len(A)
        size_B = len(B)

        if len(members_A)*len(members_B) < edge_count:
            print("warning, not enough possible edges for cluterBipartite")

        #distance between edge groups
        separation = int(math.ceil(size_B/size_A))

        #size of edge groups and remaining edges
        k = edge_count//size_A
        remainder = edge_count%size_A
        p_random = max(0, p_random - remainder/edge_count)

        for i in range(size_A):
            begin_B_edges = (i * separation - k // 2)%size_B

            for j in range(k):
                if random.random()>p_random:
                    B_side = (begin_B_edges +j)%size_B
                    self.addEdge(A[i], B[B_side], environment, weight_scalar)
                else:
                    remainder +=1


        eList = self.genRandEdgeList(members_A, members_B, remainder)
        for edge in eList: self.addEdge(edge[0], edge[1],environment, weight_scalar)


    #for clusterRandGraph
    #-------------------
    def genRandEdgeList(self, setA, setB, n_edges):
        if n_edges == 0:
            return []
        n_edges = int(n_edges)
        n_A = len(setA)
        n_B = len(setB)
        if setA == setB:
            pos_edges = n_A*(n_A-1)/2
            same_sets = True
        else:
            pos_edges = n_A*n_B
            same_sets = False

#        p_duplicate = n_edges/pos_edges
#        if p_duplicate< 0.001:
#            list = [(random.choice(setA),random.choice(setB)) for i in range(n_edges)]
#        else:
        edge_dict = {}
        while len(edge_dict)<n_edges:
            A, B = random.choice(setA), random.choice(setB)
            if A>B: edge_dict[A,B] = 1
            elif B>A: edge_dict[A,B] = 1
        list = edge_dict.keys()
        return list

    #-------------------
    def clusterRandGraph(self, environment, avg_degree):
        print("**** Enter clusterRandGraph, created by G. Erlebacher")
        # Create graph according to makeGraph, developed by G. Erlebacher (in Julia)
        #G = Gordon()
        #G.makeGraph(N, index_range, cmm)
        # len(p_sets) = 16 age categories, dictionaries
        p_sets = environment.partition
        population = environment.population
        CM = environment.returnReciprocatedCM()
        print("CM= ", CM)  # single CM matrix

        assert isinstance(environment, PartitionedEnvironment), "must be a partitioned environment"
        #determine total edges needed for entire network. There are two connections per edge)
        #a list of the number of people in each partition set
        p_sizes = [len(p_sets[i]) for i in p_sets]
        num_sets = len(p_sets) # nb age bins
        #get total contact, keeping in mind the contact matrix elements are divided by num people in group
        total_contact = 0
        #for i in range(len(CM)):
        for i,row in enumerate(CM):
            #add total contacts for everyone in set i
            total_contact +=sum(np.array(row))*p_sizes[i]
        if avg_degree == None:
            total_edges = math.floor(total_contact) / 2
        else:
            total_edges = math.floor(avg_degree*population/ 2)

        #for every entry in the contact matrix
        edge_list = []
        for i,row in enumerate(CM):
            for j, cm in enumerate(row):
                #decide how many edges it implies
                if i == j:
                    n_edges = math.floor(cm/(total_contact*2))
                else:
                    n_edges = math.floor(cm/total_contact)
                if n_edges == 0:
                    continue
                edge_list = self.genRandEdgeList(p_sets[i], p_sets[j], n_edges)
                for edge in edge_list: self.addEdge(edge[0],edge[1],environment)


    #-------------------
    def clusterPartitionedStrogatz(self, environment, avg_degree = None):
        self.clusterWithMatrix( environment, avg_degree, 'strogatz')

    #-------------------
    def clusterPartitionedRandom(self, environment, avg_degree = None):
        '''
        This calls upon clusterWithMatrix, with topology set as 'random'

        :param environment: partionedEnvironment
         the environment to add edges for
        :param avg_degree:  int or double
        edges/(2*population), or implied by the contact matrix if argument is "None"
        '''
        self.clusterWithMatrix(environment, avg_degree, 'random')

    #-------------------
    def clusterWithMatrix(self, environment, avg_degree, topology):
        """
        cluster With Matrix takes a partitioned environment, and reciprocates its contact matrix so it
        can be used to determine the number of edges needed between each pair of partition sets to match as closely as possible.
        In cases where the contact matrix expects more edges than are possible given two sets, the algorithm will add just the max possible
        edges. The algorithm used to add actually add edges is dependent on the topology

        :param environment: a PartitionedEnvironment
        the environment to add edges for
        :param avg_degree: int or double
         if avg_degree is not None, then the contact matrix will be scaled such that the average degree
        :param topology: string
        can be either 'random', or 'strogatz'
        :return:
        """
        #to clean up code just a little
        p_sets = environment.partition
        CM = environment.returnReciprocatedCM()

        assert isinstance(environment, PartitionedEnvironment), "must be a partitioned environment"
        #a list of the number of people in each partition set
        p_n = [len(p_sets[i]) for i in p_sets]
        num_sets = len(p_sets)
        #get total contact, keeping in mind the contact matrix elements are divided by num people in group
        total_contact = 0
        for i, row in enumerate(CM):
                total_contact += sum(row)*p_n[i]
        #default_weight = total_contact/totalEdges
        if avg_degree == None:
            avg_degree = total_contact/environment.population
        #print('by the sum of the CM, avg_degree should be : {}'.format(avg_degree ))
        #determine total edges needed for entire network. There are two connections per edge)
        total_edges = math.floor(avg_degree * environment.population/2)

        #for each number between two groups, don't iterate zeros
        for i in p_sets:
            for j in range(i, num_sets):
                if p_n[j] == 0:
                    continue
                #get the fraction of contact that should occur between sets i and j
                contactFraction = CM[i, j]*p_n[i]/(total_contact)
                if contactFraction == 0:
                    continue
                #make sure there are enough people to fit num_edges
                if i == j:
                    num_edges = int(total_edges * contactFraction)
                    max_edges = p_n[i] * (p_n[i]-1)
                else:
                    num_edges = int(total_edges*contactFraction*2)
                    max_edges = p_n[i] * p_n[j]
                if max_edges < num_edges:
                    num_edges = max_edges
                if num_edges == 0:
                    continue

                #if the expected number of edges cannot be added, compensate by scaling the weights up a bit
                residual_scalar = total_edges * contactFraction / num_edges
                #if residual_scalar>2 and sizeA>3:
                    #print("error in environment # {}, it's contacts count for i,j = {} is {}but there are only {} people in that set".format(environment.index, index_i, CM[index_i,index_j], len(environment.partitioned_members[index_i])))
                if topology == 'random':
                    edgeList = self.genRandEdgeList(p_sets[i], p_sets[j], num_edges)
                    for edge in edgeList:
                        self.addEdge(edge[0], edge[1], environment)
                else:
                    if i == j:
                        self.clusterStrogatz(environment, num_edges, weight_scalar =1, subgroup = p_sets[i])
                    else:
                        self.clusterBipartite(environment, p_sets[i], p_sets[j], num_edges,weight_scalar=1)

    #-------------------
    #written for the clusterMatrixGuidedPreferentialAttachment function
    def addEdgeWithAttachmentTracking(self, nodeA, nodeB, attachments, environment):
        self.add_edge(nodeA, nodeB, environment)
        groupA = environment.id_to_partition[nodeA]
        groupB = environment.id_to_partition[nodeB]

        #grow secondary list
        #Adding B's friends to A's secondary
        for key in attachments[nodeA]["secondary"][nodeB]:
            attachments[nodeA]["secondary"][key].extend(attachments[nodeB]["secondary"][key])
        #Adding A's friends to B's secondary
        for key in attachments[nodeB]["secondary"][nodeA]:
            attachments[nodeB]["secondary"][key].extend(attachments[nodeA]["secondary"][key])

        #Adding B as secondary to A's friends
        for key in attachments[nodeA]:
            pass
        #Adding A as secondary to B's friends

            # grow primary list,
            # adding B to A, A to B
        attachments[nodeA]["primary"][groupB].append(nodeB)
        attachments[nodeB]["primary"][groupA].append(nodeA)

        #Adding A's friends to B

        #Adding B to A's friends
        #Adding A to B's friends
        #try:
            #attachments[""]

    def clusterMatrixGuidedPreferentialAttachment(self, environment, avg_contacts, prob_rand):
        cumulative_weight = sum(sum(environment.contact_matrix))
        num_people = len(environment.members)
        total_pos_edges = num_people * (num_people - 1) / 2
        total_edges = num_people * avg_contacts
        random_edges = math.round(prob_rand * total_edges)
        remaining_edges = total_edges - random_edges
        vecM = np.matrix.flatten(environment.contact_matrix)
        num_partitions = len(vecM)
        partitionAttachments = {}


        # speed up, in case there aren't many duplicates likely anyways
        random_duplicate_rate = (random_edges - 1) / total_pos_edges
        if random_duplicate_rate > 0.01:
            rand_edges = random.choices(list(itertools.combinations(environment.members, 2)), k=random_edges)
            for edge in rand_edges:
                self.add_edge(edge[0], edge[1], environment)
        else:
            for i in range(random_edges):
                sel_A = random.choice(num_people)
                sel_B = (sel_A + random.choice(num_people - 1)) % num_people
                self.add_edge(environment.members[sel_A], environment.members[sel_B], environment)

        # now adding preferential attachment edges
        partition_dist = [sum(vecM[:i] for i in range(num_partitions))] / sum(vecM)
        # partition_dist projects the edge_partition to  [0,1], such that the space between elements is in proportion to
        # the elements contact

        for i in range(remaining_edges):
            # this selects a partition element using partition_dist
            # then, from vec back to row/col
            selector = random.random()
            raw_partition = list(filter(range(num_partitions),
                                        lambda i: partition_dist[i] < (selector) & partition_dist[i + 1] > (
                                        selector)))
            partition_A = raw_partition % environment.contact_matrix.shape[0]
            partition_B = raw_partition // environment.contact_matrix.shape[0]

            def addEdgeWithAttachmentTracking(self, nodeA, nodeB, attachments, id_to_partition, mask_p, weight):
                w = self.trans_weighter.genMaskScalar(mask_p) * weight
                self.graph.add_edge(nodeA, nodeB, transmission_weight=w)
                groupA = id_to_partition[nodeA]
                groupB = id_to_partition[nodeB]

                # grow secondary list
                # Adding B's friends to A's secondary
                for key in attachments[nodeA]["secondary"][nodeB]:
                    attachments[nodeA]["secondary"][key].extend(attachments[nodeB]["secondary"][key])
                # Adding A's friends to B's secondary
                for key in attachments[nodeB]["secondary"][nodeA]:
                    attachments[nodeB]["secondary"][key].extend(attachments[nodeA]["secondary"][key])

                # Adding B as secondary to A's friends
                for key in attachments[nodeA]:
                    pass
                # Adding A as secondary to B's friends

                # grow primary list,
                # adding B to A, A to B
                attachments[nodeA]["primary"][groupB].append(nodeB)
                attachments[nodeB]["primary"][groupA].append(nodeA)

                # Adding A's friends to B

                # Adding B to A's friends
                # Adding A to B's friends
                # try:
                # attachments[""]

    #-----------------------------------------
    def simulate(self, gamma, tau, simAlg = EoN.fast_SIR, title = None, full_data = True, preventions=None):
        start = time.time()
        # Bryan had the arguments reversed. 
        simResult = simAlg(self.graph, tau, gamma, rho=0.001, transmission_weight='transmission_weight', return_full_data=full_data)
        sr = simResult
        #t10 = sr.get_statuses(time=10.)
        #t20 = sr.get_statuses(time=20.)
        tlast = sr.get_statuses(time=sr.t()[-1])
        len_tlast = len(tlast)
        #for k in tlast.keys():
            #print("key: ", k)

        for i in range(0,len_tlast):
            try:
                a = tlast[i]
            except:
                print("tlast index does not exist, i= ", i)
                quit()

        print(type(tlast)); quit()

        # Next: calculate final S,I,R for the different age groups. 

        print("len(tlast)= ", len(tlast))
        #print("tlast= ", tlast)
        #print("t10.t= ", t10.t())
        #print("simResult= ", dir(sr)); 
        #print(sr.get_statuses())
        #print(sr.node_history())
        #print(sr.I())
        SIR_results = {'S':sr.S(), 'I':sr.I(), 'R':sr.R(), 't':sr.t()}
        #print("SIR_results= ", SIR_results)

        stop = time.time()
        self.record.print("simulation completed in {} seconds".format(stop - start))

        ag = self.pops_by_category["age_groups"]

        # Collect the S,I,R at the last time: tlast
        #print("tlast.R= ", list(tlast.keys())); 
        # Replace 'S', 'I', 'R' by [0,1,2]
        brackets = {}
        for bracket in ag.keys():
            start1 = time.time()
            s = i = r = 0
            nodes = ag[bracket]
            b = brackets[bracket] = []
            #print("nodes= ", nodes)
            #print("tlast= ", tlast)
            #print("len tlast= ", len(tlast))
            for n in nodes:
                #print(n); print(tlast[n])
                b.append(tlast[n])
            print("len(brackets[%d]= " % bracket, len(brackets[bracket]))
            timer = time.time() - start1
            self.record.print("time to restructure age brackets: %f sec" % timer)
            
        print("gordon"); quit()

        #doesn't work returning full results
        #time_to_immunity = simResult[0][-1]
        #final_uninfected = simResult[1][-1]
        #final_recovered = simResult[3][-1]
        #percent_uninfected = final_uninfected / (final_uninfected + final_recovered)
        #self.record.last_runs_percent_uninfected = percent_uninfected
        #self.record.print("The infection quit spreading after {} days, and {} of people were never infected".format(time_to_immunity,percent_uninfected))

        # Do all this in Record class?  (GE)
        data = {}
        u = Utils()
        SIR_results = u.interpolate_SIR(SIR_results)
        data['sim_results'] = SIR_results
        #print("SIR_results: ", SIR_results['t']) # floats as they should be
        data['title'] = title
        data['params'] = {'gamma':gamma, 'tau':tau}
        data['preventions'] = preventions

        self.sims.append([simResult, title, [gamma, tau], preventions])

        dirname = "./ge_simResults/{}".format(self.stamp)
        try:
            mkdir(dirname)
        except:
            # accept an existing directory. Not a satisfying solution
            pass
        
        x = datetime.now().strftime("%Y-%m-%d,%I.%Mpm")
        filename = "%s, gamma=%s, tau=%s, %s" % (title, gamma, tau, x)
        self.saveResults("/".join([dirname,filename]), data)

    #-------------------------------------------
    def saveResults(self, filename, data_dict):
        """
        :param filename: string
        File to save results to
        :param data_dict: dictionary
        Save SIR traces, title, [gamma, tau], preventions
        # save simulation results and metadata to filename
        """
 
        with open(filename, "wb") as pickle_file:
            pickle.dump(data_dict, pickle_file)

        """
        # reload pickle data
        fd = open(filename, "rb")
        d = pickle.load(fd)
        SIR = d['sim_results']
        print("SIR['t']= ", SIR['t'])
        quit()
        """

    #-------------------------------------------
    def returnContactMatrix(self, environment):
        graph = self.graph.subgraph(environment.members)
        partition = environment.partitioner
        contact_matrix = np.zeros([partition.num_sets, partition.num_sets])
        partition_sizes = [len(environment.partition[i]) for i in environment.partition]

        for i in graph.nodes():
            iPartition = environment.id_to_partition[i]
            contacts = graph[i]
            for j in contacts:
                jPartition = environment.id_to_partition[j]
                contact_matrix[iPartition, jPartition] += self.graph[i][j]['transmission_weight'] / partition_sizes[iPartition]
        
        
        # plt.imshow(np.array([row / np.linalg.norm(row) for row in contact_matrix]))
        return contact_matrix 


    #----------------------------------------------------
    def plotContactMatrix(self, p_env):
        '''
        This function plots the contact matrix for a partitioned environment
        :param p_env: must be a partitioned environment
        '''

        if p_env == None:
            p_env = self.returnMultiEnvironment()
        contact_matrix = self.returnContactMatrix(p_env)
        plt.imshow(contact_matrix)
        plt.title("Contact Matrix for members of {} # {}".format(p_env.type, p_env.index))
        try:
            labels = p_env.partitioner.labels
        except:
            labels = ["{}-{}".format(5 * i, (5 * (i + 1))-1) for i in range(15)]
        axisticks= list(range(15))
        plt.xticks(axisticks, labels, rotation= 'vertical')
        plt.yticks(axisticks, labels)
        plt.xlabel('Age Group')
        plt.ylabel('Age Group')
        plt.show()


    #----------------------------------------------------
    def plotNodeDegreeHistogram(self, environment = None, layout = 'bars', ax = None, normalized = True):
        """
        creates a histogram which displays the frequency of degrees for all nodes in the specified environment.
        :param environment: The environment to plot for. if not specified, a histogram for everyone in the model will be plotted
        :param layout: if 'lines', a line plot will be generated. otherwise a barplot will be used
        :param ax: if an pyplot axis is specified, the plot will be added to it. Otherwise, the plot will be shown
        :param normalized, when true the histogram will display the portion of total
        """

        if environment != None:
            people = environment.members
            graph = self.graph.subgraph(people)
            plt.title("Degree plot for members of {} # {}".format(environment.type, environment.index))
        else:
            graph = self.graph
            people = self.populace.keys()

        degreeCounts = [0] * 100
        for person in people:
            try:
                degree = len(graph[person])
            except:
                degree = 0
            degreeCounts[degree] += 1
        while degreeCounts[-1] == 0:
            degreeCounts.pop()
        if layout == 'lines':
            plt.plot(range(len(degreeCounts)), degreeCounts)
        else:
            plt.bar(range(len(degreeCounts)), degreeCounts)
        plt.ylabel("total people")
        plt.xlabel("degree")
        plt.show()
        plt.savefig("./simResults/{}/".format(self.record.stamp))


    #----------------------------------------------------
    def plotSIR(self, memberSelection = None):
        """
        For members of the entire graph, will generate three charts in one plot, representing the frequency of S,I, and R, for all nodes in each simulation
        """

        rowTitles = ['S','I','R']
        fig, ax = plt.subplots(3,1,sharex = True, sharey = True)
        simCount = len(self.sims)
        if simCount == []:
            print("no sims to show")
            return
        else:
            for sim in self.sims:
                title = sim[1]
                sim = sim[0]
                t = sim.t()
                ax[0].plot(t, sim.S())
                ax[0].set_title('S')

                ax[1].plot(t, sim.I(), label = title)
                ax[1].set_ylabel("people")
                ax[1].set_title('I')
                ax[2].plot(t, sim.R())
                ax[2].set_title('R')
                ax[2].set_xlabel("days")
        ax[1].legend()
        plt.show()

    #If a partitionedEnvironment is specified, the partition of the environment is applied, otherwise, a partition must be passed
    def plotBars(self, environment = None, SIRstatus = 'R', normalized = False):
        """
        Will show a bar chart that details the final status of each partition set in the environment, at the end of the simulation
        :param environment: must be a partitioned environment
        :param SIRstatus: should be 'S', 'I', or 'R'; is the status bars will represent
        :param normalized: whether to plot each bar as a fraction or the number of people with the given status
        #TODO finish implementing None environment as entire graph
        """
        partition = environment.partitioner
        if isinstance(environment, PartitionedEnvironment):
            partitioned_people = environment.partition
            partition = environment.partitioner

        simCount = len(self.sims)
        partitionCount = partition.num_sets
        barGroupWidth = 0.8
        barWidth = barGroupWidth/simCount
        index = np.arange(partitionCount)

        offset = 0
        for sim in self.sims:
            title = sim[1]
            sim = sim[0]

            totals = []
            end_time = sim.t()[-1]
            for index in partitioned_people:
                set = partitioned_people[index]
                if len(set) == 0:
                    #no bar if no people
                    totals.append(0)
                    continue
                    total = sum(status == SIRstatus for status in sim.get_statuses(set, end_time).values()) / len(set)
                    if normalized == True:  total = total/len(set)
                    totals.append[total]

            #totals = sorted(totals)
            xCoor = [offset + x for x in list(range(len(totals)))]
            plt.bar(xCoor,totals, barWidth, label = title)
            offset = offset+barWidth
        plt.legend()
        plt.ylabel("Fraction of people with status {}".format(SIRstatus))
        plt.xlabel("Age groups of 5 years")
        plt.show()
        plt.savefig("./simResults/{}/evasionChart".format(self.record.stamp))

    def getR0(self):
        sim = self.sims[-1]
        herd_immunity = list.index(max(sim.I))
        return(self.population/sim.S([herd_immunity]))

    def reset(self):
        self.sims = []
        self.graph = nx.Graph()
        self.total_weight = 0
        self.total_edges = 0

#----------------------------------------------------------------------
class Record:
    def __init__(self):
        self.log = ""
        self.comments = ""
        self.stamp = datetime.now().strftime("%m_%d_%H_%M_%S")
        self.graph_stats = {}
        self.last_runs_percent_uninfected = 1
        mkdir("./simResults/{}".format(self.stamp))

    def print(self, string):
        print(string)
        self.log+=('\n')
        self.log+=(string)

    def addComment(self):
        comment = input("Enter comment")
        self.comments += comment
        self.log +=comment

    def printGraphStats(self, graph, statAlgs):
        if not nx.is_connected(graph):
            self.print("graph is not connected. There are {} components".format(nx.number_connected_components(graph)))
            max_subgraph = graph.subgraph(max(nx.connected_components(graph)))
            self.print("{} of nodes lie within the maximal subgraph".format(max_subgraph.number_of_nodes()/graph.number_of_nodes()))
        else:
            max_subgraph = graph
        graphStats = {}
        for statAlg in statAlgs:
            graphStats[statAlg.__name__] = statAlg(max_subgraph)
        self.print(str(graphStats))

    def dump(self):
        log_txt = open("./simResults/{}/log.txt".format(self.stamp), "w+")
        log_txt.write(self.log)
        if self.comments != "":
            comment_txt = open("./simResults/{}/comments.txt".format(self.stamp),"w+")
            comment_txt.write(self.comments)

#----------------------------------------------------------------------
class Gordon:
    def __init__(self):
        pass

    def reciprocity(self, cm, N):
        # The simplest approach to symmetrization is Method 1 (M1) in paper by Arregui
        cmm = np.zeros([4,4])
        for i in range(4):
            for j in range(4):
                if N[i] == 0:
                    cmm[i,j] = 0
                else:
                    cmm[i,j] = 1/(2 * N[i])  * (cm[i,j]*N[i] + cm[j,i]*N[j])
    
                if N[j] == 0:
                    cmm[j,i] = 0
                else:
                    cmm[j,i] = 1/(2 * N[j])  * (cm[j,i]*N[j] + cm[i,j]*N[i])
        return cmm
    
    #---------------------------------------------
    # This is GE's algorithm, a copy of what I implemented in Julia. 
    # We need to try both approaches for our paper. 
    def makeGraph(self, N, index_range, cmm):
        # N: array of age category sizes
        # index_range: lo:hi tuple 
        # cmm: contact matrix with the property: cmm[i,j]*N[i] = cmm[j,i]*N[j]
        # Output: a list of edges to feed into a graph
    
        edge_list = []
        Nv = sum(N)
        if Nv < 25: return edge_list # <<<<< All to all connection below Nv = 25. Not done yet.
    
        lo, hi = index_range
        # Assign age groups to the nodes. Randomness not important
        # These are also the node numbers for each category, sorted
        age_bins = [np.repeat([i], N[i]) for i in range(lo,hi)]
    
        # Efficiently store cummulative sums for age brackets
        cum_N = np.append([0], np.cumsum(N))
    
        ddict = {}
        total_edges = 0
    
        print("lo,hi= ", lo, hi)
        for i in range(lo,hi):
            for j in range(lo,i+1):
                #print("lo,i= ", lo, i)
                ddict = {}
                Nij = int(N[i] * cmm[i,j])
                print("i,j= ", i, j, ",    Nij= ", Nij)
                if i == j: Nij = Nij // 2
    
                if Nij == 0:
                    continue 
    
                total_edges += Nij
                # List of nodes in both graphs for age brackets i and j
                Vi = list(range(cum_N[i], cum_N[i + 1]))  # Check limits
                Vj = list(range(cum_N[j], cum_N[j+1]))  # Check limits

                # Treat the case when the number of edges dictated by the
                # contact matrices is greater than the number of available edges
                # The connectivity is then cmoplete
                if i == j:
                    lg = len(Vi)
                    nbe = lg*(lg-1) // 2
                else:
                    nbe = len(Vi)*len(Vj)
                    if nbe == 0:
                        continue

                if Vi == Vj and Nij > nbe:
                    Nij = nbe
    
                count = 0
    
                while True:
                    # p ~ Vi, q ~ Vj
                    # no self-edges
                    # only reallocate when necessary (that would provide speedup)
                    # allocate 1000 at t time
                    #p = getRand(Vi, 1) # I could use memoization
                    #q = getRand(Vi, 1) # I could use memoization
    
                    #p = rand(Vi, 1)[]
                    #q = rand(Vj, 1)[]
                    p = random.choice(Vi)
                    q = random.choice(Vj)

                    # multiple edges between p,q not allowed
                    # Dictionaries only store an edge once
                    if p == q: continue
                    if p > q:
                        ddict[p, q] = 1
                    elif q > p:
                        ddict[q, p] = 1

                    # stop when desired number of edges is reached
                    lg = len(ddict)
                    if lg == Nij: break 
    
                for k in ddict.keys():
                    s, d = k
                    edge_list.append((s,d))
    
        print("total_edges: ", total_edges)
        print("size of edge_list: ", len(edge_list))
        return edge_list
    #------------------------------------------------------------------

class Utils:
    def __init__(self):
        pass

    def interpolate_SIR(self, SIR):
        S = SIR['S']
        I = SIR['I']
        R = SIR['R']
        t = SIR['t']
        # interpolate on daily intervals.
        new_t = np.linspace(0., int(t[-1]), int(t[-1])+1)
        func = interp1d(t, S)
        Snew = func(new_t)
        func = interp1d(t, I)
        Inew = func(new_t)
        func = interp1d(t, R)
        Rnew = func(new_t)
        #print("t= ", new_t)
        #print("S= ", Snew)
        #print("I= ", Inew)
        #print("R= ", Rnew)
        SIR['t'] = new_t
        SIR['S'] = Snew
        SIR['I'] = Inew
        SIR['R'] = Rnew
        return SIR
