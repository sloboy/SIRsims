import numpy as np
import scipy as sci
import networkx as nx
import pandas as pd
import random
import pickle
import itertools

epidemicSims = 10
houseHolds = 600
houseHoldSize = 4
people = houseHoldSize * houseHolds
schoolGroupSize = 20
workGroupSize = 10
employmentRate = 0.9
recoveryRate = 1
globalInfectionRate = 1
houseInfectivity = .1
workInfectivity = .05
tau = 1 #transmission factor
gamma = 1 #recovery rate
initial_infected = 1

#ageGroups = [[0,5], [5,8], [18,65], [65,90]]
#ageGroupWeights = [0.05, 0.119, 0.731, 0.1]  # from census.gov for tallahassee 2019
attributes = {"age": ['[0,5]', '[5,18]', '[18,65]', '[65,90]'], "gender": ['M', 'F']}
attribute_p = {"age": [0.05, 0.119, 0.731, 0.1], "gender": [0.5,0.5]}
duties = [None, 'school','work']

#incomeGroups =
#incomeGroupWeights =


class Person():
    attributes = {}
# a function which returns a list of tuples randomly assigning nodes to groups of size n
def nGroupAssign(members, groupSize):
    length = len(members)
    random.shuffle(members)
    pos = 0
    groupNumber = 0
    dict = {}
    while True:
        if(pos+groupSize>length):
            dict[groupNumber] = (itertools.islice(members, pos, pos + groupSize))
            break
        dict[groupNumber] = list(itertools.islice(members, pos, pos + groupSize))
        groupNumber = groupNumber + 1
        pos = pos+groupSize
    return dict


# a function which returns a list of tuples randomly assigning nodes to groups of size probability n
def p_nGroupAssign(memberIndices, p_n):
    length = len(memberIndices)
    random.shuffle(memberIndices)
    pos = 0
    groupNumber = 0
    dict = {}
    while True:
        groupSize = random.choices(range(len(p_n)), weights=p_n)[0]+1
        if(pos+groupSize>length):
            dict[groupNumber] = (itertools.islice(memberIndices, pos, pos + groupSize))
            break
        dict[groupNumber] = list(itertools.islice(memberIndices, pos, pos + groupSize))
        groupNumber = groupNumber + 1
        pos = pos+groupSize
    return dict

def p_attributeAssign(memberIndices, attributes, probabilities):
    random.shuffle(memberIndices)
    dict = {attribute: [] for attribute in attributes}
    for index in memberIndices:
        assignment = random.choices(attributes, weights = probabilities)[0]
        dict[assignment].append(index)
    return dict

#takes a dict of dicts to represent populace and returns a list of dicts of lists to represent groups of people with the same
#attributes

#for loading people objects from file
def loadPickledPop(filename):
    with open(filename,'rb') as file:
        x = pickle.load(file)
    #return represented by dict of dicts
    return ({key: (vars(x[key])) for key in x})#.transpose()
# assign people to households


def genPop(people, attributeClasses, attributeClass_p):
    population = {i: {} for i in range(people)}
    for attributeClass in attributeClasses:
        assignments = p_attributeAssign(list(range(people)), attributeClasses[attributeClass],attributeClass_p[attributeClass])
        for  key in assignments:
            for i in assignments[key]:
                population[i][attributeClass] = key
    
    return population


def sortPopulace(populace, categories):
    groups = {category: {} for category in categories}
    for person in populace:
        for category in categories:
            try:
                groups[category][populace[person][category]].append(person)
            except:
                groups[category][populace[person][category]] = [person]
    return groups



#connect list of groups with weight
#TODO update to use a weight calculating function
def clusterDenseGroups(graph, groups, weight):
    for key in groups.keys():
        print(key)
        if key !=None:
            memberCount = len(groups[key])
            memberWeightScalar = np.sqrt(memberCount)
            for i in range(memberCount):
                for j in range(i):
                    graph.add_edge(groups[key][i],groups[key][j] ,transmission_weight = groupWeight/memberWeightScalar)


def clusterByDegree_p(graph, groups, weight,degree_p):
    #some random edges may be duplicates, best for large groups
    connectorList = []

    for key in groups.keys():
        print(key)
        if key !=None:
            memberCount = len(groups[key])
            for i in range(memberCount):
                nodeDegree = random.choices(range(len(degree_p)), weights = degree_p)
                connectorList.extend(i*degree_p)
            random.shuffle(connectorList)

            i = 0
            while i < len(connectorList)-1:
                graph.add_edge(connectorList[i],connectorList[i+1],transmission_weight = weight)
                i = i+2

def strogatzDemCatz(graph, groups, weight, local_k, rewire_p):
    for key in groups.keys():
        if key!=None:
            memberCount = len(groups[key])
            for i in range(memberCount):


def clusteGroupsByPreferentialAttachment(graph, groups):
    for key in groups.keys():
        memberCount = len(groups[key])

#def sortAttributes(people,attributeClasses):
#populace = genPop(people, attributes, attribute_p)
populace = loadPickledPop("people_list_serialized.pkl")
populaceCategoryGroups = sortPopulace(populace,['sp_hh_id','work_id'])

graph = nx.Graph()

clusterGroupsByDegree_p(graph, populaceCategoryGroups['sp_hh_id'], [0.2,0.2,0.2,0.2,0.2])
clusterDenseGroups(graph, populaceCategoryGroups['sp_hh_id'], 0.1)


print("stop here ")

#def assignDuties(populace):

#def networkPopulace(duties):





#TODO assign households and nodes in households to neighborhoods:
#Idea: track neighborhoods and whole city as 'global groups', groups which occur global infections to eachother, but aren't necessarily bigger risks because the group is bigger
#these are contacts that occur between strangers who possibly share the same transit, gym, etc.

#TODO a function that returns the infection rate of neighborhoods and or city





#TODO a function to animate a graph in time

#TODO write a function to spline 1d t,S,I,R arrays into even time intervals so that multiple runs can be averaged

#TODO a function to draw a sparse weights matrix in a graph



