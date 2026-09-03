from object_library import all_form_factors, FormFactor

from function_library import complexconjugate, re, im, csc, sec, acsc, asec, funcfb


GGHFF = FormFactor(name = 'GGHFF',
                 type = 'complex',
                 value = '3.0*(MT**2)/regfunction(2*P(-1,1)*P(-1,2))*(2.0 + (4.0*(MT**2) - (2*P(-1,1)*P(-1,2)))*c0_function(regfunction(2*P(-1,1)*P(-1,2)),regfunction(2*P(-1,1)*P(-1,2))/(4*MT**2))) + 3.0*(MB**2)/regfunction(2*P(-1,1)*P(-1,2))*(2.0 + (4.0*(MB**2) - regfunction(2*P(-1,1)*P(-1,2)))*c0_function(regfunction(2*P(-1,1)*P(-1,2)),regfunction(2*P(-1,1)*P(-1,2))/(4*MB**2)))')
