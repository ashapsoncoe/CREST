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

To proofread in CREST, it is necessary to download an SQL database that supports proofreading of the particular agglomeration and dataset that you wish to proofread.

At present the following proofreading databases are available for download:

h01 dataset, agg20200916c3 agglomeration: 

https://storage.googleapis.com/lichtman-goog/Alex/agg20200916c3_crest_proofreading_database.db 

(files may be large and take several hours to download, depending on the size of the dataset)
 
# Launching a proofreading session in CREST

Once the CREST user interface has launched, the user should take the following steps to launch a CREST proofreading session:

(1) Click the 'Select Agglomeration Database' button to select a downloaded agglomeration database

(2) Click the 'Select Save Folder' to select a folder where the files for each proofread object will be saved

(3) Enter 'Cell Structures' that you may wish to correct in each object - for example; axon, dendrite and cell body

(4) Enter 'End Point Types' that you may wish to use - these would be reasons why you would stop proofreading a particular branch of an object - for example; exit volume, artefact, and natural end

(5) Optionally, enter a maximum number of base segments that should be added to the biological object from one agglomerated segment

(6) A CREST proofreading session can then be launched with one of three buttons, depending on what is desired:

'Proofread Batch of Cells from List' - to select a .json format list of base or agglomeration segment IDs that you wish to proofread

'Proofread Single Cell from ID' - to proofread a single cell by entering its ID into CREST

'Proofread Single Cell from file' - to proofread a particular locally-saved version of a cell, for example, one that was previously proofread to completion but which now requires revision

If a specific local file is not specified, CREST will search for the most recent proofread version of each cell identified for proofreading, both locally in associated cloud-based storage. If the most recent file found for a cell is in the cloud-based storage, this will be downloaded to the selected local save folder.

Where no pre-existing file is found, CREST will create one locally for each cell that is to be proofread, before any cell is proofread.

Once a file is present locally for all cells that are to be proofread, CREST will open a link displaying the first cell to be proofread, in your default browser (chrome is reccomended for your default browser choice).

Upon first ever use of the CREST proofreader on a given machine, you will be required to log in to neuroglancer with a google account and refresh the page.

# Proofreading in CREST - principles

A biological object / cell is considered proofread when all of its constituent base segments are selected, and no base segments that do not belong to it are selected.

To facilitate efficient proofreading, whenever a user adds on a base segment
