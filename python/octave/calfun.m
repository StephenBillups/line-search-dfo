function y = calfun(x)
%     This is a Matlab version of the subroutine calfun.f
%     This subroutine returns a function value as used in:
%
%     Benchmarking Derivative-Free Optimization Algorithms
%     Jorge J. More' and Stefan M. Wild
%     SIAM J. Optimization, Vol. 20 (1), pp.172-191, 2009.
%
%     The latest version of this subroutine is always available at
%     http://www.mcs.anl.gov/~more/dfo/
%     The authors would appreciate feedback and experiences from numerical
%     studies conducted using this subroutine.
%
%     The subroutine returns the function value f(x)
%
%       x is an input array of length n.
%       f is an output that contains the function value at x.
%
%     The rand generator should be seeded before this is called
%
%     Additional problem descriptors are passed through the global
%     variables:
%       m a positive integer (length of output from dfovec).
%          m must not exceed n.
%       nprob is a positive integer that defines the number of the problem.
%          nprob must not exceed 22.
%       probtype is a string specifying the type of problem desired:
%           'smooth' corresponds to smooth problems
%           'nondiff' corresponds to piecewise-smooth problems
%           'wild3' corresponds to deterministically noisy problems
%           'noisy3' corresponds to stochastically noisy problems
%
%     To store the evaluation history, additional variables are passed 
%     through global variables. These may be commented out if a user 
%     desires. They are:
%       nfev is a non-negative integer containing the number of function 
%          evaluations done so far (nfev=0 is a good default).
%          after calling calfun, nfev will be incremented by one.
%       np is a counter for the test problem number. np=1 is a good
%          default if only a single problem/run will be done.
%       fvals is a matrix containing the history of function
%          values, the entry fvals(nfev+1,np) being updated here.
%
%     Argonne National Laboratory
%     Jorge More' and Stefan Wild. January 2008.

global m nprob probtype fvals nfev np

n = size(x,1); % Problem dimension

% Restrict domain for some nondiff problems
xc = x;
if strcmp('nondiff',probtype)
    if nprob==8 || nprob==9 || nprob==13 || nprob==16 || nprob==17 || nprob==18
        xc = max(x,0);
    end
end

% Generate the vector
fvec = dfovec(m,n,xc,nprob); 

% Calculate the function value
switch probtype
    case 'noisy3'
        sigma=10^-3;
        u = sigma*(-ones(m,1)+2*rand(m,1));
        fvec = fvec.*(1+u);
        y = sum(fvec.^2);
    case 'wild3'
        sigma=10^-3;
        phi = 0.9*sin(100*norm(x,1))*cos(100*norm(x,inf)) + 0.1*cos(norm(x,2));
        phi = phi*(4*phi^2 -3);
        y = (1 + sigma*phi)*sum(fvec.^2);
    case 'smooth'
        y = sum(fvec.^2);
    case 'nondiff'
        y = sum(abs(fvec));
end

% Update the function value history
nfev = nfev +1;
fvals(nfev,np) = y;

%if y>1e64
%  display('Function value exceeds 10^64')
%end
