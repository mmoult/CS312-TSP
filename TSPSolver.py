#!/usr/bin/python3

from which_pyqt import PYQT_VER
if PYQT_VER == 'PYQT5':
	from PyQt5.QtCore import QLineF, QPointF
elif PYQT_VER == 'PYQT4':
	from PyQt4.QtCore import QLineF, QPointF
else:
	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))

import time
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
		This is the entry point for the branch-and-bound algorithm that you will implement
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number solutions found during search (does
		not include the initial BSSF), the best solution found, and three more ints: 
		max queue size, total number of states created, and number of pruned states.</returns> 
	'''
		
	def branchAndBound( self, time_allowance=60.0 ):
		pass



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
		
		fewest = math.inf
		
		start_time = time.time()
		
		# we can try using 2-opt, which is a local search algorithm to optimize what we get from greedy
		bssf = self.greedy(60)
		if bssf['cost'] == math.inf:
			# greedy failed to give us a result. We *need* some path for the 2-opt, so we use
			# backtracking to guarantee
			startCity, connections = initialize()
			bssf = secureGreedy(connections, startCity)

		# now we go into the main local search loop
		# we want to find pairs of paths to switch
		
		
		#bssf = TSPSolution(route)

		end_time = time.time()
		print(end_time - start_time)
		results = {}
		results['cost'] = bssf['cost']
		results['time'] = end_time - start_time
		results['count'] = bssf['count']
		results['soln'] = bssf['soln']
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results


def initialize():
	startCity = None
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
	