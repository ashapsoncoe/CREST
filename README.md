# CREST
Connectome Reconstruction and Exploration Simple Tool, or CREST, is a simple GUI tool that enables users to (1) proofread biological objects and (2) identify individual connection and cell types of interest, in the Neuroglancer interface.

# Installing CREST - Windows

For Windows, no installation is necessary - CREST is available as a standalone executable file, which can be downloaded from this repository. 

# Installing CREST - Mac

For Mac, CREST can only currently be run as a python file from the command line. 

To get set up quickly, it is recommended that Anaconda 3.9.7 is installed, and the following command lines entered in an Anaconda environment:

pip install neuroglancer==2.22

pip install scipy==1.7.3

pip install matplotlib==3.5.1 / 3.2.1

pip install cairocffi==1.3.0

pip install pycairo==1.20.1

conda install -c conda-forge python-igraph

# Getting started with proofreading in CREST

To proofread in CREST, it is necessary to download an SQL database that supports proofreading of the particulart agglomeration and dataset that you wish to proofread.

At present the following proofreading databases are available for download:

h01 dataset, agg20200916c3 agglomeration: 

https://storage.googleapis.com/lichtman-goog/Alex/agg20200916c3_crest_proofreading_database.db 

(files may be large and take several hours to download, depending on the size of the dataset)

Once the CREST user interface has launched, 
