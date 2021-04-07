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
	def __init__(self, gui_view):
		self._scenario = None

	def setupWithScenario(self, scenario):
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

	def defaultRandomTour(self, time_allowance=60.0):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()
		while not foundTour and time.time() - start_time < time_allowance:
			# create a random permutation
			perm = math.random.permutation(ncities)
			route = []
			# Now build the route using the random permutation
			for i in range(ncities):
				route.append(cities[perm[i]])
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

	def greedy(self, time_allowance=60.0):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()

		for start_city in cities:
			if time.time() - start_time > time_allowance:
				break  # time out break

			# Now build the route
			route = []
			curr_city = start_city
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

	def branchAndBound(self, time_allowance=60.0):
		pass

	''' <summary>
		This is the entry point for the algorithm you'll write for your group project.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found during search, the 
		best solution found.  You may use the other three field however you like.
		algorithm</returns> 
	'''

	def fancy(self, time_allowance=60.0):
		results = {}
		cities = self._scenario.getCities()
		connections = [[] for _ in range(len(cities))]
		fewest = math.inf
		start_time = time.time()
		startCost = math.inf
		path = []
		unused = [i for i in range(len(cities))]
		for start_city in range(len(cities)):
			for i in connections[start_city]:
				for j in connections[i]:
					if start_city in connections[j]:
						cost = cities[start_city].costTo(cities[i])
						cost += cities[i].costTo(cities[j])
						cost += cities[j].costTo(cities[start_city])
						if cost < startCost:
							path = [start_city, i, j]

		for i in path:
			unused.remove(i)

		while len(path) < len(cities):
			next_insert = None
			insert_loc = None
			next_cost = math.inf
			for i in unused:
				for j in range(len(path)):
					if i in connections[path[j - 1]] and path[j] in connections[i]:
						cost = cities[path[j - 1]].costTo(cities[i])
						cost += cities[i].costTo(cities[path[j]])
						if cost < next_cost:
							next_insert = i
							insert_loc = j
							next_cost = cost
			path.insert(insert_loc, next_insert)
			unused.remove(next_insert)

		route = []
		for i in path:
			route.append(cities[i])
		bssf = TSPSolution(route)
		end_time = time.time()
		results['cost'] = bssf.cost
		results['time'] = end_time - start_time
		results['count'] = 1
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results
