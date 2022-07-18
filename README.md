# CREST
Connectome Reconstruction and Exploration Simple Tool, or CREST, is a simple GUI tool that enables users to (1) proofread biological objects and (2) identify individual network pathways, connections and cell types of interest, in the Neuroglancer interface.
 

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

CREST can then be launched by the following command: python3 ./CREST_v0.15.py
 

# Proofreading in CREST - Downloading required databases

To proofread in CREST, it is necessary to download an SQL database that supports proofreading of the particular agglomeration and dataset that you wish to proofread.

At present the following proofreading databases are available for download:

h01 dataset, agg20200916c3 agglomeration: 

https://storage.googleapis.com/lichtman-goog/Alex/agg20200916c3_crest_proofreading_database.db 

(files may be large and take several hours to download, depending on the size of the dataset)
 
# Proofreading in CREST - Launching a session

Once the CREST user interface has launched, the user should take the following steps to launch a CREST proofreading session:

(1) Click the 'Select Agglomeration Database' button to select a downloaded agglomeration database

(2) Click the 'Select Save Folder' to select a folder where the files for each proofread object will be saved

(3) Enter 'Cell Structures', separated by commas, that you may wish to correct in each object - for example; axon, dendrite and cell body

(4) Enter 'End Point Types', separated by commas, that you may wish to use - these would be reasons why you would stop proofreading a particular branch of an object - for example; exit volume, artefact, and natural end

(5) Optionally, enter a maximum number of base segments that should be added to the biological object from one agglomerated segment

(6) A CREST proofreading session can then be launched with one of three buttons, depending on what is desired:

'Proofread Batch of Cells from List' - to select a .json format list of base or agglomeration segment IDs that you wish to proofread

'Proofread Single Cell from ID' - to proofread a single cell by entering its ID into CREST

'Proofread Single Cell from file' - to proofread a particular locally-saved version of a cell, for example, one that was previously proofread to completion but which now requires revision

If a specific local file is not specified, CREST will search for the most recent proofread version of each cell identified for proofreading, both locally in associated cloud-based storage. If the most recent file found for a cell is in the cloud-based storage, this will be downloaded to the selected local save folder.

Where no pre-existing file is found, CREST will create one locally for each cell that is to be proofread, before any cell is proofread.

Once a file is present locally for all cells that are to be proofread, CREST will open a link displaying the first cell to be proofread, in your default browser (chrome is reccomended for your default browser choice).

Upon first ever use of the CREST proofreader on a given machine, you will be required to log in to neuroglancer with a google account and refresh the page.

# Proofreading in CREST - Principles

A biological object / cell is considered proofread when all of its constituent base segments are selected, and no base segments that do not belong to it are selected.

CREST ensures that all of the included base segments at any stage of proofreading the object, are joined to one another in one connected component (i.e. form a graph)

To facilitate efficient correction of split errors, whenever a user adds on a base segment, all base segments that belong to that base segment's parent agglomeration segment are added on simultaneously.

To facilitate efficient correction of merge errors, whenever a user removes a base segment, all base segments on the 'other side' of that base segment with respect to an 'anchor segment' (which is always displayed in blue), are removed. In other words, when a base segment is removed, if this act splits the underlying base segment graph into multiple connected components, all connected components which do not contain the anchor segment are also removed. 

When proofreading complex objects / cells, it can become difficult and fatiguing for the user to remember which branches he/she has corrected. This can lead to studying a branch that one has corrected, only to find that it is already complete, wasting time. 

To avoid this, CREST allows the user to mark all base segments on the other side of any given base segment (with respect to the anchor segment), in a given colour. In other words, to mark all of a neurite branch and its sub-branches downstream of any given point, in colour. This provides a quick visual confirmation of which branhes of the cell are complete and do not need to be revisited. 

Additionally, the colour to be used corresponds to a specific 'cell structure' specified by the user in the CREST GUI (see section 'Proofreading in CREST - Launching a session'). This has the added benefit of recording which cell structure (e.g. axon, dendrite, cell body) each base segment belongs to, and the running count of each category, including 'unknown' base segments, which are shown in grey, is displayed in the bottom left of the neuroglancer interface.

When proofreading to the end of a branch of a cell, the user may wish to record, with a point, why it has become necessary to stop proofreading. CREST allows points to be marked in any of the categories specified as 'End Point Types' (see section 'Proofreading in CREST - Launching a session').

# Proofreading in CREST - User commands

Right click: change location

Mouse wheel: scroll through EM panels or zoom in/out of 3D panel

Double left click: add or remove a base segment (see 'Principles' above for more details)

Alt + left click: mark a branch and its sub-branches in colour and as members of a specified cell structure

C: change the selected colour and corresponding cell structure to mark branches as (displayed in bottom left of screen)

Control + left click: mark the end of a branch with a specific End Point Type, or mark a base segment merger

P: change the selected End Point Type (including a category to mark base segment mergers)

Shift + right click: select a new 'Anchor segment'

# Proofreading in CREST - Saving a cell

Once a cell is complete, the user should click the button 'Save Locally and to Cloud and Finish'. This will save a date and time-stamped json file with the base segments, their cell structure categories, the marked points, underlying base segment graph, and added graph edges, to the users local computer, as well as to a specific cloud storage site associated with this dataset. 

This ensures that all members of teh proofreading community can benefit from the proofreading efforts of one another, whiel preventing anyone's particular proofread version of a cell from overwriting another user's version.

The cell can also be saved locally before complete, by clicking the button 'Save Locally and Continue'. This will not save the file to the cloud but only locally. This allows an incomplete cell to be continued at a later date.



# Network Exploration in CREST - Downloading required databases

To explore neural networks in CREST, it is necessary to download an SQL database that supports browsing of the particular synapse assembly and dataset that you wish to explore.

At present the following network exploration databases are available for download:

h01 dataset, goog14r0s5c3_spinecorrected synapse assembly: 

https://storage.cloud.google.com/lichtman-goog/Alex/sqlite_databases/CREST_browsing_database_goog14r0s5c3_spinecorrected_july2022.db

(files may be large and take several hours to download, depending on the size of the dataset)

# Network Exploration in CREST - Downloading required databases
