
from numpy import random
from oct2py import octave
from octave.pyfovec import dfovec
from numpy import asarray
from octave.python_octave_utils import addOctaveToPath
from octave.python_octave_utils import bounds
from octave.python_octave_utils import arraysMatch

addOctaveToPath()

error = False
while not error:
	nprob = random.randint(1, 22)

	n = random.randint(2, 15)
	m = random.randint(2, 15)

	if nprob in bounds:
		bound = bounds[nprob]
		if 'n' in bound and n < bound['n']:
			n = bound['n']
		if 'm' in bound and m < bound['m']:
			m = bound['m']
		if 'm-from-n' in bound:
			m = bound['m-from-n'](n)
		if 'm>=n' in bound and m < n:
			m = n

	xdim = random.randint(n, 2 * n)
	x = 5 * (2 * random.rand(xdim) - 1)

	# zero is special,  and doesn't happen often with random numbers, so adding it here sometimes...
	if random.rand() < .3:
		x[random.randint(xdim)] = 0

	expected = asarray(octave.dfovec(m, n, x, nprob).T).flatten()
	actual = dfovec(m, n, x, nprob)
	tol = .0001
	if arraysMatch(expected, actual):
		continue

	error = True
	print('\t##########################################')
	print('\tnprob = ' + str(nprob))
	print('\tm = ' + str(m))
	print('\tn = ' + str(n))
	print('\tx = ' + str(x))
	print('\t##########################################')
	print('\t#expected = asarray(' + str(expected) + ')')
	print('\t#actual = asarry(' + str(actual) + ')')

if error:
	print('failed')
else:
	print('success')
