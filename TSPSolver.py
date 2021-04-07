#!/usr/bin/python3

from which_pyqt import PYQT_VER
if PYQT_VER == 'PYQT5':
	from PyQt5.QtCore import QLineF, QPointF
elif PYQT_VER == 'PYQT4':
	from PyQt4.QtCore import QLineF, QPointF
else:
	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))

import time
import copy
from TSPClasses import *


class TSPSolver:
	def __init__( self, gui_view ):
		self._scenario = None

	def setupWithScenario( self, scenario ):
		self._scenario = scenario


	''' <summary>
		This is the entry point for the default solver
		which just finds a valid random tour.  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of solution, 
		time spent to find solution, number of permutations tried during search, the 
		solution found, and three null values for fields not used for this 
		algorithm</returns> 
	'''
	
	def defaultRandomTour( self, time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()
		while not foundTour and time.time()-start_time < time_allowance:
			# create a random permutation
			perm = math.random.permutation( ncities )
			route = []
			# Now build the route using the random permutation
			for i in range( ncities ):
				route.append( cities[ perm[i] ] )
			bssf = TSPSolution(route)
			count += 1
			if bssf.cost < math.inf:
				# Found a valid route
				foundTour = True
		end_time = time.time()
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results


	''' <summary>
		This is the entry point for the greedy solver, which you must implement for 
		the group project (but it is probably a good idea to just do it for the branch-and
		bound project as a way to get your feet wet).  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found, the best
		solution found, and three null values for fields not used for this 
		algorithm</returns> 
	'''

	def greedy( self,time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()
		
		for start_city in cities:
			if time.time() - start_time > time_allowance:
				break # time out break
			
			# Now build the route
			route = []
			curr_city = start_city
			fail = False
			while len(route) < ncities:
				# the shortest path from current_city. Starts as infinity
				shortest_path = math.inf
				next_city = None
				for i in range(ncities):
					if cities[i] is curr_city: # skip paths to ourself
						continue
					if cities[i] in route: # don't go to already visited
						continue
					dist = curr_city.costTo(cities[i])
					if dist == math.inf: # verify that it is a valid path
						continue
					# If we made it thus far, then our path is valid. But is it shortest?
					if dist < shortest_path:
						shortest_path = dist
						next_city = cities[i]
				curr_city = next_city
				# Verify that we actually found a valid path (sometimes no available- fail cond)
				if shortest_path < math.inf:
					route.append(curr_city) # append this to our route
				else:
					# fail case! We have to restart, but with the next starting point
					fail = True
					break
			dist = route[-1].costTo(route[0])
			if dist == math.inf:
				fail = True
			if fail:
				continue
			
			# If we successfully found a path (no fail), then test against previous attempts
			count += 1
			path = TSPSolution(route)
			if bssf is None or path.cost < bssf.cost:
				if path.cost < math.inf:
					bssf = path
					foundTour = True

		end_time = time.time()
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results



	''' <summary>
		This is the entry point for the algorithm you'll write for your group project.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found during search, the 
		best solution found.  You may use the other three field however you like.
		algorithm</returns> 
	'''
	def fancy( self,time_allowance=60.0 ):
		cities = self._scenario.getCities()
		
		start_time = time.time()
		# we need some path to start with
		# occasionally greedy can fail. We want our algorithm to be more robust, so we have provided
		# an alternative. If greedy fails, then we run a backtracking greedy variant to guarantee some
		# valid path. Once we have a path, we can optimize it
		
		#initialize(cities)
		# we can try using 2-opt, which is a local search algorithm to optimize what we get from greedy
		bssf = self.greedy(60)
		if bssf['cost'] == math.inf:
			# greedy failed to give us a result. We *need* some path, so we use
			# backtracking to guarantee
			startCity, connections = initialize(cities)
			bssf = secureGreedy(connections, startCity)

		# now we go into the main local search loop
		# we want to find pairs of paths to switch
		'''def findCostliestEdge(path):
			expensive = None
			value = 0
			for i in range(len(path)):
				thisVal = path[i-1].costTo(path[i])
				if expensive is None or thisVal < value:
					value = thisVal
					expensive = i
			return i
		'''
		path = bssf['soln'].route
		
		# This is what we call "skip ahead-reverse:
		# ------------------------------------------
		# skip limit must be less than the number of cities in the scenario
		skipLimit = 5 
		for i in range(len(path)):
			skipStart = 2 # we have to go more than just 1, because that is the regular path
			# we use currCost and backCost to see if the skip ahead is cheaper
			# initialize current cost to the distance for the first 2 (since that is where skipping begins)
			tempIndex = (i+1) % len(cities)
			afterIndex = (i+skipStart) % len(cities) # this is started as what skip will be the first iteration
			
			currCost = path[i].costTo(path[tempIndex])
			currCost += path[tempIndex].costTo(path[afterIndex])
			backCost = 0
			
			# if any alteration was made. If so, we need to get out of the upper iteration (since the path was changed)
			alteration = False
			for j in range(skipStart, skipLimit):
				# we keep track of these to save computation time
				skipIndex = afterIndex
				afterIndex = (skipIndex + 1) % len(cities) # after is always 1 ahead of skip
				
				fail = False
				# increase the min replaced cost for the next transition being skipped
				currCost += path[skipIndex].costTo(path[afterIndex])
				# if there is a skip ahead path
				if path[i].costTo(path[skipIndex]) == math.inf:
					fail = True # there is no direct path
				# now we have to verify that the backwards path is valid
				if path[skipIndex].costTo(path[skipIndex-1]) == math.inf:
					# If there is no backwards path anywhere along the skip forward,
					# then all further checks are invalidated. The future path would fail here
					break
				backCost += path[skipIndex].costTo(path[skipIndex-1]) # Python handles negative indices (so we don't need %)
				if fail:
					continue
				
				# if we got here, then the path back is valid, now we have to make the comparison to
				# see if it is actually worth it to switch
				
				# we can keep track of the current path cost accurately
				# The back path we cannot fully keep track of since the end points change each iteration,
				# therefore, we need to add from i to skip and from the end of the reverse -> afterIndex and 
				if currCost > backCost + path[i].costTo(path[skipIndex]) + \
										path[(i+1) % len(cities)].costTo(path[afterIndex]):
					# if we are here, we need to make the path alteration
					print("Reverse worked!", i, skipIndex)
					alteration = True
					path = path[0:i+1] + path[skipIndex:i:-1] + path[skipIndex+1:]
					break
			if alteration:
				break
			
		
		bssf = TSPSolution(path)

		end_time = time.time()
		#print(end_time - start_time)
		results = {}
		results['cost'] = bssf.cost
		results['time'] = end_time - start_time
		results['count'] = 1
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results


#########################################################
	def greedyBB(self):
		# this is a simplified greedy implementation just to give us a best so far
		# for pruning on branch and bound
		cities = self._scenario.getCities()
		ncities = len(cities)
		bssf = None
		
		# Now build the route
		route = []
		curr_city = cities[0]
		fail = False
		while len(route) < ncities:
			# the shortest path from current_city. Starts as infinity
			shortest_path = math.inf
			next_city = None
			for i in range(ncities):
				if cities[i] is curr_city:  # skip paths to ourself
					continue
				if cities[i] in route:  # don't go to already visited
					continue
				dist = curr_city.costTo(cities[i])
				if dist == math.inf:  # verify that it is a valid path
					continue
				# If we made it thus far, then our path is valid. But is it shortest?
				if dist < shortest_path:
					shortest_path = dist
					next_city = cities[i]
			curr_city = next_city
			# Verify that we actually found a valid path (sometimes no available- fail cond)
			if shortest_path < math.inf:
				route.append(curr_city)  # append this to our route
			else:
				# fail case! We have to restart, but with the next starting point
				fail = True
				break
		dist = route[-1].costTo(route[0])
		if dist == math.inf:
			fail = True

		# If we successfully found a path (no fail), then test against previous attempts
		path = TSPSolution(route)
		if bssf is None or path.cost < bssf.cost:
			if path.cost < math.inf:
				bssf = path

		return bssf
	
	
	def findMaxCost(self, mat):
		# this is the min of (the sum of the max of each row) and (the sum of the max of each col)
		rowsMax = 0
		for i in range(len(mat.rowsAvailable)):
			# choose some least to start out with
			most = mat.matrix[mat.rowsAvailable[i]][mat.colsAvailable[0]]
			for j in range(1, len(mat.colsAvailable)):
				# try to find more than most but less than infinity
				curr = mat.matrix[mat.rowsAvailable[i]][mat.colsAvailable[j]]
				if most == math.inf or (curr > most and curr < math.inf):
					most = curr
				
			rowsMax += most
		colsMax = 0
		for i in range(len(mat.colsAvailable)):
			# choose some least to start out with
			most = mat.matrix[mat.rowsAvailable[0]][mat.colsAvailable[i]]
			for j in range(1, len(mat.rowsAvailable)):
				# try to find more than most but less than infinity
				curr = mat.matrix[mat.rowsAvailable[j]][mat.colsAvailable[i]]
				if most == math.inf or (curr > most and curr < math.inf):
					most = curr
				
			colsMax += most
		return min(rowsMax, colsMax)
	
	
	''' <summary>
		This is the entry point for the branch-and-bound algorithm that you will implement
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number solutions found during search (does
		not include the initial BSSF), the best solution found, and three more ints: 
		max queue size, total number of states created, and number of pruned states.</returns> 
	'''
	def branchAndBound( self, time_allowance=60.0 ):	
		# we need to start by creating the initial cost matrix from the graph
		cities = self._scenario.getCities()
		connections = [[cities[j].costTo(cities[i]) for i in range(len(cities))] for j in range(len(cities))]
		startMatrix = CostMatrix(connections, 0)
		# then we need to reduce it and find the lowest bound
		startMatrix.reduce()
		startMatrix.path.append(0) # we will always start on city 0
		
		# then we need to select some best so far to start with (use greedy)
		greedyRes = self.greedyBB()
		bssf = greedyRes
		this = self
		
		if bssf is None:
			class EmptyPath:
				def __init__(self):
					self.cost = this.findMaxCost(startMatrix)
			bssf = EmptyPath()
		
		# set up some stats variables
		count = 0
		maxFrontier = 1
		totalGenerated = 0
		totalPruned = 0
		foundTour = False
		
		# then we need to set up the queues that we will draw from
		# we will construct multiple levels, and we can take a round robin approach in analyzing them
		queue = RobinQueue()
		# then we need to put the reduced matrix on that queue and expand it (start from city 0)
		queue.insert(startMatrix)
		
		stime = time.time()
		# continue expanding in a loop until no more on the queue or until time runs out
		while queue.size > 0 and time.time()-stime <= time_allowance:
			toExpand = queue.getNext()
			# check that we haven't gotten a better solution than this since we added it
			if toExpand.lowerBound >= bssf.cost:
				totalPruned += 1
				continue
			# now we can expand it- we can expand a possibility for every non-infinite entry in the row
			cityAt = toExpand.path[-1]
			# for each matrix that it expands to, check to verify that it is not too big and add to queue
			# we also want to skip a path back to city 0 until the very end
			for i in range(1, len(toExpand.colsAvailable)):
				if toExpand.matrix[cityAt][toExpand.colsAvailable[i]] < math.inf:
					newMat = toExpand.select(toExpand.colsAvailable[i])
					totalGenerated += 1
					# check if the path is now complete
					if len(newMat.path) == len(cities):
						# we have to connect to the beginning (city 0)
						newMat.lowerBound += newMat.matrix[newMat.path[-1]][0]
						# we found a solution if lower bound is less than infinite
						if newMat.lowerBound < bssf.cost: # it was better than the bssf!
							foundTour = True
							count += 1 # we found another solution
							bssf = TSPSolution(newMat.getPathCities(cities))
						else:
							totalPruned += 1
						continue
					
					# otherwise, reduce and try to add to queue
					newMat.reduce()
					if newMat.lowerBound < bssf.cost:
						queue.insert(newMat)
						if queue.size > maxFrontier:
							maxFrontier = queue.size
					else:
						totalPruned += 1
		
		# After that is all done, set the stats from the run
		etime = time.time()
		results = {}
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = etime - stime
		results['count'] = count
		results['soln'] = bssf
		results['max'] = maxFrontier
		results['total'] = totalGenerated
		results['pruned'] = totalPruned
		return results

	
class CostMatrix:
	def __init__(self, matrix, lowerBound, rowsAvailable=None, colsAvailable=None):
		self.matrix = matrix
		self.path = []
		self.lowerBound = lowerBound
		# compute rows available and cols available from given matrix if not given
		if rowsAvailable is None:
			self.rowsAvailable = [i for i in range(len(matrix))]
		else:
			self.rowsAvailable = rowsAvailable
		if colsAvailable is None:
			self.colsAvailable = [i for i in range(len(matrix[0]))]
		else:
			self.colsAvailable = colsAvailable
	
	
	def reduce(self):
		# we need to find a zero in each row and in each column
		# There needs to be a zero in each row and column
		# For each row
		for i in range(len(self.rowsAvailable)):
			# choose some least to start out with
			least = self.matrix[self.rowsAvailable[i]][self.colsAvailable[0]]
			if least == 0:
				continue
			for j in range(1, len(self.colsAvailable)):
				# if the current index is less than least, replace it
				if self.matrix[self.rowsAvailable[i]][self.colsAvailable[j]] < least:
					least = self.matrix[self.rowsAvailable[i]][self.colsAvailable[j]]
					# if the least is now 0, we know we cannot find better
					if least == 0:
						break
				
			if least == 0:
				continue
			for j in range(0, len(self.colsAvailable)):
				self.matrix[self.rowsAvailable[i]][self.colsAvailable[j]] -= least
			self.lowerBound += least
			# early break since if we got infinity, the rest doesnt' matter
			if self.lowerBound == math.inf:
				return math.inf
		
		# For each column
		for i in range(len(self.colsAvailable)):
			# choose some least to start out with
			least = self.matrix[self.rowsAvailable[0]][self.colsAvailable[i]]
			if least == 0:
				continue
			for j in range(1, len(self.rowsAvailable)):
				# if the current index is less than least, replace it
				if self.matrix[self.rowsAvailable[j]][self.colsAvailable[i]] < least:
					least = self.matrix[self.rowsAvailable[j]][self.colsAvailable[i]]
					# if the least is now 0, we know we cannot find better
					if least == 0:
						break
				
			if least == 0:
				continue
			for j in range(0, len(self.rowsAvailable)):
				self.matrix[self.rowsAvailable[j]][self.colsAvailable[i]] -= least
			self.lowerBound += least
			# early break since if we got infinity, the rest doesn't matter
			if self.lowerBound == math.inf:
				return math.inf
		
		return self.lowerBound
	
	
	def select(self, nextCity):
		toReturn = copy.deepcopy(self)
		# the current city is the last one on the path
		currCity = toReturn.path[len(self.path)-1]
		# choose the next city by adding the cost to lower bound
		toReturn.lowerBound += toReturn.matrix[currCity][nextCity]
		
		# then make some alterations to the matrix
		# we set the row and column to unusable
		toReturn.rowsAvailable.remove(currCity)
		toReturn.colsAvailable.remove(nextCity)
		# we add this city to the path
		toReturn.path.append(nextCity)
		# and we block out the mirror
		toReturn.matrix[nextCity][currCity] = math.inf
		
		return toReturn
	
	
	def getPathCities(self, cities):
		return [cities[i] for i in self.path]
		

class RobinQueue:
	def __init__(self):
		self.levels = [] # a list of lists for the elements on each level
		self.l_on = 0 # the current level we are on
		self.size = 0 # the number of elements in the queue
	
	def getNext(self):
		if self.size <= 0:
			raise Exception("There are no elements to get!")
		isValid = False # this also serves as a good do-while loop
		# we want to know not only that the index is in range, but that there are elements to evaluate
		while not isValid:
			self.l_on -= 1 # change l_on to get what is next
			# if we have gone to the bottom, we need to loop up
			# or if a level has been removed from bottom, we have to reset to what is possible
			if self.l_on < -1 or self.l_on >= len(self.levels): # -1 serves for the last index in the list
				self.l_on = len(self.levels) - 1
			# the outer while will ensure there is something in this level to get
			isValid = len(self.levels[self.l_on]) > 0
		# now we can pop out the element at the index
		cheapest = self.levels[self.l_on][0]
		# find the cheapest on this chosen level (we know there is at least one here)
		for matrix in range(1, len(self.levels[self.l_on])):
			if self.levels[self.l_on][matrix].lowerBound < cheapest.lowerBound:
				cheapest = self.levels[self.l_on][matrix]
		# now we can actually pop the chosen one
		self.levels[self.l_on].remove(cheapest)
		self.size -= 1
		return cheapest
	
	def insert(self, matrix):
		self.size += 1
		levelOn = len(matrix.path) - 1
		while len(self.levels) <= levelOn:
			self.levels.append([])
		self.levels[levelOn].append(matrix)
		return
#########################################################


def initialize(cities):
	startCity = None
	fewest = math.inf
	connections = [[] for _ in range(len(cities))]
	for i in range(len(cities)):
		for route in range(len(cities)):
			if cities[i] is cities[route]:  # skip paths to ourself
				continue
			dist = cities[route].costTo(cities[i])
			if dist == math.inf:  # verify that it is a valid path
				continue
			# This is a digraph, so the connections are unidirectional
			connections[route].append(i)

		if len(connections[i]) < fewest:
			fewest = len(connections[i])
			startCity = i
	return startCity, connections


def secureGreedy(connections, startCity):
	used = [False] * len(cities)
	usedLen = len(cities)

	banned_edges = [[] for _ in range(len(cities))]
	path = [startCity]

	current = startCity
	backtrack = False
	while usedLen > 0:
		used[current] = True
		usedLen -= 1
		if usedLen == 0:
			if startCity in connections[current]:
				break
			else:
				backtrack = True
		next = 0 # the city index that we should go to next
		fewest = None # number of connections
		cheapest = None
		if not backtrack:
			for i in range(len(connections[current])):
				if used[connections[current][i]] or connections[current][i] in banned_edges[current]:
					continue
				if cheapest is None or cities[current].costTo(cities[connections[current][i]]) < cheapest:
					cheapest = cities[current].costTo(cities[connections[current][i]])
					next = connections[current][i]
				elif cheapest == cities[current].costTo(cities[connections[current][i]]) and \
						len(connections[connections[current][i]]) < len(connections[connections[current][next]]):
					next = connections[current][i]

		if fewest is None or backtrack is True:
			used[current] = False
			usedLen += 2
			banned_edges[path[-2]].append(current)
			next = path[-2]
			path = path[0:-2]
			backtrack = False
			# print("Back-Track")

		path.append(next)
		current = next
	route = []
	for i in path:
		route.append(cities[i])
	
	bssf = TSPSolution(route)
	results['cost'] = bssf.cost if foundTour else math.inf
	results['time'] = end_time - start_time
	results['count'] = 1
	results['soln'] = bssf
	results['max'] = None
	results['total'] = None
	results['pruned'] = None
	return results

	