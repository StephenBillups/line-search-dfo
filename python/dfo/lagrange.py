from dfo import polynomial_basis

from numpy import inf as infinity
from numpy.linalg import norm as norm
from numpy import zeros
from numpy import bmat as blockmat
from numpy import arange
from numpy import empty
from numpy import eye
from numpy import dot
from numpy import reshape
from numpy import random
import matplotlib.pyplot as plt
from numpy.linalg import lstsq
from numpy import asmatrix
from numpy import asarray
from scipy.optimize import minimize
from utilities import trust
from utilities import sys_utils

from numpy import array


class Certification:
	def __init__(self, poisedSet, params):
		self.original = poisedSet
		self.poised = False
		self.shifted = _shift(poisedSet, params.center, params.radius)
		self.lmbda = None
		self.indices = arange(0, poisedSet.shape[0])
		self.unshifted = None
		self.Lambda = None

		if params.improveWithNew:
			for i in range(1, self.shifted.shape[0]):
				if norm(self.shifted[i, :]) > params.max_radius:
					self.shifted[i, :] = zeros(self.shifted.shape[1])


	def fail(self):
		self.poised = False
		self.shifted = None
		self.lmbda = None
		self.indices = None
		self.unshifted = None

	def plot(self, filename, center, radius):
		fig = plt.figure()
		fig.set_size_inches(sys_utils.get_plot_size(), sys_utils.get_plot_size())
		ax1 = fig.add_subplot(111)


		ax1.add_artist(plt.Circle(center, radius, color='g', fill=False))
		ax1.scatter(self.original[:, 0], self.original[:, 1], s=10, c='b', marker="+", label='original')
		ax1.scatter(self.unshifted[:, 0], self.unshifted[:, 1], s=10, c='r', marker="x", label='poised')

		# ax1.axis([center[0] - 2 * radius, center[0] + 2 * radius, center[1] - 2 * radius, center[1] + 2 * radius])

		if self.Lambda is not None:
			lambdaStr = "Lambda=" + str(max(self.Lambda))
			ax1.text(center[0], center[1], lambdaStr)

		plt.legend(loc='lower left')
		fig.savefig(filename)
		plt.close()

class LagrangeParams:
	def __init__(self, center, radius, improve, xsi, consOpts=None):
		self.improveWithNew = improve
		self.xsi = xsi
		self.radius = radius
		self.center = center
		self.maxL = 2
		self.max_radius = 1.5
		self.consOpts = consOpts

	def getShiftedConstraints(self):

		# I have spent a while staring at this code
		# I can't figure out why it doesn't work.
		# There is something I don't understand about python.
		# I also tried the map function.

		# constraints = [{
		# 	'type': constraint['type'],
		# 	'fun':  lambda x: constraint['fun'](x * self.radius + self.center),
		# 	'jac':  lambda x: constraint['jac'](x * self.radius + self.center) * self.radius
		# } for constraint in self.consOpts.constraints]

		constraints = [{
			'type': 'ineq',
			'fun': lambda x: self.consOpts.constraints[0]['fun'](x * self.radius + self.center),
			'jac': lambda x: self.consOpts.constraints[0]['jac'](x * self.radius + self.center) * self.radius
		}, {
			'type': 'ineq',
			'fun': lambda x: self.consOpts.constraints[1]['fun'](x * self.radius + self.center),
			'jac': lambda x: self.consOpts.constraints[1]['jac'](x * self.radius + self.center) * self.radius
		}]

		# Test code
		# for i in range(100):
		# 	x = random.rand(2)
		# 	print(self.consOpts.constraints[0]['fun'](x))
		# 	print(self.consOpts.constraints[1]['fun'](x))
		# 	print(constraints[0]['fun']((x - self.center) / self.radius))
		# 	print(constraints[1]['fun']((x - self.center) / self.radius))
		return constraints


def _shift(set, center, radius):
	retVal = empty(set.shape)
	for i in range(0, set.shape[0]):
		retVal[i, :] = (set[i,:] - center) / radius
	return retVal

def _unshift(set, center, radius):
	retVal = empty(set.shape)
	for i in range(0, set.shape[0]):
		retVal[i, :] = set[i,:] * radius + center
	return retVal

def _testV(V, basis, poisedSet):
	p = basis.basis_dimension
	npoints = poisedSet.shape[0]
	h = npoints + p
	if norm(V[0:npoints, :] - basis.evaluateMatToMat(poisedSet) * V[npoints:h, :]) > 1e-3:
		raise Exception("did not work")

def _getMaxIdx(max):
	idx = 0
	val = max[0,0]
	for i in range(0, max.shape[0]):
		newVal = max[i, 0]
		if newVal > val:
			idx = i
			val = newVal
	return (val, idx)

def _swapRows(mat, idx1, idx2):
	mat[[idx1, idx2], :] = mat[[idx2, idx1], :]

def _getBestExistingPoint(basis, row, history):
	""" Look through points in history and try to replace the current row """
	#  Priority TODO: implement this!!!!!

	found = False
	maxX = None
	# maxY = -1
	# for point in history's keys:
	#	if too far away:
	#		continue
	#	y = dot(basis.evaluateRowToRow(point), row)
	#	if y > abs(maxY)
	#		y = abs(maxY)
	#		maxX = point
	#		found = True

	return (found, maxX)

def _maximize_lagrange_arbitrary(basis, row, tol):
	""" This method would work for any basis... """

	def thePoly(x):
		return dot(basis.evaluateRowToRow(x), row)

	minimumResult = minimize(lambda x: thePoly(x) if norm(x) < 1 else infinity,
							 zeros(basis.n), method='Nelder-Mead',
							 #				constraints = {'type':'ineq', 'fun': constraint},
							 options={'xtol': tol, 'disp': False})

	maximumResult = minimize(lambda x: -thePoly(x) if norm(x) < 1 else infinity,
							 zeros(basis.n), method='Nelder-Mead',
							 #				constraints = {'type':'ineq', 'fun': constraint},
							 options={'xtol': tol, 'disp': False})
	if abs(maximumResult.fun) > 1e300 or abs(minimumResult.fun) > 1e300:
		raise Exception('Too big!!!')

	if abs(minimumResult.fun) > abs(maximumResult.fun):
		return minimumResult.x, abs(minimumResult.fun)
	else:
		return maximumResult.x, abs(maximumResult.fun)





def _maximize_lagrange_quad(basis, row, tol, constraints):
	""" This method uses the fact that we are modelling with quadratics..."""
	quadmodel = basis.getQuadraticModel(row)

	cons = [{'type': 'ineq',
			 'fun': lambda x: 1 - dot(x, x),
			 'jac': lambda x: reshape(-2 * x, (1, basis.n))},
	]

	if constraints is not None:
		cons += constraints

	# Here, I should solve a program to find a feasible point, instead of trying several different points.

	minimumResult = None
	while minimumResult is None or not minimumResult.success or norm(minimumResult.x) >= 1 + 1e-4 + tol:
		minimumResult = minimize(quadmodel.evaluate, jac=quadmodel.gradient, x0=random.random(basis.n) / 10,
						constraints=cons, method='SLSQP', options={"disp": False, "maxiter": 1000}, tol=tol)
	if not minimumResult.success or norm(minimumResult.x) >= 1 + 1e-4:
		raise Exception('Uh oh')

	maximumResult = None
	while maximumResult is None or not maximumResult.success or norm(maximumResult.x) >= 1 + 1e-4 + tol:
		maximumResult = minimize(lambda x: -quadmodel.evaluate(x), jac=lambda x: -quadmodel.gradient(x), x0=random.random(basis.n) / 10,
						constraints=cons, method='SLSQP', options={"disp": False, "maxiter": 1000}, tol=tol)
	if not maximumResult.success or norm(maximumResult.x) >= 1 + 1e-4:
		raise Exception('Uh oh')

	# print(cons[1]['fun'](minimumResult.x))
	# print(cons[2]['fun'](minimumResult.x))
	# print(cons[1]['fun'](maximumResult.x))
	# print(cons[2]['fun'](maximumResult.x))

	if abs(minimumResult.fun) > abs(maximumResult.fun):
		return minimumResult.x, abs(minimumResult.fun)
	else:
		return maximumResult.x, abs(maximumResult.fun)

def _minimize_lagrange_trust(basis, row, tol):
	quadmodel = basis.getQuadraticModel(row)

	x1, f1, _, _, _ = trust.trust( asmatrix(quadmodel.b).T,  asmatrix(quadmodel.Q), 1)
	x2, f2, _, _, _ = trust.trust(-asmatrix(quadmodel.b).T, -asmatrix(quadmodel.Q), 1)
	f1 = quadmodel.c + f1
	f2 = quadmodel.c - f2
	if abs(f1) > abs(f2):
		return asarray(x1).flatten(), abs(f1)
	else:
		return asarray(x2).flatten(), abs(f2)



def _maximize_lagrange(basis, row, tol, constraints=None):
	# v = True
	# try:
	# 	newVal1, funVal1 = _maximize_lagrange_quad(basis, row, tol)
	# except:
	# 	v = False
	newVal1, funVal1 = _maximize_lagrange_quad(basis, row, tol, constraints)
	# newVal2, funVal2 = _maximize_lagrange_arbitrary(basis, row, tol)
	# newVal3, funVal3 = _minimize_lagrange_trust(basis, row, tol)

	# if False:
	# 	print('-------------------')
	# 	if v: print(funVal1)
	# 	print(funVal2)
	# 	print(funVal3)
	# 	print('-')
	# 	if v: print(newVal1)
	# 	print(newVal2)
	# 	print(newVal3)
	# 	print('-')
	# 	if v: print(norm(newVal1))
	# 	print(norm(newVal2))
	# 	print(norm(newVal3))
	# 	print('-------------------')

	# _maximize_lagrange_quad(basis, row, tol)
	# _maximize_lagrange_arbitrary(basis, row, tol)
	# _minimize_lagrange_trust(basis, row, tol)

	return newVal1, funVal1



def _replace(cert, i, newValue, npoints, h, V, b):
	cert.shifted[i] = newValue
	V[i] = dot(b.evaluateRowToRow(newValue), V[npoints:h, :])
	cert.indices[i] = -1
	_testV(V, b, cert.shifted)
	return _getMaxIdx(abs(V[i:npoints, i]))


def computeLagrangePolynomials(bss, poisedSet, params, history=None, tol=1e-8):
	p = bss.basis_dimension
	npoints = poisedSet.shape[0]
	h = npoints + p

	cert = Certification(poisedSet, params)

	if not npoints == p:
		raise Exception("currently, have to have all points")

	V = blockmat([[bss.evaluateMatToMat(cert.shifted)], [eye(p)]])

	for i in range(0, p):
		_testV(V, bss, cert.shifted)

		# Get maximum value in matrix
		maxVal, maxIdx = _getMaxIdx(abs(V[i:npoints, i]))

		# Check the poisedness
		if maxVal < params.xsi or maxVal > params.maxL:
			# First, check for an existing point to replace.
			found, newValue = _getBestExistingPoint(bss, V[npoints:h, i], history)
			if found:
				maxVal, maxIdx = _replace(cert, i, newValue, npoints, h, V, bss)

		if (maxVal < params.xsi or maxVal > params.maxL) and params.improveWithNew:
			# If still not poised, Then check for new points
			newValue, _ = _maximize_lagrange(bss, V[npoints:h, i], tol, params.getShiftedConstraints())
			maxVal, maxIdx = _replace(cert, i, newValue, npoints, h, V, bss)

		if maxVal < params.xsi:
			# If still not poised, we are stuck
			cert.fail()
			return cert

		# perform pivot
		if not maxIdx == 0:
			otherIdx = maxIdx + i
			_swapRows(V, i, otherIdx)
			_swapRows(cert.shifted, i, otherIdx)
			tmp = cert.indices[i]
			cert.indices[i] = cert.indices[otherIdx]
			cert.indices[otherIdx] = tmp

		# perform LU
		V[:, i] = V[:, i] / V[i, i]
		for j in range(0, p):
			if i == j:
				continue
			V[:, j] = V[:, j] - V[i, j] * V[:, i]

	cert.unshifted = _unshift(cert.shifted, params.center, params.radius)
	cert.lmbda = V[npoints:h]
	cert.poised = True

	cert.Lambda = empty(npoints)
	for i in range(npoints):
		_, cert.Lambda[i] = _maximize_lagrange(bss, V[npoints:h, i], tol)

	cert.LambdaConstrained = empty(npoints)
	for i in range(npoints):
		_, cert.LambdaConstrained[i] = _maximize_lagrange(bss, V[npoints:h, i], tol, params.getShiftedConstraints())

	return cert



def computeRegressionPolynomials(basis, shifted):
	p = basis.basis_dimension
	npoints = shifted.shape[0]
	a = basis.evaluateMatToMat(shifted)
	c,_,_,_ = lstsq(a, eye(npoints))
	return c