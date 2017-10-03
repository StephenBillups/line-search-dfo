

from dfo import polynomial_basis
from dfo import lagrange
from numpy import dot
from numpy import array as arr
from numpy import zeros
from numpy import array
from numpy import multiply
from numpy import sqrt
from numpy import arctan
from numpy import reshape
from numpy import sin
from scipy.optimize import minimize
from numpy.linalg import norm
import matplotlib.pyplot as plt

from numpy import linspace
from numpy import meshgrid
from utilities import sys_utils
import matplotlib

from dfo.dfo_model import MultiFunctionModel

tol=1e-4
n = 2
degree = 2
a = 1
xsi=1e-3
center = array((0.5, 0))
radius = 1


theConstraints = [{
	'type': 'ineq',
	'fun': lambda x: a * x[0] + x[1],
	'jac': lambda x: array((a, 1)),
}, {
	'type': 'ineq',
	'fun': lambda x: a * x[0] - x[1],
	'jac': lambda x: array((a, -1)),
}]

class objective:
	def __init__(self, minorSpeed=1e-1, amplitude=a/2, freq=2):
		self.minorSpeed = minorSpeed
		self.amplitude=amplitude
		self.freq = freq

	def evaluate(self, x):
		return  self.minorSpeed * x[0] + (x[1] - self.amplitude * x[0] * sin(self.freq * x[0])) ** 2
obj = objective()

basis = polynomial_basis.PolynomialBasis(n, degree)

class ConstraintOptions:
	def __init__(self):
		self.constraints = theConstraints
		self.useInLambda = False

model = MultiFunctionModel([obj], basis, center, radius=radius, xsi=xsi, consOpts=ConstraintOptions())


def createPlot(filename, title, model, newMin=None, rho=None):
	plt.title(title)
	fig = plt.figure()
	fig.set_size_inches(sys_utils.get_plot_size(), sys_utils.get_plot_size())
	ax1 = fig.add_subplot(111)
	matplotlib.rcParams['xtick.direction'] = 'out'
	matplotlib.rcParams['ytick.direction'] = 'out'

	plt.legend(loc='lower left')

	x = linspace(model.unshifted[0, 0] - model.modelRadius, model.unshifted[0, 0] + model.modelRadius, num=100)
	y = linspace(model.unshifted[0, 1] - model.modelRadius, model.unshifted[0, 1] + model.modelRadius, num=100)
	X, Y = meshgrid(x, y)

	Z = zeros((len(y), len(x)))

	for i in range(0, len(x)):
		for j in range(0, len(y)):
			Z[j, i] = obj.evaluate(array(([x[i], y[j]])))
	CS = plt.contour(X, Y, Z, 6, colors='k')
	plt.clabel(CS, fontsize=9, inline=1)

	quad = model.getQuadraticModel(0)
	for i in range(0, len(x)):
		for j in range(0, len(y)):
			Z[j, i] = quad.evaluate(array(([x[i], y[j]])))
	CS = plt.contour(X, Y, Z, 6, colors='y')
	plt.clabel(CS, fontsize=9, inline=1)

	for con in theConstraints:
		for i in range(0, len(x)):
			for j in range(0, len(y)):
				Z[j, i] = con['fun'](arr([x[i], y[j]]))
		CS = plt.contour(X, Y, Z, 6, colors='b')
		plt.clabel(CS, fontsize=9, inline=1)

	ax1.add_artist(plt.Circle(model.modelCenter(), model.modelRadius, color='g', fill=False))
	ax1.scatter(model.unshifted[:, 0], model.unshifted[:, 1], s=20, c='r', marker="x", label='poised set')
	if newMin is not None:
		ax1.scatter(array((newMin[0])), array((newMin[1])), s=20, c='g', marker="x", label='poised set')
		if rho is not None:
			ax1.text(newMin[0], newMin[1], 'rho' + str(rho))
	#
	# ax1.axis([center[0] - 2 * radius, center[0] + 2 * radius, center[1] - 2 * radius, center[1] + 2 * radius])
	if model.Lambda is not None:
		lmbdaStr = "Lambdas = " + ', '.join(map(str, sorted(model.Lambda, reverse=True)))
		ax1.text(model.unshifted[0, 0], model.unshifted[0, 1], lmbdaStr)

	fig.savefig(filename)
	plt.close()

def replacePointsOutsideOfTrustRegion(model):
	for i in range(1, model.unshifted.shape[0]):
		if norm(model.unshifted[i, :] - model.modelCenter()) > model.modelRadius + 1e-4:
			model.unshifted[i, :] = model.unshifted[0, :]

model.improve()

iteration = 0
while True:
	iteration += 1

	replacePointsOutsideOfTrustRegion(model)
	if not model.improve():
		createPlot('images/iteration_' + str(iteration) + '_unableToModel.png', 'Iteration ' + str(iteration), model)
		model.multiplyRadius(0.5)
		continue

	maxLambda = max(model.LambdaConstrained) if model.consOpts.useInLambda else max(model.Lambda)
	if maxLambda > 4:
		print('not poised')
		createPlot('images/iteration_' + str(iteration) + '_improve.png', 'Iteration ' + str(iteration), model)
		model.multiplyRadius(0.5)
		continue


	quad = model.getQuadraticModel(0)
	minimumResult = minimize(quad.evaluate, jac=quad.gradient, x0=0.5 * model.modelCenter() + 0.5 * center,
						constraints=theConstraints + [{
							'type': 'ineq',
			 				'fun': lambda x: model.modelRadius - dot(x - model.modelCenter(), x - model.modelCenter()),
			 				'jac': lambda x: reshape(-2 * (x - model.modelCenter()), (1, basis.n))
						}], method='SLSQP', options={"disp": False, "maxiter": 1000}, tol=tol)
	trialPoint = minimumResult.x
	newVal, called = model.computeValueFromDelegate(trialPoint)
	oldVal = obj.evaluate(model.modelCenter())
	oldValM = quad.evaluate(model.modelCenter())

	rho = (oldVal - newVal) / (oldValM - quad.evaluate(trialPoint))

	createPlot('images/iteration_' + str(iteration) + '_new_point.png', 'Iteration ' + str(iteration), model, trialPoint, rho)

	print('rho', rho)
	if rho < .5:
		print('decreasing radius')
		model.multiplyRadius(0.5)
		continue


	delta = norm(model.modelCenter() - trialPoint)
	if delta < model.modelRadius / 4:
		if delta < tol:
			print('delta less than tolerance')
			break
		print('decreasing radius')
		model.multiplyRadius(.5)
		continue

	print('new function value:' + str(newVal))
	if minimumResult.success:
		model.setNewModelCenter(trialPoint)

print(model.functionEvaluations)