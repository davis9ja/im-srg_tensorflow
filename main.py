# Main program for IM-SRG(2).


# Author: Jacob Davison
# Date:   07/10/2019

# import packages, libraries, and modules
# libraries
from scipy.integrate import odeint, ode
import numpy as np
import time
import pickle
#import tensorflow as tf
#tf.enable_v2_behavior()
#print("GPU available: ",tf.test.is_gpu_available())
import tracemalloc
import os, sys
#from memory_profiler import profile
import itertools
import random
#import tensornetwork as tn
#tn.set_default_backend("tensorflow")
#sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(log_device_placement=True))
#sess.close()

# user files
# sys.path.append('C:\\Users\\davison\\Research\\exact_diagonalization\\')
from oop_imsrg.hamiltonian import *
from oop_imsrg.occupation_tensors import *
from oop_imsrg.generator import *
from oop_imsrg.flow import *
from oop_imsrg.plot_data import *
# from oop_imsrg.display_memory import *
import oop_imsrg.ci_pairing.cipy_pairing_plus_ph as ci_matrix
from oop_imsrg.tests2B import *

# @profile
def derivative(t, y, hamiltonian, occ_tensors, generator, flow):
    """Defines the derivative to pass into ode object.

    Arguments:
    (required by scipy.integrate.ode)
    t -- points at which to solve for y
    y -- in this case, 1D array that contains E, f, G

    (additional parameters)
    hamiltonian -- Hamiltonian object
    occ_tensors -- OccupationTensors object
    generator -- Generator object
    flow -- Flow object

    Returns:

    dy -- next step in flow"""

    assert isinstance(hamiltonian, Hamiltonian), "Arg 2 must be Hamiltonian object"
    assert isinstance(occ_tensors, OccupationTensors), "Arg 3 must be OccupationTensors object"
    assert isinstance(generator, Generator), "Arg 4 must be Generator object"
    assert isinstance(flow, Flow), "Arg 5 must be a Flow object"

    E, f, G = ravel(y, hamiltonian.n_sp_states)

#    timefi = time.time()
    generator.f = f
#    timeff = time.time()

#    timegi = time.time()
    generator.G = G
#    timegf = time.time()

#    timefli = time.time()
    dE, df, dG = flow.flow(generator)
#    timeflf = time.time()

    # print("""
    # f time:     {:2.4f} s
    # G time:     {:2.4f} s
    # Flow time:  {:2.4f} s
    # """.format(timeff-timefi, timegf-timegi, timeflf-timefli))

    dy = unravel(dE, df, dG)

    return dy

# @profile
def unravel(E, f, G):
    """Transforms E, f, and G into a 1D array. Facilitates
    compatability with scipy.integrate.ode.

    Arguments:

    E, f, G -- normal-ordered pieces of Hamiltonian

    Returns:

    concatenation of tensors peeled into 1D arrays"""
    unravel_E = np.reshape(E, -1)
    unravel_f = np.reshape(f, -1)
    unravel_G = np.reshape(G, -1)

    return np.concatenate([unravel_E, unravel_f, unravel_G], axis=0)

# @profile
def ravel(y, bas_len):
    """Transforms 1D array into E, f, and G. Facilitates
    compatability with scipy.integrate.ode.

    Arugments:

    y -- 1D data array (output from unravel)
    bas_len -- length of single particle basis

    Returns:

    E, f, G -- normal-ordered pieces of Hamiltonian"""

    # bas_len = len(np.append(holes,particles))

    ravel_E = np.reshape(y[0], ())
    ravel_f = np.reshape(y[1:bas_len**2+1], (bas_len, bas_len))
    ravel_G = np.reshape(y[bas_len**2+1:bas_len**2+1+bas_len**4],
                         (bas_len, bas_len, bas_len, bas_len))
    

    return(ravel_E, ravel_f, ravel_G)

# @profile
def main(n_holes, n_particles, ref=None, d=1.0, g=0.5, pb=0.0, verbose=1):
    """Main method uses scipy.integrate.ode to solve the IMSRG(2) flow
    equations."""

    start = time.time() # start full timer

    initi = time.time() # start instantiation timer

    if ref == None:
        ha = PairingHamiltonian2B(n_holes, n_particles, d=d, g=g, pb=pb)
        ref = ha.reference # this is just for printing
    else:
        ha = PairingHamiltonian2B(n_holes, n_particles, ref=ref, d=d, g=g, pb=pb)

    ot = OccupationTensors(ha.sp_basis, ha.reference)
    wg = WegnerGenerator(ha, ot)
    fl = Flow_IMSRG2(ha, ot) 

    initf = time.time() # finish instantiation timer

    if verbose:
        print("Initialized objects in {:2.4f} seconds\n".format(initf-initi))

    if verbose:
        print("""Pairing model IM-SRG(2) flow:
        d              = {:2.4f}
        g              = {:2.4f}
        pb             = {:2.4f}
        SP basis size  = {:2d}
        n_holes        = {:2d}
        n_particles    = {:2d}
        ref            = {d}""".format(ha.d, ha.g, ha.pb, ha.n_sp_states,
                                       len(ha.holes), len(ha.particles),
                                       d=ref) )
    if verbose:
        print("Flowing...")
    flowi = time.time()

    # --- Solve the IM-SRG flow
    y0 = unravel(ha.E, ha.f, ha.G)

    solver = ode(derivative,jac=None)
    solver.set_integrator('vode', method='bdf', order=5, nsteps=500)
    solver.set_f_params(ha, ot, wg, fl)
    solver.set_initial_value(y0, 0.)

    sfinal = 50
    ds = 0.1
    s_vals = []
    E_vals = []

    iters = 0
    convergence = 0
    while solver.successful() and solver.t < sfinal:

        ys = solver.integrate(sfinal, step=True)
        Es, fs, Gs = ravel(ys, ha.n_sp_states)
        s_vals.append(solver.t)
        E_vals.append(Es)

        iters += 1
        # if iters == 176:
        #     break
        if iters %10 == 0 and verbose: print("iter: {:>6d} \t scale param: {:0.4f} \t E = {:0.8f}".format(iters, solver.t, Es))

        if len(E_vals) > 100 and abs(E_vals[-1] - E_vals[-2]) < 10**-8 and E_vals[-1] != E_vals[0]:

            if verbose: print("---- Energy converged at iter {:>06d} with energy {:1.8f}\n".format(iters,E_vals[-1]))
            convergence = 1
            break

        if len(E_vals) > 100 and abs(E_vals[-1] - E_vals[-2]) > 1:
            if verbose: print("---- Energy diverged at iter {:>06d} with energy {:3.8f}\n".format(iters,E_vals[-1]))
            break

        if iters > 20000:
            if verbose: print("---- Energy diverged at iter {:>06d} with energy {:3.8f}\n".format(iters,E_vals[-1]))
            break

        if iters % 1000 == 0 and verbose:
            print('Iteration {:>06d}'.format(iters))
    flowf = time.time()
    end = time.time()
    time_str = "{:2.5f}".format(end-start)

    if verbose: print("IM-SRG(2) converged in {:2.5f} seconds".format(flowf-flowi))

    del ha, ot, wg, fl, solver, y0, sfinal, ds
    
    return (convergence, iters, d, g, pb, n_holes+n_particles, s_vals, E_vals, time_str)
 

if __name__ == '__main__':


    #test_exact('plots_exact_2b/', main)

    main(4,4)

    #holes = int(sys.argv[1])

    # print('convergence,iters,d,g,pb,num states,GS energy,total time')
    # for num_pairs in range(1,21):
    #     #print(n)55
    #     #n = int(num_sp/2)
    #     #holes = num_pairs*2
    #     particles = num_pairs*2

    #     convergence,iters,d,g,pb,sp_states,s_vals,E_vals,time_str = main(holes, particles, verbose=0)
    #     print('{},{},{},{},{},{},{},{}'.format(convergence,iters,d,g,pb,sp_states,E_vals[-1],time_str))
    
    #     del convergence, iters, d, g, pb, sp_states, s_vals, E_vals, time_str
