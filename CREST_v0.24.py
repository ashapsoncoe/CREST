import ctypes
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
process_array = (ctypes.c_uint8 * 1)()
num_processes = kernel32.GetConsoleProcessList(process_array, 1)
if num_processes < 3: ctypes.WinDLL('user32').ShowWindow(kernel32.GetConsoleWindow(), 0)

#import pyi_splash
import cairo
from time import time, sleep
from google.cloud import storage
from tkinter.constants import X
import neuroglancer
from requests.exceptions import ConnectionError
from numpy import array, unravel_index, argmin, mean
from webbrowser import open as wb_open
from webbrowser import open_new as wb_open_new
from json import load as json_load
from json import dump as json_dump
import sys
from os import listdir, getcwd, remove
from os.path import exists as path_exists
from os.path import dirname as path_dirname
from copy import deepcopy
from datetime import datetime
from tkinter import Frame, Tk, IntVar, filedialog, simpledialog, Checkbutton, TOP, BOTH, WORD, INSERT
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Notebook, Label, Entry, Button
from PIL import Image, ImageTk
from scipy.spatial.distance import cdist
from igraph import Graph as ig_Graph
from igraph import plot as ig_plot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from threading import Thread
from itertools import combinations
from collections import Counter
from random import choice as random_choice
from sqlite3 import connect as sqlite3_connect
from sqlite3 import DatabaseError, OperationalError
from re import escape
from func_timeout import func_timeout, FunctionTimedOut
from warnings import filterwarnings
from contextlib import suppress




class UserInterface:

    def __init__(self):

        self.set_pre_loaded_settings()
        self.dimensions = [1400, 680]
        self.viewer = neuroglancer.Viewer()

        self.added_keybindings = set()

        self.get_script_directory()
        self.get_settings_dict()
        self.user_selections = {'Cell Reconstruction': {}, 'Network Exploration': {}}
        
        current_link = str(self.viewer)
        self.window = Tk()
        self.window.title(f"CREST: Connectome Reconstruction and Exploration Simple Tool")
        self.window.geometry(f'{self.dimensions[0]}x{self.dimensions[1]}')
        self.tab_control = Notebook(self.window)

        self.tabs = {}
        self.textboxes = {}

        for tab_type, col, row, width, length, rowspan, columnspan in [('Network Exploration', 4,13,66,16,16,66), ('Cell Reconstruction',0,10,178,20,20,178), ('Figures',None,None,None,None,None,None)]:

            self.tabs[tab_type] = Frame(self.tab_control)
            self.tab_control.add(self.tabs[tab_type], text=tab_type)

            if tab_type != 'Figures':
                self.textboxes[tab_type] = ScrolledText(self.tabs[tab_type], wrap = WORD, width = width, height = length, font = ("Arial", 10))
                self.textboxes[tab_type].grid(row=row, column=col, columnspan=columnspan, rowspan=rowspan, sticky='w', padx=10)
                self.textboxes[tab_type].tag_config('error', background="yellow", foreground="red")
        
        self.link_opened = False

        for tab_name, row1, col1, row2, col2 in [('Network Exploration', 23, 0, 24, 0), ('Cell Reconstruction', 7, 0, 7, 1)]:

            Label(self.tabs[tab_name], text=f'CURRENT NEUROGLANCER LINK:').grid(row=row1, column=col1, columnspan=2, sticky='w', padx=10)
            clickable_link = Label(self.tabs[tab_name], text=str(current_link), cursor="hand2")
            clickable_link.grid(row=row2, column=col2, columnspan=2, sticky='w', padx=10, pady=10)
            clickable_link.bind("<Button-1>", self.callback)
            
        self.db_cursors = {}
        self.db_connections = {}
        self.db_paths = {}

        self.layer_type_d = {}

        self.make_labels_and_entries()
        self.make_checkbuttons()
        self.make_clickbuttons()

        self.tab_control.pack(expand=2, fill="both") 
    

    def redirector_stdout(self, inputStr):

        current_tab = self.tab_control.tab(self.tab_control.select(), "text")

        if current_tab == 'Figures':
            text_boxes_to_update = ['Network Exploration', 'Cell Reconstruction']
        else:
            text_boxes_to_update = [current_tab]
        
        for tb in text_boxes_to_update:
            self.textboxes[tb].insert(INSERT, inputStr + "\n")
            self.textboxes[tb].see("end")


    def redirector_stderr(self, inputStr):

        current_tab = self.tab_control.tab(self.tab_control.select(), "text")

        if current_tab == 'Figures':
            text_boxes_to_update = ['Network Exploration', 'Cell Reconstruction']
        else:
            text_boxes_to_update = [current_tab]
        
        for tb in text_boxes_to_update:
            self.textboxes[tb].insert(INSERT, inputStr + "\n", 'error')
            self.textboxes[tb].see("end")


    def set_pre_loaded_settings(self):

        self.pre_loaded_settings = {

            'Cell Reconstruction':   {
                'cred': 'No CREST proofreading database file selected',
                'save_dir': 'No save folder selected',
                'other_points': 'exit volume, natural, uncorrected split, bad alignment, artefact', 
                'cell_structures': 'cell body, axon, dendrite',
                'max_base_seg_add': 1000,
                #'pre_load_edges': 0,
                },
          
            'Network Exploration': {
                'cred': 'No CREST browsing database file selected', 
                'min_p_len_displayed_cells': 1,
                'min_syn_per_c': '1', 
                'max_syn_plot': '40',
                'min_syn_from': '',
                'min_syn_to': '',
                'min_syn_received_total': '', 
                'min_syn_given_total': '',     
                }   
                }

        self.field_titles = {
            'save_dir': "Directory to Load / Save", 
            'other_points': "End Point Types", 
            'cell_structures': "Cell Structures", 
            'max_base_seg_add': "Maximum Base Segs to add on", 
            'min_syn_per_c': "Min Synapses Per Connection",
            'min_p_len_displayed_cells': "Min Path Length From Displayed Cells", 
            'max_syn_plot': "Max Synapses to Plot per Partner",
            'min_syn_received_total': 'Min total synapses received',
            'min_syn_from': 'Min synapses from at least one partner',
            'min_syn_given_total': 'Min total synapses given',
            'min_syn_to': 'Min synapses to at least one partner',
            }


    def get_script_directory(self):

        self.script_directory = path_dirname(sys.argv[0])

        if self.script_directory == '':

            self.script_directory = getcwd()      # Fix for certain mac setups


    def callback(self, event):
        wb_open_new(event.widget.cget("text"))


    def get_settings_dict(self):

        if 'CREST_settings.json' in listdir(self.script_directory):

            with open(f'{self.script_directory}/CREST_settings.json', 'r') as fp:
                self.settings_dict = json_load(fp)

        else:
            self.settings_dict = {'file_completion': {}}

        for use_type in ['Cell Reconstruction', 'Network Exploration']:
            if use_type not in self.settings_dict:
                self.settings_dict[use_type] = self.pre_loaded_settings[use_type]


    def update_segments(self, segments, layer, seg_col=None): 

        with self.viewer.txn(overwrite=True) as s:
            if seg_col != None:
                s.layers[layer].segment_colors = {int(x): seg_col for x in segments}

            s.layers[layer].segments = set([int(x) for x in segments])


    def clear_all_msg(self):

        with self.viewer.config_state.txn() as s:
            
            for layer in s.status_messages:
                s.status_messages[layer] = ''


    def update_msg(self, msg, layer='status'):

        with self.viewer.config_state.txn() as s:
            s.status_messages[layer] = msg


    def change_view(self, location, css=None, ps=None):

        with self.viewer.txn(overwrite=True) as s:

            dimensions = neuroglancer.CoordinateSpace(
                scales=self.vx_sizes['em'],
                units='nm',
                names=['x', 'y', 'z']   )

            s.showSlices = False
            s.dimensions = dimensions
            s.position = array(location)

            if css != None:
                s.crossSectionScale = css
            
            if ps != None:
                s.projectionScale = ps

    
    def get_vx_sizes(self, mode):
        
        self.db_cursors[mode].execute('SELECT * FROM voxel_sizes_table')

        self.vx_sizes = {}

        for dtype, x, y, z, x_size, y_size, z_size in self.db_cursors[mode].fetchall():

            self.vx_sizes[dtype] = [x, y, z]

            if dtype == 'em':
                self.starting_location = [int(x_size/2), int(y_size/2), int(z_size/2),]


    def make_labels_and_entries(self):

        self.db_path_labels = {}
        
        for mode, row, col, colspan in (('Network Exploration', 2, 0, 2), ('Cell Reconstruction', 2, 1, 4)):

            self.db_path_labels[mode] = Label(self.tabs[mode], text='')
            self.db_path_labels[mode].grid(row=row, column=col, columnspan=colspan, sticky='w', padx=10)

            self.update_selected_db(self.settings_dict[mode]['cred'], mode)

        self.save_path_label = Label(self.tabs['Cell Reconstruction'], text='')
        self.save_path_label.grid(row=3, column=1, columnspan=4, sticky='w', padx=10)
        self.update_save_dir(self.settings_dict['Cell Reconstruction']['save_dir'])

        labels = { 
            'Cell Reconstruction': [
                [" ", None, 0, 0, 6],
                ["PROOFREADING OPTIONS:", None, 0, 1, 3],
                [" ", None, 0, 2, 6],
                [" ", None, 0, 5, 6],
                [" ", None, 0, 9, 6],
                [" ", None, 0, 6, 6],
                [" "*210, None, 0, 8, 9],
                ["MESSAGES:", None, 0, 9, 1],
                ["START PROOFREADING", None, 5, 1, 4],
                ["SAVE CURRENT CELL", None, 6, 1, 4],
                [" ", None, 5, 12, 6],
                ["End Point Type:", 'other_points', 0, 5, 4],  
                ["Cell Structures:", 'cell_structures', 0, 4, 4], 
                ["Maximum Base Segs to add on:", 'max_base_seg_add', 0, 6, 1],
                ],

            'Network Exploration': [
                ["CELL TYPES:                               ", None, 2, 1, 1],
                ["BRAIN REGIONS:                            ", None, 3, 1, 1],
                ["SYNAPTIC INCLUSION CRITERIA:", None, 4, 1, 1],
                ["Pre-synaptic structures          ", None, 4, 2, 1],
                ["Post-synaptic structures         ", None, 5, 2, 1],
                ["Synapse types                    ", None, 6, 2, 1],
                [" ", None, 0, 0, 4],
                ["SYNAPTIC DATABASE SELECTION:", None, 0, 1, 4],
                ["-"*95, None, 4, 12, 3],
                ["MESSAGES:         ", None, 4, 13, 3],
                [" ", None, 0, 4, 1],
                ["NETWORK PATHS EXPLORATION OPTIONS:", None, 0, 5, 2],
                ["Min Synapses Per Connection",'min_syn_per_c', 0, 6, 1],
                ["Min Path Length From Displayed Cells", 'min_p_len_displayed_cells', 0, 7, 1],
                #["Max Cell Pair Path Search Length", 'max_p_len', 4, 4, 1],
                ["                 ", None, 0, 9, 2],
                ["SEQUENTIAL CELL EXPLORATION OPTIONS:", None, 0, 10, 2],
                ["Max Synapses to Plot per Partner",'max_syn_plot', 0, 11, 1],
                ['Min Total Synapses Given','min_syn_given_total', 0, 12, 1],
                ['Min Synapses To At Least One Partner','min_syn_to', 0, 13, 1],
                [" ", None, 0, 18, 1],
                ["----------------------------------------------------------------------------", None, 0, 19, 2],
                [" ", None, 0, 22, 1],
                ['Min Total Synapses Received','min_syn_received_total', 0, 14, 1],
                ['Min Synapses From At Least One Partner','min_syn_from', 0, 15, 1],
                ]
            }


        for tab_type in labels.keys():

            for label, dkey, col, row, colspan in labels[tab_type]:

                if label != None:
                    if dkey == None:
                        text_colspan = colspan
                    else:
                        text_colspan = 1

                    Label(self.tabs[tab_type], text=label).grid(
                        row=row, column=col, sticky='w', padx=10, pady=2, columnspan = text_colspan)
                
                if dkey == None: continue

                self.user_selections[tab_type][dkey] = Entry(self.tabs[tab_type])

                self.user_selections[tab_type][dkey].grid(row=row, column=col+1, padx=10, sticky='ew', columnspan=colspan)

                val_from_settings = self.settings_dict[tab_type][dkey]

                self.user_selections[tab_type][dkey].insert(0, val_from_settings)


    def make_checkbuttons(self):

        checkbutton_data = {
            'Cell Reconstruction': [
                #['Pre-load Next Segments', 'pre_load_edges', 5, 8],  
                ],
            'Network Exploration': [
                #['Directed Cell Pair Path Search', 'dir_p_only', 4, 5],
                #['Use True Locations for Plotting','true_loc_plot', 4, 5],
                ]
            }


        for tab_key in checkbutton_data.keys():

            if tab_key == 'Cell Reconstruction':
                colspan = 1

            if tab_key == 'Network Exploration':
                colspan = 2
            
            for label, d_key, col, row in checkbutton_data[tab_key]:

                associated_f = None

                self.user_selections[tab_key][d_key] = IntVar(value=self.settings_dict[tab_key][d_key])

                self.user_selections[tab_key][f'{d_key}_sel'] = Checkbutton( 
                        self.tabs[tab_key], 
                        text = label,
                        variable=self.user_selections[tab_key][d_key], 
                        onvalue=1, 
                        offvalue=0,
                        command = associated_f         )

                self.user_selections[tab_key][f'{d_key}_sel'].grid(
                    row = row, column=col, sticky='w', padx=10, columnspan=colspan)


    def make_clickbuttons(self):
        
        button_labels = {
            'Cell Reconstruction':[
                ["Select Agglomeration Database", 'choose_agglo_db', 0, 2, 1],
                ["Select Save Folder", 'choose_save_dir', 0, 3, 1],
                ["Proofread Batch of Cells from List", 'pr_batch_seg', 5, 2, 1],
                ["Proofread Single Cell from Segment ID", 'load_n_from_seg_id', 5, 3, 1], ###
                ["Proofread Single Cell from File", 'load_single_n_for_pr', 5, 4, 1],
                ["Save Locally and Continue", 'save_and_continue', 6, 2, 1],
                ["Save Locally and to Cloud and Finish", 'save_and_next', 6, 3, 1],
                ["Skip Current Cell", 'skip_seg_pr', 6, 4, 1],
                ],
            'Network Exploration': [
                ["Load Previous State", 'prev_sess', 0, 20, 2],
                ["Save Current State", 'save_sess', 0, 21, 2],
                ["Start Network Path Exploration",'np_start', 0, 8, 2],
                ["Explore Connections of Cells Meeting Specified Criteria", 'new_ss_start', 0, 16, 2],
                ["Explore Single Cell's Connections from Segment ID", 'browse_from_seg_id', 0, 17, 2], ###
                ["Select Synaptic Database", 'choose_browsing_db', 0, 3, 2],
                ]
        }


        button_functions = {

            'choose_save_dir': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.choose_save_directory, 99999999999999999, 'Cell Reconstruction'], 
                name='choose_save_dir',
                daemon=True).start(),

            'pr_batch_seg': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.seg_pr_batch_start, 99999999999999999, 'Cell Reconstruction'], 
                name='pr_batch_seg',
                daemon=True).start(),

            'load_single_n_for_pr': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.pr_single_neuron, 99999999999999999, 'Cell Reconstruction'], 
                name='load_single_n_for_pr',
                daemon=True).start(),

            'load_n_from_seg_id': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.pr_single_neuron_from_seg_id, 99999999999999999, 'Cell Reconstruction'], 
                name='load_n_from_seg_id',
                daemon=True).start(),
            
            'browse_from_seg_id': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.browse_from_seg_id, 99999999999999999, 'Network Exploration'], 
                name='browse_from_seg_id',
                daemon=True).start(),

            'skip_seg_pr': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.skip_pr, 99999999999999999, 'Cell Reconstruction'], 
                name='skip_seg_pr',
                daemon=True).start(),

            'save_and_continue': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.save_cell_seg, 99999999999999999, 'Cell Reconstruction'], 
                name='save_and_continue',
                daemon=True).start(),

            'save_and_next': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.save_cell_seg_and_next, 99999999999999999, 'Cell Reconstruction'], 
                name='save_and_next',
                daemon=True).start(),

            'prev_sess': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.open_a_state, 99999999999999999, 'Network Exploration'], 
                name='prev_sess',
                daemon=True).start(),

            'save_sess': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.save_current_state, 99999999999999999, 'Network Exploration'], 
                name='save_sess',
                daemon=True).start(),

            'choose_browsing_db': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.choose_browsing_db, 99999999999999999, 'Network Exploration'], 
                name='choose_browsing_db',
                daemon=True).start(),

            'choose_agglo_db': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.choose_proofreading_db, 99999999999999999, 'Cell Reconstruction'], 
                name='choose_agglo_db',
                daemon=True).start(),

            'np_start': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.networkp_start, 120, 'Network Exploration'], 
                name='np_start',
                daemon=True).start(),

            'new_ss_start': lambda: Thread(
                target=self.run_one_func_from_button, 
                args=[self.start_ss_session, 120, 'Network Exploration'], 
                name='new_ss_start',
                daemon=True).start(),
        }

        for tab_key in button_labels.keys():

            for lab, k, col, row, colspan in button_labels[tab_key]:

                self.user_selections[tab_key][k] = Button(    
                    self.tabs[tab_key], 
                    text=lab, 
                    command=button_functions[k]       )

                self.user_selections[tab_key][k].grid(
                    row=row, column=col, padx=10, pady=2, sticky = 'ew', columnspan=colspan)



    def run_one_func_from_button(self, func, max_wait, mode):

        self.change_all_buttons_status('disabled')

        with suppress(Exception):

            try:
                func_timeout(max_wait, func)

            except FunctionTimedOut:
                self.update_mtab('Query time exceeded 2 minutes, please resubmit a more restrictive query', mode)

                try:
                    self.db_connections[mode].interrupt()

                except:
                    pass

        self.change_all_buttons_status('normal')


    def get_segs_and_layers(self, browsing_db_cursor):  

        for dtype in self.layer_type_d.keys():
            for x in self.layer_type_d[dtype]['buttons'].keys():
                self.layer_type_d[dtype]['buttons'][x].destroy()
                self.layer_type_d[dtype]['buttons'][x].update()

        self.layer_type_d = {}

        for dtype, col, start_row in (('region', 3, 2), ('type', 2, 2), ('pre_struc_type', 4, 3), ('post_struc_type', 5, 3), ('ei_type', 6, 3)):

            if dtype == 'ei_type':
                final_list = ['excitatory', 'inhibitory', 'unknown']
            else:
                if dtype in ['region', 'type']:
                    query = f"""SELECT {dtype} FROM unique_seg_{dtype}s_table"""

                else:
                    pre_or_post = dtype.split('_')[0]
                    query = f"""SELECT {pre_or_post}_struc_type FROM unique_{pre_or_post}_structures_table"""
               
                browsing_db_cursor.execute(query)
                
                final_list = [x[0] for x in browsing_db_cursor.fetchall()]
                final_list.sort()
                
            self.layer_type_d[dtype] = {'buttons': {}, 'values': {}} 
     
            for pos, x in enumerate(final_list):
                
                row = pos+start_row
                
                self.layer_type_d[dtype]['values'][x] = IntVar(value=0)
              
                self.layer_type_d[dtype]['buttons'][x] = Checkbutton(
                    self.tabs['Network Exploration'], 
                    text=x,
                    variable=self.layer_type_d[dtype]['values'][x], 
                    onvalue=1, 
                    offvalue=0
                    )
               
                self.layer_type_d[dtype]['buttons'][x].grid(
                    row=row, column=col, sticky='w', padx=20, pady=0
                    )
               
            
    def update_btn_text(self, dtype, min_or_max):

        if self.user_selections['Network Exploration'][f'{dtype}_{min_or_max}_text'].get().strip() == '':
            return

        try:
            int(self.user_selections['Network Exploration'][f'{dtype}_{min_or_max}_text'].get().strip())

        except ValueError:
            return
        
        current_text_list = self.user_selections['Network Exploration'][f'{dtype}_btn_text'].get().strip().split(' ')

        if min_or_max == 'min':
            current_text_list[5] = self.user_selections['Network Exploration'][f'{dtype}_{min_or_max}_text'].get().strip()
        
        if min_or_max == 'max':
            current_text_list[7] = self.user_selections['Network Exploration'][f'{dtype}_{min_or_max}_text'].get().strip()

        self.user_selections['Network Exploration'][f'{dtype}_btn_text'].set(' '.join(current_text_list))


    def update_mtab(self, new_message, tab):

        self.textboxes[tab].insert(INSERT, new_message + "\n")
        self.textboxes[tab].see("end")

 
    def save_current_state(self):

        ftypes = (("json files","*.json"), ("all files","*.*"))

        selected_file = filedialog.asksaveasfilename(initialdir = "/", title = "Select file", filetypes = ftypes)

        if selected_file == '': return

        json_whole_state = self.viewer.state.to_json()

        with open(selected_file + '.json', 'w') as fp:
            json_dump(json_whole_state, fp)

        if self.explore_mode == 'sequential_segment':
            self.figure.savefig(selected_file + '_partner_profile.png')

        if self.explore_mode == 'network_path':
            img = ImageTk.getimage(self.network_img.image)
            img.save(selected_file + '_network_map.png')


    def choose_save_directory(self):

        selected_path = filedialog.askdirectory(initialdir = "/", title = "Select Folder to Save Proofread Cells")

        if selected_path == '': return

        self.update_save_dir(selected_path)


    def choose_cell_list_successfully(self):

        ftypes = (("json files","*.json"), ("all files","*.*"))

        selected_file = filedialog.askopenfilename(initialdir = "/", title = "Select list of cell segment IDs to proofread", filetypes = ftypes)

        if selected_file == '': 
            return False

        try:
            with open(selected_file, 'r') as fp:
                c = json_load(fp)

        except:
            return False

        self.cell_list_path = selected_file

        return True


    def update_save_dir(self, selected_path):

        self.save_dir = selected_path

        self.save_path_label['text'] = selected_path

        self.settings_dict['Cell Reconstruction']['save_dir'] = selected_path


    def choose_browsing_db(self):

        ftypes = (("database files","*.db"), ("all files","*.*"))

      
        selected_file = filedialog.askopenfilename(initialdir = "/", title = "Select database file", filetypes = ftypes)
    
   
        if selected_file == '': return

        self.update_selected_db(selected_file, 'Network Exploration')


    def choose_proofreading_db(self):

        ftypes = (("database files","*.db"), ("all files","*.*"))

        selected_file = filedialog.askopenfilename(initialdir = "/", title = "Select database file", filetypes = ftypes)

        if selected_file == '': return

        self.update_selected_db(selected_file, 'Cell Reconstruction')
    
    
    def update_selected_db(self, db_path, mode):

        if not 'No CREST' in db_path: 
     
            try:
                db_connection = sqlite3_connect(db_path, check_same_thread=False) 
                db_cursor = db_connection.cursor()

            except OperationalError:

                if mode == 'Network Exploration':
                    db_path = 'No CREST browsing database file selected'
                    
                if mode == 'Cell Reconstruction':
                    db_path = 'No CREST proofreading database file selected'

                self.update_mtab('Selected database could not be opened', mode)
            
            else:

                if mode == 'Network Exploration':
                   
                    self.get_segs_and_layers(db_cursor)
                  
                    # try:
                    #     self.get_segs_and_layers(db_cursor)

                    # except DatabaseError:
                    #     self.update_mtab('Selected database does not have required format', 'Network Exploration')
                    #     db_path = 'No CREST browsing database file selected'

                    # else:
                    self.db_cursors[mode] = db_cursor
                    self.db_connections[mode] = db_connection

                if mode == 'Cell Reconstruction':
                    ### Something here to test database file 
                    self.db_cursors[mode] = db_cursor
                    self.db_connections[mode] = db_connection

            self.db_paths[mode] = db_path
            self.settings_dict[mode]['cred'] = db_path
        
        if len(db_path) > 50 and mode == 'Network Exploration':
            db_path_to_display = db_path[:25] + ' ... ' + db_path[-25:]
        else:
            db_path_to_display = db_path
        
        self.db_path_labels[mode]['text'] = db_path_to_display

    
    def open_a_state(self):

        ftypes = (("json files","*.json"), ("all files","*.*"))

        selected_file = filedialog.askopenfilename(initialdir = "/", title = "Select file", filetypes = ftypes)

        if selected_file == '': return

        for ftype in ('_partner_profile.png', '_network_map.png'):

            pp_file_path = selected_file.split('.json')[0] + ftype

            if path_exists(pp_file_path):
                load = Image.open(pp_file_path)
                render = ImageTk.PhotoImage(load)
                img = Label(self.tabs['Figures'], image=render)
                img.image = render
                img.place(x=0, y=0)

        with open(selected_file, 'r') as fp:
            state_to_load = json_load(fp)

        self.viewer.set_state(state_to_load)

        wb_open(str(self.viewer))
  

    def fields_complete(self, required_info, mode, opf=[]):

        for dkey in required_info:

            curr_val = self.user_selections[mode][dkey].get()

            if curr_val == '' and dkey not in opf:

                wrong_field = self.field_titles[dkey]

                self.update_mtab(f'Field {wrong_field} is empty: Please complete it', mode)

                return False
                
            else:
                self.settings_dict[mode][dkey] = curr_val

        with open(f'{self.script_directory}/CREST_settings.json', 'w') as fp:
            json_dump(self.settings_dict, fp)

        return True


    def create_connectome_graph(self):

        self.update_mtab(f'Creating the connectome graph for path browsing', 'Network Exploration')

        self.set_sd_dict()
        
        rt_types_to_query = []
        syn_types_to_query = []

        for dtype in self.layer_type_d.keys():
            if len(self.sd[dtype]) == 0:
                self.update_mtab(f'No specific cell {dtype}s selected, all will be used', 'Network Exploration')
            else:
                if dtype in ('region', 'type'):
                    rt_types_to_query.append(dtype)
                else:
                    syn_types_to_query.append(dtype)
        
        region_type_query = self.get_syn_region_type_query_string(rt_types_to_query)
        pre_rt_query = region_type_query.replace('region', 'pre_region').replace('type', 'pre_type')[4:]
        post_rt_query = region_type_query.replace('region', 'post_region').replace('type', 'post_type')

        syn_type_query = self.get_syn_region_type_query_string(syn_types_to_query)

        query = f"""
        WITH edge_list_prelim AS (

            SELECT DISTINCT 
            pre_seg_id, 
            post_seg_id,
            SUM(pair_count) AS pair_count
            FROM edge_list_table
            WHERE 
            {pre_rt_query}
            {post_rt_query} 
            {syn_type_query}
            GROUP BY pre_seg_id, post_seg_id
            )
            SELECT DISTINCT
                CAST(pre_seg_id AS STRING), 
                CAST(post_seg_id AS STRING),
                pair_count
                FROM edge_list_prelim
                WHERE
                pair_count >= {self.min_syn}
            """
        
        
        
        try:
            self.db_cursors['Network Exploration'].execute(query)
            syn_edge_list = [(str(x[0]), str(x[1]), int(x[2])) for x in self.db_cursors['Network Exploration'].fetchall()]
        except OperationalError:
            return False
      
        # Make graph:
        self.browsing_graph = ig_Graph(directed=True)
        self.all_vertices_set = set([str(a) for b in [e[:2] for e in syn_edge_list] for a in b])
        self.all_vertices = list(self.all_vertices_set)
        self.browsing_graph.add_vertices(self.all_vertices)
        self.browsing_graph.add_edges([x[:2] for x in syn_edge_list])
        self.browsing_graph.es['weight'] = [x[2] for x in syn_edge_list]

        # Then get vertices meeting criteria for path depth of the minimum connection strength

        if self.min_path_legnth_displayed_cells == 1:
            self.segs_to_display = self.all_vertices_set
        else:
            num_nodes_reachable_at_n = self.browsing_graph.neighborhood_size(self.all_vertices, order=self.min_path_legnth_displayed_cells-1, mode='OUT', mindist=self.min_path_legnth_displayed_cells-1)
            self.segs_to_display = set([node_id for node_id, count_at_n in zip(self.all_vertices, num_nodes_reachable_at_n) if count_at_n>0])

        self.update_mtab(f'{len(self.all_vertices)} cells in total , with {len(self.segs_to_display)} giving rise to a pathway of {self.min_path_legnth_displayed_cells} cells, with at least {self.min_syn} synapses per connection', 'Network Exploration')

        if len(self.segs_to_display) == 0:
            return False
        else:
            return True


    def get_addresses(self, required_addresses, mode):

        a = ', '.join(required_addresses)

        self.db_cursors[mode].execute(f'''SELECT {a} FROM addresses_table LIMIT 1''')

        results = self.db_cursors[mode].fetchall()[0]

        return results


    def common_browse_start(self):

        self.agglo_seg, self.em = self.get_addresses(['agglo_address', 'em_address'], 'Network Exploration')
        self.get_vx_sizes('Network Exploration')

        with self.viewer.config_state.txn() as s:
            s.show_layer_panel = True


    def set_sd_dict(self):

        self.sd = {}
        syn_type_lookup = {'inhibitory': 1, 'excitatory': 2, 'unknown': 3}

        for dtype in self.layer_type_d.keys():

            self.sd[dtype] = []

            for x in self.layer_type_d[dtype]['buttons'].keys():
                if self.layer_type_d[dtype]['values'][x].get() == 1:
                    if dtype == 'ei_type':
                        self.sd[dtype].append(syn_type_lookup[x])
                    else:
                        self.sd[dtype].append(x)


    def get_region_type_query(self):

        self.set_sd_dict()
        
        types_to_query = []

        for dtype in self.layer_type_d.keys():
            if len(self.sd[dtype]) == 0:
                self.update_mtab(f'No specific cell {dtype}s selected, all will be used', 'Network Exploration')
            else:
                types_to_query.append(dtype)
        
        region_type_query = self.get_syn_region_type_query_string(types_to_query)

        return region_type_query


    def get_syn_region_type_query_string(self, types_to_query):

        if len(types_to_query) == 0: 
            region_type_query = ''

        else:

            for pos, curr_criterion in enumerate(types_to_query):

                if curr_criterion == 'ei_type':
                    q = ','.join([str(f"{x}") for x in self.sd[curr_criterion]])
                else:
                    q = ','.join([str(f"'{x}'") for x in self.sd[curr_criterion]])

                if pos == 0:
                    region_type_query = f"""AND {curr_criterion} IN ({q})"""
                else:
                    region_type_query = f"""{region_type_query} AND {curr_criterion} IN ({q})"""

        return region_type_query


    def networkp_start(self):

        if 'No CREST' in self.db_paths['Network Exploration']:
            self.update_mtab('No Synaptic Database selected', 'Network Exploration')
            return

        self.viewer.set_state({})
        self.clear_all_msg()

        # Check required fields are completed:

        required_info = ['min_p_len_displayed_cells', 'min_syn_per_c'] #,'true_loc_plot',]   

        optional_fields = [
            'min_syn_from',
            'min_syn_to',
            'min_syn_received_total', 
            'min_syn_given_total', 
        ]     
        
        if not self.fields_complete(required_info, 'Network Exploration', opf=optional_fields): return

        self.explore_mode = 'network_path'
        self.min_path_legnth_displayed_cells = int(self.user_selections['Network Exploration']['min_p_len_displayed_cells'].get().strip())
        self.min_syn = int(self.user_selections['Network Exploration']['min_syn_per_c'].get().strip())

        self.common_browse_start()

        self.network_img = Label(self.tabs['Figures'])
        self.network_img.place(x=0, y=0)

        cells_to_click = self.create_connectome_graph()

        if not cells_to_click: return

        self.set_np_keybindings()

        self.change_view(self.starting_location, css=0.22398, ps=4000)

        self.reset_np()

        #self.open_ng_link()

        #self.tab_control.select(self.tabs['Figures'])

        # Setup graph plotting:


    def add_keybindings_no_duplicates(self, dict):

        for k in dict:

            if k not in self.added_keybindings:

                self.viewer.actions.add(k, dict[k])
                self.added_keybindings.add(k)


    def set_np_keybindings(self):

        np_keybindings = {
            'clear-connections': lambda s: self.reset_np(),
            'pair-paths': self.pair_paths,
            'min-dist-paths': self.start_min_dist_paths,
            'partner-gens': self.start_partner_view,
            'inc-partner': lambda s: self.inc_partner(),
            'dec-partner': lambda s: self.dec_partner(),
            'inc-partner-individual': lambda s: self.inc_partner_individual(),
            'dec-partner-individual': lambda s: self.dec_partner_individual(),
            'review-subpaths': lambda s: self.review_subpaths('subpaths_breadth'),
            'return-to-subpaths': lambda s: self.return_to_subpaths(),
            'return-to-partners': lambda s: self.return_to_partners(),
            'inc-ind-path': lambda s: self.inc_ind_path(),
            'dec-ind-path': lambda s: self.dec_ind_path(),
            'start-individual-path-members': lambda s: self.start_individual_path_members(),
        }

        self.add_keybindings_no_duplicates(np_keybindings)
         
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.data_view['shift+mousedown0'] = 'min-dist-paths'
            s.input_event_bindings.data_view['alt+mousedown0'] = 'partner-gens'
            s.input_event_bindings.viewer['keyc'] = 'clear-connections'



    def start_min_dist_paths(self, action):

        if self.min_path_legnth_displayed_cells < 2:
            self.update_mtab('Please start browing session with a minimum path length of two to view individual paths', 'Network Exploration')
            return

        self.clear_current_synapses()

        selected_segment = self.check_selected_segment('Segmentation', action, acceptable_segs=self.all_vertices_set)

        if selected_segment == 'None': return

        self.update_msg(f'Now individual paths of length {self.min_path_legnth_displayed_cells} from segment {selected_segment}')
        self.seed_segment = selected_segment
        self.gen_num = self.min_path_legnth_displayed_cells-1
        self.path_status = 'one_gen'

        self.review_subpaths('subpaths_depth')


    def update_individual_path_view(self):

        self.update_segments(self.current_individual_path_members, 'Segmentation')
        self.clear_current_synapses()

        first_seg = self.current_individual_path_members[0]

        first_seg_gen = self.current_path.index(first_seg)+1

        if len(self.current_individual_path_members) == 1:

            self.update_msg(f'Cell {first_seg_gen} (ID {first_seg}) of path length {len(self.current_path)} displayed')
        
        else:

            second_seg = self.current_individual_path_members[1]
            second_seg_gen = self.current_path.index(second_seg)+1

            self.update_msg(f'Cell {first_seg_gen} (ID {first_seg}) and {second_seg_gen} (ID {second_seg}) of path length {len(self.current_path)} displayed')
        
            self.add_synapses_to_pairs()


    def return_to_subpaths(self):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'dec-ind-path'
            s.input_event_bindings.data_view['arrowleft'] = 'dec-ind-path'
            s.input_event_bindings.viewer['arrowright'] = 'inc-ind-path'
            s.input_event_bindings.data_view['arrowright'] = 'inc-ind-path'
            s.input_event_bindings.viewer['arrowdown'] = 'start-individual-path-members'
            s.input_event_bindings.data_view['arrowdown'] = 'start-individual-path-members'

            if self.np_mode == 'single_path_breadth':
                s.input_event_bindings.viewer['arrowup'] = 'return-to-partners'
                s.input_event_bindings.data_view['arrowup'] = 'return-to-partners'
                
            if self.np_mode == 'single_path_depth':
                s.input_event_bindings.viewer['arrowup'] = None
                s.input_event_bindings.data_view['arrowup'] = None
                

        if self.np_mode == 'single_path_breadth':
            self.update_msg(f'Key Commands: RIGHT: Next individual path, LEFT: Previous individual path, DOWN: Browse individual path members, UP: Return to browsing by pre/post generation, C: Clear all', layer='key_commands')
      
        if self.np_mode == 'single_path_depth':
            self.update_msg(f'Key Commands: RIGHT: Next individual path, LEFT: Previous individual path, DOWN: Browse individual path members, C: Clear all', layer='key_commands')
      
        self.np_mode = 'subpaths_' + self.np_mode.split('_')[-1] 

        self.update_ind_path()



    def start_individual_path_members(self):

        self.update_msg(f'Key Commands: RIGHT: Forward to next path member, LEFT: Backward to previous path member, UP: Return to exploring paths, C: Clear all', layer='key_commands')
        
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'dec-partner-individual'
            s.input_event_bindings.data_view['arrowleft'] = 'dec-partner-individual'
            s.input_event_bindings.viewer['arrowright'] = 'inc-partner-individual'
            s.input_event_bindings.data_view['arrowright'] = 'inc-partner-individual'
            s.input_event_bindings.viewer['arrowup'] = 'return-to-subpaths'
            s.input_event_bindings.data_view['arrowup'] = 'return-to-subpaths'
            s.input_event_bindings.viewer['arrowdown'] = None
            s.input_event_bindings.data_view['arrowdown'] = None

        self.np_mode = 'single_path_' + self.np_mode.split('_')[-1]

        self.current_path = self.ind_paths[self.ind_path_pos]

        assert self.seed_segment == self.current_path[0]

        if self.gen_num < 0:
            self.current_path = list(reversed(self.current_path))

        self.current_individual_path_members = [self.current_path[0]]

        self.update_individual_path_view()



    def inc_partner_individual(self):

        if len(self.current_individual_path_members) == 1:

            current_member = self.current_individual_path_members[0]

            pos_in_path = self.current_path.index(current_member)

            if pos_in_path == len(self.current_path)-1:
                return

            additional_member = self.current_path[pos_in_path+1]

            self.current_individual_path_members.append(additional_member)

        else:

            assert len(self.current_individual_path_members) == 2

            self.current_individual_path_members = [self.current_individual_path_members[1]]

        self.update_individual_path_view()



    def dec_partner_individual(self):

        if len(self.current_individual_path_members) == 1:

            current_member = self.current_individual_path_members[0]

            pos_in_path = self.current_path.index(current_member)

            if pos_in_path == 0:
                return

            additional_member = self.current_path[pos_in_path-1]

            self.current_individual_path_members = [additional_member, current_member] 

        else:

            assert len(self.current_individual_path_members) == 2

            self.current_individual_path_members = [self.current_individual_path_members[0]]

        self.update_individual_path_view()



    def reset_np(self):

        self.network_img.configure(image=None)
        self.network_img.image = None

        with self.viewer.txn(overwrite=True) as s:
            s.layers['EM aligned stack'] = neuroglancer.ImageLayer(source=self.em)
            s.layers['Segmentation'] = neuroglancer.SegmentationLayer(source=self.agglo_seg, segments=self.segs_to_display)
            s.layers['Current synapses'] = neuroglancer.AnnotationLayer()
            s.selected_layer.layer = 'Current synapses'
            s.selected_layer.visible = True
            s.layers['Current synapses'].tab = "annotations"

        self.update_msg('No cells selected: select a cell to start browsing pathways')
        self.update_msg(f'Key Commands:  ALT + L.CLICK: Select a cell to start browsing pre/post-synaptic generations from, SHIFT + L.CLICK: Select a cell to view paths of at least length {self.min_path_legnth_displayed_cells} from', layer = 'key_commands')
        self.np_mode = 'general' 
        self.show_syn_status = None
        self.pair_selection = []
        self.graph_layout = []

        self.update_plot()
           

    def clear_current_synapses(self):

        with self.viewer.txn(overwrite=True) as s:
            s.layers['Current synapses'].annotations = []
            s.selected_layer.layer = 'Current synapses'
            s.selected_layer.visible = True
            s.layers['Current synapses'].tab = "annotations"


    def check_selected_segment(self, layer, action, banned_segs = [], acceptable_segs='all'):

        if layer not in action.selectedValues: 
            return 'None'

        if  isinstance(action.selected_values.get(layer).value, neuroglancer.viewer_config_state.SegmentIdMapEntry):

            selected_segment = str(action.selected_values.get(layer).value.key)
            
        else:
            selected_segment = str(action.selected_values.get(layer).value)

        banned_segs.extend(['None', '0'])

        if selected_segment in banned_segs:
            return 'None'
        else:
            if acceptable_segs != 'all':
                if selected_segment not in acceptable_segs:
                    
                    self.update_msg(f'Segment {selected_segment} not in current graph')
                  
                    return 'None'

            return selected_segment


    def start_partner_view(self, action):

        self.clear_current_synapses()

        selected_segment = self.check_selected_segment('Segmentation', action, acceptable_segs=self.all_vertices_set)

        if selected_segment == 'None': return

        self.update_msg(f'Now browsing paths from segment {selected_segment}')
        self.update_msg(f'Key Commands: RIGHT: Forward to next outputs, LEFT: Backward to previous inputs, DOWN: Review individual paths, C: Clear all', layer='key_commands')
        self.seed_segment = selected_segment
        
        self.path_segments = {}
        self.gen_num = 0
        self.path_segments[self.gen_num] = [self.seed_segment]
        self.update_segments(self.path_segments[self.gen_num], 'Segmentation')
        self.path_status = 'one_gen'
        
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'dec-partner'
            s.input_event_bindings.data_view['arrowleft'] = 'dec-partner'
            s.input_event_bindings.viewer['arrowright'] = 'inc-partner'
            s.input_event_bindings.data_view['arrowright'] = 'inc-partner'
            s.input_event_bindings.viewer['arrowdown'] = 'review-subpaths'
            s.input_event_bindings.data_view['arrowdown'] = 'review-subpaths'

        self.np_mode = 'paths'

        self.update_plot()


    def update_plot(self):

        all_vertices = set()
        node_gen_lookup = {}

        if self.np_mode in ['paths', 'subpaths_breadth', 'subpaths_depth']:

            for gen_num in self.path_segments.keys():
                for seg_id in self.path_segments[gen_num]:
                    all_vertices.add(seg_id)
                    node_gen_lookup[seg_id] = gen_num

            self.plot_current_subgraph([self.seed_segment], all_vertices, node_gen_lookup)

        if self.np_mode == 'pairs':

            for individual_path in self.ind_paths:
                for gen_num, seg_id in enumerate(individual_path):
                    all_vertices.add(seg_id)
                    node_gen_lookup[seg_id] = gen_num

            self.plot_current_subgraph(self.pair_selection, all_vertices, node_gen_lookup)


    def get_graph_layout(self, sg, all_vertices):

        #graph_real_positions = int(self.user_selections['Network Exploration']['true_loc_plot'].get())

        graph_real_positions = 0 ###

        if graph_real_positions == 1:

            all_vertices_str = ','.join(all_vertices)

            query = f"""SELECT DISTINCT CAST(seg_id AS STRING), x, y
                        FROM segment_lookup_table
                        WHERE seg_id IN ({all_vertices_str})
                     """

            self.db_cursors['Network Exploration'].execute(query)
            
            result = self.db_cursors['Network Exploration'].fetchall()

            r_dict = {x[0]: [x[1], x[2]] for x in result}

            graph_layout = [r_dict[node['name']] for node in sg.vs]

        else:
            #graph_layout = sg.layout_auto()
            graph_layout = sg.layout_fruchterman_reingold()

        return graph_layout


    def plot_current_subgraph(self, root_nodes, all_vertices, node_gen_lookup):

        displayed_segs = set([str(x) for x in self.viewer.state.layers['Segmentation'].segments])

        sg = self.browsing_graph.subgraph(all_vertices, implementation="create_from_scratch")

        node_colours, node_lab_colours, node_labels = self.get_node_colours_and_labels(sg, displayed_segs, node_gen_lookup, root_nodes)
        edge_colours = self.get_edge_colours(sg, displayed_segs, node_gen_lookup)
        edge_weights = [x['weight'] for x in sg.es]
        
        if len(self.graph_layout) != len(all_vertices):
            self.graph_layout = self.get_graph_layout(sg, all_vertices)

        temp_save_path = f'{self.script_directory}/temp_subgraph.png'

        ig_plot(
            sg, 
            target=temp_save_path,
            margin = 100, 
            bbox=(self.dimensions[0],self.dimensions[1]), 
            edge_width = edge_weights,
            edge_color =  edge_colours,
            vertex_label = node_labels,
            vertex_label_color = node_lab_colours,
            vertex_label_dist = [0 for v in sg.vs],
            vertex_label_font = [0.1 for v in sg.vs],
            vertex_color = node_colours, 
            vertex_size = 20, 
            edge_arrow_size=1.0, 
            layout=self.graph_layout
            )

        load = Image.open(temp_save_path)
        render = ImageTk.PhotoImage(load)
        self.network_img.configure(image=render)
        self.network_img.image = render
        
        if path_exists(temp_save_path):
            remove(temp_save_path)


    def get_next_gen(self, mode):

        if mode == 'post':
            graphmode = 'OUT'
            all_prev_segs = [self.path_segments[a] for a in range(self.gen_num+1)]

        if mode == 'pre':
            graphmode = 'IN'
            all_prev_segs = [self.path_segments[-a] for a in range(abs(self.gen_num)+1)]

        all_prev_segs = [x for y in all_prev_segs for x in y]

        next_gen_segs = []

        for seg in self.path_segments[self.gen_num]:

            for l in self.browsing_graph.get_all_simple_paths(seg, cutoff=1, mode=graphmode):

                if self.all_vertices[l[1]] not in all_prev_segs:

                    next_gen_segs.append(self.all_vertices[l[1]])

        return next_gen_segs


    def update_pair_partners(self, gens_to_show):

        self.clear_current_synapses()
        segs_to_show = [self.path_segments[x] for x in gens_to_show]
        segs_to_show = [a for b in segs_to_show for a in b]

        self.update_segments(segs_to_show, 'Segmentation')

        if 'two_gen' in self.path_status:
            self.add_synapses_to_pairs()

        self.update_plot()


    def inc_partner(self):

        if self.gen_num >= 0:

            if self.path_status == 'one_gen':

                next_gen_segs = self.get_next_gen('post')

                if len(next_gen_segs) == 0: 
                    return
                else:
                    self.path_segments[self.gen_num+1] = next_gen_segs

                gens_to_show = [self.gen_num, self.gen_num+1]
                self.path_status = 'two_gen_inc'

                self.update_msg(f'Post-synaptic generations {self.gen_num} and {self.gen_num+1} displayed')
                
            else:

                if self.path_status == 'two_gen_inc':
                    self.gen_num += 1
                gens_to_show = [self.gen_num]
                self.path_status = 'one_gen'
                self.update_msg(f'Post-synaptic generation {self.gen_num} displayed')

        if self.gen_num < 0:

            if self.path_status == 'one_gen': 

                gens_to_show = [self.gen_num, self.gen_num+1]
                self.path_status = 'two_gen_inc'
                self.update_msg(f'Pre-synaptic generations {abs(self.gen_num+1)} and {abs(self.gen_num)} displayed')
                
            else:

                if self.path_status == 'two_gen_inc':
                    self.gen_num += 1
                gens_to_show = [self.gen_num]
                self.path_status = 'one_gen'
                self.update_msg(f'Pre-synaptic generation {abs(self.gen_num)} displayed')

        self.update_pair_partners(gens_to_show)


    def dec_partner(self):

        if self.gen_num <= 0:

            if self.path_status == 'one_gen':

                next_gen_segs = self.get_next_gen('pre')

                if len(next_gen_segs) == 0: 
                    return
                else:
                    self.path_segments[self.gen_num-1] = next_gen_segs

                gens_to_show = [self.gen_num, self.gen_num-1]
                self.path_status = 'two_gen_dec'
                self.update_msg(f'Pre-synaptic generations {abs(self.gen_num)} and {abs(self.gen_num-1)} displayed')

            else:
                if self.path_status == 'two_gen_dec':
                    self.gen_num -= 1
                gens_to_show = [self.gen_num]
                self.path_status = 'one_gen'
                self.update_msg(f'Pre-synaptic generation {abs(self.gen_num)} displayed')

        if self.gen_num > 0:

            if self.path_status == 'one_gen': 
                gens_to_show = [self.gen_num, self.gen_num-1]
                self.path_status = 'two_gen_dec'
                self.update_msg(f'Post-synaptic generations {self.gen_num-1} and {self.gen_num} displayed')

            else:
                if self.path_status == 'two_gen_dec':
                    self.gen_num -= 1
                gens_to_show = [self.gen_num]
                self.path_status = 'one_gen'
                self.update_msg(f'Post-synaptic generation {self.gen_num} displayed')

        self.update_pair_partners(gens_to_show)


    def get_corrected_xyz(self, xyz, adj_key, rel_to_em=False):

        result = []

        for pos, coord in enumerate(xyz):
            result.append(coord*self.vx_sizes[adj_key][pos])
            
        if rel_to_em==True:
            result = [int(result[x]/self.vx_sizes['em'][x]) for x in range(3)]

        return result


    def get_synapses_for_set_of_neurons(self, neurons, mode='Network Exploration'):

        set_of_neurons = set([str(x) for x in neurons])

        set_of_neurons_str = ','.join(set_of_neurons)

        types_to_query = [x for x in ('pre_struc_type', 'post_struc_type', 'ei_type') if len(self.sd[x])>0]

        syn_type_query = self.get_syn_region_type_query_string(types_to_query)
        
        query = f"""SELECT DISTINCT pre_seg_id, post_seg_id, x, y, z
                    FROM individual_synapses_table
                    WHERE pre_seg_id IN ({set_of_neurons_str})
                    {syn_type_query}
                 """

        self.db_cursors[mode].execute(query)
        
        result = self.db_cursors[mode].fetchall()

        result = [x for x in result if str(x[1]) in set_of_neurons]

        result = [{'pre_seg_id': x[0], 'post_seg_id': x[1], 'x': x[2], 'y': x[3], 'z': x[4]} for x in result]
        
        return result


    def add_synapses_to_pairs(self):

        if 'single_path' in self.np_mode:

            prox_type, dist_type = 'pre_seg_id', 'post_seg_id'  
            prox_segs = [self.current_individual_path_members[0]]
            distal_segs = [self.current_individual_path_members[1]]
        

        else:

            if 'two_gen' not in self.path_status: return

            if self.path_status == 'two_gen_inc':
                if self.gen_num >= 0:
                    prox_gen, dist_gen = self.gen_num, self.gen_num+1
                    prox_type, dist_type = 'pre_seg_id', 'post_seg_id'  
                else:
                    prox_gen, dist_gen = self.gen_num+1, self.gen_num
                    prox_type, dist_type = 'post_seg_id', 'pre_seg_id'

            if self.path_status == 'two_gen_dec':
                if self.gen_num <= 0:
                    prox_gen, dist_gen = self.gen_num, self.gen_num-1
                    prox_type, dist_type = 'post_seg_id', 'pre_seg_id'
                else:
                    prox_gen, dist_gen = self.gen_num-1, self.gen_num
                    prox_type, dist_type = 'pre_seg_id', 'post_seg_id'

            distal_segs = [str(x) for x in self.path_segments[dist_gen]]
            prox_segs = [str(x) for x in self.path_segments[prox_gen]]


        r = self.get_synapses_for_set_of_neurons(distal_segs+prox_segs)
        results = [x for x in r if str(x[dist_type]) in distal_segs and str(x[prox_type]) in prox_segs]

        point_annotations = []

        for pos, row in enumerate(results):
            
            pre_seg_id, post_seg_id = row['pre_seg_id'], row['post_seg_id']
            loc = [row[a] for a in ('x','y','z')]

            point = array(self.get_corrected_xyz(loc, 'syn_seg', rel_to_em=True)) 

            if prox_type == 'pre_seg_id':
                desc = f'{pre_seg_id}->{post_seg_id}'

            if prox_type == 'post_seg_id':
                desc = f'{post_seg_id}<-{pre_seg_id}'

            pid = f'{pre_seg_id}_{post_seg_id}_{pos}'

            pa = neuroglancer.PointAnnotation(id=pid, description=desc, point=point)

            point_annotations.append(pa)

        with self.viewer.txn(overwrite=True) as s:
            s.layers['Current synapses'].annotations = point_annotations
            s.selectedLayer.layer = 'Current synapses'


    def return_to_partners(self):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'dec-partner'
            s.input_event_bindings.data_view['arrowleft'] = 'dec-partner'
            s.input_event_bindings.viewer['arrowright'] = 'inc-partner'
            s.input_event_bindings.data_view['arrowright'] = 'inc-partner'
            s.input_event_bindings.viewer['arrowdown'] = 'review-subpaths'
            s.input_event_bindings.data_view['arrowdown'] = 'review-subpaths'
            s.input_event_bindings.viewer['arrowup'] = None
            s.input_event_bindings.data_view['arrowup'] = None
            
        self.ind_paths = None

        self.clear_current_synapses()

        self.update_segments(self.path_segments[self.gen_num], 'Segmentation')

        if self.gen_num > 0:
            self.update_msg(f'Post-synaptic generation {self.gen_num} displayed')
        else:
            self.update_msg(f'Pre-synaptic generation {abs(self.gen_num)} displayed')

        self.update_msg(f'Key Commands: RIGHT: Forward to next outputs, LEFT: Backward to previous inputs, DOWN: Review individual paths, C: Clear all', layer='key_commands')
      
        self.np_mode = 'paths'

        self.update_plot()


    def review_subpaths(self, mode):

        if not self.path_status:
            self.update_msg('Please first navigate to view a single pre- or post-synaptic generation to view all paths for')
            return

        if 'two_gen' in self.path_status or self.gen_num == 0:
            self.update_msg('Please first navigate to view a single pre- or post-synaptic generation to view all paths for')
            return
        
        if self.gen_num < 0:
            search_mode = 'IN'
        else:
            search_mode = 'OUT'

        target_vertex_ids = self.browsing_graph.neighborhood(self.seed_segment, order=self.gen_num, mode=search_mode, mindist=self.gen_num)

        paths = self.browsing_graph.get_all_shortest_paths(self.seed_segment, to=target_vertex_ids, mode=search_mode)

        self.ind_paths = [[self.all_vertices[x] for x in path] for path in paths]

        if mode == 'subpaths_depth':

            self.path_segments = {}

            for path in self.ind_paths:

                for pos, path_mem in enumerate(path):

                    if pos not in self.path_segments:
                        self.path_segments[pos] = []

                    self.path_segments[pos].append(path_mem)
            
            for pos in range(max(self.path_segments.keys())+1):

                earlier_members = set([a for b in [self.path_segments[x] for x in range(pos)] for a in b])
                self.path_segments[pos] = list(set([x for x in self.path_segments[pos] if not x in earlier_members]))


        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'dec-ind-path'
            s.input_event_bindings.data_view['arrowleft'] = 'dec-ind-path'
            s.input_event_bindings.viewer['arrowright'] = 'inc-ind-path'
            s.input_event_bindings.data_view['arrowright'] = 'inc-ind-path'
            s.input_event_bindings.viewer['arrowdown'] = 'start-individual-path-members'
            s.input_event_bindings.data_view['arrowdown'] = 'start-individual-path-members'

            if mode == 'subpaths_breadth':
                s.input_event_bindings.viewer['arrowup'] = 'return-to-partners'
                s.input_event_bindings.data_view['arrowup'] = 'return-to-partners'

            if mode == 'subpaths_depth':
                s.input_event_bindings.viewer['arrowup'] = None
                s.input_event_bindings.data_view['arrowup'] = None
            
        if mode == 'subpaths_breadth':
            self.update_msg(f'Key Commands: RIGHT: Next individual path, LEFT: Previous individual path, DOWN: Browse individual path members, UP: Return to browsing by pre/post generation, C: Clear all', layer='key_commands')
      
        if mode == 'subpaths_depth':
            self.update_msg(f'Key Commands: RIGHT: Next individual path, LEFT: Previous individual path, DOWN: Browse individual path members, C: Clear all', layer='key_commands')
      
        self.np_mode = mode
        self.ind_path_pos = 0
        self.update_ind_path()
        

    def update_ind_path(self):

        self.update_segments(self.ind_paths[self.ind_path_pos],'Segmentation')

        curr = self.ind_path_pos+1
        tot = len(self.ind_paths)

        if 'subpaths' in self.np_mode:

            origin = self.seed_segment
            target =  self.ind_paths[self.ind_path_pos][-1]
            
            if self.np_mode == 'subpaths_breadth':

                if self.gen_num > 0:
                    pre_or_post = 'post'
                else:
                    pre_or_post = 'pre'

                g = abs(self.gen_num)
                self.update_msg(f'Path {curr} of {tot} to {pre_or_post}-synaptic generation {g}, from segment {origin} to segment {target}')

            if self.np_mode == 'subpaths_depth':
                path_len = len(self.ind_paths[self.ind_path_pos])
                self.update_msg(f'Path {curr} of {tot} of length {path_len}, from segment {origin} to segment {target}')

        if self.np_mode == 'pairs':

            origin  = self.pair_selection[0]
            target = self.pair_selection[1]

            self.update_msg(f'Path {curr} of {tot}, from segment {origin} to segment {target}')

        self.clear_current_synapses()
        self.get_synapses_for_a_path()
        self.update_plot()


    def inc_ind_path(self):

        if self.ind_path_pos == len(self.ind_paths)-1:
            return

        else:
            self.ind_path_pos += 1
            self.update_ind_path()


    def dec_ind_path(self):

        if self.ind_path_pos == 0:
            return

        else:
            self.ind_path_pos -= 1
            self.update_ind_path()


    def get_synapses_for_a_path(self):

        if 'subpaths' in self.np_mode:

            if self.gen_num > 0:
                path_type = 'post'
            else:
                path_type = 'pre'

        if self.np_mode == 'pairs':

            if self.dir_status == 1:
                path_type = 'post'

            if self.dir_status == 0:
                path_type = 'undirected'

        r = self.get_synapses_for_set_of_neurons(self.ind_paths[self.ind_path_pos])

        normal_syn, fb_syn, ff_syn = self.sort_synapse_order(r, path_type)
    
        point_annotations = []

        for dtype, results in [['f', normal_syn], ['fb', fb_syn], ['ff', ff_syn]]:

            for pos, row in enumerate(results):

                loc = [row[a] for a in ('x', 'y', 'z')]

                point = array(self.get_corrected_xyz(loc, 'syn_seg', rel_to_em=True))

                pre_seg_id, post_seg_id = row['pre_seg_id'], row['post_seg_id']

                if dtype == 'f':
                    if path_type == 'post' or path_type == 'undirected':
                        desc = f'{pre_seg_id}->{post_seg_id}'

                    if path_type == 'pre':
                        desc = f'{post_seg_id}<-{pre_seg_id}'
 
                if dtype == 'fb':

                    if path_type == 'post' or path_type == 'undirected':
                        desc = f'{post_seg_id}<-{dtype}-{pre_seg_id}'

                    if path_type == 'pre':
                        desc = f'{pre_seg_id}-{dtype}->{post_seg_id}'
                        
                if dtype == 'ff':

                    if path_type == 'post' or path_type == 'undirected':
                        desc = f'{pre_seg_id}-{dtype}->{post_seg_id}'

                    if path_type == 'pre':
                        desc = f'{post_seg_id}<-{dtype}-{pre_seg_id}'

                pa = neuroglancer.PointAnnotation(id= f'{pre_seg_id}_{post_seg_id}_{pos}', description=desc, point=point)
                point_annotations.append(pa)
        
        with self.viewer.txn(overwrite=True) as s:
            s.layers['Current synapses'].annotations = point_annotations
            s.selectedLayer.layer = 'Current synapses'
            s.layers['Current synapses'].tab = 'Annotations' #####


    def get_node_colours_and_labels(self, sg, displayed_segs, node_gen_lookup, root_nodes):

        node_labels = []
        node_colours = []
        node_lab_colours = []

        for node in sg.vs:

            seg_id = node['name']

            gen_num = node_gen_lookup[seg_id]

            if seg_id in displayed_segs:

                lab = f'.                           {gen_num}    ID{seg_id}'

                if seg_id in root_nodes:
                    lc, nc = 'yellow', 'red'
                else:
                    lc, nc = 'lightskyblue', 'black'

            else:

                lab = gen_num

                if seg_id in root_nodes:
                    lc, nc = 'yellow', 'red'
                else:
                    lc, nc = 'black', 'grey'

            node_colours.append(nc)
            node_lab_colours.append(lc)
            node_labels.append(lab)

        return node_colours, node_lab_colours, node_labels


    def get_edge_colours(self, sg, displayed_segs, node_gen_lookup):

        edge_colours = []

        for edge in sg.es:

            source_seg_id = sg.vs[edge.source]['name']
            target_seg_id = sg.vs[edge.target]['name']

            if not (source_seg_id in displayed_segs and target_seg_id in displayed_segs):
                edge_colours.append('grey')
            
            else:

                source_gen = node_gen_lookup[source_seg_id]
                target_gen = node_gen_lookup[target_seg_id]

                if source_gen == target_gen:
                    edge_colours.append('olivedrab')

                if source_gen < target_gen:
                    edge_colours.append('black')
                
                if source_gen > target_gen:
                    edge_colours.append('red')

        return edge_colours
                    

    def sort_synapse_order(self, r, path_type):

        segment_id_list = self.ind_paths[self.ind_path_pos]

        normal_syn = []
        fb_syn = []
        ff_syn = []

        for seg_id in segment_id_list:

            for result in r:

                pre_seg_id = str(result['pre_seg_id'])
                post_seg_id = str(result['post_seg_id'])
                pre_position = segment_id_list.index(pre_seg_id)
                post_position = segment_id_list.index(post_seg_id)

                if path_type == 'pre' and post_seg_id == seg_id:

                    if post_position > pre_position:
                        fb_syn.append(result)

                    if post_position == pre_position-1:
                        normal_syn.append(result)

                    if post_position < pre_position-1:
                        ff_syn.append(result)

                if path_type == 'post' and pre_seg_id == seg_id:

                    if post_position < pre_position:
                        fb_syn.append(result)

                    if post_position == pre_position+1:
                        normal_syn.append(result)

                    if post_position > pre_position+1:
                        ff_syn.append(result)

                if path_type == 'undirected' and seg_id in (pre_seg_id, post_seg_id):

                    if abs(pre_position-post_position) == 1:
                        normal_syn.append(result)
        
        return normal_syn, fb_syn, ff_syn


    def pair_paths(self, action):

        selected_id = self.check_selected_segment('Segmentation', action, acceptable_segs=self.all_vertices_set)

        if selected_id == 'None': return

        if len(self.pair_selection) == 2:
            self.pair_selection = []

        self.pair_selection.append(selected_id)

        if len(self.pair_selection) < 2:
            self.update_msg(f'Path origin segment selected: {self.pair_selection[0]}')
            self.update_segments(self.pair_selection, 'Segmentation')
            return

        if len(self.pair_selection) == 2:

            origin = self.pair_selection[0]
            target = self.pair_selection[1]

            self.update_msg(f'Path origin segment selected: {origin}, Path destination segment selected: {target}')
            self.update_segments(self.pair_selection, 'Segmentation')
            self.update_mtab(f'Getting all paths from segment {origin} to segment {target} with path legnth {self.max_path_legnth} or less', 'Network Exploration')

            if self.dir_status == 1:
                search_mode = 'OUT'
            else:
                search_mode = 'ALL'

            res = self.browsing_graph.get_all_simple_paths(origin, to=target, cutoff=self.max_path_legnth, mode=search_mode)

            if len(res) == 0:
                self.update_msg(f'No paths found from {origin} to {target}')
                self.reset_np()
                return

            else:
                self.ind_paths = [[self.all_vertices[x] for x in y] for y in res]

                with self.viewer.config_state.txn() as s:
                    s.input_event_bindings.viewer['arrowleft'] = 'dec-ind-path'
                    s.input_event_bindings.data_view['arrowleft'] = 'dec-ind-path'
                    s.input_event_bindings.viewer['arrowright'] = 'inc-ind-path'
                    s.input_event_bindings.data_view['arrowright'] = 'inc-ind-path'

                self.update_msg(f'Key Commands: RIGHT: Next individual path, LEFT: Previous individual path, C: Clear all', layer='key_commands')
      
                self.np_mode = 'pairs'
                self.ind_path_pos = 0
                self.update_ind_path()

    def change_all_buttons_status(self, state):

        for k in self.user_selections:

            for bk in self.user_selections[k]:

                self.user_selections[k][bk].config(state = state)
                self.user_selections[k][bk].update()


    def start_ss_session(self, specific_seg_id=None):

        

        if 'No CREST' in self.db_paths['Network Exploration']:
            self.update_mtab('No Synaptic Database selected', 'Network Exploration')
            self.change_all_buttons_status('normal')
            return

        self.viewer.set_state({})
        self.clear_all_msg()

        required_info = ['max_syn_plot',]

        optional_fields = [
            'min_syn_from',
            'min_syn_to',
            'min_syn_received_total', 
            'min_syn_given_total', 
        ]

        if not self.fields_complete(required_info, 'Network Exploration', opf=optional_fields): return

        self.explore_mode = 'sequential_segment'

        self.max_plot_c = int(self.user_selections['Network Exploration']['max_syn_plot'].get().strip())
        
        self.common_browse_start()
        self.set_syn_thresholds(specific_seg_id=specific_seg_id)

        self.set_sd_dict()

        got_seg_ids = self.get_seg_ids(specific_seg_id=specific_seg_id)

        if not got_seg_ids:
            return
        
        if len(self.seg_ids) == 0:
            if specific_seg_id != None:
                self.update_mtab(f'Cell {specific_seg_id} not found, please revise', 'Network Exploration')
            else:
                self.update_mtab('No cells meet selected criteria, please revise', 'Network Exploration')
            self.change_all_buttons_status('normal')
            return
        else:
            if specific_seg_id == None:
                self.update_mtab(f'{len(self.seg_ids)} cells meeting selected criteria to view', 'Network Exploration')

        self.ss_col = {
            'pre partners': 'fuchsia',
            'post partners': 'pink',
            'selected segment': 'lawngreen',
            'pre_syn_points': 'red',
            'post_syn_points': 'orange',
        }

        self.create_ss_keybindings()
        self.create_ss_layers()
        self.create_ss_plotter()
        self.ss_mode = 'general'
        self.pre_or_post_display = 'post'
        self.change_pre_post()
        self.pos = 0
        self.main_seg = None
        self.change_view(self.starting_location, css=0.22398, ps=4000)
        self.start_all_partners_mode()
        #self.open_ng_link()

        self.change_all_buttons_status('normal')


    def change_pre_post(self):

        if self.ss_mode != 'general': return

        if self.pre_or_post_display == 'post':
            self.pre_or_post_display = 'pre'
        else:
            self.pre_or_post_display = 'post'

        with self.viewer.txn(overwrite=True) as s:
            s.selected_layer.layer = f'{self.pre_or_post_display} synapses'
            s.selected_layer.visible = True
            s.layers[f'{self.pre_or_post_display} synapses'].tab = "annotations"
        
        self.update_msg(f'Selected partners to view (Key P): {self.pre_or_post_display}-synaptic', layer='pre_or_post')


    def create_ss_keybindings(self):

        ss_keybindings_dict = {
            'add-or-remove-seg-ss': self.add_or_remove_seg_ss,
            'prev-case': lambda s: self.prev_case(),
            'next-case': lambda s: self.next_case(),
            'seg-inc': lambda s: self.inc_seg(),
            'seg-dec': lambda s: self.dec_seg(),
            'start-batch-review': lambda s: self.start_batch_review(),
            'review-subbatch': lambda s: self.review_subbatch(),
            'change-pre-post': lambda s: self.change_pre_post(),
            'update-partners': lambda s: self.start_all_partners_mode(),
            'return-to-all-partners': lambda s: self.start_all_partners_mode(use_saved_viewing_prefs=True),
        }

        self.add_keybindings_no_duplicates(ss_keybindings_dict)

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.data_view['dblclick0'] = 'add-or-remove-seg-ss'
            s.input_event_bindings.viewer['arrowleft'] = 'prev-case'
            s.input_event_bindings.data_view['arrowleft'] = 'prev-case'
            s.input_event_bindings.viewer['arrowright'] = 'next-case'
            s.input_event_bindings.data_view['arrowright'] = 'next-case'
            s.input_event_bindings.viewer['arrowdown'] = 'start-batch-review'
            s.input_event_bindings.data_view['arrowdown'] = 'start-batch-review'
            s.input_event_bindings.viewer['keyp'] = 'change-pre-post'

        self.update_msg(f'Key Commands: RIGHT: Next case, LEFT: Previous case, DOWN: Review partners by strength', layer='key_commands')


    def add_or_remove_seg_ss(self, action_state):  

        with self.viewer.txn(overwrite=True) as s:

            selected_layer = s.selectedLayer.layer 

        if not selected_layer in ['selected segment', 'pre partners', 'post partners', 'review segs']:
            return
        
        agglo_seg = self.check_selected_segment(selected_layer, action_state)

        if agglo_seg == 'None': return

        seg_list = [str(x) for x in self.viewer.state.layers[selected_layer].segments]

        if agglo_seg in seg_list:
            seg_list.remove(agglo_seg)
        else:
            seg_list.append(agglo_seg)

        if selected_layer == 'review segs':
            seg_col = self.ss_col[f'{self.pre_or_post_display} partners']
        else:
            seg_col = self.ss_col[selected_layer]
            
        self.update_segments(seg_list, selected_layer, seg_col = seg_col)


    def create_ss_layers(self):

        with self.viewer.txn(overwrite=True) as s:

            s.layers['EM aligned stack'] = neuroglancer.ImageLayer(source=self.em)
            s.layers['selected segment'] = neuroglancer.SegmentationLayer(source=self.agglo_seg)

            for dtype in ('pre', 'post'):

                s.layers[f'{dtype} partners'] = neuroglancer.SegmentationLayer( source=self.agglo_seg)
                s.layers[f'{dtype} synapses'] = neuroglancer.AnnotationLayer()

            s.layers['review segs'] = neuroglancer.SegmentationLayer(source=self.agglo_seg)
            s.layers['review segs'].visible = False
            s.layers['review syn'] = neuroglancer.AnnotationLayer()
            s.layers['review syn'].visible = False
 

    def create_ss_plotter(self):

        for item in self.tabs['Figures'].winfo_children():
            item.pack_forget()

        self.figure = Figure(dpi=100)
        self.plotter = FigureCanvasTkAgg(self.figure, master=self.tabs['Figures'])
        self.axes = {}
        self.axes['pre'] = self.figure.add_subplot(211)
        self.axes['post'] = self.figure.add_subplot(212)
        self.axes['pre'].set_yscale('log') 
        self.axes['post'].set_yscale('log') 
        self.figure.text(0.5, 0.04, 'Number of synapses', ha='center', va='center')
        self.figure.text(0.06, 0.5, 'Number of post-synaptic partners                Number of pre-synaptic partners', ha='center', va='center', rotation='vertical')
        self.plotter.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
   

    def set_syn_thresholds(self, specific_seg_id=None):

        self.syn_thresholds = {}

        sel_keys = [
            'min_syn_received_total',
            'min_syn_given_total', 
            'min_syn_from', 
            'min_syn_to',
            ]

        for k in sel_keys:

            raw_val = self.user_selections['Network Exploration'][k].get().strip()

            try:
                self.syn_thresholds[k] = int(raw_val)

            except ValueError:
                
                if 'max' in k:
                    self.syn_thresholds[k] = 1000000
                if 'min' in k:
                    self.syn_thresholds[k] = 0


        if specific_seg_id == None:

            self.update_mtab('Selecting cells with:', 'Network Exploration') 
            self.update_mtab(f"- At least {self.syn_thresholds['min_syn_received_total']} synapses received in total", 'Network Exploration')
            self.update_mtab(f"- At least {self.syn_thresholds['min_syn_given_total']} synapses made in total", 'Network Exploration')
            self.update_mtab(f"- At least one pre-synaptic partner with {self.syn_thresholds['min_syn_from']} or more synapses", 'Network Exploration')
            self.update_mtab(f"- At least one post-synaptic partner with {self.syn_thresholds['min_syn_to']} or more synapses", 'Network Exploration')


    def get_seg_ids(self, specific_seg_id=None):

        if specific_seg_id != None:

            query = f"""SELECT DISTINCT CAST(seg_id AS STRING) AS seg_id, region, type FROM segment_lookup_table WHERE seg_id = {specific_seg_id}"""

        else:

            region_type_query = self.get_region_type_query()
            
            query = f"""
                WITH selected_ids AS (
                SELECT DISTINCT seg_id, region, type
                FROM segment_lookup_table
                WHERE
                        total_out_syn >= {self.syn_thresholds['min_syn_given_total']} AND
                        greatest_post_partner >= {self.syn_thresholds['min_syn_to']} AND
                        total_in_syn >= {self.syn_thresholds['min_syn_received_total']} AND 
                        greatest_pre_partner >= {self.syn_thresholds['min_syn_from']} 
                {region_type_query}
                
                )
                
                SELECT DISTINCT 
                    CAST(seg_id AS STRING) AS seg_id, region, type
                FROM selected_ids 
                ORDER BY seg_id
                """

        try:
            self.db_cursors['Network Exploration'].execute(query)
            result = self.db_cursors['Network Exploration'].fetchall()
        except OperationalError:
            return False

        self.seg_ids = [x[0] for x in result]

        self.agglo_2_region_and_type = {x[0]: [x[1], x[2]] for x in result}

        return True

    def next_case(self):

        if self.pos == len(self.seg_ids)-1:
            return
        
        self.pos += 1
        self.start_all_partners_mode()


    def prev_case(self):

        if self.pos == 0:
            return
        
        self.pos -= 1
        self.start_all_partners_mode()


    def load_main_seg_synapses_and_partners(self):

        self.main_seg = deepcopy(self.seg_ids[self.pos])
        self.pa_dict = {}
        all_locations = []

        for mode in ('pre', 'post'):

            self.pa_dict[mode] = {}

            if mode == 'pre':
                opposite = 'post'
                range_min = self.syn_thresholds['min_syn_from']

            if mode == 'post':
                opposite = 'pre'
                range_min = self.syn_thresholds['min_syn_to']

            # Get synapse data:
            types_to_query = [x for x in ('pre_struc_type', 'post_struc_type', 'ei_type') if len(self.sd[x])>0]

            syn_type_query = self.get_syn_region_type_query_string(types_to_query)

            query = f"""
                    SELECT DISTINCT CAST({mode}_seg_id AS STRING), x, y, z 
                    FROM individual_synapses_table
                    WHERE {opposite}_seg_id = {self.main_seg}
                    {syn_type_query}
            """
          
            self.db_cursors['Network Exploration'].execute(query)
            
            all_synapses = self.db_cursors['Network Exploration'].fetchall()

            partners = [x[0] for x in all_synapses]

            partner_counts = Counter(partners)
            strength_counts = Counter(partner_counts.values())

            # Add point annotations and appropriate partners:
            partners = set([x for x in partner_counts if (partner_counts[x] >= range_min)])
            point_annos = []

            for partner in partners:

                n_syn = partner_counts[partner]

                if n_syn not in self.pa_dict[mode]:
                    self.pa_dict[mode][n_syn] = {}

                self.pa_dict[mode][n_syn][partner] = []

                synapse_locs = [x[1:] for x in all_synapses if x[0]==partner]
                all_locations.extend(synapse_locs)

                for pos, loc in enumerate(synapse_locs):

                    desc = f'{mode}-synaptic partner {partner}, synapse {pos} of {n_syn}'
                 
                    pa = neuroglancer.PointAnnotation(id=f'{partner}_{pos}', point=array(loc), description=desc)
                    
                    self.pa_dict[mode][n_syn][partner].append(pa)
                    point_annos.append(pa)

            target_layer = f'{mode} partners'
            target_syn = f'{mode} synapses'    

            if partners != set():
                self.update_segments(partners, target_layer, seg_col=self.ss_col[target_layer])
    
            with self.viewer.txn(overwrite=True) as s:
                s.layers[target_syn].annotations = point_annos
                s.layers[target_syn].annotationColor = self.ss_col[f'{mode}_syn_points']

            # Update plot:
            x_axis_data = list(range(1,self.max_plot_c+1))
            y_axis_data = [strength_counts[n] for n in x_axis_data]
            self.axes[mode].clear()
            self.axes[mode].bar(x_axis_data, y_axis_data, tick_label=x_axis_data)
            self.axes[mode].set_yscale('log')
    
        self.plotter.draw_idle()

        self.update_segments([self.main_seg], 'selected segment', self.ss_col['selected segment'])

        # Change location:
        self.change_view(mean(all_locations, axis=0))


    def start_all_partners_mode(self, use_saved_viewing_prefs=False):

        if self.seg_ids[self.pos] != self.main_seg:
            self.load_main_seg_synapses_and_partners()

        # Update message:
        seg_region, seg_type = self.agglo_2_region_and_type[self.main_seg]
        self.update_msg(f'Case {self.pos+1} of {len(self.seg_ids)}: Partners of segment {self.main_seg}, {seg_region} {seg_type}')

        # Clear any review segs and synapses:
        with self.viewer.txn(overwrite=True) as s:

            s.layers['review segs'].segments = set()
            s.layers['review segs'].visible = False

            s.layers['review syn'].annotations = []
            s.layers['review syn'].visible = False

            if self.ss_mode != 'general':
       
                for dtype in ('pre', 'post'):
                    s.layers[f'{dtype} partners'].visible = deepcopy(self.saved_viewer_prefs[f'{dtype} partners'])
                    s.layers[f'{dtype} synapses'].visible = deepcopy(self.saved_viewer_prefs[f'{dtype} synapses'])

            s.selected_layer.layer = f'{self.pre_or_post_display} synapses'
            s.selected_layer.visible = True
            s.layers[f'{self.pre_or_post_display} synapses'].tab = "annotations"
            
        # Set appropriate keybindings:
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.data_view['dblclick0'] = 'add-or-remove-seg-ss'
            s.input_event_bindings.viewer['arrowleft'] = 'prev-case'
            s.input_event_bindings.data_view['arrowleft'] = 'prev-case'
            s.input_event_bindings.viewer['arrowright'] = 'next-case'
            s.input_event_bindings.data_view['arrowright'] = 'next-case'
            s.input_event_bindings.viewer['arrowdown'] = 'start-batch-review'
            s.input_event_bindings.data_view['arrowdown'] = 'start-batch-review'
            s.input_event_bindings.viewer['arrowup'] = None
            s.input_event_bindings.data_view['arrowup'] = None
            s.input_event_bindings.viewer['keyp'] = 'change-pre-post'

        self.update_msg(f'Key Commands: RIGHT: Next case, LEFT: Previous case, DOWN: Review partners by strength', layer='key_commands')

        self.ss_mode = 'general'

    
    def start_batch_review(self):
        
        if self.ss_mode not in ['general', 'subbatch']:
            return

        with self.viewer.txn(overwrite=True) as s:
            s.selected_layer.layer = f'{self.pre_or_post_display} synapses'
            s.selected_layer.visible = True
            s.layers[f'{self.pre_or_post_display} synapses'].tab = "annotations"

        self.seg_rev_data = []

        for n in sorted(self.pa_dict[self.pre_or_post_display].keys()):

            this_n_segs = []
            this_n_locations = []

            for p in self.pa_dict[self.pre_or_post_display][n].keys():
                this_n_segs.append(p)
                this_n_locations.extend(self.pa_dict[self.pre_or_post_display][n][p])

            msg = f'P{self.pre_or_post_display[1:]}-synaptic partners with {n} synapses'

            self.seg_rev_data.append([this_n_segs, this_n_locations, msg])
        
        if self.seg_rev_data == []:
            self.update_msg(f'No {self.pre_or_post_display}-synaptic partners to view for this segment')
            return

        if self.ss_mode == 'subbatch':
            self.seg_pos = self.seg_pos_backup
        else:
            self.seg_pos = 0
        
        if self.ss_mode == 'general':

            self.saved_viewer_prefs = {}

            with self.viewer.txn(overwrite=True) as s:

                for l in ('pre partners', 'post partners', 'pre synapses', 'post synapses'):

                    self.saved_viewer_prefs[l] = deepcopy(s.layers[l].visible) 
                    s.layers[l].visible = False
            
        self.ss_mode = 'batch'

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'seg-dec'
            s.input_event_bindings.data_view['arrowleft'] = 'seg-dec'
            s.input_event_bindings.viewer['arrowright'] = 'seg-inc'
            s.input_event_bindings.data_view['arrowright'] = 'seg-inc'
            s.input_event_bindings.viewer['arrowdown'] = 'review-subbatch'
            s.input_event_bindings.data_view['arrowdown'] = 'review-subbatch'
            s.input_event_bindings.viewer['arrowup'] = 'update-partners'
            s.input_event_bindings.data_view['arrowup'] = 'update-partners'

        n_individual_partners = len(self.seg_rev_data[self.seg_pos][0])

        self.update_msg(f'Key Commands: RIGHT: Next connection strength batch, LEFT: Previous connection strength batch, UP: View all partners, DOWN: View {n_individual_partners} individual partners of this batch', layer='key_commands')

        self.update_seg_review()


    def review_subbatch(self):
        
        if self.ss_mode == 'subbatch':
            self.start_batch_review()
            return
        
        if self.ss_mode != 'batch':
            return

        n = int(self.seg_rev_data[self.seg_pos][2].split(' ')[-2])

        self.seg_rev_data = []

        for p in self.pa_dict[self.pre_or_post_display][n].keys():

            point_anns = self.pa_dict[self.pre_or_post_display][n][p]
            msg = f'P{self.pre_or_post_display[1:]}-synaptic partner {p} with {n} synapses'

            self.seg_rev_data.append([[p], point_anns, msg])
        
        self.seg_pos_backup = deepcopy(self.seg_pos)
        self.seg_pos = 0
        self.ss_mode = 'subbatch'

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['arrowleft'] = 'seg-dec'
            s.input_event_bindings.data_view['arrowleft'] = 'seg-dec'
            s.input_event_bindings.viewer['arrowright'] = 'seg-inc'
            s.input_event_bindings.data_view['arrowright'] = 'seg-inc'
            s.input_event_bindings.viewer['arrowdown'] = None
            s.input_event_bindings.data_view['arrowdown'] = None
            s.input_event_bindings.viewer['arrowup'] = 'start-batch-review'
            s.input_event_bindings.data_view['arrowup'] = 'start-batch-review'

        self.update_msg(f'Key Commands: RIGHT: Next partner, LEFT: Previous partner, UP: Review partners by strength', layer='key_commands')

        self.update_seg_review()


    def update_seg_review(self):

        segs = self.seg_rev_data[self.seg_pos][0]
        points = self.seg_rev_data[self.seg_pos][1]
        message = self.seg_rev_data[self.seg_pos][2]

        if self.ss_mode == 'batch':
            n_individual_partners = len(self.seg_rev_data[self.seg_pos][0])
            self.update_msg(f'Key Commands: RIGHT: Next connection strength batch, LEFT: Previous connection strength batch, UP: View all partners, DOWN: View {n_individual_partners} individual partners of this batch', layer='key_commands')
            self.update_msg(message)
        else:
            self.update_msg(f'{message}, {self.seg_pos+1} of {len(self.seg_rev_data)}')
        
        self.change_view([x.point for x in points][0])

        self.update_segments(segs, 'review segs', self.ss_col[f'{self.pre_or_post_display} partners'])

        with self.viewer.txn(overwrite=True) as s:

            s.layers['review segs'].visible = True
            s.layers['review syn'].visible = True
            s.selected_layer.layer = 'review syn'
            s.selected_layer.visible = True
            s.layers['review syn'].tab = "annotations"
            s.layers['review syn'].annotations = points
            s.layers['review syn'].annotationColor = 'blue'
  

    def dec_seg(self):
   
        if self.seg_pos == 0: return
        self.seg_pos += -1
        self.update_seg_review()
         

    def inc_seg(self):

        if self.seg_pos+1 == len(self.seg_rev_data): return
        self.seg_pos += 1
        self.update_seg_review()
 

    def save_cell_graph(self, file_name=None, save_to_cloud=False):
        
        cell_data = deepcopy(self.cell_data)
        cell_data['graph_nodes'] = [x['name'] for x in self.pr_graph.vs]
        cell_data['graph_edges'] = [(self.pr_graph.vs[x.source]['name'], self.pr_graph.vs[x.target]['name']) for x in self.pr_graph.es]

        # Convert sets to lists for saving in json file:
        for dtype in cell_data['base_segments'].keys():
            cell_data['base_segments'][dtype] = list(cell_data['base_segments'][dtype])
        
        cell_data['removed_base_segs'] = list(cell_data['removed_base_segs'])

        timestamp = str(datetime.now())[:-7].replace(':','.')
        main_seg_id = cell_data['metadata']['main_seg']['base']

        completion_list = list(set(cell_data['metadata']['completion']))
        completion_list.sort()
        completion_string = ','.join(completion_list).replace('_', ' ')

        if file_name == None:
         
            agg_to_save = str(self.agglo_seg)
            agg_to_save = escape(agg_to_save) # Get rid of any single backslashes

            for char in ['//', '/', '\\', ':', '_']:
                agg_to_save = agg_to_save.replace(char, '-')
            
            file_name = f'cell_graph_{main_seg_id}_{completion_string}_{agg_to_save}_{timestamp}.json'

        cell_data['metadata']['data_sources']['agglo'] = self.agglo_seg

        with open(f'{self.save_dir}/{file_name}', 'w') as fp:
            json_dump(cell_data, fp)

        if save_to_cloud == True:

            try:
                blob = self.proofread_files_bucket.blob(file_name)
                blob.upload_from_filename(f'{self.save_dir}/{file_name}')

            except ConnectionError:
                self.create_cloud_storage_client()
                blob = self.proofread_files_bucket.blob(file_name)
                blob.upload_from_filename(f'{self.save_dir}/{file_name}')

            self.update_mtab(f'Saved cell {main_seg_id} locally and to cloud', 'Cell Reconstruction')

        else:
            self.update_mtab(f'Saved cell {main_seg_id} locally', 'Cell Reconstruction')


    def update_base_locations(self, seg_list):

        seg_list = [x for x in seg_list if x not in self.cell_data['base_locations'].keys()]

        result_dict = self.get_locations_from_base_segs(seg_list)

        for r in result_dict:
            self.cell_data['base_locations'][r] = self.get_corrected_xyz(result_dict[r], 'seg')


    def add_cc_bridging_edges_pairwise(self):

        con_comms = list(self.pr_graph.clusters(mode='weak'))

        while len(con_comms) > 1:

            candidate_edges = []

            for cc1, cc2 in combinations(con_comms, 2):

                cc1_base_segs = [self.pr_graph.vs[x]['name'] for x in cc1]
                cc2_base_segs = [self.pr_graph.vs[x]['name'] for x in cc2]

                cc1_list = [x for x in cc1_base_segs if x in self.cell_data['base_locations']]
                cc2_list = [x for x in cc2_base_segs if x in self.cell_data['base_locations']]

                if cc1_list == [] or cc2_list == []:
                    continue

                sel_cc1, sel_cc2, dist = self.get_closest_dist_between_ccs(cc1_list, cc2_list)
                candidate_edges.append([sel_cc1, sel_cc2, dist])

            if candidate_edges == []: 
                return

            origin, target, dist = min(candidate_edges, key = lambda x: x[2])

            self.pr_graph.add_edges([(origin, target)])

            ### CAN REMOVE THIS BIT LATER
            if 'added_graph_edges_pre_proofreading' not in self.cell_data:
                self.cell_data['added_graph_edges_pre_proofreading'] = []
            ###
            
            self.cell_data['added_graph_edges_pre_proofreading'].append([origin, target, dist])
            self.update_mtab(f'Added an edge between segments {origin} and {target}, {dist} nm apart', 'Cell Reconstruction')

            con_comms = list(self.pr_graph.clusters(mode='weak'))


    def making_starting_cell_data(self, main_base_id):

        self.update_mtab(f'Creating starting file for {main_base_id}', 'Cell Reconstruction')

        self.cell_data = {
            'graph_edges': [],
            'graph_nodes': [],
            'base_locations': {},
            'added_graph_edges': [], 
            'selected_base_segs_to_remove': [],
            'added_graph_edges_pre_proofreading': [],
            'end_points': {},
            'base_seg_merge_points': [],
            'removed_base_segs': set(),
            'anchor_seg': str(main_base_id),
            'metadata': {   
                'main_seg' : {'agglo' : {}, 'base' : str(main_base_id)},
                'data_sources': {
                    'em' : self.em, 
                    'base': self.base_seg, 
                    'agglo': self.agglo_seg,
                    },
                'timing' : [],
                'completion' : []
                }
        }

        if type(self.cells_todo) == dict:

            if 'unknown' not in self.cells_todo[main_base_id].keys():
                self.cells_todo[main_base_id]['unknown'] = set()

            self.cell_data['base_segments'] = self.cells_todo[main_base_id]

        if type(self.cells_todo) == list:  

            self.cell_data['base_segments'] = {}

            agglo_seg = self.get_agglo_seg_of_base_seg(main_base_id)
            base_ids = self.get_base_segs_of_agglo_seg(agglo_seg)
            
            self.cell_data['base_segments']['unknown'] = set(base_ids)

            for dtype in self.selected_types:
                self.cell_data['base_segments'][dtype] = set()


    def create_pr_graph(self):

        seg_id = self.cell_data['metadata']['main_seg']['base']

        self.update_mtab(f'Creating base segment graph for cell {seg_id}', 'Cell Reconstruction')

        all_base_segs = [str(a) for b in self.cell_data['base_segments'].values() for a in b]

        self.update_base_locations(all_base_segs)

        possible_edges = []
        agglo_segs_done = set()
        base_segs_done = set()
        
        for base_seg in all_base_segs:

            if base_seg in base_segs_done: continue

            agglo_seg = self.get_agglo_seg_of_base_seg(base_seg)
            children_base_segs = self.get_base_segs_of_agglo_seg(agglo_seg)
            base_segs_done.update(children_base_segs)

            if not agglo_seg in agglo_segs_done:

                edges = self.get_edges_from_agglo_seg(agglo_seg)
                
                agglo_segs_done.add(agglo_seg)
                possible_edges.extend(edges)

        all_bs_set = set(all_base_segs)
        possible_edges = [x for x in possible_edges if x[0] in all_bs_set]
        chosen_edges = [x for x in possible_edges if x[1] in all_bs_set]

        self.pr_graph = ig_Graph(directed=False)
        self.pr_graph.add_vertices(all_base_segs)
        self.pr_graph.add_edges(chosen_edges)
        self.add_cc_bridging_edges_pairwise()
        self.attach_noloc_segs()

        assert len(self.pr_graph.clusters(mode='weak')) == 1



    def attach_noloc_segs(self):

        # For isolated segments without locations, attach to largest connected component:
        remaining_cc = list(self.pr_graph.clusters(mode='weak'))

        if len(remaining_cc) == 1: return

        if len(remaining_cc) > 1:
            no_loc_base_segs = set([x['name'] for x in self.pr_graph.vs if x['name'] not in self.cell_data['base_locations']])
            largest_cc = max(remaining_cc, key = lambda x: len(x))
            for cc in remaining_cc:
                no_loc_this_cc = cc & no_loc_base_segs
                if cc != largest_cc and no_loc_this_cc != set():
                    rand_seg1 = random_choice(list(no_loc_this_cc))
                    rand_seg2 = random_choice(list(largest_cc))
                    self.pr_graph.add_edges([(rand_seg1, rand_seg2)])
                    self.cell_data['added_graph_edges_pre_proofreading'].append([rand_seg1, rand_seg2, 'unknown'])
                    self.update_mtab(f'Added an edge between segments {rand_seg1} and {rand_seg2}', 'Cell Reconstruction')


    def get_most_recent_cell_files(self, main_seg_id, modes):

        files_to_sort = []

        if 'local' in modes:
            files_to_sort.extend([x for x in listdir(self.save_dir) if str(main_seg_id) in x])

        if 'cloud' in modes:
            this_seg_cloud_file_names = [x.name for x in self.proofread_files_bucket.list_blobs() if x.name.split('_')[2] == str(main_seg_id)]
            files_to_sort.extend(this_seg_cloud_file_names)

        dates = [(z, z.split('_')[-1]) for z in files_to_sort]
        dates.sort(reverse=True, key = lambda x: x[1])
        sorted_files = [x[0] for x in dates]
        
        return sorted_files


    def get_closest_dist_between_ccs(self, cc1_node_list, cc2_node_list):

        cc1_node_locs = [self.cell_data['base_locations'][x] for x in cc1_node_list]
        cc2_node_locs = [self.cell_data['base_locations'][x] for x in cc2_node_list]

        f = cdist(cc1_node_locs, cc2_node_locs, 'euclidean')

        min_indices = unravel_index(argmin(f, axis=None), f.shape)

        sel_cc1 = cc1_node_list[min_indices[0]]
        sel_cc2 = cc2_node_list[min_indices[1]]
        dist = int(f[min_indices])  

        return sel_cc1, sel_cc2, dist


    def add_closest_edge_to_graph(self, new_segs, seg_to_link):

        assert len(self.pr_graph.clusters(mode='weak')) == 2

        # Some segments do not have locations recorded:
        current_cell_node_list = [x['name'] for x in self.pr_graph.vs if x['name'] not in new_segs]
        current_cell_node_list = [x for x in current_cell_node_list if x in self.cell_data['base_locations']]
        
        # Then determine new segments that are acceptable as partners
        if seg_to_link in self.cell_data['base_locations'].keys():
            new_segs = [seg_to_link]
        else:
            new_segs = [x for x in new_segs if x in self.cell_data['base_locations']]

        sel_curr, sel_new, dist = self.get_closest_dist_between_ccs(current_cell_node_list, new_segs)
        
        self.pr_graph.add_edges([(sel_curr, sel_new)])
        self.cell_data['added_graph_edges'].append([sel_curr, sel_new, dist])

        assert len(self.pr_graph.clusters(mode='weak')) == 1     

        return f', linked base segments {sel_curr} and {sel_new}, {round(dist)}nm apart, '


    def resolving_seg_overlap(self):

        for p1, p2 in combinations(self.cell_data['base_segments'].keys(), 2):

            common_segments = set(self.cell_data['base_segments'][p1]) & set(self.cell_data['base_segments'][p2])

            if common_segments != set():

                self.update_mtab(f"Base segments {common_segments} are present in both {p1} and {p2} layers, moving to 'unknown'", 'Cell Reconstruction')

                for dtype in p1, p2:
                    if dtype != 'unknown':
                        self.cell_data['base_segments'][dtype] -= common_segments

                self.cell_data['base_segments']['unknown'].update(common_segments)


    def load_graph_from_celldata(self):

        self.pr_graph = ig_Graph()
        self.pr_graph.add_vertices(self.cell_data['graph_nodes'])
        self.pr_graph.add_edges(self.cell_data['graph_edges'])


    def load_cell_to_edit(self):

        main_seg_id = self.cells_todo[self.cell_pos]

        most_recent_file = self.get_most_recent_cell_files(main_seg_id, ['local'])[0]
        load_path = f'{self.save_dir}/{most_recent_file}'
        
        with open(load_path, 'r') as fp:
            self.cell_data = json_load(fp)

        # Turn lists back to sets:
        for dtype in self.cell_data['base_segments'].keys():
            correct_form = set([str(x) for x in self.cell_data['base_segments'][dtype]])
            self.cell_data['base_segments'][dtype] = correct_form

        self.cell_data['removed_base_segs'] = set(self.cell_data['removed_base_segs'])
    
        # Get the graph from edges
        self.load_graph_from_celldata()

        all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]

        # Get preloaded edges, if selected:
        if self.pre_load_edges == 1:
            self.get_new_gen_dict_entries(all_base_segs, 0)
            
        # Check for segments present in two structures:
        self.resolving_seg_overlap()

        # Record the relevant agglo ID in the metadata
        main_agglo_id = self.get_agglo_seg_of_base_seg(main_seg_id)
        self.cell_data['metadata']['main_seg']['agglo'][self.agglo_seg] = main_agglo_id
        self.start_time = time()

        self.update_mtab(f'Now starting cell {main_seg_id}, number {self.cell_pos+1} of {len(self.cells_todo)} remaining cells', 'Cell Reconstruction')


    def get_base_segs_of_agglo_seg(self, agglo_seg):

        agglo_seg = str(agglo_seg)

        query = f"""SELECT DISTINCT base_id FROM agglo_base_resolved WHERE agglo_id = {agglo_seg}"""

        self.db_cursors['Cell Reconstruction'].execute(query)
        
        base_segs = [str(x[0]) for x in self.db_cursors['Cell Reconstruction'].fetchall()]
        base_segs.append(agglo_seg)

        return base_segs


    def get_agglo_seg_of_base_seg(self, base_seg):

        base_seg = str(base_seg)

        query = f"""SELECT DISTINCT agglo_id FROM agglo_base_resolved WHERE base_id = {base_seg}"""

        self.db_cursors['Cell Reconstruction'].execute(query)
        
        agglo_segs = [str(x[0]) for x in self.db_cursors['Cell Reconstruction'].fetchall()]

        assert len(agglo_segs) <= 1

        if agglo_segs == []:
            return base_seg
        else:
            return agglo_segs[0]


    def get_edges_from_agglo_seg(self, agglo_seg):

        agglo_seg = str(agglo_seg)

        query = f"""SELECT DISTINCT label_a, label_b FROM agglo_to_edges WHERE agglo_id = {agglo_seg}"""

        self.db_cursors['Cell Reconstruction'].execute(query)
        
        edges = [(str(x[0]), str(x[1])) for x in self.db_cursors['Cell Reconstruction'].fetchall()]

        return edges


    def get_locations_from_base_segs(self, base_segs, batch_size = 1000):

        results = {}

        if len(base_segs) > 0:
        
            num_batches = int(len(base_segs)/batch_size)
            
            for batch in range(num_batches+1):

                q = ','.join([str(x) for x in base_segs[batch*batch_size:(batch+1)*batch_size]])
                
                query = f"""SELECT DISTINCT seg_id, x, y, z FROM base_location WHERE seg_id IN ({q})"""

                self.db_cursors['Cell Reconstruction'].execute(query)
                
                this_batch = {str(x[0]): (int(x[1]), int(x[2]), int(x[3])) for x in self.db_cursors['Cell Reconstruction'].fetchall()}

                results.update(this_batch)

        return results


    def set_base_seg_merger_layer(self):

        self.point_types.append('Base Segment Merger')

        with self.viewer.txn(overwrite=True) as s:

            s.layers['Base Segment Merger'] = neuroglancer.AnnotationLayer()
            s.layers['Base Segment Merger'].filterBySegmentation = ["segments"]
            s.layers['Base Segment Merger'].linkedSegmentationLayer = {"segments": 'base_segs'}
            s.layers['Base Segment Merger'].annotationColor = '#ffa500'
            s.layers['Base Segment Merger'].tool = "annotatePoint"

            for pos, point in enumerate(self.cell_data['base_seg_merge_points']):

                point_array = array([int(point[x]/self.vx_sizes['em'][x]) for x in range(3)])
                pa = neuroglancer.PointAnnotation(id=f'bm_{pos}', point = point_array, segments=[[point[3]]])
                s.layers['Base Segment Merger'].annotations.append(pa)


    def set_endpoint_annotation_layers(self): 

        self.point_types = list(set(self.point_types + list(self.cell_data['end_points'].keys())))
        self.point_types = [x for x in self.point_types if not ('base' in x.lower() and 'merge' in x.lower())]

        with self.viewer.txn(overwrite=True) as s:

            for point_type in self.point_types:

                s.layers[point_type] = neuroglancer.AnnotationLayer()
                s.layers[point_type].annotationColor = '#ffffff'
                s.layers[point_type].tool = "annotatePoint"
                s.layers[point_type].tab = 'Annotations'

                # If data already exists for this point type:
                if point_type in self.cell_data['end_points'].keys():

                    for pos, point in enumerate(self.cell_data['end_points'][point_type]):
                        
                        point_array = array([int(point[x]/self.vx_sizes['em'][x]) for x in range(3)])
                        point_id = f'{point_type}_{pos}'
                        pa = neuroglancer.PointAnnotation(id=point_id, point = point_array)
                        s.layers[point_type].annotations.append(pa)


    def set_endpoint_annotation_layers(self): 

        self.point_types = list(set(self.point_types + list(self.cell_data['end_points'].keys())))
        self.point_types = [x for x in self.point_types if not ('base' in x.lower() and 'merge' in x.lower())]

        with self.viewer.txn(overwrite=True) as s:

            for point_type in self.point_types:

                s.layers[point_type] = neuroglancer.AnnotationLayer()
                s.layers[point_type].annotationColor = '#ffffff'
                s.layers[point_type].tool = "annotatePoint"
                s.layers[point_type].tab = 'Annotations'

                # If data already exists for this point type:
                if point_type in self.cell_data['end_points'].keys():

                    for pos, point in enumerate(self.cell_data['end_points'][point_type]):

                        point_array = array([int(point[x]/self.vx_sizes['em'][x]) for x in range(3)])
                        point_id = f'{point_type}_{pos}'
                        
                        if len(point)==3: # then there is no segment ID associated with the annotation point
                        
                            pa = neuroglancer.PointAnnotation(id=point_id, point = point_array)

                        if len(point)==4: # then include the segment ID with the annotation point

                            segment_id = point[3]
                            pa = neuroglancer.PointAnnotation(id=point_id, point = point_array, segments = [[segment_id]])
                        
                        s.layers[point_type].annotations.append(pa)


    def next_cell(self):

        if self.cell_pos == len(self.cells_todo)-1:
            self.update_mtab('You have completed the final cell of this batch', 'Cell Reconstruction')
            return
        
        else:
            self.cell_pos += 1
            self.load_cell_to_edit()
            self.start_new_cell_seg_pr()


    def pr_single_neuron(self):

        selected_file_path = filedialog.askopenfilename(
                                initialdir = "/",
                                title = "Select file",
                                filetypes = (
                                    ("json files","*.json"),
                                    ("all files","*.*")
                                    )
                                )

        if selected_file_path == '': return

        self.seg_pr_batch_start(specific_file=selected_file_path)


    def pr_single_neuron_from_seg_id(self):

        new_window = Tk()
        new_window.withdraw()
        selected_seg_id = simpledialog.askstring(title="Enter Segment ID", prompt="Segment ID", parent=new_window)
        new_window.destroy()

        try:
            selected_seg_id = int(selected_seg_id)

        except (ValueError, TypeError):
            return

        self.seg_pr_batch_start(specific_seg_id=selected_seg_id)


    def browse_from_seg_id(self):

        new_window = Tk()
        new_window.withdraw()
        selected_seg_id = simpledialog.askstring(title="Enter Segment ID", prompt="Segment ID", parent=new_window)
        new_window.destroy()

        try:
            selected_seg_id = int(selected_seg_id)

        except ValueError:
            return

        self.start_ss_session(specific_seg_id=selected_seg_id)


    def most_recent_file_complete(self, main_seg_id, sources_to_check):

        most_recent_files = self.get_most_recent_cell_files(main_seg_id, sources_to_check)

        if most_recent_files == []:
            return False

        f = most_recent_files[0]

        completed_structures_this_file = f.split('_')[3].split(',')

        self.settings_dict['file_completion'][f] = completed_structures_this_file

        if set(self.selected_types).issubset(set(completed_structures_this_file)):
            return True
        else:
            return False


    def add_new_base_segs_from_new_agglo(self, seg_id):
                    
        parent_agglo_seg = self.get_agglo_seg_of_base_seg(seg_id) 
        new_agglo_base_ids = set(self.get_base_segs_of_agglo_seg(parent_agglo_seg))
        all_current_segs = set([a for b in self.cell_data['base_segments'].values() for a in b])
        new_unknown_segs = new_agglo_base_ids - all_current_segs
        self.cell_data['base_segments']['unknown'].extend(list(new_unknown_segs))
        self.update_mtab(f'Added {len(new_unknown_segs)} new base segments from updated agglomeration {self.agglo_seg}', 'Cell Reconstruction')
        

    def ensure_all_cells_have_graphs(self, specific_file, specific_seg_id):
  
        self.cells_todo_d = {}

        # If a specific file is provided, set that to be the only item in the todo list:
        if specific_file != None:

            file_name = specific_file.split('/')[-1]
            seg_id = file_name.split('_')[2]
            self.cells_todo = [seg_id]
            self.save_dir = specific_file[:-len(file_name)]

        else:
            if specific_seg_id != None:
                self.cells_todo = [specific_seg_id]
            else:
                with open(self.cell_list_path, 'r') as fp:
                    self.cells_todo = json_load(fp)

        # Ensure input data is in correct format:
        assert type(self.cells_todo) in [dict, list]

        if type(self.cells_todo) == list:
            self.cells_todo = [str(x) for x in self.cells_todo]
            
        if type(self.cells_todo) == dict:
            self.cells_todo = {str(seg_id): {cell_struc: set([str(a) for a in self.cells_todo[seg_id][cell_struc]]) for cell_struc in self.cells_todo[seg_id]} for seg_id in self.cells_todo.keys()}


        # Get all file names from cloud for seg_ids of interest:
        all_cloud_file_names = [x.name for x in self.proofread_files_bucket.list_blobs() if x.name.split('_')[2] in self.cells_todo]
        all_local_file_names = [x for x in listdir(self.save_dir) if 'cell' in x and x.split('_')[2] in self.cells_todo]

        all_cloud_seg_ids = set([x.split('_')[2] for x in all_cloud_file_names])
        all_local_seg_ids = set([x.split('_')[2] for x in all_local_file_names])
        cells_with_files = all_cloud_seg_ids.union(all_local_seg_ids)
        cells_without_files = [x for x in self.cells_todo if x not in cells_with_files]

        num_fileless_cells = len(cells_without_files)

        if num_fileless_cells > 0:
            self.update_mtab(f'No starting file found locally or in cloud for {num_fileless_cells} cells', 'Cell Reconstruction')
        else:
            self.update_mtab(f'Starting files found for all cells, checking completion status of each file ...', 'Cell Reconstruction')

        complete_cells = []

        for seg_id in self.cells_todo:

            # If a seg ID already has a file, we need to choose which one to use
            if seg_id in cells_with_files:

                if self.most_recent_file_complete(seg_id, ['local']) and specific_file == None:
                    complete_cells.append(seg_id)
                    continue

                # If no complete cell locally, start most recent file, whether it originates from cloud or local:

                if specific_file != None:
                    most_recent_file = file_name
                else:
                    most_recent_file = self.get_most_recent_cell_files(seg_id, ['cloud', 'local'])[0]

                if most_recent_file in listdir(self.save_dir):

                    msg = f'Cell {seg_id} not completed for all the selected cell structures in the most recent (local) version'

                    file_source = 'local'

                else:

                    this_seg_cloud_file_names = [x.name for x in self.proofread_files_bucket.list_blobs() if x.name.split('_')[2] == str(seg_id)]

                    assert most_recent_file in this_seg_cloud_file_names

                    file_source = 'cloud'

                    if self.most_recent_file_complete(seg_id, ['cloud']):
                        msg = f'Cell {seg_id} completed for all the selected cell structures in the most recent (cloud) version'
                    else:
                        msg = f'Cell {seg_id} not completed for all the selected cell structures in the most recent (cloud) version'

                if file_source == 'cloud':
                    
                    try:
                        blob = self.proofread_files_bucket.blob(most_recent_file)
                        blob.download_to_filename(f'{self.save_dir}/{most_recent_file}')

                    except ConnectionError:
                        self.create_cloud_storage_client()
                        blob = self.proofread_files_bucket.blob(most_recent_file)
                        blob.download_to_filename(f'{self.save_dir}/{most_recent_file}')

                    self.update_mtab(f'Proofread cell file {most_recent_file} downloaded from cloud', 'Cell Reconstruction')

                with open(f'{self.save_dir}/{most_recent_file}', 'r') as fp:
                    self.cell_data = json_load(fp)

                # If agglo_id has changed from last time, add new base segments - currently disabled:
                last_agglo_id = self.cell_data['metadata']['data_sources']['agglo']
                changed_agglo_id = (last_agglo_id != self.agglo_seg)
       
                if changed_agglo_id:

                    self.add_new_base_segs_from_new_agglo(seg_id)
                
                    # Wipe clean the stored graph:
                    self.cell_data['graph_edges'] = []
                    self.cell_data['graph_nodes'] = []

                    self.create_pr_graph()
                    self.save_cell_graph()


            # Otherwise, it depends on whether the input cells todo is a list or dictionary:
            else:
                self.making_starting_cell_data(seg_id)

                # if self.pre_load_edges == 1:
                #     all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]
                #     self.get_new_gen_dict_entries(all_base_segs, 0)

                self.create_pr_graph()
                self.save_cell_graph()


            self.cells_todo_d[seg_id] = self.cell_data['base_segments']

        # Save new settings file for quick completion lookup next time:
        with open(f'{self.script_directory}/CREST_settings.json', 'w') as fp:
            json_dump(self.settings_dict, fp)

        # Make sure cells todo is a list:
        self.cells_todo = [x for x in self.cells_todo if x not in complete_cells]

        if specific_file == None:
            self.remove_skipped_cells()


    def create_cloud_storage_client(self):
        self.storage_client = storage.Client.create_anonymous_client()
        self.proofread_files_bucket = self.storage_client.bucket(self.cloud_storage_address)
        self.update_mtab('Created new connection to Google Cloud Storage', 'Cell Reconstruction')


    def seg_pr_batch_start(self, specific_file=None, specific_seg_id=None):

        if (specific_file == None and specific_seg_id == None):
            if not self.choose_cell_list_successfully(): 
                self.update_mtab('Input list of cell segments not in correct json format, please revise', 'Cell Reconstruction')
                return

        if not path_exists(self.save_dir):
            self.update_mtab('Selected save directory not found, please revise', 'Cell Reconstruction')
            return

        # Check required fields are available:
        required_info = ['cell_structures', 'max_base_seg_add', 'other_points']

        opf = []

        if not self.fields_complete(required_info, 'Cell Reconstruction', opf=opf): return

        self.update_mtab('Starting segment proofreading of batch of cells', 'Cell Reconstruction')

        self.viewer.set_state({})
        self.clear_all_msg()

        self.add_keybindings_no_duplicates({'change-point': lambda s: self.change_point()})

        with self.viewer.config_state.txn() as s:
            s.show_layer_panel = False ###

        self.cell_pos = 0

        req_addresses = ['agglo_address', 'base_address', 'em_address', 'cloud_storage_address']
        self.agglo_seg, self.base_seg, self.em, self.cloud_storage_address = self.get_addresses(req_addresses, 'Cell Reconstruction')

        # Create link to cloud storage:
        self.create_cloud_storage_client()

        self.point_types = [x.strip() for x in self.user_selections['Cell Reconstruction']['other_points'].get().split(',')]
        self.selected_types = self.user_selections['Cell Reconstruction']['cell_structures'].get().strip()
        self.selected_types = [x.strip() for x in self.selected_types.split(',')]

        if self.selected_types == []:
            self.update_mtab('Please specify at least one cell structure to correct splits or mergers for', 'Cell Reconstruction')
            return

        # Get segmentation proofreading-specific field values:
        #self.pre_load_edges = int(self.user_selections['Cell Reconstruction']['pre_load_edges'].get())
        self.pre_load_edges = 0 ### Make active later
        self.max_num_base_added = int(self.user_selections['Cell Reconstruction']['max_base_seg_add'].get().strip())

        # Create client
        self.get_vx_sizes('Cell Reconstruction')

        # Get cells todo
        self.ensure_all_cells_have_graphs(specific_file, specific_seg_id)

        if self.cells_todo == []:
            self.update_mtab('All cells in this batch are complete, exiting', 'Cell Reconstruction')
            return

        # Create list of cells that will be dropped to avoid duplicate proofreading:
        self.shared_bs_path = f'{self.save_dir}/dropped_cells_shared_base_segs.json'

        if path_exists(self.shared_bs_path):
            with open(self.shared_bs_path, 'r') as fp:
                self.dropped_cells = json_load(fp)
        else:
            self.dropped_cells = {}

        # Add keybindings:

        pr_keybindings = {
            'change-structure': lambda s: self.change_cell_structure(),
            'change-anchor-seg': self.change_anchor_seg,
            'add-or-remove-seg': self.add_or_remove_seg,
            'mark-branch-in-colour': self.mark_branch_in_colour,
            # 'grow-graph': lambda s: self.grow_graph(),
            # 'increase-threshold': lambda s: self.increase_threshold(),
            # 'decrease-threshold': lambda s: self.decrease_threshold(),
            # 'start-branch-focus': self.branch_focus,
            # 'accept-new-segs': lambda s: self.accept_new_segs(),        
        }
        
        self.add_keybindings_no_duplicates(pr_keybindings)            

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyc'] = 'change-structure'
            s.input_event_bindings.data_view['dblclick0'] = 'add-or-remove-seg'
            s.input_event_bindings.data_view['alt+mousedown0'] = 'mark-branch-in-colour'
            s.input_event_bindings.data_view['shift+mousedown2'] = 'change-anchor-seg'
            # s.input_event_bindings.viewer['keyg'] = 'grow-graph'
            # s.input_event_bindings.viewer['keyk'] = 'increase-threshold'
            # s.input_event_bindings.viewer['keyj'] = 'decrease-threshold'
            # s.input_event_bindings.viewer['keya'] = 'accept-new-segs'
            # s.input_event_bindings.data_view['shift+mousedown0'] = 'start-branch-focus'
            

        # Create seg queue and seg adding worker thread:
        # self.segs_to_add_queue = Queue()
        # Thread(target=self.add_seg_in_background, args=(), name='seg_adding_worker').start()

        # Create edge adding worker
        # if self.pre_load_edges == 1:
        #     self.pre_load_edges_queue = Queue()
        #     Thread(target=self.update_potential_graph_in_background, args=(), name='edge_adding_worker').start()

        # Create graph growth variables:
        self.current_score_threshold = 0.0
        # self.update_msg(f'Current Agglomeration Threshold (J/K): {self.current_score_threshold}', layer='threshold')
        self.current_red_seg = None
        self.growing_graph = False

        # Start proofreading first cell:
        self.load_cell_to_edit()
        self.start_new_cell_seg_pr()
        #self.open_ng_link()


    def setup_point_ann(self, include_base_seg_merger=True):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyp'] = 'change-point'

        self.set_endpoint_annotation_layers()

        if include_base_seg_merger==True:
            self.set_base_seg_merger_layer()

        self.point_pos = -1
        self.change_point()


    def open_ng_link(self):

        if not self.link_opened:
            wb_open(str(self.viewer))
            self.link_opened = True


    '''
    def increase_threshold(self):

        if self.current_score_threshold == 1.0:
            return

        self.current_score_threshold += 0.01
        self.current_score_threshold = float(round(self.current_score_threshold, 2))
        self.update_msg(f'Current Agglomeration Threshold (J/K): {self.current_score_threshold}', layer='threshold')

    def decrease_threshold(self):

        if self.current_score_threshold == 0.0:
            return

        self.current_score_threshold -= 0.01
        self.current_score_threshold = float(round(self.current_score_threshold, 2))
        self.update_msg(f'Current Agglomeration Threshold (J/K): {self.current_score_threshold}', layer='threshold')

    def accept_new_segs(self):

        self.remove_white_segs(self.cell_structures[self.cell_structure_pos])
        self.growing_graph = False

    def get_new_gen_dict_entries(self, starting_base_segs, score_threshold):

        for seg_id in starting_base_segs:
            if seg_id not in self.cell_data['next_gen_dict'].keys():
                self.cell_data['next_gen_dict'][seg_id] = []

        scored_edges = self.get_scored_edges(list(starting_base_segs), score_threshold)
            
        for seg1, seg2, score in scored_edges:
            if seg1 in starting_base_segs:
                self.cell_data['next_gen_dict'][seg1].append((seg2, score))
            if seg2 in starting_base_segs:
                self.cell_data['next_gen_dict'][seg2].append((seg1, score))

        self.update_mtab(f'Added {len(scored_edges)} new edges from {len(starting_base_segs)} seed base segments', 'Cell Reconstruction')

    def get_scored_edges(self, starting_base_segs, threshold):

        results = []

        if len(starting_base_segs) > 0:

            for batch in range(int(len(starting_base_segs)/10000)+1):

                q = ','.join([str(x) for x in starting_base_segs[batch*10000:(batch+1)*10000]])
                
                query = f"""SELECT DISTINCT label_a, label_b, score FROM {self.agglo_all_edges}
                            WHERE score >= {threshold} AND (label_a IN ({q}) OR label_b IN ({q}))"""

                res = self.ensure_results_from_bq(query, self.agglo_all_edges)
                results.extend(res)

        scored_edges = [(str(r['label_a']), str(r['label_b']), float(r['score'])) for r in results]

        return scored_edges

    def get_white_segs(self):

        white_segs = set()

        f = self.viewer.state.layers['focus_segs']

        for bs in f.segment_colors.keys():
            if f.segment_colors[bs] == '#ffffff' and int(bs) != 0:
                if bs in f.segments:
                    white_segs.add(str(bs))
        
        return white_segs

    def remove_white_segs(self, curr_s):

        # Any segments being added must be allowed to complete first:
        if self.segs_to_add_queue.unfinished_tasks != 0:
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...', 'Cell Reconstruction')
            return

        segs_to_remove = self.get_white_segs()

        self.cell_data['removed_base_segs'].update(segs_to_remove)

        self.cell_data['base_segments'][curr_s] -= segs_to_remove
        self.pr_graph.remove_nodes_from(segs_to_remove)

        self.focus_seg_set -= segs_to_remove
        
        with self.viewer.txn(overwrite=True) as s:
            for bs in segs_to_remove:
                if int(bs) in s.layers['focus_segs'].segments:
                    s.layers['focus_segs'].segments.remove(int(bs))
                if int(bs) in s.layers['base_segs'].segments:
                    s.layers['base_segs'].segments.remove(int(bs))
        
        self.update_displayed_segs()             

    def get_new_edges(self, starting_base_segs):

        bs_with_edge_info = set([str(x) for x in self.cell_data['next_gen_dict'].keys()])
        assert starting_base_segs.issubset(bs_with_edge_info)

        new_edges = []

        # Identify edges that introduce a new segment:
        all_current_segs = set(self.pr_graph.nodes())

        for base_seg in starting_base_segs:
            for partner, score in self.cell_data['next_gen_dict'][base_seg]:
                if score > self.current_score_threshold:
                    if not set((base_seg, partner)).issubset(all_current_segs):
                        if partner not in self.cell_data['removed_base_segs']:
                            new_edges.append((base_seg, partner))

        return new_edges

    def grow_graph(self):

        # Any segments being added must be allowed to complete first:
        if self.segs_to_add_queue.unfinished_tasks != 0:
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...', 'Cell Reconstruction')
            return

        # Any growing of the potential graph must be allowed to complete first:
        if self.pre_load_edges == 1:
            self.update_mtab(f'Ensuring all displayed segments have next partners available', 'Cell Reconstruction')
            self.pre_load_edges_queue.join()

        if self.current_red_seg == None: return

        self.growing_graph = True
        curr_s = self.cell_structures[self.cell_structure_pos]
        self.remove_white_segs(curr_s)

        self.update_mtab(f'Adding edges with scores above {self.current_score_threshold} to {curr_s} ...', 'Cell Reconstruction')
       
        starting_base_segs = set([str(x) for x in self.viewer.state.layers['focus_segs'].segments if str(x) != '0'])

        if self.pre_load_edges == 0:
            self.get_new_gen_dict_entries(starting_base_segs, self.current_score_threshold)

        new_edges = self.get_new_edges(starting_base_segs)

        new_base_segs = set([str(x[1]) for x in new_edges])
        seed_segs = set([x[0] for x in new_edges])
        assert seed_segs.issubset(starting_base_segs)

        self.update_seg_lookup(new_base_segs)

        self.pr_graph.add_nodes_from(new_base_segs)
        self.pr_graph.add_edges_from(new_edges)
        self.cell_data['base_segments'][curr_s].update(new_base_segs)

        self.focus_seg_set.update(set(new_base_segs))

        with self.viewer.txn(overwrite=True) as s:

            for bs in new_base_segs:
                s.layers['focus_segs'].segment_colors[int(bs)] = '#ffffff'
                s.layers['focus_segs'].segments.add(int(bs))
                s.layers['base_segs'].segments.add(int(bs))

        # Get potential edges for the next generation:
        if self.pre_load_edges == 1:
            for bs in new_base_segs:
                if bs not in self.cell_data['next_gen_dict'].keys():
                    self.pre_load_edges_queue.put(bs)

        self.update_mtab(f'{len(new_base_segs)} new base segments added to {curr_s}', 'Cell Reconstruction')
        self.update_displayed_segs()  


    def turn_white_seg_grey(self, base_seg):

        white_segs = self.get_white_segs()

        if base_seg in white_segs:

            with self.viewer.txn(overwrite=True) as s:
                s.layers['focus_segs'].segment_colors[int(base_seg)] = '#708090'
                s.layers['base_segs'].segment_colors[int(base_seg)] = '#708090'

    def switch_to_focus_segs_view(self, downstream_segs, base_seg):

        with self.viewer.txn(overwrite=True) as s:

            for bs in downstream_segs:

                if bs == base_seg:
                    s.layers['focus_segs'].segment_colors[int(bs)] = '#ff6347'
                else:
                    s.layers['focus_segs'].segment_colors[int(bs)] = '#708090'

            s.layers['focus_segs'].segments = set([int(x) for x in downstream_segs])
            s.layers['focus_segs'].pick = True
            s.layers['focus_segs'].visible = True

            s.layers['base_segs'].pick = False
            s.layers['base_segs'].selectedAlpha = 0.00 #For 2D     
            s.layers['base_segs'].objectAlpha = 0.10 #For 3D  

    def switch_from_focus_segs_view(self):

        with self.viewer.txn(overwrite=True) as s:

            s.layers['focus_segs'].segments = set()

            s.layers['focus_segs'].visible = False
            s.layers['focus_segs'].pick = False
            s.layers['focus_segs'].segments = set()

            s.layers['base_segs'].pick = True
            s.layers['base_segs'].selectedAlpha = 0.90 #For 2D     
            s.layers['base_segs'].objectAlpha = 1.0 #For 3D 

    def branch_focus(self, action_state):

        if self.segs_to_add_queue.unfinished_tasks != 0:
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...', 'Cell Reconstruction')
            return

        if self.growing_graph == True: 
            self.update_mtab("Press 'A' to accept any incorporated base segments from this round of growing before exiting branch focus mode", 'Cell Reconstruction')
            return

        if self.current_red_seg != None:

            base_seg = self.check_selected_segment('focus_segs', action_state)

            if base_seg != self.current_red_seg: return

            self.switch_from_focus_segs_view()
            self.focus_seg_set = set()
            self.current_red_seg = None

        else:
            base_seg = self.check_selected_segment('base_segs', action_state, acceptable_segs=self.pr_graph.nodes())

            if base_seg == 'None': return

            downstream_segs = self.get_ds_segs_of_certain_col(base_seg, '#708090')

            if downstream_segs == set(): return

            self.switch_to_focus_segs_view(downstream_segs, base_seg)
            self.focus_seg_set = downstream_segs
            self.current_red_seg = base_seg
    '''


    def change_cell_structure(self):

        if self.current_red_seg != None: return
     
        if self.cell_structure_pos == len(self.cell_structures)-1:
            self.cell_structure_pos = 0

        else:
            self.cell_structure_pos += 1

        self.update_msg(f'Current Cell Structure (C): {self.cell_structures[self.cell_structure_pos]}', layer='Current Cell Structure')


    def change_point(self):

        if self.point_pos == len(self.point_types)-1:
            self.point_pos = 0
        else:
            self.point_pos += 1

        selected_layer = self.point_types[self.point_pos]

        with self.viewer.txn(overwrite=True) as s:
            s.selectedLayer.layer = selected_layer
            s.selected_layer.visible = True
            s.layers[selected_layer].tab = 'Annotations'

        self.update_msg(f'Current Point Annotation Type (P): {selected_layer}', layer='current point type')


    def remove_downstream_base_segs(self, base_seg):

        segs_to_remove, n_con_com = self.get_downstream_base_segs(base_seg)

        self.assert_segs_in_sync()

        # Remove from lists and segmentation layer:
        for cs in self.cell_data['base_segments'].keys():
            self.cell_data['base_segments'][cs] -= set(segs_to_remove)

        self.pr_graph.delete_vertices(segs_to_remove)
        self.focus_seg_set -= set(segs_to_remove)

        with self.viewer.txn(overwrite=True) as s:

            for bs in segs_to_remove:

                if int(bs) in s.layers['base_segs'].segments:
                    s.layers['base_segs'].segments.remove(int(bs))

                # if int(bs) in s.layers['focus_segs'].segments:
                #     s.layers['focus_segs'].segments.remove(int(bs))

        self.assert_segs_in_sync()
            
        self.cell_data['removed_base_segs'].update(set(segs_to_remove))

        self.update_mtab(f'{len(segs_to_remove)} base segments removed from {n_con_com} connected components', 'Cell Reconstruction')
        self.cell_data['added_graph_edges'] = [x for x in self.cell_data['added_graph_edges'] if (x[0] not in segs_to_remove) and (x[1] not in segs_to_remove)]
        self.update_seg_counts_msg()

        if 'selected_base_segs_to_remove' not in self.cell_data:   ### can eventually remove
            self.cell_data['selected_base_segs_to_remove'] = []

        self.cell_data['selected_base_segs_to_remove'].append(base_seg)

    

    def change_anchor_seg(self, action_state):  

        base_seg = self.check_selected_segment('base_segs', action_state, banned_segs=[self.cell_data['anchor_seg']])
        if base_seg == 'None': return

        with self.viewer.txn(overwrite=True) as s:
            s.layers['base_segs'].segment_colors[int(self.cell_data['anchor_seg'])] = '#708090'
            s.layers['base_segs'].segment_colors[int(base_seg)] = '#1e90ff'
            
        self.cell_data['anchor_seg'] = deepcopy(base_seg)


    def assert_segs_in_sync(self, return_segs=False):

        displayed_segs = set([str(x) for x in self.viewer.state.layers['base_segs'].segments])
        graph_segs = set([x['name'] for x in self.pr_graph.vs])
        listed_segs = set([a for b in [self.cell_data['base_segments'][cs] for cs in self.cell_data['base_segments'].keys()] for a in b])

        assert listed_segs == graph_segs

        if not displayed_segs == graph_segs:
            self.update_displayed_segs()
        

        if return_segs:
            return displayed_segs
        else:
            return None


    def add_or_remove_seg(self, action_state):  

        if self.current_red_seg == None:
            rel_layer = 'base_segs'
        else:
            rel_layer = 'focus_segs'
        
        base_seg = self.check_selected_segment(rel_layer, action_state, banned_segs = [self.cell_data['anchor_seg']])

        if base_seg == 'None': return

        # If in graph growing mode, change seg from white to grey:
        if self.growing_graph == True:
            self.turn_white_seg_grey(base_seg)
            return

        # Otherwise, add or remove to main layer:
        
        displayed_segs = self.assert_segs_in_sync(return_segs=True)

        if base_seg in displayed_segs:

            self.remove_downstream_base_segs(base_seg)

        
        else:

            # Adding a segment:

            agglo_seg = self.check_selected_segment('agglo', action_state)
  
            if agglo_seg == 'None': return

            constituent_base_ids = self.get_base_segs_of_agglo_seg(agglo_seg)

            if len(constituent_base_ids) > self.max_num_base_added:
                base_ids = [base_seg]
            else:
                base_ids = constituent_base_ids

            current_segs = self.assert_segs_in_sync(return_segs=True)

            num_base_segs_this_agglo_seg = len(base_ids)
            base_ids = [x for x in base_ids if x not in current_segs]
            num_base_segs_not_already_included = len(base_ids)

            if num_base_segs_this_agglo_seg > num_base_segs_not_already_included:

                base_ids = [x for x in base_ids if x not in self.cell_data['removed_base_segs']]

                if not base_seg in base_ids:
                    base_ids.append(base_seg)
    
            self.update_base_locations(base_ids)
            self.pr_graph.add_vertices(base_ids)

            if len(base_ids) > 1:
                edges = self.get_edges_from_agglo_seg(agglo_seg)
                edges = [x for x in edges if (x[0] in base_ids and x[1] in base_ids)]
                self.pr_graph.add_edges(edges)

            join_msg = self.add_closest_edge_to_graph(base_ids, base_seg) 

            # Update lists of base segments and displayed segs:
            self.cell_data['base_segments']['unknown'].update(set(base_ids))

            if self.current_red_seg != None:
                self.focus_seg_set.update(set(base_ids))

            with self.viewer.txn(overwrite=True) as s:

                for bs in base_ids:
                    s.layers['base_segs'].segment_colors[int(bs)] = '#708090'
                    s.layers['base_segs'].segments.add(int(bs))

                    # if self.current_red_seg != None:
                    #     s.layers['focus_segs'].segment_colors[int(bs)] = '#708090'
                    #     s.layers['focus_segs'].segments.add(int(bs))
            

            # Get next generation of links for new IDs:
            if self.pre_load_edges == 1:
                for bs in base_ids:
                    self.pre_load_edges_queue.put(bs)

            self.update_displayed_segs() 
            self.assert_segs_in_sync()

            self.update_mtab(f'Added {len(base_ids)} base segments from agglomerated segment {agglo_seg}{join_msg}', 'Cell Reconstruction')


    def get_downstream_base_segs(self, base_seg):

        edge_backup = [(self.pr_graph.vs[p_ix]['name'], base_seg) for p_ix in self.pr_graph.neighbors(base_seg)]

        self.pr_graph.delete_vertices([base_seg])

        current_cc = list(self.pr_graph.clusters(mode='weak'))
        current_cc_seg_ids = [[self.pr_graph.vs[i]['name'] for i in c] for c in current_cc]
        ccs_to_remove = [cc for cc in current_cc_seg_ids if self.cell_data['anchor_seg'] not in cc]
        segs_to_remove = [str(x) for y in ccs_to_remove for x in y if str(x) != '0']
        segs_to_remove.append(base_seg)

        self.pr_graph.add_vertices([base_seg])
        self.pr_graph.add_edges(edge_backup)

        return segs_to_remove, len(current_cc)


    def get_ds_segs_of_certain_col(self, base_seg, colour):

        ds = self.get_downstream_base_segs(base_seg)[0]

        # If any of the downstream segments doesn't have a colour, set it to grey:
        with self.viewer.txn(overwrite=True) as s:

            for bs in ds:
                if int(bs) not in s.layers['base_segs'].segment_colors.keys():
                    s.layers['base_segs'].segment_colors[int(bs)] = '#708090'

            ds = set([x for x in ds if s.layers['base_segs'].segment_colors[int(x)] == colour])
        
        return ds


    def mark_branch_in_colour(self, action_state):

        if self.growing_graph == True: return
        if self.current_red_seg != None: return

        base_seg = self.check_selected_segment('base_segs', action_state, banned_segs = [self.cell_data['anchor_seg']])

        if base_seg == 'None': return

        if base_seg not in [x['name'] for x in self.pr_graph.vs]:
            self.update_mtab(f'Base segment {base_seg} was not in the base segment graph, updating displayed segments ...', 'Cell Reconstruction')
            self.update_displayed_segs()
            return

        col = self.viewer.state.layers['base_segs'].segment_colors

        if int(base_seg) not in col.keys(): return

        current_colour = col[int(base_seg)]
        downstream_segs = self.get_ds_segs_of_certain_col(base_seg, current_colour)

        if current_colour != '#708090':
            cell_part = 'unknown'
        else:
            cell_part = self.cell_structures[self.cell_structure_pos]
        
        new_colour = self.chosen_seg_colours[cell_part]

        for cs in self.cell_data['base_segments'].keys():

            if cs == cell_part:
                self.cell_data['base_segments'][cs].update(downstream_segs)
            else:
                self.cell_data['base_segments'][cs] -= downstream_segs

        with self.viewer.txn(overwrite=True) as s:
            for bs in downstream_segs:
                s.layers['base_segs'].segment_colors[int(bs)] = new_colour

        self.update_seg_counts_msg()


    def update_potential_graph_in_background(self):

        while True:

            base_segs_to_get_edges = []

            while not self.pre_load_edges_queue.empty():
                base_segs_to_get_edges.append(self.pre_load_edges_queue.get())

            if base_segs_to_get_edges == []:
                sleep(0.1)
                continue

            self.get_new_gen_dict_entries(base_segs_to_get_edges, 0)

            for bs in base_segs_to_get_edges:
                self.pre_load_edges_queue.task_done()


    def update_displayed_segs(self):

        displayed_segs = set([str(x) for x in self.viewer.state.layers['base_segs'].segments])
        listed_segs = set([x for y in self.cell_data['base_segments'].values() for x in y])
        graph_segs = set([x['name'] for x in self.pr_graph.vs])

        assert listed_segs == graph_segs

        segs_to_remove = displayed_segs - listed_segs

        # Identify segments that failed to be added to the viewer:
        missing_segs = listed_segs - displayed_segs
        missing_focus_segs = self.focus_seg_set - set([str(x) for x in self.viewer.state.layers['focus_segs'].segments])

        if not (missing_segs == set() and missing_focus_segs == set()):
            # Correct the viewer:
            with self.viewer.txn(overwrite=True) as s:
                
                for layer, missing_list in [['base_segs', missing_segs], ['focus_segs', missing_focus_segs]]:

                    for bs in missing_list:
                        s.layers[layer].segment_colors[int(bs)] = '#708090'
                        s.layers[layer].segments.add(int(bs)) 

                    for bs in segs_to_remove:
                        if int(bs) in s.layers[layer].segments:
                            s.layers[layer].segments.remove(int(bs))

        self.update_seg_counts_msg()


    def update_seg_counts_msg(self):

        b = self.cell_data['base_segments']
        second_part = ', '.join([f'{x}: {len(b[x])}' for x in b.keys()])

        self.update_msg(f'Current Base Segment Counts: {second_part}', layer='current_seg_count')
            

    def save_timing_and_user(self):

        ### CAN GET RID OF LATER
        if type(self.cell_data['metadata']['timing']) == dict:
            self.cell_data['metadata']['timing'] = [a for b in self.cell_data['metadata']['timing'].values() for a in b]
        ### CAN GET RID OF LATER

        time_taken = (time()-self.start_time)/60
        self.cell_data['metadata']['timing'].append(time_taken)
        

    def update_and_save_dropped_cells(self):

        base_merge_segs = set([x[3] for x in self.cell_data['base_seg_merge_points']])
        
        current_seg = self.cells_todo[self.cell_pos]
    
        for dtype in self.cell_data['base_segments'].keys():

            current_base_segs = set(self.cell_data['base_segments'][dtype])

            for index_seg in self.cells_todo[self.cell_pos+1:]:

                if dtype not in self.cells_todo_d[index_seg].keys(): continue

                seg_list = set(self.cells_todo_d[index_seg][dtype])

                overlapping_segs = current_base_segs & seg_list

                overlapping_segs -= base_merge_segs
            
                if len(overlapping_segs) > 0:

                    if index_seg not in self.dropped_cells.keys():
                        self.dropped_cells[index_seg] = {}
                        
                    if current_seg not in self.dropped_cells[index_seg].keys():
                        self.dropped_cells[index_seg][current_seg] = {}
                    
                    self.dropped_cells[index_seg][current_seg][dtype] = list(overlapping_segs)

                    if index_seg in self.cells_todo:
                        self.cells_todo.remove(index_seg)

                    self.update_mtab(f'{len(overlapping_segs)} segments from {dtype} of cell {current_seg} are present in the {dtype}, of cell {index_seg}, removing this cell from to-do list', 'Cell Reconstruction')
                    
        with open(self.shared_bs_path, 'w') as fp:
            json_dump(self.dropped_cells, fp)


    def save_cell_seg_and_next(self):
     
        self.save_cell_seg(save_completion=True)

        # Ensure that any base segs incorporated into this cell are removed from the to-do list:
        if len(self.cells_todo) > 1:
            self.update_and_save_dropped_cells()
       
        self.next_cell()
     


    def save_point_types_successfully(self):

        for t in self.point_types:

            this_type_points = []

            for x in self.viewer.state.layers[t].annotations:
                if t == 'Base Segment Merger' and x.segments == None:
                    c = [int(y) for y in x.point]
                    self.update_mtab(f'Error, no segment for point {c}, for point layer {t}, correct and re-save')
                    return False

                else:
                    co_ords = [float(x) for x in list(x.point)]
                    co_ords_and_id = [co_ords[x]*self.vx_sizes['em'][x] for x in range(3)]

                    if x.segments != None: 
                        if len(x.segments[0]) > 0:
                            co_ords_and_id.append(str(x.segments[0][0]))
                        else:
                            co_ords_and_id.append('0')
                    else:
                        co_ords_and_id.append('0')

                    this_type_points.append(co_ords_and_id)

            if t == 'Base Segment Merger':
                self.cell_data['base_seg_merge_points'] = this_type_points
            else:
                self.cell_data['end_points'][t] = this_type_points

        return True



    def save_cell_seg(self, save_completion=False):

        if self.pre_load_edges == 1:
            self.pre_load_edges_queue.join()
        
       
        self.resolving_seg_overlap()
      
        if not self.save_point_types_successfully(): return
     
        self.update_displayed_segs() 
        self.save_timing_and_user()

        ### CAN REMOVE LATER
        if type(self.cell_data['metadata']['completion']) == dict:
            self.cell_data['metadata']['completion'] = list(set([a for b in self.cell_data['metadata']['completion'].values() for a in b]))
        ### CAN REMOVE LATER

        if save_completion == True:
            self.cell_data['metadata']['completion'] = list(set(self.cell_data['metadata']['completion']).union(set(self.selected_types)))
            self.save_cell_graph(save_to_cloud=True)
        else:
            self.save_cell_graph()


    def set_seg_colours(self):

        self.chosen_seg_colours = {'unknown': '#708090'}

        acceptable_colours = set(['#FFFF00', '#800080', '#008000', '#FF00FF', '#00FF00', '#FF69B4', '#FF8C00'])
        used_colours = set()

        for x in self.cell_structures:

            available_colours = acceptable_colours - used_colours

            if len(available_colours) == 0:
                available_colours = acceptable_colours
                
            if 'axon' in x:
                chosen_col = '#008000'

            if 'dendrite' in x:
                chosen_col = '#FFFF00'
    
            if 'axon' not in x and 'dendrite' not in x:
                chosen_col = random_choice(list(available_colours))

            used_colours.add(chosen_col)
            self.chosen_seg_colours[x] = chosen_col

            
    def set_cell_structures(self):

        existing_struc = [x for x in self.cell_data['base_segments'].keys() if x!= 'unknown']

        self.cell_structures = list(set(self.selected_types) | set(existing_struc))

        for dtype in self.cell_structures:
            if dtype not in self.cell_data['base_segments'].keys():
                self.cell_data['base_segments'][dtype] = set()


    def reset_seg_pr_layers(self, two_d_intensity = 0.5):

        with self.viewer.txn(overwrite=True) as s:

            s.layers['em'] = neuroglancer.ImageLayer(source = self.em)

            s.layers['agglo'] = neuroglancer.SegmentationLayer(source = self.agglo_seg, segment_colors={})
            s.layers['agglo'].pick = False
            s.layers['agglo'].visible = True
            s.layers['agglo'].ignoreNullVisibleSet = False
            s.layers['agglo'].selectedAlpha = two_d_intensity
            s.layers['agglo'].objectAlpha = 1.00

            # s.layers['focus_segs'] = neuroglancer.SegmentationLayer(source = self.base_seg, segment_colors={})
            # s.layers['focus_segs'].visible = False
            # s.layers['focus_segs'].pick = False
            # s.layers['focus_segs'].ignoreNullVisibleSet = False
            # s.layers['focus_segs'].selectedAlpha = two_d_intensity
            # s.layers['focus_segs'].objectAlpha = 1.00
            
            all_segs = [a for b in self.cell_data['base_segments'].values() for a in b]

            s.layers['base_segs'] = neuroglancer.SegmentationLayer(source = self.base_seg, segments=all_segs, segment_colors={})
            s.layers['base_segs'].ignoreNullVisibleSet = False
            s.layers['base_segs'].pick = False
            s.layers['base_segs'].selectedAlpha = two_d_intensity #For 2D

            for dtype in self.cell_data['base_segments'].keys():

                for seg in self.cell_data['base_segments'][dtype]:
                    s.layers['base_segs'].segment_colors[int(seg)] = self.chosen_seg_colours[dtype]

            s.layers['base_segs'].segment_colors[int(self.cell_data['anchor_seg'])] = '#1e90ff'


    def start_new_cell_seg_pr(self):

        self.setup_point_ann()

        self.set_cell_structures()
        self.focus_seg_set = set()
        self.set_seg_colours()

        self.cell_structure_pos = -1
        self.change_cell_structure()

        main_seg_id = self.cells_todo[self.cell_pos]
        loc = self.get_locations_from_base_segs([main_seg_id])[main_seg_id]
        self.change_view(loc, css=0.22398, ps=389.338)
        self.reset_seg_pr_layers()
        self.update_seg_counts_msg()


    def remove_skipped_cells(self):
        
        if 'not_proofread.json' not in listdir(self.save_dir):
            self.skipped = []
        else:
            with open(f'{self.save_dir}/not_proofread.json', 'r') as fp:
                self.skipped = json_load(fp)
            
        self.cells_todo = [x for x in self.cells_todo if str(x) not in self.skipped]

    
    def skip_pr(self):

        cell_id = str(self.cells_todo[self.cell_pos])

        if cell_id not in self.skipped:
            self.skipped.append(cell_id)

        with open(f'{self.save_dir}/not_proofread.json', 'w') as fp:
            json_dump(self.skipped, fp)

        self.update_mtab(f'Skipped cell {self.cells_todo[self.cell_pos]}', 'Cell Reconstruction')

        self.next_cell()

    

        
if __name__ == '__main__':

    #pyi_splash.close()
    filterwarnings("ignore")
    inst = UserInterface()

    #sys.stdout.write = inst.redirector_stdout 
    #sys.stderr.write = inst.redirector_stderr

    inst.window.mainloop()  









    

    

 
