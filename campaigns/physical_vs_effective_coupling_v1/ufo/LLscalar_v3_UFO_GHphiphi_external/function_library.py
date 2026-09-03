# This file is part of the UFO.
#
# This file contains definitions for functions that
# are extensions of the cmath library, and correspond
# either to functions that are in cmath, but inconvenient
# to access from there (e.g. z.conjugate()),
# or functions that are simply not defined.
#
#

__date__ = "22 July 2010"
__author__ = "claude.duhr@durham.ac.uk"

import cmath
from object_library import all_functions, Function

#
# shortcuts for functions from cmath
#

complexconjugate = Function(name = 'complexconjugate',
                            arguments = ('z',),
                            expression = 'z.conjugate()')


re = Function(name = 're',
              arguments = ('z',),
              expression = 'z.real')

im = Function(name = 'im',
              arguments = ('z',),
              expression = 'z.imag')

# New functions (trigonometric)

sec = Function(name = 'sec',
             arguments = ('z',),
             expression = '1./cmath.cos(z.real)')

asec = Function(name = 'asec',
             arguments = ('z',),
             expression = 'cmath.acos(1./(z.real))')

csc = Function(name = 'csc',
             arguments = ('z',),
             expression = '1./cmath.sin(z.real)')

acsc = Function(name = 'acsc',
             arguments = ('z',),
             expression = 'cmath.asin(1./(z.real))')

cot = Function(name = 'cot',
               arguments = ('z',),
               expression = '1./cmath.tan(z.real)')

# Heaviside theta function

theta_function = Function(name = 'theta_function',
             arguments = ('x','y','z'),
             expression = 'y if x else z')

# Auxiliary functions for NLO

cond = Function(name = 'cond',
                arguments = ('condition','ExprTrue','ExprFalse'),
                expression = '(ExprTrue if condition==0.0 else ExprFalse)')

reglog = Function(name = 'reglog',
                arguments = ('z'),
                expression = '(0.0 if z==0.0 else cmath.log(z.real))')
                
                
## Needed by the form factor
funcfb = Function(name = 'funcfb',
             arguments = ('beta',),
             expression = '(-1.0/(4.0))*(cmath.log((cmath.sqrt(1.0-beta.real)+1.0)/(1.0-cmath.sqrt(1.0-beta.real))-1j*3.141592653589793)**2) if (beta.real<1.0) else cmath.asin(1/cmath.sqrt(beta.real))**2')

c0_function = Function(name = 'c0_function',
             arguments = ('ss','tau'),
             expression = '(1.0/(2.0*ss)*(cmath.log((cmath.sqrt(1.0-(1.0/tau))+1.0)/(1.0-cmath.sqrt(1.0-(1.0/tau))))-1j*3.141592653589793)**2) if (tau.real>=1.0 and ss.real>0.0) else (-(2.0/ss)*cmath.asin(cmath.sqrt(tau))**2)')

## gives a small number if something is zero
regfunction = Function(name = 'regfunction',
             arguments = ('ss',),
             expression = '0.00000000001 if ss.real==0.0 else ss')


funcFf = Function(name = 'funcFf',
             arguments = ('beta',),
             expression = '-2*beta.real*(1+(1-beta.real)*(-1.0/(4.0))*(cmath.log((cmath.sqrt(1.0-beta.real)+1.0)/(1.0-cmath.sqrt(1.0-beta.real))-1j*3.141592653589793)**2)) if (beta.real<1.0) else -2*beta.real*(1+(1-beta.real)*cmath.asin(1/cmath.sqrt(beta.real))**2)')

funcFW = Function(name = 'funcFW',
             arguments = ('beta',),
             expression = '2 + 3*beta.real + 3*beta.real*(2-beta.real)*(-1.0/(4.0))*(cmath.log((cmath.sqrt(1.0-beta.real)+1.0)/(1.0-cmath.sqrt(1.0-beta.real))-1j*3.141592653589793)**2) if (beta.real<1.0) else 2 + 3*beta.real + 3*beta.real*(2-beta.real)*cmath.asin(1/cmath.sqrt(beta.real))**2')


