# Introduction
This is intended to be used to enable the use of a MATLAB script in other languages.

In this case, we use the MATLAB compiler option to compile a script to a portable format.

This usually requires MATLAB to be run on the platform it intends to run on in the future, i.e. Linux if you want to run it on Linux.

To begin, the code supplied here first creates a MATLAB script that allows for calling functions you want to expose. This is the code that should be compiled using MATLAB compiler. The idea behind this is that this acts as a gateway to your other MATLAB functions. 

TODO: Modify to current standard!