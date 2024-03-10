#STUDENT NAME:Guilherme Ferreira Duarte
#STUDENT NUMBER:107766

#DISCUSSED TPI-1 WITH: (names and numbers):
#João Paulo Caetano Rodrigues (108214)
#Guilherme Chapelo Andrade(107696)
#Fábio Alves (108016) 
#André Miragaia Rodrigues (108412)


from tree_search import *
import math

class OrderDelivery(SearchDomain):

    def __init__(self, connections, coordinates):
        self.connections = connections
        self.coordinates = coordinates
        self.initial = None
        self.targets = []

    def actions(self, state):
        city = state[0]
        actlist = []
        for (C1, C2, D) in self.connections:
            if C1 == city:
                actlist += [(C1, C2)]
            elif C2 == city:
                actlist += [(C2, C1)]
        return actlist

    def result(self, state, action):
        (C1, C2) = action
        newcity = C2 if C1 == state[0] else C1
        new_remaining_cities = [city for city in state[1] if city != newcity]
        return (newcity, new_remaining_cities)

    def satisfies(self, state, goal):
        return state[0] == goal and not state[1]

    def cost(self, state, action):
        for (city1, city2, distance) in self.connections:
            if (city1, city2) == action or (city2, city1) == action:
                return distance

    def heuristic(self, state, goal):
        
        if not state[1]: 
            return math.dist(self.coordinates[state[0]], self.coordinates[goal])

        nearest_city_distance = min(math.dist(self.coordinates[state[0]], self.coordinates[city]) for city in state[1])

       
        avg_distance_unvisited = sum(math.dist(self.coordinates[city1], self.coordinates[city2])
                                    for i, city1 in enumerate(state[1])
                                    for city2 in state[1][i+1:]) / len(state[1])

        
        back_to_goal_distance = math.dist(self.coordinates[state[1][0]], self.coordinates[goal])

        
        heuristic = nearest_city_distance + avg_distance_unvisited * len(state[1]) + back_to_goal_distance

        return heuristic


    
def orderdelivery_search(domain, city, targets, strategy='breadth', maxsize=None):
    problem = SearchProblem(domain, (city, targets), city)
    tree = MyTree(problem, strategy, maxsize)
    path = tree.search2()
    final_path = [state[0] for state in path]  # Extracting just the city from each state
    return (tree, final_path)
    


class MyNode(SearchNode):

    def __init__(self,state,parent,depth,cost,heuristic,marked=False):
        super().__init__(state,parent)
        self.depth=depth
        self.cost=cost
        self.heuristic=heuristic
        self.eval=round(self.cost+self.heuristic)
        self.marked = marked
        self.parent = parent
        self.NODE_MARKED = []
        
       
        

class MyTree(SearchTree):

    def __init__(self,problem, strategy='breadth',maxsize=None):
        super().__init__(problem,strategy)
        root = MyNode(problem.initial, None, 0, 0, problem.domain.heuristic(problem.initial, problem.goal))
        self.open_nodes = [root]
        self.terminals = 0
        self.maxsize = maxsize
        
        
        
        
        

    def astar_add_to_open(self,lnewnodes):
         for node in lnewnodes:
            inserted = False
            for i in range(len(self.open_nodes)):
                if node.eval < self.open_nodes[i].eval or (node.eval == self.open_nodes[i].eval and node.state[0] < self.open_nodes[i].state[0]):
                    self.open_nodes.insert(i, node)
                    inserted = True
                    break
            if not inserted:
                self.open_nodes.append(node) 


    def search2(self):
       
        while self.open_nodes!=[]:
            node = self.open_nodes.pop(0)
            
            
            if self.problem.goal_test(node.state):
                self.solution = node
                self.terminals = len(self.open_nodes)+1
                return self.get_path(node)
            
            lnewnodes = []
            self.non_terminals+=1


            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state,a)
                if newstate not in self.get_path(node):
                    newnode = MyNode(newstate, node, node.depth + 1, node.cost + self.problem.domain.cost(node.state, a), self.problem.domain.heuristic(newstate, self.problem.goal)) 
                    lnewnodes.append(newnode)
            if self.strategy == 'A*' and self.maxsize != None:
                    self.manage_memory()
            self.add_to_open(lnewnodes)
           
        
        return None
    
    
 
    def manage_memory(self):
        total_nodes = self.non_terminals+len(self.open_nodes)
        #print("Total nodes = ", total_nodes )
        while total_nodes > self.maxsize:
            #print("Entering mem management")
            self.open_nodes.sort(key=lambda node:node.eval,reverse=True) # sort by eval decreasingly
            for i in range(len(self.open_nodes)):
                if not self.open_nodes[i].marked:
                        self.open_nodes[i].marked = True
                        marked_node = self.open_nodes[i]
                        break
                    
            if marked_node == None or marked_node.parent == None:
                return
            
            siblings = []
            for node in self.open_nodes:
                if node.parent == marked_node.parent:
                    siblings.append(node)
                           
            if all(node.marked for node in siblings):   # if all siblings are marked
                [self.open_nodes.remove(node) for node in siblings ]
                marked_node.parent.eval = min(node.eval for node in siblings + [marked_node])
                self.non_terminals -= 1
                total_nodes = len(self.open_nodes)+self.non_terminals
                    
         


    

    
            
    

    
  