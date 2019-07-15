# im-srg_tensorflow

#### PURPOSE:
The purpose of this code is to write the IM-SRG flow solution for the pairing model into the TensorFlow architecture. The motivation for this project is that the IM-SRG flow equation terms can be written as operations on tensors built from N-body interactions in the nuclear Hamiltonian. The TensorFlow library offers optimized and intuitive tools for performing tensor operations. We want to know if these methods can be used to efficiently solve the flow equations; if so, we would like to apply those methods to solve for three-body interactions.

We solve the IMSRG flow in two architectures; 1) pure TensorFlow and 2) TensorNetwork, a library that uses TensorFlow as a backend.

#### FILES:
* `testing_tensorflow_v2.ipynb`: main notebook for TensorFlow implementation
* `IMSRG_tensornetwork.ipynb`: main notebook for TensorNetwork implementation
* `oop_imsrg/`: directory for object-oriented IM-SRG
  * hamiltonian: module defines pairing Hamiltonian
  * occupation_tensors: module defines the common occupation tensors used in the flow
  * generator: module defines the generator used in the flow
  * flow: module defines the IM-SRG flow structure (uses TensorNetwork architecture)
  * main: runs the IM-SRG flow for various parameters
  * plot_data: module defines plotting function used in main
* `TODO.md`: information regarding future tasks or strategies to implement
* `README.md`: overview of project (this file)

#### SUMMARY OF `testing_tensorflow_v2.ipynb`:

__Cell 1:__
Import libraries and print TensorFlow version. This code was written in the API r1.13 (latest stable version at the time of writing).

__Cell 2:__
`def build_hamiltonian()` Build the one-body (1B) and two-body (2B) pieces of the Hamiltonian (H). The `H1B` is a rank 2 tensor (two indices), while the `H2B` is a rank 4 tensor (four indices). The pairing Hamiltonian is defined by the equation

![equation](https://latex.codecogs.com/gif.latex?%24%24H%20%3D%20%5Csum_%7BP%5Csigma%7D%5Cdelta%28P-1%29a%5E%7B%5Cdagger%7D_%7BP%5Csigma%7D%20a_%7BP%5Csigma%7D%20-%20%5Csum_%7Bpq%7D%5Cfrac%7Bg%7D%7B2%7Da%5E%7B%5Cdagger%7D_%7Bp%2C&plus;1%7Da%5E%7B%5Cdagger%7D_%7Bp%2C-1%7D%20a_%7Bq%2C-1%7Da_%7Bq%2C&plus;1%7D.%24%24).

Here we also build some useful tensors that represent occupation in the reference state. _We define our reference state as a Slater determinant with equal hole and particle states_. `occA` is a rank 4 tensor given by n_a - n_b (two dummy indices). `occB` is a rank 4 tensor given by 1 - n_a - n_b (two dummy indices). `occC` is a rank 6 tensor given by n_a n_b + (1 - n_a - n_b)n_c (three dummy indices). `occD` is a rank 4 tensor given by n_a n_b (1 - n_c - n_d) + n_a n_b n_c n_d (no dummy indices). n is a rank 1 tensor where n_a = 1 if _a_ is hole index, and n_a = 0 if _a_ is particle index.

__Cell 3:__
`def normal_order()` Normal-order the Hamiltonian and return numpy arrays that correspond to graph evaluations. The normal-ordered Hamiltonian consists of zero-, one-, and two-body pieces. `E` is a rank 0 tensor. `f` is rank 2 tensor. `G` is rank 4 tensor.

__Cell 4:__
`def white()` Disabled code for White's generator. Still in development.

__Cell 5:__
`def wegner()` Graph that calculates Wegner's generator and returns the results as numpy arrays. Find the equations in _An Advanced Course in Computational Nuclear Physics_ (Ch. 10, 2017).

__Cell 6:__
`def flow()` Graph that calculates the IM-SRG flow equations for `E`, `f`, and `G`. Returns the results as numpy arrays. Find the equations in _An Advanced Course in Computational Nuclear Physics_ (Ch. 10, 2017).

__Cell 7:__
`def derivative()` Defines the derivative function to pass into scipy.integrate.ode solver. The arguments _must_ be a dummy variable `t`, followed by a 1-D list `y` of all data to pass into the derivative and iterate. We need to shape `E`, `f`, `G` into a 1-D before passing into derivative, and then reconstruct them in order to pass into `wegner()` and `flow()`. Finally, we need to return another 0-D array. The proceeding cell defines functions for this "unraveling" and "raveling" process.

__Cell 8:__
`def unravel()` Reshape `E`, `f`, and `G` into 1-D lists and stick them together. Return the result.

`def ravel()` Reshape `y` into its original components `E`, `f`, and `G`.

__Cell 9:__
Main procedure that initializes variables and runs the scipy.integrate.ode solver. First, we build the Hamiltonian and retrieve all necessary components (1B and 2B tensors, reference state, holes, particles, and single-particle basis). Then, we construct the occupation tensors using information in the reference state. We normal order the Hamiltonian and pass the components into the scipy.integrate.ode solver, including any necessary additional arguments required by `derivative()`. The solver iterates until our scale parameter _s_ = 2, at which point the ground state energy has reached convergence.

#### SUMMARY OF `IMSRG_tensornetwork.ipynb`:

__Cell 1:__
Import libraries. We use the ncon interface, provided in TensorNetwork, for calculating tensor contractions. Print out the TensorFlow version and TensorNetwork version.

__Cell 2:__
`def build_hamiltonian()`: Here we build the pairing Hamiltonian following the same logic as in `testing_tensorflow_v2`. The difference is that we have included delta functions `delta2B()` and `deltaPB()` that decide the value of the matrix element defined by the input single particle states. The `deltaPB()` function gives us matrix elements defined by a new pair-breaking/-creating term we have introduced to couple off-diagonal blocks of the Hamiltonian (e.g. 0p-0h couples to 1p-1h, 1p-1h couples to 2p-2h). This term is written as

![equation](https://latex.codecogs.com/gif.latex?f_\text{p-break}&space;=&space;\frac{f}{2}\sum_{p'\ne&space;p,q}\left(a^\dag_{p',&plus;1}&space;a^\dag_{p,-1}a_{q,-1}a_{q,&plus;1}&space;&plus;&space;a^\dag_{q,&plus;1}a^\dag_{q,-1}a_{p,-1}a_{p',&plus;1}&space;\right).

__Cell 3:__
Functions that define occupation tensors in the same way as `testing_tensorflow_v2`.
