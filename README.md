# CREST
Connectome Reconstruction and Exploration Simple Tool, or CREST, is a simple GUI tool that enables users to (1) proofread biological objects and (2) identify individual network pathways, connections and cell types of interest, in the Neuroglancer interface.

CREST is written in Python and makes extensive use of the Neuroglancer Python API.

# Installing CREST - Windows

[Demonstration of downloading CREST and databases](https://www.youtube.com/watch?v=xErVpJKY0F0&list=PLQ7HdIJG6wbKhAweb_M409OComyPntaWb&index=1)

For Windows, no installation is necessary - CREST is available as a standalone executable file, which can be downloaded from here: 

https://storage.cloud.google.com/h01_paper_public_files/CREST_v0.23.exe

[Demonstration of Launching CREST](https://www.youtube.com/watch?v=fHkkmbcDXfU&list=PLQ7HdIJG6wbKhAweb_M409OComyPntaWb&index=2)
 
# Installing CREST - Mac

CREST is not yet available as an application for Mac. Advanced users may run the python CREST_v0.23.py script above on Mac systems, but this has not been extensively tested.


# Network Exploration in CREST - Downloading required databases

To explore neural networks in CREST, it is necessary to download an SQL database that supports browsing of the particular synapse assembly and dataset that you wish to explore.

At present the following network exploration databases are available for download:

h01 dataset, goog14r0s5c3_eirepredict2023 synapse assembly: 

[https://storage.cloud.google.com/crest_program/CREST_browsing_database_goog14r0s5c3_eirepredict2023.db](https://storage.cloud.google.com/h01_paper_public_files/CREST_browsing_database_goog14r0s5c3_eirepredict2023.db)

(files may be large and take several hours to download, depending on the size of the dataset)

# Network Exploration in CREST - Selecting synapse and cell types

[Demonstration of filtering synapse types in CREST](https://www.youtube.com/watch?v=qZw64zrV6R8&list=PLQ7HdIJG6wbKhAweb_M409OComyPntaWb&index=3)

Once the CREST user interface has launched, the user should take the following steps to launch a CREST network exploration session:

- (1) Click the 'Select Synaptic Database' button to select a downloaded synapse assembly database. This will populate the Cell Types, Brain Regions and Synaptic Inclusion Criteria columns.
- (2) Each synapse in the dataset will have an excitatory/inhibitory type, a pre-synaptic structure (mostly axonal) and a post-synaptic structure (mostly dendritic). The user must decide what he/she wants to consider as a legitimate synapse for the purposes of exploring the dataset, and select the individual criteria in each of these three categories under the 'Synaptic Inclusion Criteria' columns. If none are selected, then all will be considered to have been selected in each category.
- (3) Every biological object in the dataset will have a cell type (which may include neurite fragments), as well as a brain region (for example, a cortical layer). The user must then indicate which objects they want to include in their subsequent query, by selecting desired types and regions under the 'Cell Types' and 'Brain Regions' columns. If none are selected, then all will be considered to have been selected in both cases.

# Network Exploration in CREST - Launching a Network Path Exploration session

[Demonstration of Path Exploration mode in CREST](https://www.youtube.com/watch?v=qZw64zrV6R8&list=PLQ7HdIJG6wbKhAweb_M409OComyPntaWb&index=4)

The Network Path Exploration mode allows the user to generate a connectome formed only of the biological objects meeting the criteria specified under the 'Cell Types' and 'Brain Regions' columns, and only of the synapses between these objects meeting the criteria specified under the 'Synaptic Inclusion Criteria' columns.

Additionally, the user may further refine the connectome generated, by specifying two further criteria:

- Min Synapses Per Connection: Where a connection is all of the synapses between a pair of cells, only connections of at least the number of synapses specified will be included in the connectome.
- Min Path Length From Displayed Cells: Only cells giving rise to an outgoing path of at least this length will be displayed in neuroglancer. The underlying connectome will not be affected by this setting. This enables the user to identify paths of a certain minimum length.

Once these settings have been set, the user should click the button 'Start Network Path Exploration', upon which CREST will generate the connectome meeting the criteria set above. 

CREST will then open a neuroglancer link in your default browser (chrome is recommended for your default browser choice) displaying all the cells giving rise to a path of at least the length specified by the 'Min Path Length From Displayed Cells' value. If the user wishes to see all of the cells included in the generated connectome, they can set this value to 1.

Upon first ever use of CREST on a given machine, you will be required to log in to neuroglancer with a google account and refresh the page.

# Network Exploration in CREST - Network Path Exploration commands

Network Path Exploration has two main modes for exploring the connections from any given cell:

ALT + LEFT CLICK on a given cell:
- This will allow the user to browse all outgoing and incoming connections from the cell, over multiple generations
- LEFT arrow key will display the pre-synaptic inputs to the selected cell, and if pressed again their inputs, and so on.
- RIGHT arrow key will display the post-synaptic outputs from the selected cell, and if pressed again their outputs, and so on. 
- When two generations are shown, synapses linking them will be automatically shown as point annotations
- When one post- or pre-synaptic generation is shown, the user can press the DOWN arrow key to view all individual paths from the initially selected cell to this generation. 
- RIGHT and LEFT will now allow the user to look at each individual path in turn. UP will return to moving through generations rather than individual paths.
- For each individual path, synapses will be shown as point annotations, with synapses that 'skip' generations indicated by the label 'ff' and those that form connections in the opposite direction to the path indicated by the label 'fb'.
- Upon identifying an individual path of interest, the user can press the DOWN arrow key to view each cell member of the path one at a time, in order, navigating again with the RIGHT and LEFT arrow keys. UP now returns the user to moving through individual paths rather than members of the given path.

SHIFT + LEFT CLICK on a given cell:
- This will show all individual paths of at least the length specified by the 'Min Path Length From Displayed Cells' value, originating from the selected cell
- The RIGHT and LEFT arrow keys allow the user to navigate between individual paths. 
- Upon identifying an individual path of interest, the user can press the DOWN arrow key to view each cell member of the path one at a time, in order, navigating again with the RIGHT and LEFT arrow keys. UP now returns the user to moving through individual paths rather than members of the given path.

In each of these modes, the part of the connectome being explored is continuously plotted in a simplified 2D form in the 'Figures' tab of the CREST GUI. Each cell is represented by a circle, connections between them are represented by arrows, with the thickness of the arrow proportional to the number of synapses (strength) of that connection. The initial cell selected is shown as an orange circle, and each circle has a number indicating its post-synaptic (positive numbers) or pre-synaptic (negative numbers) generation with respect to the initially selected cell. Cells and connections currently being displayed in the neuroglancer window are shown in black, with their segment ID displayed next to them, whereas those cells and connections not currently displayed are greyed out.

The key C will reset the session.

# Network Exploration in CREST - Launching a Sequential Cell Exploration session

[Demonstration of Single cell connections exploration mode in CREST](https://www.youtube.com/watch?v=qZw64zrV6R8&list=PLQ7HdIJG6wbKhAweb_M409OComyPntaWb&index=5)

The Sequential Cell Exploration mode allows the user to select all cells / biological objects meeting the region and type criteria specified (see 'Network Exploration in CREST - Selecting synapse and cell types'), as well as several additional criteria related to the pre-synaptic and post-synaptic connectivity of the cell:

- Min Total Synapses Given - only cells making at least this many outgoing synapses in total will be included
- Min Total Synapses Received - only cells receiving at least this many incoming synapses in total will be included
- Min Synapses To At Least One Partner - only cells making at least this many synapses with at least one post-synaptic partner will be included
- Min Synapses From At Least One Partner - only cells receiving at least this many synapses with at least one pre-synaptic partner will be included

Note that these criteria will make use of counts of synapses, which in turn are determined by what the user wishes to include as a 'legitimate synapse' through the Synaptic Inclusion Criteria (see 'Network Exploration in CREST - Selecting synapse and cell types').

For any cell to be included, it must meet each one of these connectivity criteria, as well as the Cell Type and Brain Region criteria specified under these columns.

Once all the criteria are set to the user's satisfaction, he/she should click the button 'Explore Connections of Cells Meeting Specified Criteria', upon which CREST will identify all cells / biological objects meeting these criteria and open a neuroglancer link in your default browser (chrome is recommended for your default browser choice) showing the first of these cells (the order is random). Note: Upon first ever use of CREST on a given machine, you will be required to log in to neuroglancer with a google account and refresh the page.

Alternatively, the user may disregard the Cell Type, Brain Region and Connectivity criteria and explore the connections of a single cell, specified by its segment ID, by clicking the 'Explore Single Cell's Connections From Cell ID' button. Note that the incoming and outgoing synapses displayed for this cell will only be those considered 'legitimate' according to the user-specified 'Synaptic Inclusion Criteria'.

# Network Exploration in CREST - Sequential Cell Exploration commands

CREST will display the first cell meeting the specified criteria, as well as its pre-synaptic and post-synaptic partners with connection strength greater than or equal to the value specified by the Min Synapses From/To At Least One Partner criteria.

- RIGHT arrow key: will show the next cell meeting the criteria
- LEFT arrow key: will show the previous cell meeting the criteria
- P: Toggles whether pre- or post-synaptic partners will be explored by pressing the DOWN arrow key
- DOWN arrow key: will show all the pre-synaptic or post-synaptic partners of a particular connection strength, with RIGHT and LEFT arrow keys then allowing the user to increase or decrease the strength of the connections displayed, and DOWN arrow key then allows viewing individual partners at this connection strength
- UP arrow key: returns from viewing individual partners of a given connection strength to all partners of a given connection strength, and thereafter to all partners of the cell in question
- DOUBLE LEFT CLICK: Add an agglomerated segment to the cell in question, or one of its partners. This is a limited form of proofreading that facilitates the discovery of further connections between the cell and partner in question. Note that the colour of the added agglomerated segment will be determined by which one of the 'pre segments', 'post segments' and 'selected segment' layers are selected (by right clicking on the layer desired). This ensures that the proofread pre/post partner or cell in question will be of one colour.

Synapses are automatically displayed as point annotations

For each cell meeting the specified criteria, the distribution of connection strengths among its pre- and post-synaptic partners is plotted as a pair of histograms in the 'Figures' tab of the CREST console. The upper limit of this histogram (i.e. strongest connection frequency plotted) can be set by the user by the

# Network Exploration in CREST - Saving and Reloading States

At any point in either of the Network Exploration modes described above, the state can be saved to local storage by clicking the 'Save Current State', which will allow the user to save the neuroglancer state in the format of a json file. The current figure displayed in the CREST console will also be saved.

Any saved state can subsequently be re-loaded (but only to be viewed - further navigation is not possible), along with its associated figure, by clicking the 'Load Previous State' button.

# Proofreading in CREST - Downloading required databases

To proofread in CREST, it is necessary to download an SQL database that supports proofreading of the particular agglomeration and dataset that you wish to proofread.

At present the following proofreading databases are available for download:

h01 dataset, 'c3' agglomeration: 

https://storage.cloud.google.com/h01_paper_public_files/agg20200916c3_crest_proofreading_database.db

h01 dataset, 'c2' agglomeration: 

https://storage.cloud.google.com/h01_paper_public_files/agg20201123c2_crest_proofreading_database.db

(files may be large and take several hours to download, depending on the size of the dataset)
 
# Proofreading in CREST - Launching a session

Once the CREST user interface has launched, the user should take the following steps to launch a CREST proofreading session:

- (1) Click the 'Select Agglomeration Database' button to select a downloaded agglomeration database
- (2) Click the 'Select Save Folder' to select a folder where the files for each proofread object will be saved
- (3) Enter 'Cell Structures', separated by commas, that you may wish to correct in each object - for example; axon, dendrite and cell body
- (4) Enter 'End Point Types', separated by commas, that you may wish to use - these would be reasons why you would stop proofreading a particular branch of an object for example; exit volume, artefact, and natural end 
- (5) Optionally, enter a maximum number of base segments that should be added to the biological object from one agglomerated segment
- (6) A CREST proofreading session can then be launched with one of three buttons, depending on what is desired:

'Proofread Batch of Cells from List' - to select a .json format list of base or agglomeration segment IDs that you wish to proofread. For example, if a user wished to proofread the cells with segment IDs 9263784928, 7394837267 and 73849950392, the json file should read: [9263784928, 7394837267, 73849950392].

'Proofread Single Cell from ID' - to proofread a single cell by entering its ID into CREST

'Proofread Single Cell from file' - to proofread a particular locally-saved version of a cell, for example, one that was previously proofread to completion but which now requires revision

If a specific local file is not specified, CREST will search for the most recent proofread version of each cell identified for proofreading, both locally in associated cloud-based storage. If the most recent file found for a cell is in the cloud-based storage, this will be downloaded to the selected local save folder.

Where no pre-existing file is found, CREST will create one locally for each cell that is to be proofread, before any cell is proofread.

Once a file is present locally for all cells that are to be proofread, CREST will open a link displaying the first cell to be proofread, in your default browser (chrome is recommended for your default browser choice).

Upon first ever use of the CREST proofreader on a given machine, you will be required to log in to neuroglancer with a google account and refresh the page.

# Proofreading in CREST - Principles

A biological object / cell is considered proofread when all of its constituent base segments are selected, and no base segments that do not belong to it are selected.

CREST ensures that all of the included base segments at any stage of proofreading the object, are joined to one another in one connected component (i.e. form a graph)

To facilitate efficient correction of split errors, whenever a user adds on a base segment, all base segments that belong to that base segment's parent agglomeration segment are added on simultaneously.

To facilitate efficient correction of merge errors, whenever a user removes a base segment, all base segments on the 'other side' of that base segment with respect to an 'anchor segment' (which is always displayed in blue), are removed. In other words, when a base segment is removed, if this act splits the underlying base segment graph into multiple connected components, all connected components which do not contain the anchor segment are also removed. 

When proofreading complex objects / cells, it can become difficult and fatiguing for the user to remember which branches he/she has corrected. This can lead to studying a branch that one has corrected, only to find that it is already complete, wasting time. 

To avoid this, CREST allows the user to mark all base segments on the other side of any given base segment (with respect to the anchor segment), in a given colour. In other words, to mark all of a neurite branch and its sub-branches downstream of any given point, in colour. This provides a quick visual confirmation of which branches of the cell are complete and do not need to be revisited. 

Additionally, the colour to be used corresponds to a specific 'cell structure' specified by the user in the CREST GUI (see section 'Proofreading in CREST - Launching a session'). This has the added benefit of recording which cell structure (e.g. axon, dendrite, cell body) each base segment belongs to, and the running count of each category, including 'unknown' base segments, which are shown in grey, is displayed in the bottom left of the neuroglancer interface.

When proofreading to the end of a branch of a cell, the user may wish to record, with a point, why it has become necessary to stop proofreading. CREST allows points to be marked in any of the categories specified as 'End Point Types' (see section 'Proofreading in CREST - Launching a session').

# Proofreading in CREST - User commands

- Right click: change location
- Mouse wheel: scroll through EM panels or zoom in/out of 3D panel
- Double left click: add or remove a base segment (see 'Principles' above for more details)
- Alt + left click: mark a branch and its sub-branches in colour and as members of a specified cell structure
- C: change the selected colour and corresponding cell structure to mark branches as (displayed in bottom left of screen)
- Control + left click: mark the end of a branch with a specific End Point Type, or mark a base segment merger
- P: change the selected End Point Type (including a category to mark base segment mergers)
- Shift + right click: select a new 'Anchor segment'

# Proofreading in CREST - Saving a cell

Once a cell is complete, the user should click the button 'Save Locally and to Cloud and Finish'. This will save a date and time-stamped json file with the base segments, their cell structure categories, the marked points, underlying base segment graph, and added graph edges, to the users local computer, as well as to a specific cloud storage site associated with this dataset. 

This ensures that all members of the proofreading community can benefit from the proofreading efforts of one another, while preventing anyone's particular proofread version of a cell from overwriting another user's version.

The cell can also be saved locally before complete, by clicking the button 'Save Locally and Continue'. This will not save the file to the cloud but only locally. This allows an incomplete cell to be continued at a later date.

# Source files

Python scripts used to make proofreading and network path browsing databases are available in this repository

The current CREST python script is available in this respository

The CREST standalone executable was created using pyinstaller from the CREST python script, using the spec file included in this repository
