import time
import neuroglancer
import numpy as np
import webbrowser
import json
import sys
import os
from copy import deepcopy
import datetime
import networkx as nx
from tkinter import Frame, Tk, IntVar, filedialog, Checkbutton, TOP, BOTH, StringVar
from tkinter.ttk import Notebook, Label, Entry, Button
from PIL import Image, ImageTk
from google.cloud import bigquery 
from google.cloud import bigquery_storage            
from google.oauth2 import service_account
from google.auth.transport import requests as auth_request
from google.api_core.exceptions import NotFound
from scipy.spatial.distance import euclidean, cdist
import igraph as ig
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from googleapiclient.discovery import build
from queue import Queue
import threading
from itertools import combinations, product
import random
import pandas as pd




class MemoryCache():
    # Workaround for error 'https://github.com/googleapis/google-api-python-client/issues/325':
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

class UserInterface:

    def __init__(self):

        self.set_pre_loaded_settings()
        self.dimensions = [1200, 640]
        self.lowest_line = 23
        self.viewer = neuroglancer.Viewer()

        self.get_script_directory()
        self.get_settings_dict()
        self.user_selections = {'Cell Reconstruction': {}, 'Network Exploration': {}}
        
        self.window = Tk()
        self.window.title("CREST: Connectome Reconstruction and Exploration Simple Tool")
        self.window.geometry(f'{self.dimensions[0]}x{self.dimensions[1]}')
        self.tab_control = Notebook(self.window)

        self.tabs = {}

        for tab_type in ['Network Exploration', 'Cell Reconstruction', 'Figures', 'Messages']:

            self.tabs[tab_type] = Frame(self.tab_control)
            self.tab_control.add(self.tabs[tab_type], text=tab_type)

        self.current_messages = {i: '' for i in range(36)}

        self.make_special_string_variables()
        self.make_labels_and_entries()
        self.make_checkbuttons()
        self.make_clickbuttons()

        self.tab_control.pack(expand=2, fill="both")
        threading.Thread(target=self.get_segs_and_layers, args=[], name='get_segs_and_layers').start(),
        self.window.mainloop()  
    
    def set_pre_loaded_settings(self):

        self.pre_loaded_settings = {

            'Cell Reconstruction':   {

                'cred': '/path/to/yourcredentialsfile.json',
                'em': 'goog14r0_8nm',
                'user': '964355253395:h01',
                'input_neurons': '/path/to/input_list.json',
                'save_dir': 'path/to/save_directory',
                'seg': 'agg20201123b',
                'base_seg': 'goog14r0seg1',
                'other_points': 'exit_volume,natural,uncorrected_split,bad_alignment,artefact', 
                'skel_seg': 'goog14r0seg1_agg20200916_flat', 
                'max_stalk': '3000', 
                'syn_seg': 'goog14r0s4',
                'skel_source_id': '/pni_sub256_o128_er100_dns300_psize32.0_32.0_33.0_mio', 
                'max_syn_merge': '5000', 
                'cell_structures': 'cell_body, axon, dendrite',
                'max_base_seg_add': 1000,
                'outgoing': 1,
                'incoming': 1, 
                'partner_splits': 0, 
                'ends_of_shafts_marked': 0,
                'merge_syn': 0,
                'correct_split': 1,
                'correct_merge': 1,
                'custom_syn_cell_0_options': '',
                'custom_syn_cell_0_category': '',
                'custom_syn_cell_1_options': '',
                'custom_syn_cell_1_category': '',
                'custom_syn_cell_2_options': '',
                'custom_syn_cell_2_category': '',
                'custom_syn_cell_3_options': '',
                'custom_syn_cell_3_category': '',
                'custom_syn_cell_4_options': '',
                'custom_syn_cell_4_category': '',
                'custom_syn_cell_5_options': '',
                'custom_syn_cell_5_category': '',
                'custom_syn_cell_6_options': '',
                'custom_syn_cell_6_category': '',
                'custom_syn_cell_7_options': '',
                'custom_syn_cell_7_category': '',
                'custom_syn_cell_8_options': '',
                'custom_syn_cell_8_category': '',
                'custom_syn_cell_9_options': '',
                'custom_syn_cell_9_category': '',
                'pre_load_edges': 0,
                'use_syn_for_seg': 0,
                'root_points_marked': 0,
                'false_negatives_marked': 0   
                
                },
            
            'Network Exploration': {

                'cred': '/path/to/yourcredentialsfile.json', 
                'em': 'goog14r0_8nm', 
                'seg': 'agg20201123b', 
                'user': '964355253395:h01', 
                'base_seg': 'goog14r0seg1', 
                'true_loc_plot': 0,
                'syn_seg': 'goog14r0s4', 
                'max_p_len': '5', 
                'min_syn_per_c': '1', 
                'dir_p_only': 1, 
                'max_syn_plot': '40',
                'max_cases_view': '500',
                'min_syn_from': '',
                'min_syn_to': '',
                'max_syn_from': '',
                'max_syn_to': '',
                'min_syn_received_total': '', 
                'max_syn_received_total': '',
                'min_pre': '',
                'max_pre': '',
                'min_syn_given_total': '', 
                'max_syn_given_total': '',
                'min_post': '',
                'max_post': '',
                'show_all_pre': 0, 
                'show_greatest_pre': 0,
                'show_pre_range': 1, 
                'show_all_post': 0,
                'show_greatest_post': 0, 
                'show_post_range': 1       }   

                }

        self.field_titles = {

            'user': "Project ID", 
            'input_neurons': "Input Neurons List File", 
            'save_dir': "Directory to Load / Save", 
            'base_seg': "Base Segmentation",          
            'syn_seg': "Synapses ID",   
            'skel_seg': "Skeleton Segmentation ID", 
            'skel_source_id': "Skeleton Source ID", 
            'other_points': "End Point Types separated by ',': ", 
            'cell_structures': "Cell Structures separated by ','", 
            'em': "EM Alignment", 
            'max_base_seg_add': "Maximum Base Segs to add on", 
            'seg': "Agglomerated Segmentation", 
            'cred': "Credentials File Path",
            'min_syn_per_c': "Min Synapses Per Connection",
            'max_p_len': "Max Cell Pair Path Search Length", 
            'max_syn_plot': "Max Synapses to Plot per Partner",
            'max_cases_view': "Max Number of Cases to View",
            'min_syn_received_total': 'Min total synapses received',
            'max_syn_received_total': 'Max total synapses received',
            'min_pre': 'Min pre-synaptic partners',
            'max_pre': 'Max pre-synaptic partners',
            'min_syn_from': 'Min synapses from at least one partner',
            'max_syn_from': 'Max synapses from any one partner',
            'min_syn_given_total': 'Min total synapses given',
            'max_syn_given_total': 'Max total synapses given',
            'min_post': 'Min post-synaptic partners', 
            'max_post': 'Max post-synaptic partners', 
            'min_syn_to': 'Min synapses to at least one partner',
            'max_syn_to': 'Max synapses to any one partner',
            'merge_syn': 'Check synapse pairs closer than (nm):', 
            'partner_splits': 'Check for splits if partner smaller than (nm):'

            }

    def get_script_directory(self):

        self.script_directory = os.path.dirname(sys.argv[0])

        if self.script_directory == '':

            self.script_directory = os.getcwd()      # Fix for certain mac setups

    def ensure_results_from_bq(self, query, table_name):

        res = None
        informed_of_error = False

        while res == None:

            try:
                c = bigquery.job.QueryJobConfig(allow_large_results = True)
                query_job = self.client.query(query, job_config=c)  
                res = [dict(row) for row in query_job.result()]

            except:
                if informed_of_error == False:
                    self.update_mtab(f'Problem retrieving data from Big Query table {table_name}')
                    informed_of_error = True
                continue

        return res

    def get_info_from_bigquery(self, info_to_get, info_to_use, info_to_use_ids, db_name, batch_size=10000):
            
        results = []

        if len(info_to_use_ids) > 0:
        
            num_batches = int(len(info_to_use_ids)/batch_size)
            
            info_to_get = ','.join([str(x) for x in info_to_get])
            
            for batch in range(num_batches+1):

                q = ','.join([str(x) for x in info_to_use_ids[batch*batch_size:(batch+1)*batch_size]])
                
                query = f"""
                            SELECT {info_to_get}
                            FROM {db_name}
                            WHERE {info_to_use} IN ({q})
                        """

                res = self.ensure_results_from_bq(query, db_name)
                results.extend(res)
            
        return results

    def callback(self, event):
        webbrowser.open_new(event.widget.cget("text"))

    def get_settings_dict(self):

        if 'CREST_settings.json' in os.listdir(self.script_directory):

            with open(f'{self.script_directory}/CREST_settings.json', 'r') as fp:
                self.settings_dict = json.load(fp)

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

    def update_msg(self, msg, layer='status'):

        with self.viewer.config_state.txn() as s:
            s.status_messages[layer] = msg

    def change_view(self, location, css, ps):

        with self.viewer.txn(overwrite=True) as s:

            dimensions = neuroglancer.CoordinateSpace(
                scales=self.vx_sizes['em'],
                units='nm',
                names=['x', 'y', 'z']   )

            s.showSlices = False
            s.dimensions = dimensions
            s.crossSectionScale = css
            s.projectionScale = ps
            s.position = np.array(location)

    def create_client(self, mode):

        cred_path = self.user_selections[mode]['cred'].get().strip()
        self.credentials = service_account.Credentials.from_service_account_file(cred_path)
        self.user = str(self.credentials.service_account_email).split('@')[0]
        self.client = bigquery.Client(project=self.credentials.project_id, credentials=self.credentials)
        self.bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=self.credentials)

        self.scoped_credentials = self.credentials.with_scopes(['https://www.googleapis.com/auth/brainmaps'])
        self.scoped_credentials.refresh(auth_request.Request())

        self.service = build(
            'brainmaps',
            discoveryServiceUrl='https://brainmaps.googleapis.com/$discovery/rest?key=AIzaSyBAaxW5lG3PhdRxsj6tQGa322PoJ2WBUz8', 
            version='v1',
            credentials=self.scoped_credentials,
            cache=MemoryCache()  
            )

    def get_vx_sizes(self, mode):

        self.create_client(mode)

        # Set all voxel sizes and starting points:
        self.vx_sizes = {}

        for seg_id, dtype in [[self.em, 'em'], [self.agglo_seg, 'seg'], [self.syn_seg, 'syn_seg']]:

            if self.user_selections[mode][dtype].get().strip() == '': continue

            req_id = seg_id.split('brainmaps://')[-1]

            if req_id.count(':') == 3:
                req_id = req_id[:req_id.rindex(':')]

            vol_data = self.service.volumes().get(volumeId=req_id).execute()

            g = vol_data['geometry'][0]

            pixel_size = [int(g['pixelSize'][x]) for x in ['x', 'y','z']]

            self.vx_sizes[dtype] = pixel_size

            if dtype == 'em':
                self.starting_location = [int(int(g['volumeSize'][x])/2) for x in ['x', 'y','z']]

    def make_special_string_variables(self):

        for dtype in ['pre', 'post']:
            
            self.user_selections['Network Exploration'][f'{dtype}_btn_text'] = StringVar()

            self.user_selections['Network Exploration'][f'{dtype}_btn_text'].set(
                f"Only {dtype} partners making between 0 and infinite synapses")

            for min_or_max in ['min', 'max']:
                self.user_selections['Network Exploration'][f'{dtype}_{min_or_max}_text'] = self.make_linked_string(dtype, min_or_max)

    def make_labels_and_entries(self):

        labels = { 
            'Cell Reconstruction': [
                [" ", None, 0, 0, 6],
                ["COMMON OPTIONS:", None, 0, 1, 4],
                ["SYNAPSE PROOFREADING OPTIONS:", None, 5, 11, 4],
                ["Synapse Types to Check:", None, 6, 14, 4],
                ["Cell/Synapse category name", None, 0, 13, 1],
                ["Cell/Synapse category options separated by ','", None, 1, 13, 1],
                ["SEGMENTATION PROOFREADING OPTIONS:", None, 5, 5, 4],
                [" ", None, 5, 12, 6],
                ["Credentials File Path", 'cred', 0, 2, 4],
                ["Input Neurons List File", 'input_neurons', 0, 3, 4],
                ["Directory to Load / Save", 'save_dir', 0, 4, 4],
                ["Project ID", 'user', 0, 5, 4],
                ["EM Alignment ID", 'em', 0, 6, 4],
                ["Base Segmentation ID", 'base_seg', 0, 7, 4],
                ["Agglomerated Segmentation ID", 'seg', 0, 8, 4],           
                ["Synapses ID", 'syn_seg', 0, 9, 4],  
                ["Skeleton Segmentation ID",'skel_seg', 0, 10, 4],  
                ["Skeleton Source ID", 'skel_source_id', 0, 11, 4],
                ["End Point Types separated by ',' :", 'other_points', 5, 3, 4],  
                ["Cell Structures separated by ',' :", 'cell_structures', 5, 2, 4], 
                ["Maximum Base Segs to add on:", 'max_base_seg_add', 6, 6, 1],
                [None, 'max_syn_merge', 5, 12, 1],
                [None, 'max_stalk', 5, 13, 1],
                ],

            'Network Exploration': [
                ["CELL TYPE FILTERS:                                    ", None, 2, 1, 1],
                ["BRAIN REGION FILTERS:                  ", None, 3, 1, 1],
                [" ", None, 0, 0, 4],
                ["CORE SETTINGS:", None, 0, 1, 4],
                
                ["Credentials File Path", 'cred',  0, 2, 1],
                ["Project ID", 'user', 0, 3, 1],
                ["EM Alignment", 'em', 0, 4, 1],
                ["Base ID", 'base_seg',  0, 5, 1],
                ["Agglomeration ID", 'seg',  0, 6, 1],
                ["Synapses ID", 'syn_seg',  0, 7, 1],
                #[" ", None, 4, 0, 2],
                ["NETWORK PATHS EXPLORATION OPTIONS:", None, 4, 1, 2],
                ["Min Synapses Per Connection",'min_syn_per_c', 4, 2, 1],
                ["Max Cell Pair Path Search Length", 'max_p_len', 4, 3, 1],
                ["SEQUENTIAL CELL EXPLORATION OPTIONS:", None, 4, 8, 2],
                ["Max Synapses to Plot per Partner",'max_syn_plot', 4, 9, 1],
                ["Max Number of Cases to View",'max_cases_view', 4, 10, 1],
                [" ", None, 4, 11, 1],
                ['POST-SYNAPTIC CONNECTIVITY FILTERS:', None, 0, 17, 2],
                ['Min post-synaptic partners', 'min_post', 0, 18, 1],
                ['Max post-synaptic partners', 'max_post', 0, 19, 1],
                ['Min total synapses given','min_syn_given_total', 0, 20, 1],
                ['Max total synapses given','max_syn_given_total', 0, 21, 1],
                ['Min synapses to at least one partner','min_syn_to', 0, 22, 1],
                ['Max synapses to any one partner','max_syn_to', 0, 23, 1],
                [" ", None, 0, 14, 1],
                [" ", None, 4, 20, 1],
                ["----------------------------------------------------------------------", None, 4, 21, 2],
                ['Partner Display Options:', None, 4, 12, 1],
                ['PRE-SYNAPTIC CONNECTIVITY FILTERS:', None, 0, 9, 2],
                ['Min pre-synaptic partners','min_pre', 0, 10, 1],
                ['Max pre-synaptic partners','max_pre', 0, 11, 1],
                ['Min total synapses received','min_syn_received_total', 0, 12, 1],
                ['Max total synapses received','max_syn_received_total', 0, 13, 1],
                ['Min synapses from at least one partner','min_syn_from', 0, 14, 1],
                ['Max synapses from any one partner','max_syn_from', 0, 15, 1],
                [" ", None, 0, 16, 1],
                ]
            }

        # Put in custom categories:
        for col, dtype in [[-1, 'category'], [0, 'options']]:

            for i in range(10):
                labels['Cell Reconstruction'].append(
                    [None, f'custom_syn_cell_{i}_{dtype}', col, i+14, 1]
                    )

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

                if dkey in ['min_syn_from', 'max_syn_from', 'min_syn_to', 'max_syn_to']:

                    if dkey.split('_')[-1] == 'from':
                        dtype = 'pre'

                    if dkey.split('_')[-1] == 'to':
                        dtype = 'post'

                    min_or_max = dkey.split('_')[0]

                    vartext = self.user_selections[tab_type][f'{dtype}_{min_or_max}_text']

                    self.user_selections[tab_type][dkey] = Entry(self.tabs[tab_type], textvariable=vartext)
                
                else:
                    self.user_selections[tab_type][dkey] = Entry(self.tabs[tab_type])

                self.user_selections[tab_type][dkey].grid(row=row, column=col+1, padx=10, sticky='ew', columnspan=colspan)

                val_from_settings = self.settings_dict[tab_type][dkey]

                self.user_selections[tab_type][dkey].insert(0, val_from_settings)

    def make_checkbuttons(self):

        self.mutually_exclusive_options = {
            'show_pre_range': ['show_greatest_pre', 'show_all_pre'], 
            'show_greatest_pre': ['show_pre_range', 'show_all_pre'],
            'show_all_pre': ['show_greatest_pre', 'show_pre_range'],
            'show_post_range': ['show_greatest_post', 'show_all_post'], 
            'show_greatest_post': ['show_post_range', 'show_all_post'],
            'show_all_post': ['show_greatest_post', 'show_post_range']
            }

        checkbutton_data = {
            'Cell Reconstruction': [
                ['Check synapse pairs closer than (nm):', 'merge_syn', 5, 12],
                ['Check for splits if partner smaller than (nm):','partner_splits', 5, 13],
                ['Mark shaft end-points', 'ends_of_shafts_marked', 5, 16],
                ['Outgoing Chemical', 'outgoing', 6, 15],
                ['Incoming Chemical', 'incoming', 6, 16], 
                ['Mark synapse root points', 'root_points_marked', 5, 15], 
                ['Mark false negatives', 'false_negatives_marked', 5, 14], 
                ['Correct Splits', 'correct_split', 5, 6],
                ['Correct Mergers', 'correct_merge', 5, 7],
                ['Pre-load Next Segments', 'pre_load_edges', 5, 8],  
                ['Load Synapses', 'use_syn_for_seg', 5, 9],  
                ],
            'Network Exploration': [
                ['Directed Cell Pair Path Search', 'dir_p_only', 4, 4],
                ['Use True Locations for Plotting','true_loc_plot', 4, 5],
                [self.user_selections['Network Exploration']['pre_btn_text'], 'show_pre_range', 4, 13],
                ['Only greatest pre partner','show_greatest_pre', 4, 14],
                ['All pre partners', 'show_all_pre', 4, 15],
                [self.user_selections['Network Exploration']['post_btn_text'],'show_post_range', 4, 16],
                ['Only greatest post partner','show_greatest_post', 4, 17],
                ['All post partners', 'show_all_post', 4, 18],
                ]
            }

        checkbutton_functions = {
            'show_pre_range': lambda: self.one_sel_only('Network Exploration', 'show_pre_range'),
            'show_greatest_pre': lambda: self.one_sel_only('Network Exploration', 'show_greatest_pre'),
            'show_all_pre': lambda: self.one_sel_only('Network Exploration', 'show_all_pre'),
            'show_post_range': lambda: self.one_sel_only('Network Exploration', 'show_post_range'),
            'show_greatest_post': lambda: self.one_sel_only('Network Exploration', 'show_greatest_post'),
            'show_all_post': lambda: self.one_sel_only('Network Exploration', 'show_all_post')
        }


        for tab_key in checkbutton_data.keys():

            if tab_key == 'Cell Reconstruction':
                colspan = 1

            if tab_key == 'Network Exploration':
                colspan = 2
            
            for label, d_key, col, row in checkbutton_data[tab_key]:

                if d_key in checkbutton_functions:
                    associated_f = checkbutton_functions[d_key]
                else:
                    associated_f = None

                self.user_selections[tab_key][d_key] = IntVar(value=self.settings_dict[tab_key][d_key])

                if d_key in ['show_post_range', 'show_pre_range']:
                    self.user_selections[tab_key][f'{d_key}_sel'] = Checkbutton( 
                        self.tabs[tab_key], 
                        textvariable = label,
                        variable=self.user_selections[tab_key][d_key], 
                        onvalue=1, 
                        offvalue=0,
                        command =  associated_f         )

                else:
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
        
        # Make all buttons: ############ Need to complete one for cell classification.##############
        button_labels = {
            'Cell Reconstruction':[
                ["Start Proofreading Batch", 'pr_batch_seg', 6, 7, 1, ],
                ["Start Proofreading Single Cell", 'load_single_n_for_pr', 6, 8, 1],
                ["Start Classifying Batch", 'skip_seg_pr', 6, 9, 1],
                ["Save Cell", 'save_and_continue', 7, 7, 1],
                ["Next Cell", 'save_and_next', 7, 8, 1],
                ["Skip Current Cell", 'skip_seg_pr', 7, 9, 1],
                ["Start Proofreading Batch", 'pr_batch_syn', 7, 12, 1],
                ["Start Proofreading Single Cell", 'single_n_pr_syn', 7, 13, 1],
                ["Skip Current Cell", 'skip_syn_pr', 7, 14, 1],
                ],
            'Network Exploration': [
                ["Load Previous State", 'prev_sess', 4, 22, 2],
                ["Save Current State", 'save_sess', 4, 23, 2],
                ["Start Network Path Exploration",'np_start', 4, 6, 2],
                ["Start Sequential Cell Exploration", 'new_ss_start', 4, 19, 2],
                ]
        }


        button_functions = {

            'pr_batch_seg': lambda: threading.Thread(
                target=self.seg_pr_batch_start, 
                args=[], 
                name='pr_batch_seg').start(),

            'load_single_n_for_pr': lambda: threading.Thread(
                target=self.pr_single_neuron, 
                args=['seg'], 
                name='load_single_n_for_pr').start(),

            'skip_seg_pr': lambda: threading.Thread(
                target=self.skip_pr, 
                args=['segmentation'], 
                name='skip_seg_pr').start(),

            'save_and_continue': lambda: threading.Thread(
                target=self.save_cell_seg, 
                args=[], 
                name='save_and_continue').start(),

            'save_and_next': lambda: threading.Thread(
                target=self.save_cell_seg_and_next, 
                args=[], 
                name='save_and_next').start(),

            'pr_batch_syn': lambda: threading.Thread(
                target=self.synapse_seg_pr_batch_start, 
                args=[], 
                name='pr_batch_syn').start(),

            'single_n_pr_syn': lambda: threading.Thread(
                target=self.pr_single_neuron, 
                args=['syn'], 
                name='single_n_pr_syn').start(),

            'skip_syn_pr': lambda: threading.Thread(
                target=self.skip_pr, 
                args=['synapses'], 
                name='skip_syn_pr').start(),

            'prev_sess': lambda: threading.Thread(
                target=self.open_a_state, 
                args=[], 
                name='prev_sess').start(),

            'save_sess': lambda: threading.Thread(
                target=self.save_current_state, 
                args=[], 
                name='save_sess').start(),

            'np_start': lambda: threading.Thread(
                target=self.networkp_start, 
                args=[], 
                name='np_start').start(),

            'new_ss_start': lambda: threading.Thread(
                target=self.start_ss_session, 
                args=[], 
                name='new_ss_start').start(),
        }

        for tab_key in button_labels.keys():

            for lab, k, col, row, colspan in button_labels[tab_key]:

                self.user_selections[tab_key][k] = Button(    
                    self.tabs[tab_key], 
                    text=lab, 
                    command=button_functions[k]       )

                self.user_selections[tab_key][k].grid(
                    row=row, column=col, padx=10, pady=2, sticky = 'ew', columnspan=colspan)
        
    def make_linked_string(self, dtype, min_or_max):

        temp = StringVar()

        temp.trace(
            "w", 
            lambda name, 
            index, 
            mode, 
            sv=temp: self.update_btn_text(dtype, min_or_max)
            )

        return temp

    def one_sel_only(self, mode, to_sel):

        to_unsel_list = self.mutually_exclusive_options[to_sel]

        if self.user_selections[mode][to_sel].get() == 1:

            for to_unsel in to_unsel_list:

                if self.user_selections[mode][to_unsel].get() == 1:

                    self.user_selections[mode][to_unsel].set(0)

    def get_segs_and_layers(self):  

        self.layer_type_d = {}

        retrieved_info = set()
        most_recent_agglo_id = None
        last_tried_path = None
        region_type_status = Label(self.tabs['Network Exploration'], text='')
        region_type_status.grid(row=2, column=2, columnspan=2, sticky='w', padx=10)

        while True:

            time.sleep(1)

            current_path = self.user_selections['Network Exploration']['cred'].get().strip()

            if current_path != last_tried_path:

                last_tried_path = current_path

                try:
                    self.create_client('Network Exploration')
                    time.sleep(0.5)
                
                except FileNotFoundError:
                    if retrieved_info != set(['region', 'type']):
                        region_type_status['text'] = 'Selected Credentials File Not Found'

                    time.sleep(0.5)
                    continue

                except PermissionError:
                    time.sleep(0.5)
                    continue

                except AttributeError:
                    if retrieved_info != set(['region', 'type']):
                        region_type_status['text'] = 'Selected Credentials File Not Functional'
                    time.sleep(0.5)
                    continue
            else:
                continue

            base_id = self.user_selections['Network Exploration']['base_seg'].get().strip()
            agglo_id = self.user_selections['Network Exploration']['seg'].get().strip()

            agglo_layer_db = f'{base_id}.{agglo_id}_regions_types'

            if agglo_layer_db == most_recent_agglo_id:
                time.sleep(0.5)
                continue
            else:
                most_recent_agglo_id = agglo_layer_db
            
            try:
                self.client.get_table(agglo_layer_db)
                
            except NotFound:
                if retrieved_info != set(['region', 'type']):
                    region_type_status['text'] = f'No Database {agglo_layer_db}'
                time.sleep(0.5)
                continue
                
            region_type_status['text'] = f'Querying Database {agglo_layer_db}'
            self.agglo_layer_db = agglo_layer_db

            for dtype, col in (('region', 3), ('type', 2)):

                query = f"""SELECT DISTINCT {dtype} FROM {agglo_layer_db}"""

                res = self.client.query(query).result()
                final_list = [x[dtype] for x in res if x[dtype]!=dtype]
                final_list.sort()

                self.layer_type_d[dtype] = {'buttons': {}, 'values': {}} 

                for x in self.layer_type_d[dtype]['buttons'].keys():
                    self.layer_type_d[dtype]['buttons'][x].grid_forget()

                region_type_status['text'] = ''

                for pos, x in enumerate(final_list):
                
                    row = pos+2

                    self.layer_type_d[dtype]['values'][x] = IntVar(0)

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
                
                retrieved_info.add(dtype)
                
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

    def update_mtab(self, new_message):
        
        for i in range(1, self.lowest_line+8):

            Label(self.tabs['Messages'], text=self.current_messages[i+1]+' '*200).grid(
                    row=i, column=0, columnspan=6, sticky='w', padx=10)

            self.current_messages[i] = self.current_messages[i+1]  

        Label(self.tabs['Messages'], text=new_message+ ' '*200).grid(
                row=self.lowest_line+8, column=0, columnspan=6, sticky='w', padx=10)

        self.current_messages[self.lowest_line+8] = new_message + ' '*200
 
    def save_current_state(self):

        ftypes = (("json files","*.json"), ("all files","*.*"))

        selected_file = filedialog.asksaveasfilename(initialdir = "/", title = "Select file", filetypes = ftypes)

        if selected_file == '': return

        json_whole_state = self.viewer.state.to_json()

        with open(selected_file + '.json', 'w') as fp:
            json.dump(json_whole_state, fp)

        if self.explore_mode == 'sequential_segment':
            self.figure.savefig(selected_file + '_partner_profile.png')

        if self.explore_mode == 'network_path':
            print('need to save network fig here')

    def open_a_state(self):

        ftypes = (("json files","*.json"), ("all files","*.*"))

        selected_file = filedialog.askopenfilename(initialdir = "/", title = "Select file", filetypes = ftypes)

        if selected_file == '': return

        pp_file_path = selected_file.split('.json')[0]+'_partner_profile.png'

        print('need something here to extend to network path')

        if os.path.exists(pp_file_path):
            load = Image.open(pp_file_path)
            render = ImageTk.PhotoImage(load)
            img = Label(self.tabs['Figures'], image=render)
            img.image = render
            img.place(x=0, y=0)

        with open(selected_file, 'r') as fp:
            state_to_load = json.load(fp)

        self.viewer.set_state(state_to_load)

        webbrowser.open(str(self.viewer))
  
    def fields_complete(self, required_info, mode, opf=[]):

        for dkey in required_info:

            curr_val = self.user_selections[mode][dkey].get()

            if curr_val == '' and dkey not in opf:

                wrong_field = self.field_titles[dkey]

                self.update_mtab(f'Field {wrong_field} is empty: Please complete it')

                return False
                
            else:
                self.settings_dict[mode][dkey] = curr_val

        if mode == 'Cell Reconstruction':
            for a in range(10):
                custom_ops = self.user_selections[mode][f'custom_syn_cell_{a}_options'].get().strip()
                custom_cat = self.user_selections[mode][f'custom_syn_cell_{a}_category'].get().strip()
                self.settings_dict[mode][f'custom_syn_cell_{a}_options'] = deepcopy(custom_ops)
                self.settings_dict[mode][f'custom_syn_cell_{a}_category'] = deepcopy(custom_cat)

        with open(f'{self.script_directory}/CREST_settings.json', 'w') as fp:
            json.dump(self.settings_dict, fp)

        return True

    def create_edge_list(self):
        
        self.update_mtab('Downloading connectome data from BigQuery')

        query = f"""

            {self.common_browse_query} 
        
            SELECT 
                e.pre_seg_id,
                e.post_seg_id,
                e.pair_count
                FROM 
                all_edges AS e
                INNER JOIN selected_ids AS a
                    ON e.pre_seg_id = a.seg_id
                INNER JOIN selected_ids AS b
                    ON e.post_seg_id = b.seg_id
            WHERE e.pre_seg_id IS NOT NULL AND e.post_seg_id IS NOT NULL AND e.pair_count >= {self.min_syn}"""

                     

        df = self.client.query(query).result().to_dataframe(bqstorage_client=self.bqstorageclient)#, progress_bar_type='tqdm_gui')
        self.update_mtab('Converting downloaded data into edge list')

        self.syn_edge_list = [(x[0], x[1], int(x[2])) for x in json.loads(df.to_json(orient='values'))]
        
    def get_sel_types_regions_query(self):

        sd = {}
        types_to_query = []

        for dtype in self.layer_type_d.keys():

            sd[dtype] = []

            for x in self.layer_type_d[dtype]['buttons'].keys():
                if self.layer_type_d[dtype]['values'][x].get() == 1:
                    sd[dtype].append(x)

            if len(sd[dtype]) == 0:
                self.update_mtab(f'No specific cell {dtype}s selected, all will be used')
            else:
                types_to_query.append(dtype)
        
        if len(types_to_query) == 0: 
            return ''

        criterion1 = types_to_query[0]
        q1 = ','.join([str(f"'{x}'") for x in sd[criterion1]])

        query = f"""SELECT CAST(agglo_id AS STRING) AS seg_id
                    FROM {self.agglo_layer_db}
                    WHERE {criterion1} IN ({q1})"""
        
        if len(types_to_query) == 2:

            criterion2 = types_to_query[1]
            q2 = ','.join([str(f"'{x}'") for x in sd[criterion2]])

            query = f"""{query} AND {criterion2} IN ({q2})"""

        query = f"""layer_type_ids AS ({query}),"""
        
        return query

    def create_connectome_graph(self):

        self.update_mtab(f'Creating the connectome graph for path browsing')

        self.browsing_graph = ig.Graph(directed=True)

        self.update_mtab('Adding all vertices')
        self.all_vertices_set = set([str(a) for b in [e[:2] for e in self.syn_edge_list] for a in b])
        self.all_vertices = list(self.all_vertices_set)
        self.browsing_graph.add_vertices(self.all_vertices)

        self.update_mtab('Adding all edges')
        self.browsing_graph.add_edges([x[:2] for x in self.syn_edge_list])
        self.browsing_graph.es['weight'] = [x[2] for x in self.syn_edge_list]

    def common_browse_start(self):

        self.project_id = self.user_selections['Network Exploration']['user'].get().strip()
        self.em_id = self.user_selections['Network Exploration']['em'].get().strip()
        self.em = f'brainmaps://{self.project_id}:{self.em_id}'
        self.base_id = self.user_selections['Network Exploration']['base_seg'].get().strip()
        self.agglo_id = self.user_selections['Network Exploration']['seg'].get().strip()
        self.agglo_seg = f'brainmaps://{self.project_id}:{self.base_id}:{self.agglo_id}' ###
        self.agglo_seg = f'brainmaps://{self.project_id}:{self.base_id}_{self.agglo_id}_flat'
        self.agglo_info_db = f'{self.base_id}.{self.agglo_id}_objinfo'
        self.syn_id = self.user_selections['Network Exploration']['syn_seg'].get().strip()
        self.syn_seg = f'brainmaps://{self.project_id}:{self.syn_id}'
        self.syn_db_name = f'{self.syn_id}.synaptic_connections_with_skeleton_classes'

        self.get_vx_sizes('Network Exploration')

        with self.viewer.config_state.txn() as s:
            s.show_layer_panel = True

        self.set_syn_thresholds()

        # Set common browsing query
        region_type_query = self.get_sel_types_regions_query()
        
        if region_type_query == '':
            final_selected_ids_statement = f"""
                selected_ids AS (
                    SELECT seg_id FROM connectivity_selected_ids
                    LIMIT {self.max_cases_view})"""

        else:
            final_selected_ids_statement = f"""
                selected_ids AS (
                    SELECT seg_id FROM (
                        SELECT seg_id FROM connectivity_selected_ids
                        INTERSECT DISTINCT 
                        SELECT seg_id FROM layer_type_ids
                    )
                    LIMIT {self.max_cases_view})"""


        if '_with_skeleton_classes' in self.syn_db_name:
            where_statement =  "WHERE pre_synaptic_site.skel_type = 'axon' AND post_synaptic_partner.skel_type IN ('dendrite', 'soma')"
        else:
            where_statement = ""
       
        self.common_browse_query = f"""
            WITH
            
            {region_type_query}

            all_edges AS (
                SELECT 
                    CAST(pre_synaptic_site.neuron_id AS STRING) AS pre_seg_id, 
                    CAST(post_synaptic_partner.neuron_id AS STRING) AS post_seg_id, 
                    COUNT(*) AS pair_count
                FROM {self.syn_db_name}
                {where_statement}
                GROUP BY pre_synaptic_site.neuron_id, post_synaptic_partner.neuron_id
                ),
            post_data AS (
                SELECT 
                    pre_seg_id, 
                    COUNT(pre_seg_id) AS num_post_partners, 
                    SUM(pair_count) AS total_out_syn, 
                    MAX(pair_count) AS greatest_post_partner
                FROM all_edges
                GROUP BY pre_seg_id
                ),
            pre_data AS (
                SELECT 
                    post_seg_id, 
                    COUNT(post_seg_id) AS num_pre_partners, 
                    SUM(pair_count) AS total_in_syn, 
                    MAX(pair_count) AS greatest_pre_partner
                FROM all_edges
                GROUP BY post_seg_id
                ),
            selected_pre AS (
                SELECT pre_seg_id AS seg_id
                FROM post_data
                WHERE 
                    num_post_partners >= {self.syn_thresholds['min_post']} AND 
                    num_post_partners <= {self.syn_thresholds['max_post']} AND 
                    total_out_syn >= {self.syn_thresholds['min_syn_given_total']} AND 
                    total_out_syn <= {self.syn_thresholds['max_syn_given_total']} AND 
                    greatest_post_partner >= {self.syn_thresholds['min_syn_to']} AND 
                    greatest_post_partner <= {self.syn_thresholds['max_syn_to']}
                ),
            selected_post AS (
                SELECT post_seg_id AS seg_id
                FROM pre_data
                WHERE 
                    num_pre_partners >= {self.syn_thresholds['min_pre']} AND 
                    num_pre_partners <= {self.syn_thresholds['max_pre']} AND 
                    total_in_syn >= {self.syn_thresholds['min_syn_received_total']} AND 
                    total_in_syn <= {self.syn_thresholds['max_syn_received_total']} AND 
                    greatest_pre_partner >= {self.syn_thresholds['min_syn_from']} AND 
                    greatest_pre_partner <= {self.syn_thresholds['max_syn_from']}
                ),

            connectivity_selected_ids AS (
                SELECT seg_id FROM (
                    SELECT seg_id FROM selected_pre
                    INTERSECT DISTINCT 
                    SELECT seg_id FROM selected_post
                )
                ),

            {final_selected_ids_statement} """
        

    def networkp_start(self):

        self.viewer.set_state({})

        # Switch to messages tab and check required fields are completed:
        self.tab_control.select(self.tabs['Messages'])

        required_info = [
            'user', 'base_seg', 'cred', 'em', 'seg', 'syn_seg', 
            'max_p_len', 'min_syn_per_c', 'dir_p_only', 'true_loc_plot'
            ]   

        optional_fields = [
            'min_syn_from',
            'min_syn_to',
            'max_syn_from',
            'max_syn_to',
            'min_syn_received_total', 
            'max_syn_received_total', 
            'min_pre',
            'max_pre',
            'min_syn_given_total', 
            'max_syn_given_total', 
            'min_post',
            'max_post',
        ]     
        
        if not self.fields_complete(required_info, 'Network Exploration', opf=optional_fields): return

        self.explore_mode = 'network_path'
        self.max_path_legnth = int(self.user_selections['Network Exploration']['max_p_len'].get().strip())
        self.dir_status = int(self.user_selections['Network Exploration']['dir_p_only'].get())
        self.min_syn = int(self.user_selections['Network Exploration']['min_syn_per_c'].get().strip())
        self.max_cases_view = 1000000000

        self.common_browse_start()
        
        self.create_edge_list()

        self.update_mtab(f'{len(self.syn_edge_list)} connections in total')

        self.create_connectome_graph()

        self.set_np_keybindings()
        self.change_view(self.starting_location, 0.22398, 4000)
        self.reset_np()
        self.create_and_open_pr_link('Network Exploration', 3, 25, label=False)

        # Setup graph plotting:
        threading.Thread(target=self.continous_plot_updating, args=(), name='plot_updating_worker').start()

    def set_np_keybindings(self):

        self.viewer.actions.add('clear-connections', lambda s: self.reset_np())
        self.viewer.actions.add('pair-paths', self.pair_paths)
        self.viewer.actions.add('partner-gens', self.start_partner_view)
        self.viewer.actions.add('inc-partner', lambda s: self.inc_partner())
        self.viewer.actions.add('dec-partner', lambda s: self.dec_partner())
        self.viewer.actions.add('review-subpaths', lambda s: self.review_subpaths())
        self.viewer.actions.add('inc-ind-path', lambda s: self.inc_ind_path())
        self.viewer.actions.add('dec-ind-path', lambda s: self.dec_ind_path())
        self.viewer.actions.add('add-syn-to-pairs', lambda s: self.add_synapses_to_pairs())
        self.viewer.actions.add('add-syn-to-individual-path', lambda s: self.get_synapses_for_a_path())
         
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.data_view['shift+mousedown0'] = 'pair-paths'
            s.input_event_bindings.data_view['alt+mousedown0'] = 'partner-gens'
            s.input_event_bindings.viewer['keyc'] = 'clear-connections'
            s.input_event_bindings.viewer['keyy'] = 'review-subpaths'

    def reset_np(self):

        with self.viewer.txn(overwrite=True) as s:
            s.layers['EM aligned stack'] = neuroglancer.ImageLayer(source=self.em)
            s.layers['Segmentation'] = neuroglancer.SegmentationLayer(source=self.agglo_seg)
            s.layers['Current synapses'] = neuroglancer.AnnotationLayer()

        self.update_msg('Now in general browsing mode')
        self.np_mode = 'general' 
        self.show_syn_status = None
        self.pair_selection = []
        self.graph_real_positions = 0
        self.graph_layout = []
           
    def clear_current_synapses(self):

        with self.viewer.txn(overwrite=True) as s:
            s.layers['Current synapses'].annotations = []

    def check_selected_segment(self, layer, action, banned_segs = [], acceptable_segs='all'):

        if layer not in action.selectedValues: 
            return 'None'

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
        self.seed_segment = selected_segment
        
        self.path_segments = {}
        self.gen_num = 0
        self.path_segments[self.gen_num] = [self.seed_segment]
        self.update_segments(self.path_segments[self.gen_num], 'Segmentation')
        self.path_status = 'one_gen'
        
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyf'] = 'inc-partner'
            s.input_event_bindings.viewer['keyd'] = 'dec-partner'
            s.input_event_bindings.viewer['keys'] = 'add-syn-to-pairs'

        self.np_mode = 'paths'

    def continous_plot_updating(self):

        while True:

            all_vertices = set()
            node_gen_lookup = {}

            if self.np_mode in ['paths', 'subpaths']:

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

            time.sleep(0.1)

    def get_graph_layout(self, sg, all_vertices):

        if self.graph_real_positions == 1:

            r = self.get_info_from_bigquery(['id', 'bbox'], 'id', all_vertices, self.agglo_info_db)

            r_dict = {  str(x['id']): 
                            [   x['bbox']['start']['x']+(x['bbox']['size']['x']/2),
                                x['bbox']['start']['y']+(x['bbox']['size']['y']/2),
                                ]
                    for x in r
                    }
            
            graph_layout = [r_dict[node['name']] for node in sg.vs]

        else:
            graph_layout = sg.layout_auto()

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

        ig.plot(
            sg, 
            target=temp_save_path,
            margin = (100,100,100,100), 
            bbox=(self.dimensions[0],self.dimensions[1]), 
            edge_width = edge_weights,
            edge_color =  edge_colours,
            vertex_label = node_labels,
            vertex_label_color = node_lab_colours,
            vertex_label_dist = [0 for v in sg.vs],
            vertex_label_font = [0.1 for v in sg.vs],
            #vertex_shape = vertex_shapes, 
            vertex_color = node_colours, 
            vertex_size = 20, 
            edge_arrow_size=1.0, 
            layout=self.graph_layout
            )

        load = Image.open(temp_save_path)
        render = ImageTk.PhotoImage(load)
        img = Label(self.tabs['Figures'], image=render)
        img.image = render
        img.place(x=0, y=0)
        os.remove(temp_save_path)

    def get_next_gen(self):

        if self.gen_num >= 0:
            graphmode = 'OUT'
            all_prev_segs = [self.path_segments[a] for a in range(self.gen_num+1)]

        else:
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

    def inc_partner(self):

        if self.gen_num >= 0:

            if self.path_status == 'one_gen':

                next_gen_segs = self.get_next_gen()

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

                next_gen_segs = self.get_next_gen()

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

    def get_corrected_bbox_centre(self, bbox, adj_key, rel_to_em=False):

        result = []

        coords = ['x', 'y', 'z']

        for coord in coords:
            unadj = bbox['start'][coord] + (bbox['size'][coord] // 2)
            result.append(unadj*self.vx_sizes[adj_key][coords.index(coord)])
            
        if rel_to_em==True:
            result = [int(result[x]/self.vx_sizes['em'][x]) for x in range(3)]

        return result

    def get_synapses_for_set_of_neurons(self, set_of_neurons, pre_or_post, agglo_or_base):

        set_of_neurons = [str(x) for x in set_of_neurons]

        if agglo_or_base == 'base':
            id_key = 'base_neuron_ids'

        if agglo_or_base == 'agglo':
            id_key = 'neuron_id'

        info_to_get = [
            'bounding_box AS bounding_box',
            'pre_synaptic_site.id AS pre_syn_id',
            f'pre_synaptic_site.{id_key} AS pre_seg_id',
            'post_synaptic_partner.id AS post_syn_id',
            f'post_synaptic_partner.{id_key} AS post_seg_id'
        ]

        if '_with_skeleton_classes' in self.syn_db_name:
            info_to_get.append('pre_synaptic_site.skel_type AS pre_skel')
            info_to_get.append('post_synaptic_partner.skel_type AS post_skel')

        results = self.get_info_from_bigquery(info_to_get, f'{pre_or_post}.{id_key}', set_of_neurons, self.syn_db_name)

        if '_with_skeleton_classes' in self.syn_db_name:
            print('before', len(results))
            results = [x for x in results if str(x['pre_skel']) == 'axon' and str(x['post_skel']) in ['dendrite', 'soma']]
            print('after', len(results))
        
        return results

    def add_synapses_to_pairs(self):

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
        r = self.get_synapses_for_set_of_neurons(distal_segs+prox_segs, 'pre_synaptic_site', 'agglo')
        results = [x for x in r if str(x['post_seg_id']) in distal_segs+prox_segs]
        results = [x for x in r if str(x[dist_type]) in distal_segs and str(x[prox_type]) in prox_segs]

        point_annotations = []

        for row in results:
            
            pre_seg_id, post_seg_id = row['pre_seg_id'], row['post_seg_id']
            pre_syn_id, post_syn_id = row['pre_syn_id'], row['post_syn_id']

            point = np.array(self.get_corrected_bbox_centre(row['bounding_box'], 'syn_seg', rel_to_em=True))

            if prox_type == 'pre_seg_id':
                desc = f'{pre_seg_id}->{post_seg_id}'

            if prox_type == 'post_seg_id':
                desc = f'{post_seg_id}<-{pre_seg_id}'

            pid = f'{pre_syn_id}->{post_syn_id}'

            pa = neuroglancer.PointAnnotation(id=pid, description=desc, point=point)

            point_annotations.append(pa)

        with self.viewer.txn(overwrite=True) as s:
            s.layers['Current synapses'].annotations = point_annotations
            s.selectedLayer.layer = 'Current synapses'


    def return_to_partners(self):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyf'] = 'inc-partner'
            s.input_event_bindings.viewer['keyd'] = 'dec-partner'
            s.input_event_bindings.viewer['keys'] = 'add-syn-to-pairs'
            
        self.ind_paths = None
        self.clear_current_synapses()

        self.update_segments(self.path_segments[self.gen_num], 'Segmentation')

        if self.gen_num > 0:
            self.update_msg(f'Post-synaptic generation {self.gen_num} displayed')
        else:
            self.update_msg(f'Pre-synaptic generation {abs(self.gen_num)} displayed')

        self.np_mode = 'paths'

    def review_subpaths(self):

        if self.np_mode == 'subpaths':
            self.return_to_partners()
            return

        if not self.path_status:
            self.update_msg('Please first navigate to one non-zero generation to view all paths for')
            return

        if 'two_gen' in self.path_status or self.gen_num == 0:
            self.update_msg('Please select only one non-zero generation to view all paths for')
            return
        
        if self.gen_num < 0:
            paths = self.browsing_graph.get_all_simple_paths(self.seed_segment, cutoff=abs(self.gen_num), mode='IN')
        else:
            paths = self.browsing_graph.get_all_simple_paths(self.seed_segment, cutoff=self.gen_num, mode='OUT')

        self.ind_paths = []
        
        for path in paths:
            if len(path) == abs(self.gen_num)+1:
                seg_ids_path = [self.all_vertices[x] for x in path]
                self.ind_paths.append(seg_ids_path)
                                
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyf'] = 'inc-ind-path'
            s.input_event_bindings.viewer['keyd'] = 'dec-ind-path'
            s.input_event_bindings.viewer['keys'] = 'add-syn-to-individual-path'

        self.np_mode = 'subpaths' 
        self.ind_path_pos = 0
        self.update_ind_path()
        
    def update_ind_path(self):

        self.update_segments(self.ind_paths[self.ind_path_pos],'Segmentation')

        curr = self.ind_path_pos+1
        tot = len(self.ind_paths)

        if self.np_mode == 'subpaths':

            if self.gen_num > 0:
                pre_or_post = 'post'
            else:
                pre_or_post = 'pre'

            origin = self.seed_segment
            target =  self.ind_paths[self.ind_path_pos][-1]
            g = abs(self.gen_num)

            self.update_msg(f'Path {curr} of {tot} to {pre_or_post}-synaptic generation {g}, from segment {origin} to segment {target}')

        if self.np_mode == 'pairs':

            origin  = self.pair_selection[0]
            target = self.pair_selection[1]

            self.update_msg(f'Path {curr} of {tot}, from segment {origin} to segment {target}')

        self.clear_current_synapses()

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

        if self.np_mode == 'subpaths':

            if self.gen_num > 0:
                path_type = 'post'
            else:
                path_type = 'pre'

        if self.np_mode == 'pairs':

            if self.dir_status == 1:
                path_type = 'post'

            if self.dir_status == 0:
                path_type = 'undirected'

        r = self.get_synapses_for_set_of_neurons(self.ind_paths[self.ind_path_pos], 'pre_synaptic_site', 'agglo')
        results = [x for x in r if str(x['post_seg_id']) in self.ind_paths[self.ind_path_pos]]

        normal_syn, fb_syn, ff_syn = self.sort_synapse_order(r, path_type)
    
        point_annotations = []

        for dtype, results in [['f', normal_syn], ['fb', fb_syn], ['ff', ff_syn]]:

            for row in results:

                point = np.array(self.get_corrected_bbox_centre(row['bounding_box'], 'syn_seg', rel_to_em=True))

                pre_seg_id, post_seg_id = row['pre_seg_id'], row['post_seg_id']
                pre_syn_id, post_syn_id = row['pre_syn_id'], row['post_syn_id']

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

                pa = neuroglancer.PointAnnotation(id= f'{pre_syn_id}->{post_syn_id}', description=desc, point=point)
                point_annotations.append(pa)
        
        with self.viewer.txn(overwrite=True) as s:
            s.layers['Current synapses'].annotations = point_annotations
            s.selectedLayer.layer = 'Current synapses'

    def get_node_colours_and_labels(self, sg, displayed_segs, node_gen_lookup, root_nodes):

        node_labels = []
        node_colours = []
        node_lab_colours = []

        for node in sg.vs:

            seg_id = node['name']

            gen_num = node_gen_lookup[seg_id]

            if seg_id in displayed_segs:

                lab = f'                            {gen_num}    ID{seg_id}'

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
            self.update_mtab(f'Getting all paths from segment {origin} to segment {target} with path legnth {self.max_path_legnth} or less')

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
                    s.input_event_bindings.viewer['keyf'] = 'inc-ind-path'
                    s.input_event_bindings.viewer['keyd'] = 'dec-ind-path'
                    s.input_event_bindings.viewer['keys'] = 'add-syn-to-individual-path'
                
                self.np_mode = 'pairs'
                self.ind_path_pos = 0
                self.update_ind_path()

    def start_ss_session(self):

        self.viewer.set_state({})

        self.tab_control.select(self.tabs['Messages'])

        required_info = [
            'cred', 'em', 'seg', 'user', 'base_seg', 
            'syn_seg', 'max_syn_plot',
            'show_all_pre', 'show_greatest_pre',
            'show_pre_range', 'show_all_post',
            'show_greatest_post', 'show_post_range',
            ]

        optional_fields = [
            'min_syn_from',
            'min_syn_to',
            'max_syn_from',
            'max_syn_to',
            'min_syn_received_total', 
            'max_syn_received_total', 
            'min_pre',
            'max_pre',
            'min_syn_given_total', 
            'max_syn_given_total', 
            'min_post',
            'max_post',
            'max_cases_view',
        ]

        if not self.fields_complete(required_info, 'Network Exploration', opf=optional_fields): return

        self.explore_mode = 'sequential_segment'
        self.max_plot_c = int(self.user_selections['Network Exploration']['max_syn_plot'].get().strip())

        mcv = self.user_selections['Network Exploration']['max_cases_view'].get().strip()

        if mcv == '':
            self.max_cases_view = 10000000
        else:
            self.max_cases_view = int(mcv)
        
        self.common_browse_start()
        
        self.set_pre_and_post_display()
        self.get_partner_point_annos()
        
        
        if len(self.seg_ids) == 0:
            self.update_mtab('No cells meet selected criteria, please revise')
            return
        else:
            self.update_mtab(f'{len(self.seg_ids)} cells meeting selected criteria to view')

        self.ss_col = {
            'pre': 'skyblue',
            'post': 'pink',
            'sel': 'lightgreen',
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
        self.change_view(self.starting_location, 0.22398, 4000)
        self.update_partners()
        self.create_and_open_pr_link('Network Exploration', 3, 25, label=False)

    def change_pre_post(self):

        if self.ss_mode != 'general': return

        if self.pre_or_post_display == 'post':
            self.pre_or_post_display = 'pre'
        else:
            self.pre_or_post_display = 'post'
        
        self.update_msg(f'Select partners to view (P): {self.pre_or_post_display}-synaptic', layer='pre_or_post')

    def create_ss_keybindings(self):

        self.viewer.actions.add('add-or-remove-seg-ss', self.add_or_remove_seg_ss)
        self.viewer.actions.add('prev-case', lambda s: self.prev_seg())
        self.viewer.actions.add('next-case', lambda s: self.next_seg())
        self.viewer.actions.add('seg-inc', lambda s: self.inc_seg())
        self.viewer.actions.add('seg-dec', lambda s: self.dec_seg())
        self.viewer.actions.add('start-seg-review', lambda s: self.start_single_seg_review())
        self.viewer.actions.add('start-batch-review', lambda s: self.start_batch_review())
        self.viewer.actions.add('review-subbatch', lambda s: self.review_subbatch())
        self.viewer.actions.add('change-pre-post', lambda s: self.change_pre_post())

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.data_view['dblclick0'] = 'add-or-remove-seg-ss'
            s.input_event_bindings.viewer['keyd'] = 'prev-case'
            s.input_event_bindings.viewer['keyf'] = 'next-case'
            s.input_event_bindings.viewer['keyq'] = 'start-seg-review'
            s.input_event_bindings.viewer['keyw'] = 'start-batch-review'
            s.input_event_bindings.viewer['keya'] = 'review-subbatch'
            s.input_event_bindings.viewer['keyp'] = 'change-pre-post'

    def add_or_remove_seg_ss(self, action_state):  

        agglo_seg = self.check_selected_segment('review segs', action_state)

        if agglo_seg == 'None': return

        all_segs = [str(x) for x in self.viewer.state.layers['review segs'].segments]

        if agglo_seg in all_segs:
            all_segs.remove(agglo_seg)
        else:
            all_segs.append(agglo_seg)
        
        self.update_segments(all_segs, 'review segs', seg_col=self.ss_col[self.pre_or_post_display])


    def create_ss_layers(self):

        with self.viewer.txn(overwrite=True) as s:

            s.layers['EM aligned stack'] = neuroglancer.ImageLayer(source=self.em)
            s.layers['selected segment'] = neuroglancer.SegmentationLayer(source=self.agglo_seg)

            for dtype in ('pre', 'post'):

                if self.display[dtype] != 'none':
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
        self.figure.text(0.5, 0.04, 'Number of synapses', ha='center', va='center')
        self.figure.text(0.06, 0.5, 'Number of post-synaptic partners                Number of pre-synaptic partners', ha='center', va='center', rotation='vertical')
        self.plotter.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
   
    def set_syn_thresholds(self):

        self.syn_thresholds = {}

        sel_keys = [
            'min_syn_received_total',
            'max_syn_received_total',
            'min_pre', 
            'max_pre', 
            'min_syn_given_total', 
            'max_syn_given_total', 
            'min_post',
            'max_post',
            'min_syn_from', 
            'min_syn_to',
            'max_syn_to',
            'max_syn_from',
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

                #self.update_mtab(f"No valid entry for field {self.field_titles[k]}, value set to {self.syn_thresholds[k]}")

        self.update_mtab('Selecting cells with:') 

        self.update_mtab(f"- At least {self.syn_thresholds['min_syn_received_total']} synapses received in total")
        self.update_mtab(f"- At most {self.syn_thresholds['max_syn_received_total']} synapses received in total")

        self.update_mtab(f"- At least {self.syn_thresholds['min_syn_given_total']} synapses made in total")
        self.update_mtab(f"- At most {self.syn_thresholds['max_syn_given_total']} synapses made in total")

        self.update_mtab(f"- At least {self.syn_thresholds['min_pre']} pre-synaptic partners")
        self.update_mtab(f"- At most {self.syn_thresholds['max_pre']} pre-synaptic partners")

        self.update_mtab(f"- At least {self.syn_thresholds['min_post']} post-synaptic partners")
        self.update_mtab(f"- At most {self.syn_thresholds['max_post']} post-synaptic partners")

        self.update_mtab(f"- At least one pre-synaptic partner with {self.syn_thresholds['min_syn_from']} or more synapses")
        self.update_mtab(f"- No pre-synaptic partners with {self.syn_thresholds['max_syn_from']} or more synapses")

        self.update_mtab(f"- At least one post-synaptic partner with {self.syn_thresholds['min_syn_to']} or more synapses")
        self.update_mtab(f"- No post-synaptic partners with {self.syn_thresholds['max_syn_to']} or more synapses")

    def set_pre_and_post_display(self):

        self.display = {}

        for dtype in ('pre', 'post'):

            self.display[dtype] = 'none'

            options = (f'show_all_{dtype}', f'show_greatest_{dtype}', f'show_{dtype}_range')

            for selection in options:

                if int(self.user_selections['Network Exploration'][selection].get()) == 1:

                    chosen_opt = [x for x in selection.split('_') if x not in ('show', dtype)][0]

                    self.display[dtype] = chosen_opt

    def get_partner_point_annos(self):

        self.update_mtab(f'Pre-loading synapse locations')

        query = f"""
        
            {self.common_browse_query} 
            
            SELECT 
                CAST(c.seg_id AS STRING) AS sel_seg,
                e.location.x,
                e.location.y, 
                e.location.z,
                CAST(e.pre_synaptic_site.neuron_id AS STRING) AS pre_seg_id,
                CAST(e.post_synaptic_partner.neuron_id AS STRING) AS post_seg_id
                FROM 
                {self.syn_db_name} AS e
                INNER JOIN selected_ids AS c
                    ON ((CAST(e.pre_synaptic_site.neuron_id AS STRING) = c.seg_id) OR (CAST(e.post_synaptic_partner.neuron_id AS STRING) = c.seg_id))
            WHERE e.pre_synaptic_site.neuron_id IS NOT NULL AND e.post_synaptic_partner.neuron_id IS NOT NULL"""


        raw = self.ensure_results_from_bq(query, self.syn_db_name)

        # Organize synapse locations:
        coords = ['x', 'y', 'z']

        first_d = {}

        for r in raw:

            location = [int((r[coords[x]]*self.vx_sizes['syn_seg'][x])/self.vx_sizes['em'][x]) for x in range(3)]

            if r['sel_seg'] == r['pre_seg_id']:
                partner_seg_key = 'post_seg_id'
                mode = 'post'
            else:
                assert r['sel_seg'] == r['post_seg_id']
                partner_seg_key = 'pre_seg_id'
                mode = 'pre'

            if r['sel_seg'] not in first_d:
                first_d[r['sel_seg']] = {x: {} for x in ('pre', 'post')}

            if r[partner_seg_key] not in first_d[r['sel_seg']][mode]:
                first_d[r['sel_seg']][mode][r[partner_seg_key]] = []

            first_d[r['sel_seg']][mode][r[partner_seg_key]].append(location)

        # Create all point annotations:
        self.pa_dict = {}
        self.plot_dict = {}
        
        for mode in ('pre', 'post'):

            self.pa_dict[mode] = {}

            for sel_seg in first_d.keys():

                for partner_seg in first_d[sel_seg][mode]:

                    point_annos = []

                    n_syn = len(first_d[sel_seg][mode][partner_seg])

                    for pos, loc in enumerate(first_d[sel_seg][mode][partner_seg]):

                        desc = f'{mode}-synaptic partner {partner_seg}, synapse {pos} of {n_syn}'
                        pa = {'point': np.array(loc), 'id': f'{partner_seg}_{pos}', 'description': desc}
                        point_annos.append(pa)

                    if sel_seg not in self.pa_dict[mode]:
                        self.pa_dict[mode][sel_seg] = {}
                    
                    if n_syn not in self.pa_dict[mode][sel_seg]:
                        self.pa_dict[mode][sel_seg][n_syn] = {}

                    self.pa_dict[mode][sel_seg][n_syn][partner_seg] = tuple(point_annos)

            self.plot_dict[mode] = {} 
            
            for sel_seg in self.pa_dict[mode].keys():

                y_axis_data = []

                for x in range(1, self.max_plot_c+1):

                    if x in self.pa_dict[mode][sel_seg].keys():
                        n_syn = len(self.pa_dict[mode][sel_seg][x].keys())
                        y_axis_data.append(n_syn)

                    else:
                        y_axis_data.append(0)
                
                self.plot_dict[mode][sel_seg] = y_axis_data

            # Drop any point annotations that you don't want to show:

            if mode == 'pre':
                range_min = self.syn_thresholds['min_syn_from']
                range_max = self.syn_thresholds['max_syn_from']

            if mode == 'post':
                range_min = self.syn_thresholds['min_syn_to']
                range_max = self.syn_thresholds['max_syn_to']

            for seg in self.pa_dict[mode].keys():

                if self.display[mode] == 'none':
                    n_to_keep = set()

                if self.display[mode] == 'greatest':
                    n_to_keep = set([max(self.pa_dict[mode][seg])])

                if self.display[mode] == 'all':
                    n_to_keep = set(self.pa_dict[mode][seg])

                if self.display[mode] == 'range':
                    n_to_keep = set([x for x in self.pa_dict[mode][seg] if (x >= range_min and x <= range_max)])
                
                self.pa_dict[mode][seg] = {x: self.pa_dict[mode][seg][x] for x in n_to_keep}

        self.seg_ids = list(self.pa_dict['pre'].keys() | self.pa_dict['post'].keys())

    def next_seg(self):

        if self.pos == len(self.seg_ids)-1:
            return
        
        self.pos += 1
        self.update_partners()

    def prev_seg(self):

        if self.pos == 0:
            return
        
        self.pos -= 1
        self.update_partners()

    def update_pre_or_post(self, mode):

        if mode == 'pre':
            colour = 'yellow'
            seg_col = 'green'

        if mode == 'post':
            colour = 'red'
            seg_col = 'orange'

        target_layer = f'{mode} partners'
        target_syn = f'{mode} synapses'
            
        partners = []
        point_annos = []

        if self.main_seg in self.pa_dict[mode]:
          
            for n in self.pa_dict[mode][self.main_seg].keys():

                for p in self.pa_dict[mode][self.main_seg][n].keys():
             
                    partners.append(p)

                    for indiv_point in self.pa_dict[mode][self.main_seg][n][p]:

                        pa = neuroglancer.PointAnnotation(
                            id=indiv_point['id'], 
                            point=indiv_point['point'], 
                            description=indiv_point['description']
                            )

                        point_annos.append(pa)

        self.update_segments(partners, target_layer, seg_col=self.ss_col[mode])
    
        with self.viewer.txn(overwrite=True) as s:
            s.layers[target_syn].annotations = point_annos
            s.layers[target_syn].annotationColor = self.ss_col[f'{mode}_syn_points']

        all_points = [x.point for x in point_annos]
    
        return all_points

    def update_ss_plot(self):
        
        x_axis_data = list(range(1,self.max_plot_c+1))

        for dtype in ('pre', 'post'):

            if self.main_seg not in self.plot_dict[dtype]:
                y_axis_data = tuple([0 for x in range(1, self.max_plot_c+1)])

            else:
                y_axis_data = self.plot_dict[dtype][self.main_seg]

            self.axes[dtype].clear()
            self.axes[dtype].bar(x_axis_data, y_axis_data, tick_label=x_axis_data)

        self.plotter.draw_idle()

    def update_partners(self):

        self.main_seg = self.seg_ids[self.pos]

        self.update_ss_plot()

        self.update_segments([self.main_seg], 'selected segment', self.ss_col['sel'])

        # Change location:
        all_locations = []

        for dtype in ('pre', 'post'):
            if self.display[dtype] != 'none':
                locs = self.update_pre_or_post(dtype)
                all_locations.extend(locs)
                
        self.change_view(np.mean(all_locations, axis=0), 0.22398, 4000)

        # Update message:

        self.agglo_2_region_and_type = None ###

        if self.agglo_2_region_and_type != None:
            seg_region, seg_type = self.agglo_2_region_and_type[self.main_seg]
            self.update_msg(f'Case {self.pos+1} of {len(self.seg_ids)}: Partners of segment {self.main_seg}, {seg_region} {seg_type}')
        else:
            self.update_msg(f'Case {self.pos+1} of {len(self.seg_ids)}: Partners of segment {self.main_seg}')


        # Clear any review segs and synapses:
        with self.viewer.txn(overwrite=True) as s:

            s.layers['review segs'].segments = set()
            s.layers['review segs'].visible = False

            s.layers['review syn'].annotations = []
            s.layers['review syn'].visible = False

            for dtype in ('pre', 'post'):
                if self.display[dtype] != 'none':
                    s.layers[f'{dtype} partners'].visible = True
                    s.layers[f'{dtype} synapses'].visible = True

            s.selectedLayer.layer = 'selected segment'

        # Set appropriate keybindings:
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyd'] = 'prev-case'
            s.input_event_bindings.viewer['keyf'] = 'next-case'

        self.ss_mode = 'general'

    def start_batch_review(self):
        
        if self.ss_mode == 'batch':
            self.update_partners()
            return
        
        if self.ss_mode not in ['general', 'subbatch']:
            return

        with self.viewer.txn(overwrite=True) as s:
            s.selectedLayer.layer = f'{self.pre_or_post_display} partners'

        self.seg_rev_data = []

        for n in self.pa_dict[self.pre_or_post_display][self.main_seg].keys():

            this_n_segs = []
            this_n_locations = []

            for p in self.pa_dict[self.pre_or_post_display][self.main_seg][n].keys():
                this_n_segs.append(p)
                this_n_locations.extend(self.pa_dict[self.pre_or_post_display][self.main_seg][n][p])

            msg = f'P{self.pre_or_post_display[1:]}-synaptic partners with {n} synapses'

            self.seg_rev_data.append([this_n_segs, this_n_locations, msg])
        
        if self.seg_rev_data == []:
            self.update_msg(f'No {self.pre_or_post_display}-synaptic partners to view for this segment')
            return

        if self.ss_mode == 'subbatch':
            self.seg_pos = self.seg_pos_backup
        else:
            self.seg_pos = 0

        self.ss_mode = 'batch'
        self.update_seg_review()

    def start_single_seg_review(self):

        if self.ss_mode == 'single_seg':
            self.update_partners()
            return

        if self.ss_mode != 'general':
            return

        with self.viewer.txn(overwrite=True) as s:
            s.selectedLayer.layer = f'{self.pre_or_post_display} partners'

        self.seg_rev_data = []

        for n in self.pa_dict[self.pre_or_post_display][self.main_seg].keys():

            for p in self.pa_dict[self.pre_or_post_display][self.main_seg][n].keys():

                point_anns = self.pa_dict[self.pre_or_post_display][self.main_seg][n][p]
                msg = f'P{self.pre_or_post_display[1:]}-synaptic partner {p}'

                self.seg_rev_data.append([[p], point_anns, msg])
        
        if self.seg_rev_data == []:
            self.update_msg(f'No {self.pre_or_post_display}-synaptic partners to view for this segment')
            return
        
        self.seg_pos = 0
        self.ss_mode = 'single_seg'
        self.update_seg_review()

    def review_subbatch(self):
        
        if self.ss_mode == 'subbatch':
            self.start_batch_review()
            return
        
        if self.ss_mode != 'batch':
            return

        n = int(self.seg_rev_data[self.seg_pos][2].split(' ')[-2])

        self.seg_rev_data = []

        for p in self.pa_dict[self.pre_or_post_display][self.main_seg][n].keys():

            point_anns = self.pa_dict[self.pre_or_post_display][self.main_seg][n][p]
            msg = f'P{self.pre_or_post_display[1:]}-synaptic partner {p} with {n} synapses'

            self.seg_rev_data.append([[p], point_anns, msg])
        
        self.seg_pos_backup = deepcopy(self.seg_pos)
        self.seg_pos = 0
        self.ss_mode = 'subbatch'
        self.update_seg_review()

    def update_seg_review(self):

        segs = self.seg_rev_data[self.seg_pos][0]
        points = self.seg_rev_data[self.seg_pos][1]
        message = self.seg_rev_data[self.seg_pos][2]

        if self.ss_mode == 'batch':
            self.update_msg(message)
        else:
            self.update_msg(f'{message}, {self.seg_pos+1} of {len(self.seg_rev_data)}')
        
        self.change_view([x['point'] for x in points][0], 0.22398, 4000)

        pa = [neuroglancer.PointAnnotation(id=x['id'], description=x['description'], point=x['point']) for x in points]

        self.update_segments(segs, 'review segs', self.ss_col[self.pre_or_post_display])

        with self.viewer.txn(overwrite=True) as s:

            s.layers['review segs'].visible = True
            s.layers['review syn'].visible = True
            s.layers['review syn'].annotations = pa
            s.layers['review syn'].annotationColor = 'blue'
            s.selectedLayer.layer = 'review syn'
            
            for l in ('pre partners', 'post partners', 'pre synapses', 'post synapses'):
                s.layers[l].visible = False
            
        # Set appropriate keybindings:
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyf'] = 'seg-inc'
            s.input_event_bindings.viewer['keyd'] = 'seg-dec'
              
    def dec_seg(self):
   
        if self.seg_pos == 0: return
        self.seg_pos += -1
        self.update_seg_review()
         
    def inc_seg(self):

        if self.seg_pos+1 == len(self.seg_rev_data): return
        self.seg_pos += 1
        self.update_seg_review()

    def common_pr(self):

        self.tab_control.select(self.tabs['Messages'])

        self.viewer.set_state({})

        self.viewer.actions.add('change-point', lambda s: self.change_point())

        with self.viewer.config_state.txn() as s:
            s.show_layer_panel = False

        self.cell_pos = 0

        self.save_dir = self.user_selections['Cell Reconstruction']['save_dir'].get().strip()
        
        self.project_id = self.user_selections['Cell Reconstruction']['user'].get().strip()
        self.em_id = self.user_selections['Cell Reconstruction']['em'].get().strip()
        self.em = f'brainmaps://{self.project_id}:{self.em_id}'
        self.base_id = self.user_selections['Cell Reconstruction']['base_seg'].get().strip()
        self.agglo_id = self.user_selections['Cell Reconstruction']['seg'].get().strip()
        self.base_seg = f'brainmaps://{self.project_id}:{self.base_id}'
        self.agglo_seg = f'brainmaps://{self.project_id}:{self.base_id}:{self.agglo_id}'
        self.base_agglo_map = f'{self.base_id}.{self.agglo_id}_resolved'
        self.agglo_all_edges = f'{self.base_id}.{self.agglo_id}_alledges'
        self.agglo_to_edges = f'{self.base_id}.{self.agglo_id}_agglotoedges'
        self.base_info_db = f'{self.base_id}.objinfo'
        self.agglo_info_db = f'{self.base_id}.{self.agglo_id}_objinfo'
        self.syn_id = self.user_selections['Cell Reconstruction']['syn_seg'].get().strip()
        self.syn_seg = f'brainmaps://{self.project_id}:{self.syn_id}'
        self.syn_db_name = f'{self.syn_id}.synaptic_connections_with_skeleton_classes'
        
        self.point_types = [x.strip() for x in self.user_selections['Cell Reconstruction']['other_points'].get().split(',')]
        self.selected_types = self.user_selections['Cell Reconstruction']['cell_structures'].get().strip()
        self.selected_types = [x.strip() for x in self.selected_types.split(',')]

    def save_cell_graph(self, mode, file_name=None):
        
        self.update_agglo_segs()
        cell_data = deepcopy(self.cell_data)

        if mode == 'segmentation':
            cell_data['graph_nodes'] = list(self.pr_graph.nodes())
            cell_data['graph_edges'] = list(self.pr_graph.edges())

        # Convert sets to lists for saving in json file:
        for dtype in cell_data['base_segments'].keys():
            cell_data['base_segments'][dtype] = list(cell_data['base_segments'][dtype])
        
        for agglo_id in cell_data['agglo2edges'].keys():
            for agglo_seg in cell_data['agglo2edges'][agglo_id].keys():
               cell_data['agglo2edges'][agglo_id][agglo_seg] = list(cell_data['agglo2edges'][agglo_id][agglo_seg])

        for mapping in cell_data['agglo_segments'].keys():
            cell_data['agglo_segments'][mapping] = list(cell_data['agglo_segments'][mapping])

        cell_data['removed_base_segs'] = list(cell_data['removed_base_segs'])

        timestamp = str(datetime.datetime.now())[:-7].replace(':','.')
        main_seg_id = cell_data['metadata']['main_seg']['base']

        split_c = ''.join([x[0] for x in cell_data['metadata']['completion']['split']])
        merge_c = ''.join([x[0] for x in cell_data['metadata']['completion']['merge']])

        core_sd = [
            'false_negatives_marked', 
            'ends_of_shafts_marked', 
            'merge_syn',
            'root_points_marked', 
            'partner_splits',
        ]

        completion_letters = {}

        for dtype in ['outgoing', 'incoming']:
            completion_letters[dtype] = set()
            for x in cell_data['metadata']['completion'][dtype]:
                if x in core_sd:
                    completion_letters[dtype].add(x[0])
                else:
                    completion_letters[dtype].add('c')

        out_c = ''.join(list(completion_letters['outgoing']))
        in_c = ''.join(list(completion_letters['incoming']))
        
        if file_name == None:
            file_name = f'cell_graph_{main_seg_id}_split_{split_c}_merge_{merge_c}_out_{out_c}_in_{in_c}_{timestamp}.json'

        cell_data['metadata']['data_sources']['agglo'] = self.agglo_id

        with open(f'{self.save_dir}/{file_name}', 'w') as fp:
            json.dump(cell_data, fp)

        self.update_mtab(f'Saved cell {main_seg_id}')

    def update_agglo2base_edges(self, agglo_segs):

        if self.agglo_id not in self.cell_data['agglo2edges'].keys():
            self.cell_data['agglo2edges'][self.agglo_id] = {}

        agglo_segs = [x for x in agglo_segs if x not in self.cell_data['agglo2edges'][self.agglo_id].keys()]

        r = self.get_info_from_bigquery(['label_a', 'label_b', 'agglo_id'], 'agglo_id', agglo_segs, self.agglo_to_edges)

        for x in r:
            edge = [str(x['label_a']), str(x['label_b'])]
            edge.sort()
            agglo_seg = str(x['agglo_id'])

            if agglo_seg not in self.cell_data['agglo2edges'][self.agglo_id].keys():
                self.cell_data['agglo2edges'][self.agglo_id][agglo_seg] = set()

            self.cell_data['agglo2edges'][self.agglo_id][agglo_seg].add(tuple(edge))

        for agglo_seg in agglo_segs:
            if agglo_seg not in self.cell_data['agglo2edges'][self.agglo_id].keys():
                self.cell_data['base2agglo'][self.agglo_id][agglo_seg] = agglo_seg
            else:
                for bs1, bs2 in self.cell_data['agglo2edges'][self.agglo_id][agglo_seg]:
                    self.cell_data['base2agglo'][self.agglo_id][bs1] = agglo_seg
                    self.cell_data['base2agglo'][self.agglo_id][bs2] = agglo_seg

    def update_base_locations(self, seg_list):

        seg_list = [x for x in seg_list if x not in self.cell_data['base_locations'].keys()]

        result = self.get_info_from_bigquery(['id', 'bbox'], 'id', seg_list, self.base_info_db)

        for r in result:
            self.cell_data['base_locations'][str(r['id'])] = self.get_corrected_bbox_centre(r['bbox'], 'seg')

    def add_cc_bridging_reseg_edges(self, all_base_segs):

        con_comms = list(nx.connected_components(self.pr_graph))

        if len(con_comms) == 1: return

        all_edges = self.get_edges_between_base_segments(all_base_segs)

        for origin, target in all_edges:

            if self.edge_spans_multi_cc(origin, target, con_comms):

                self.pr_graph.add_edge(origin, target)
                self.cell_data['added_graph_edges'].append([origin, target, 'unknown'])
                #self.update_mtab(f'Added an edge between segments {origin} and {target}, unknown distance apart')

                con_comms = list(nx.connected_components(self.pr_graph))

                if len(con_comms) == 1:
                    return
    
    def add_cc_bridging_edges_pairwise(self):

        con_comms = list(nx.connected_components(self.pr_graph))

        while len(con_comms) > 1:

            candidate_edges = []

            for cc1, cc2 in combinations(con_comms, 2):

                cc1_list = [x for x in cc1 if x in self.cell_data['base_locations']]
                cc2_list = [x for x in cc2 if x in self.cell_data['base_locations']]

                if cc1_list == [] or cc2_list == []:
                    continue

                sel_cc1, sel_cc2, dist = self.get_closest_dist_between_ccs(cc1_list, cc2_list)
                candidate_edges.append([sel_cc1, sel_cc2, dist])

            if candidate_edges == []: 
                return

            origin, target, dist = min(candidate_edges, key = lambda x: x[2])

            self.pr_graph.add_edge(origin, target)
            self.cell_data['added_graph_edges'].append([origin, target, dist])
            self.update_mtab(f'Added an edge between segments {origin} and {target}, {dist} nm apart')

            con_comms = list(nx.connected_components(self.pr_graph))


    def edge_spans_multi_cc(self, origin, target, con_comms):

        for cc in con_comms:
            if ((origin in cc) and (target in cc)):
                return False

        return True

    def making_starting_cell_data(self, main_base_id):

        self.update_mtab(f'Creating starting file for {main_base_id}')

        self.cell_data = {
            'all_syn': {},
            'agglo2edges': {},
            'base2agglo': {},
            'graph_edges': [],
            'graph_nodes': [],
            'base_locations': {},
            'added_graph_edges': [],
            'agglo_segments': {},    
            'end_points': {},
            'base_seg_merge_points': [],
            'classification_decisions': {},
            'removed_base_segs': set(),
            'verified_synapses': {'incoming': {}, 'outgoing': {}},
            'fn_synapses': {'incoming': [], 'outgoing': []},
            'anchor_seg': str(main_base_id),
            'metadata': {   
                'main_seg' : {'agglo' : {}, 'base' : str(main_base_id)},
                'users' : {'split': [], 'merge': [], 'both': [], 'syn': []},
                'data_sources': {
                    'project_id': self.project_id, 
                    'em' : self.em_id, 
                    'base': self.base_id, 
                    'agglo': self.agglo_id,
                    },
                'timing' : {'split' : [], 'merge' : [], 'both' : [], 'syn': []},
                'completion' : {'split' : [], 'merge' : [], 'outgoing' : [], 'incoming' : []}
                }
        }

        if type(self.cells_todo) == dict:

            if 'unknown' not in self.cells_todo[main_base_id].keys():
                self.cells_todo[main_base_id]['unknown'] = set()

            self.cell_data['base_segments'] = self.cells_todo[main_base_id]

        if type(self.cells_todo) == list:  

            self.update_seg_lookup([main_base_id])

            self.cell_data['base_segments'] = {}

            agglo_seg = self.cell_data['base2agglo'][self.agglo_id][main_base_id]
            base_ids = self.agglo2base_segs(agglo_seg, base_seg=main_base_id)
            
            self.cell_data['base_segments']['unknown'] = set(base_ids)

            for dtype in self.selected_types:
                self.cell_data['base_segments'][dtype] = set()

    def create_pr_graph(self):

        seg_id = self.cell_data['metadata']['main_seg']['base']

        self.update_mtab(f'Creating base segment graph for cell {seg_id}')

        all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]

        self.update_base_locations(all_base_segs)
        self.update_seg_lookup(all_base_segs)

        agglo_segs = set([self.cell_data['base2agglo'][self.agglo_id][x] for x in all_base_segs])

        possible_edges = []
        
        for agglo_id in agglo_segs:
            if agglo_id in self.cell_data['agglo2edges'][self.agglo_id].keys():
                possible_edges.extend(self.cell_data['agglo2edges'][self.agglo_id][agglo_id])

        all_bs_set = set(all_base_segs)
        possible_edges = [x for x in possible_edges if x[0] in all_bs_set]
        chosen_edges = [x for x in possible_edges if x[1] in all_bs_set]

        self.pr_graph = nx.Graph()
        self.pr_graph.add_nodes_from(all_base_segs)
        self.pr_graph.add_edges_from(chosen_edges)

        self.add_cc_bridging_reseg_edges(all_base_segs)
        self.add_cc_bridging_edges_pairwise()
        self.attach_noloc_segs()

        assert nx.number_connected_components(self.pr_graph) == 1

    def attach_noloc_segs(self):

        # For isolated segments without locations, attach to largest connected component:
        remaining_cc = list(nx.connected_components(self.pr_graph))

        if len(remaining_cc) == 1: return

        if len(remaining_cc) > 1:
            no_loc_base_segs = set([x for x in self.pr_graph.nodes() if x not in self.cell_data['base_locations']])
            largest_cc = max(remaining_cc, key = lambda x: len(x))
            for cc in remaining_cc:
                no_loc_this_cc = cc & no_loc_base_segs
                if cc != largest_cc and no_loc_this_cc != set():
                    rand_seg1 = random.choice(list(no_loc_this_cc))
                    rand_seg2 = random.choice(list(largest_cc))
                    self.pr_graph.add_edge(rand_seg1, rand_seg2)
                    self.cell_data['added_graph_edges'].append([rand_seg1, rand_seg2, 'unknown'])
                    self.update_mtab(f'Added an edge between segments {rand_seg1} and {rand_seg2}')

    def get_most_recent_cell_files(self, main_seg_id):
            
        files_to_load = [y for y in os.listdir(self.save_dir) if str(main_seg_id) in y and 'cell' in y]
        dates = [(z, z.split('_')[-1]) for z in files_to_load]
        dates.sort(reverse=True, key = lambda x: x[1])
        sorted_files = [x[0] for x in dates]
        
        return sorted_files

    def get_closest_dist_between_ccs(self, cc1_node_list, cc2_node_list):

        cc1_node_list = list(cc1_node_list)
        cc2_node_list = list(cc2_node_list)

        cc1_node_locs = [self.cell_data['base_locations'][x] for x in cc1_node_list]
        cc2_node_locs = [self.cell_data['base_locations'][x] for x in cc2_node_list]

        f = cdist(cc1_node_locs, cc2_node_locs, 'euclidean')

        min_indices = np.unravel_index(np.argmin(f, axis=None), f.shape)

        sel_cc1 = cc1_node_list[min_indices[0]]
        sel_cc2 = cc2_node_list[min_indices[1]]
        dist = int(f[min_indices])  

        return sel_cc1, sel_cc2, dist

    def add_closest_edge_to_graph(self, new_segs, seg_to_link):

        assert nx.number_connected_components(self.pr_graph) == 2

        # Some segments do not have locations recorded:
        current_cell_node_list = [x for x in self.pr_graph.nodes() if x not in new_segs]
        current_cell_node_list = [x for x in current_cell_node_list if x in self.cell_data['base_locations']]
        
        # Then determine new segments that are acceptable as partners
        if seg_to_link in self.cell_data['base_locations'].keys():
            new_segs = [seg_to_link]
        else:
            new_segs = [x for x in new_segs if x in self.cell_data['base_locations']]

        sel_curr, sel_new, dist = self.get_closest_dist_between_ccs(current_cell_node_list, new_segs)
        
        self.pr_graph.add_edge(sel_curr, sel_new)
        self.cell_data['added_graph_edges'].append([sel_curr, sel_new, dist])

        assert nx.number_connected_components(self.pr_graph) == 1     

        return f', linked base segments {sel_curr} and {sel_new}, {round(dist)}nm apart, '

    def get_edges_between_base_segments(self, base_ids):

        base_ids = [str(x) for x in base_ids if str(x) != '0']

        results = []
    
        if len(base_ids) > 0:

            num_batches = int(len(base_ids)/10000)

            for batch in range(num_batches+1):

                q = ','.join([str(x) for x in base_ids[batch*10000:(batch+1)*10000]])
                
                query = f"""
                            SELECT label_a, label_b
                            FROM {self.agglo_all_edges}
                            WHERE label_a IN ({q}) AND label_b IN ({q})
                        """

                res = self.ensure_results_from_bq(query, self.agglo_all_edges)
                results.extend(res)

        graph_edges = [[str(x['label_a']), str(x['label_b'])] for x in results] 

        if len(base_ids) > 100 and graph_edges == []:
            self.update_mtab("Warning, no graph edges returned from over 100 base segments, ensure that agglomeration edges database uses fields 'label_a' and 'label_b'")

        return graph_edges

    def resolving_seg_overlap(self):

        for p1, p2 in combinations(self.cell_data['base_segments'].keys(), 2):

            common_segments = set(self.cell_data['base_segments'][p1]) & set(self.cell_data['base_segments'][p2])

            if common_segments != set():

                self.update_mtab(f"Base segments {common_segments} are present in both {p1} and {p2} layers, moving to 'unknown'")

                for dtype in p1, p2:
                    if dtype != 'unknown':
                        self.cell_data['base_segments'][dtype] -= common_segments

                self.cell_data['base_segments']['unknown'].update(common_segments)

    def load_graph_from_celldata(self):

        self.pr_graph = nx.Graph()
        self.pr_graph.add_nodes_from(self.cell_data['graph_nodes'])
        self.pr_graph.add_edges_from(self.cell_data['graph_edges'])

    def load_cell_to_edit(self):

        main_seg_id = self.cells_todo[self.cell_pos]

        most_recent_file = self.get_most_recent_cell_files(main_seg_id)[0]
        load_path = f'{self.save_dir}/{most_recent_file}'
        
        with open(load_path, 'r') as fp:
            self.cell_data = json.load(fp)

        # Turn lists back to sets:
        for dtype in self.cell_data['base_segments'].keys():
            correct_form = set([str(x) for x in self.cell_data['base_segments'][dtype]])
            self.cell_data['base_segments'][dtype] = correct_form

        for agglo_id in self.cell_data['agglo2edges'].keys():
            for agglo_seg in self.cell_data['agglo2edges'][agglo_id].keys():
                correct_form = set([tuple(x) for x in self.cell_data['agglo2edges'][agglo_id][agglo_seg]])
                self.cell_data['agglo2edges'][agglo_id][agglo_seg] = correct_form
        
        ### Can eventually remove this part:

        if 'unknown' not in self.cell_data['base_segments'].keys():
            self.cell_data['base_segments']['unknown'] = set()

        if 'coloured_base_segs' in self.cell_data.keys():
            completed_segs = set(self.cell_data['coloured_base_segs'])
            for dtype in self.cell_data['base_segments'].keys():
                if dtype != 'unknown':
                    actually_completed = self.cell_data['base_segments'][dtype] & completed_segs
                    not_completed = set([x for x in self.cell_data['base_segments'][dtype] if x not in completed_segs])
                    self.cell_data['base_segments'][dtype] = deepcopy(actually_completed)
                    self.cell_data['base_segments']['unknown'].update(deepcopy(not_completed))
            del self.cell_data['coloured_base_segs']

        if 'anchor_seg' not in self.cell_data.keys():
            self.cell_data['anchor_seg'] = main_seg_id

        if 'next_gen_dict' not in self.cell_data:
            self.cell_data['next_gen_dict'] = {}

        if 'agglo2edges' not in self.cell_data:
            self.cell_data['agglo2edges'][self.agglo_id] = {}

        if 'base2agglo' not in self.cell_data:
            self.cell_data['agglo2edges'][self.agglo_id] = {}
        
        all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]
        self.update_seg_lookup(all_base_segs)

        ###

        for mapping in self.cell_data['agglo_segments'].keys():
            self.cell_data['agglo_segments'][mapping] = set(self.cell_data['agglo_segments'][mapping])

        self.cell_data['removed_base_segs'] = set(self.cell_data['removed_base_segs'])
    
        # Get the graph from edges
        self.load_graph_from_celldata()

        # Get preloaded edges, if selected:
        all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]

        if self.pre_load_edges == 1:
            self.get_new_gen_dict_entries(all_base_segs, 0)
            
        # Check for segments present in two structures:
        self.resolving_seg_overlap()

        # Create base and agglo lookup dictionaries:
        self.update_seg_lookup(all_base_segs)

        # Record the relevant agglo ID in the metadata
        self.update_base2agglo([main_seg_id])
        main_agglo_id = self.cell_data['base2agglo'][self.agglo_id][main_seg_id]
        self.cell_data['metadata']['main_seg']['agglo'][self.agglo_id] = main_agglo_id
        self.large_agglo_segs = set([main_agglo_id])
        self.start_time = time.time()

        self.update_mtab(f'Now starting cell {main_seg_id}, number {self.cell_pos+1} of {len(self.cells_todo)}')

    def update_seg_lookup(self, base_segs):

        base_segs = list(base_segs)

        self.update_base2agglo(base_segs)

        agglo_segs = set([self.cell_data['base2agglo'][self.agglo_id][x] for x in base_segs])

        self.update_agglo2base_edges(agglo_segs)

    def set_base_seg_merger_layer(self):

        self.point_types.append('Base Segment Merger')

        with self.viewer.txn(overwrite=True) as s:

            s.layers['Base Segment Merger'] = neuroglancer.AnnotationLayer()
            s.layers['Base Segment Merger'].filterBySegmentation = ["segments"]
            s.layers['Base Segment Merger'].linkedSegmentationLayer = {"segments": 'base_segs'}
            s.layers['Base Segment Merger'].annotationColor = '#ffa500'
            s.layers['Base Segment Merger'].tool = "annotatePoint"

            for pos, point in enumerate(self.cell_data['base_seg_merge_points']):

                point_array = np.array([int(point[x]/self.vx_sizes['em'][x]) for x in range(3)])
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

                # If data already exists for this point type:
                if point_type in self.cell_data['end_points'].keys():

                    for pos, point in enumerate(self.cell_data['end_points'][point_type]):
                        
                        point_array = np.array([int(point[x]/self.vx_sizes['em'][x]) for x in range(3)])
                        point_id = f'{point_type}_{pos}'
                        pa = neuroglancer.PointAnnotation(id=point_id, point = point_array)
                        s.layers[point_type].annotations.append(pa)

    def create_syn_seg_layer(self):

        with self.viewer.txn(overwrite=True) as s:
            s.layers['synapses'] = neuroglancer.AnnotationLayer()
            s.layers['synapses'].annotationColor = '#ffffff'

        all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]
        self.update_syn_locs(all_base_segs)

    def save_point_types(self):

        for t in self.point_types:

            this_type_points = []

            for x in self.viewer.state.layers[t].annotations:
                if t == 'Base Segment Merger' and x.segments == None:
                    c = [int(y) for y in x.point]
                    self.update_mtab(f'Error, no segment for point {c}, for point layer {t}, correct and re-save')
                    return 'redo'

                else:
                    co_ords = [float(x) for x in list(x.point)]
                    co_ords_and_id = [co_ords[x]*self.vx_sizes['em'][x] for x in range(3)]

                    if x.segments != None:
                        if len(x.segments[0]) > 0:
                            co_ords_and_id.append(str(x.segments[0][0]))

                    this_type_points.append(co_ords_and_id)

            if t == 'Base Segment Merger':
                self.cell_data['base_seg_merge_points'] = this_type_points
            else:
                self.cell_data['end_points'][t] = this_type_points

        return 'fine'

    def next_cell(self, mode):
        
        start = time.time()

        if self.cell_pos == len(self.cells_todo)-1:
            self.update_mtab('You have completed the final cell of this batch')
            return
        
        else:
            self.cell_pos += 1
            self.load_cell_to_edit()
            
            if mode == 'segmentation':
                self.start_new_cell_seg_pr()

            if mode == 'synapses':
                self.start_new_cell_syn_pr()

        print(f'time taken to start cell {self.cell_pos} is {time.time()-start}')

    def start_new_cell_syn_pr(self):

        if self.syn_id not in self.cell_data['all_syn'].keys():
            self.get_current_synapses()

        self.create_syn_pr_layers()
        
        if self.cell_decisions != []:
            self.start_cell_decisions()
        else:
            self.start_synapses()

    def get_seg_locs(self, base_segs): 

        seg_bboxes = self.get_info_from_bigquery(['id', 'bbox'], 'id', base_segs, self.base_info_db)

        locations = {}

        for x in seg_bboxes:
            locations[str(x['id'])] = self.get_corrected_bbox_centre(x['bbox'], 'seg', rel_to_em=True)

        return locations

    def update_syn_locs(self, base_segs):

        syn_locs = {}

        self.update_mtab('Retrieving synapses from database')

        for x in ['pre_synaptic_site', 'post_synaptic_partner']:

            results = self.get_synapses_for_set_of_neurons(base_segs, x, 'base')

            with self.viewer.txn(overwrite=True) as s:

                for pos, r in enumerate(results):
                    point = np.array(self.get_corrected_bbox_centre(r['bounding_box'], 'syn_seg', rel_to_em=True))
                    base_seg = r['neuron_id']
                    pre_or_post = x.split('_')[0]
                    syn_id = f'{base_seg}_{pre_or_post}_{pos}'
                    pa = neuroglancer.PointAnnotation(id=syn_id, point = point)
                    s.layers['synapses'].annotations.append(pa)
                    syn_locs[syn_id] = point

        self.syn_locs.update(syn_locs)

        self.update_mtab('Retrieved synapses from database')

    def pr_single_neuron(self, mode):

        selected_file_path = filedialog.askopenfilename(
                                initialdir = "/",
                                title = "Select file",
                                filetypes = (
                                    ("json files","*.json"),
                                    ("all files","*.*")
                                    )
                                )

        if selected_file_path == '': return

        if mode == 'seg':
            self.seg_pr_batch_start(specific_file=selected_file_path)

        if mode == 'syn':
            self.synapse_seg_pr_batch_start(specific_file=selected_file_path)

    def has_a_complete_file(self, main_seg_id):

        most_recent_files = self.get_most_recent_cell_files(main_seg_id)

        for f in most_recent_files:

            if f not in self.settings_dict['file_completion']:
                
                try:
                    with open(f'{self.save_dir}/{f}', 'r') as fp:
                        self.settings_dict['file_completion'][f] = json.load(fp)['metadata']['completion']
                except UnicodeDecodeError:
                    #self.update_mtab(f'File {f} could not be loaded, skipping to next file of this cell')
                    continue

            
            c = self.settings_dict['file_completion'][f]

            comp = set([set(self.todo[t]).issubset(set(c[t])) for t in self.todo.keys()])

            if comp == {True}:
                return True
        
        return False


    def agglo2base_segs(self, agglo_seg, base_seg=None):

        agglo_seg = str(agglo_seg)
        base_seg = str(base_seg)

        if agglo_seg in self.cell_data['agglo2edges'][self.agglo_id].keys():
            base_ids = [str(a) for b in self.cell_data['agglo2edges'][self.agglo_id][agglo_seg] for a in b]

        else:
            if base_seg != None:
                assert agglo_seg == base_seg

            base_ids = [agglo_seg]

        return base_ids

    def add_new_base_segs_from_new_agglo(self, seg_id):
                    
        parent_agglo_seg = self.cell_data['base2agglo'][self.agglo_id][seg_id]
        new_agglo_base_ids = set(self.agglo2base_segs(parent_agglo_seg))
        all_current_segs = set([a for b in self.cell_data['base_segments'].values() for a in b])
        new_unknown_segs = new_agglo_base_ids - all_current_segs

        self.update_seg_lookup(new_agglo_base_ids)
        self.cell_data['base_segments']['unknown'].extend(list(new_unknown_segs))
        self.update_mtab(f'Added {len(new_unknown_segs)} new base segments from updated agglomeration {self.agglo_id}')

    def ensure_all_cells_have_graphs(self, specific_file, mode):

        ### Can remove this later:
        
        if 'file_completion' not in self.settings_dict:
            self.settings_dict['file_completion'] = {}
        ###

        self.cells_todo_d = {}

        # If a specific file is provided, set that to be the only item in the todo list:
        if specific_file != None:

            file_name = specific_file.split('/')[-1]
            seg_id = file_name.split('_')[2]
            self.cells_todo = [seg_id]
            self.save_dir = specific_file[:-len(file_name)]

        else:
            load_path = self.user_selections['Cell Reconstruction']['input_neurons'].get()

            with open(load_path, 'r') as fp:
                self.cells_todo = json.load(fp)

        # Ensure input data is in correct format:
        assert type(self.cells_todo) in [dict, list]

        if type(self.cells_todo) == list:
            self.cells_todo = [str(x) for x in self.cells_todo]
            
        if type(self.cells_todo) == dict:
            self.cells_todo = {str(x): set([str(a) for a in self.cells_todo[x]]) for x in self.cells_todo.keys()}

        cells_with_files = set([x.split('_')[2] for x in os.listdir(self.save_dir) if 'cell' in x])
        cells_without_files = [x for x in self.cells_todo if x not in cells_with_files]

        num_fileless_cells = len(cells_without_files)

        if num_fileless_cells > 0:
            self.update_mtab(f'No starting file found for {num_fileless_cells} cells')
        else:
            self.update_mtab(f'Starting files found for all cells')

        complete_cells = []

        for seg_id in self.cells_todo:

            # If a seg ID already has a file, that is used
            if seg_id in cells_with_files:

                if self.has_a_complete_file(seg_id) and specific_file == None:
                    complete_cells.append(seg_id)
                    continue
                
                most_recent_file = self.get_most_recent_cell_files(seg_id)[0]

                with open(f'{self.save_dir}/{most_recent_file}', 'r') as fp:
                    self.cell_data = json.load(fp)

                ### Can remove this later:
                for temp in ['all_syn', 'base2agglo', 'agglo2edges']:
                    if temp not in self.cell_data:
                        self.cell_data[temp] = {}

                if 'unknown' not in self.cell_data['base_segments']:
                    self.cell_data['base_segments']['unknown'] = []
                
                if type(self.cell_data['metadata']['data_sources']['agglo']) == list:
                    if len(self.cell_data['metadata']['data_sources']['agglo']) > 0:
                        self.cell_data['metadata']['data_sources']['agglo'] = self.cell_data['metadata']['data_sources']['agglo'][0]
                    else:
                        self.cell_data['metadata']['data_sources']['agglo'] = 'agg20200916'
                ###


                # If seg lookup doesn't exist for current agglo_id, update:
                base2agglo_incomplete = self.agglo_id not in self.cell_data['base2agglo']
                agglo2edges_incomplete = self.agglo_id not in self.cell_data['agglo2edges']
                seg_lookup_incomplete = (base2agglo_incomplete or agglo2edges_incomplete)

                if seg_lookup_incomplete:
                    self.update_mtab(f'Updating agglo-base lookup in file for cell {seg_id}')
                    all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]
                    self.update_seg_lookup(all_base_segs)


                # If agglo_id has changed from last time, add new base segments:
                last_agglo_id = self.cell_data['metadata']['data_sources']['agglo']
                changed_agglo_id = (last_agglo_id != self.agglo_id)

                if changed_agglo_id:

                    self.add_new_base_segs_from_new_agglo(seg_id)
                
                    # Wipe clean the stored graph:
                    self.cell_data['graph_edges'] = []
                    self.cell_data['graph_nodes'] = []

                # If graph is needed and doesn't exist, create it:
                cell_graph_incomplete = (mode == 'segmentation' and self.cell_data['graph_edges'] == [])

                if cell_graph_incomplete:
                    self.create_pr_graph()
                else:
                    self.load_graph_from_celldata()

                # If synapses are needed and not up to date, update them:
                synapses_incomplete = (mode == 'synapses' and self.syn_id not in self.cell_data['all_syn'].keys())
                
                if synapses_incomplete:
                    self.get_current_synapses()

                
                # Finally, save file:
                if changed_agglo_id:

                    # Only this will have changed the base segments, so don't want to overwrite old file:
                    self.save_cell_graph(mode)

                else:

                    # Otherwise, if any other updates have been performed, can overwrite old file:
                    if (cell_graph_incomplete or synapses_incomplete or seg_lookup_incomplete):
                        self.save_cell_graph(mode, file_name=most_recent_file)

            # Otherwise, it depends on whether the input cells todo is a list or dictionary:
            else:
                self.making_starting_cell_data(seg_id)

                self.update_mtab(f'Creating agglo-base lookup for cell {seg_id}')
                all_base_segs = [a for b in self.cell_data['base_segments'].values() for a in b]
                self.update_seg_lookup(all_base_segs)

                if self.pre_load_edges == 1:
                    self.get_new_gen_dict_entries(all_base_segs, 0)

                if mode == 'segmentation':
                    self.create_pr_graph()

                if mode == 'synapses':
                    self.get_current_synapses()

                self.save_cell_graph(mode)


            self.cells_todo_d[seg_id] = self.cell_data['base_segments']

        # Save new settings file for quick completion lookup next time:
        with open(f'{self.script_directory}/CREST_settings.json', 'w') as fp:
            json.dump(self.settings_dict, fp)

        # Make sure cells todo is a list:
        self.cells_todo = [x for x in self.cells_todo if x not in complete_cells]

        if specific_file == None:
            self.remove_skipped_cells(mode)

    def seg_pr_batch_start(self, specific_file=None):

        self.update_mtab('Starting segment proofreading of batch of cells')

        # Check required fields are available:
        required_info = [
            'cred','em','user','input_neurons','save_dir',
            'seg','base_seg','other_points', 'cell_structures',
            'max_base_seg_add','skel_seg','syn_seg', 'skel_source_id'
            ]

        opf = ['other_points','skel_seg', 'skel_source_id']

        if int(self.user_selections['Cell Reconstruction']['use_syn_for_seg'].get()) == 0:
            opf.append('syn_seg')

        if not self.fields_complete(required_info, 'Cell Reconstruction', opf=opf): return

        # Get user options common to synapse and segmentation proofreading:
        self.common_pr()

        # Get segmentation proofreading-specific field values:
        self.use_syn_for_seg = int(self.user_selections['Cell Reconstruction']['use_syn_for_seg'].get())
        self.pre_load_edges = int(self.user_selections['Cell Reconstruction']['pre_load_edges'].get())
        self.max_num_base_added = int(self.user_selections['Cell Reconstruction']['max_base_seg_add'].get().strip())

        # Create client
        self.get_vx_sizes('Cell Reconstruction')

        # Get split and merge options:
        self.todo = {}

        for correction_type in ['merge', 'split']:
            c = int(self.user_selections['Cell Reconstruction'][f'correct_{correction_type}'].get())
            self.todo[correction_type] = [x for x in self.selected_types if c == 1]

        if self.todo['merge'] == [] and self.todo['split'] == []:
            self.update_mtab('Please specify at least one cell structure to correct splits or mergers for')
            return

        # Get cells todo
        self.ensure_all_cells_have_graphs(specific_file, 'segmentation')

        if self.cells_todo == []:
            self.update_mtab('All cells in this batch are complete, exiting')
            return

        # Create list of cells that will be dropped to avoid duplicate proofreading:
        self.shared_bs_path = f'{self.save_dir}/dropped_cells_shared_base_segs.json'

        if os.path.exists(self.shared_bs_path):
            with open(self.shared_bs_path, 'r') as fp:
                self.dropped_cells = json.load(fp)
        else:
            self.dropped_cells = {}

        # Add keybindings:
        self.viewer.actions.add('change-structure', lambda s: self.change_cell_structure())
        self.viewer.actions.add('change-anchor-seg', self.change_anchor_seg)
        self.viewer.actions.add('add-or-remove-seg', self.add_or_remove_seg)
        self.viewer.actions.add('view-synapses', lambda s: self.view_synapses())
        self.viewer.actions.add('grow-graph', lambda s: self.grow_graph())
        self.viewer.actions.add('increase-threshold', lambda s: self.increase_threshold())
        self.viewer.actions.add('decrease-threshold', lambda s: self.decrease_threshold())
        self.viewer.actions.add('start-branch-focus', self.branch_focus)
        self.viewer.actions.add('mark-branch-in-colour', self.mark_branch_in_colour)
        self.viewer.actions.add('accept-new-segs', lambda s: self.accept_new_segs())                    

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyc'] = 'change-structure'
            s.input_event_bindings.viewer['keys'] = 'view-synapses'
            s.input_event_bindings.viewer['keyg'] = 'grow-graph'
            s.input_event_bindings.viewer['keyk'] = 'increase-threshold'
            s.input_event_bindings.viewer['keyj'] = 'decrease-threshold'
            s.input_event_bindings.viewer['keya'] = 'accept-new-segs'
            s.input_event_bindings.data_view['dblclick0'] = 'add-or-remove-seg'
            s.input_event_bindings.data_view['shift+mousedown0'] = 'start-branch-focus'
            s.input_event_bindings.data_view['alt+mousedown0'] = 'mark-branch-in-colour'
            s.input_event_bindings.data_view['shift+mousedown2'] = 'change-anchor-seg'







        # Create seg queue and seg adding worker thread:
        self.segs_to_add_queue = Queue()
        threading.Thread(target=self.add_seg_in_background, args=(), name='seg_adding_worker').start()

        # Create edge adding worker
        if self.pre_load_edges == 1:
            self.pre_load_edges_queue = Queue()
            threading.Thread(target=self.update_potential_graph_in_background, args=(), name='edge_adding_worker').start()

        # Create graph growth variables:
        self.current_score_threshold = 0.0
        self.update_msg(f'Current Agglomeration Threshold (J/K): {self.current_score_threshold}', layer='threshold')
        self.current_red_seg = None
        self.growing_graph = False
        self.syn_locs = {}

        # Start proofreading first cell:
        self.load_cell_to_edit()
        self.start_new_cell_seg_pr()
        self.create_and_open_pr_link('Cell Reconstruction', 5, 21)

    def setup_point_ann(self, include_base_seg_merger=True):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyp'] = 'change-point'

        self.set_endpoint_annotation_layers()

        if include_base_seg_merger==True:
            self.set_base_seg_merger_layer()

        self.point_pos = -1
        self.change_point()

    def create_and_open_pr_link(self, tab, col, row, label=True):

        if label:
            Label(self.tabs[tab], text=f'Current {tab} Link:').grid(
                row=row, column=col, columnspan=1, sticky='w', padx=10)

        clickable_link = Label(self.tabs[tab], text=str(self.viewer), cursor="hand2")
        clickable_link.grid(row=row, column=col+1, columnspan=3, sticky='w', padx=10)
        clickable_link.bind("<Button-1>", self.callback)
        webbrowser.open(str(self.viewer))

    def view_synapses(self):

        with self.viewer.txn(overwrite=True) as s:
            if s.layers['synapses'].visible == True:
                s.layers['synapses'].visible = False
            else:
                s.layers['synapses'].visible = True

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

        self.update_mtab(f'Added {len(scored_edges)} new edges from {len(starting_base_segs)} seed base segments')

    def get_scored_edges(self, starting_base_segs, threshold):

        results = []

        if len(starting_base_segs) > 0:

            for batch in range(int(len(starting_base_segs)/10000)+1):

                q = ','.join([str(x) for x in starting_base_segs[batch*10000:(batch+1)*10000]])
                
                query = f"""SELECT label_a, label_b, score FROM {self.agglo_all_edges}
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
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...')
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
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...')
            return

        # Any growing of the potential graph must be allowed to complete first:
        if self.pre_load_edges == 1:
            self.update_mtab(f'Ensuring all displayed segments have next partners available')
            self.pre_load_edges_queue.join()

        if self.current_red_seg == None: return

        self.growing_graph = True
        curr_s = self.cell_structures[self.cell_structure_pos]
        self.remove_white_segs(curr_s)

        self.update_mtab(f'Adding edges with scores above {self.current_score_threshold} to {curr_s} ...')
       
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

        self.update_mtab(f'{len(new_base_segs)} new base segments added to {curr_s}')
        self.update_displayed_segs()  
 
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

        self.update_msg(f'Current Point Annotation Type (P): {selected_layer}', layer='current point type')

    def get_agglo_segs_from_base_segs(self, starting_base_segs):

        results = []

        if len(starting_base_segs) > 0:

            for batch in range(int(len(starting_base_segs)/10000)+1):

                q = ','.join([str(x) for x in starting_base_segs[batch*10000:(batch+1)*10000]])
                
                query = f"""SELECT label_a, label_b, agglo_id FROM {self.agglo_to_edges}
                            WHERE (label_a IN ({q}) OR label_b IN ({q}))"""

                res = self.ensure_results_from_bq(query, self.agglo_all_edges)
                results.extend(res)

        return results
 

    def update_base2agglo(self, base_segs):

        if self.agglo_id not in self.cell_data['base2agglo'].keys():
            self.cell_data['base2agglo'][self.agglo_id] = {}

        base_segs = list(set([str(x) for x in base_segs if str(x) not in self.cell_data['base2agglo'][self.agglo_id].keys()]))

        r = self.get_info_from_bigquery(['agglo_id', 'base_id'], 'base_id', base_segs, self.base_agglo_map)

        for x in r:
            self.cell_data['base2agglo'][self.agglo_id][str(x['base_id'])] = str(x['agglo_id'])

        for base_id in base_segs:
            if base_id not in self.cell_data['base2agglo'][self.agglo_id].keys():
                self.cell_data['base2agglo'][self.agglo_id][base_id] = base_id


    def update_agglo_segs(self):

        all_current_base_segs = set([x for y in self.cell_data['base_segments'].values() for x in y])
        required_segs = all_current_base_segs-self.cell_data['base2agglo'][self.agglo_id].keys()
        self.update_base2agglo(required_segs)
        all_agglo_segs = set([self.cell_data['base2agglo'][self.agglo_id][x] for x in all_current_base_segs])
        self.cell_data['agglo_segments'][self.agglo_id] = all_agglo_segs

    def remove_syns_with_segs(self, segs_to_remove):

        point_ids_to_remove = set()

        for base_seg in segs_to_remove:
            point_ids_to_remove.update(set([x for x in self.syn_locs.keys() if str(base_seg) in x]))

        with self.viewer.txn(overwrite=True) as s:
            new_ann = [x for x in s.layers['synapses'].annotations if x.id not in point_ids_to_remove]
            s.layers['synapses'].annotations = new_ann

    def remove_downstream_base_segs(self, base_seg):

        segs_to_remove, n_con_com = self.get_downstream_base_segs(base_seg)

        # Remove from lists and segmentation layer:
        for cs in self.cell_data['base_segments'].keys():
            self.cell_data['base_segments'][cs] -= set(segs_to_remove)

        self.pr_graph.remove_nodes_from(segs_to_remove)
        self.focus_seg_set -= set(segs_to_remove)

        with self.viewer.txn(overwrite=True) as s:
            for bs in segs_to_remove:
                if int(bs) in s.layers['base_segs'].segments:
                    s.layers['base_segs'].segments.remove(int(bs))
                if int(bs) in s.layers['focus_segs'].segments:
                    s.layers['focus_segs'].segments.remove(int(bs))

        # Get synapses to remove:
        if self.use_syn_for_seg == 1:
            self.remove_syns_with_segs(segs_to_remove)
            
        self.cell_data['removed_base_segs'].update(set(segs_to_remove))
        self.update_mtab(f'{len(segs_to_remove)} base segments removed from {n_con_com} connected components')

        self.update_seg_counts_msg()

    def turn_white_seg_grey(self, base_seg):

        white_segs = self.get_white_segs()

        if base_seg in white_segs:

            with self.viewer.txn(overwrite=True) as s:
                s.layers['focus_segs'].segment_colors[int(base_seg)] = '#708090'
                s.layers['base_segs'].segment_colors[int(base_seg)] = '#708090'

    def change_anchor_seg(self, action_state):  

        base_seg = self.check_selected_segment('base_segs', action_state, banned_segs=[self.cell_data['anchor_seg']])
        if base_seg == 'None': return

        with self.viewer.txn(overwrite=True) as s:
            s.layers['base_segs'].segment_colors[int(self.cell_data['anchor_seg'])] = '#708090'
            s.layers['base_segs'].segment_colors[int(base_seg)] = '#1e90ff'
            
        self.cell_data['anchor_seg'] = deepcopy(base_seg)

    def add_or_remove_seg(self, action_state):  

        start = time.time()

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
        displayed_segs = set([str(x) for x in self.viewer.state.layers['base_segs'].segments])

        if base_seg in displayed_segs:

            # Removing a segment:
            if self.segs_to_add_queue.unfinished_tasks != 0:
                self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...')
                return

            if base_seg not in self.pr_graph.nodes():
                self.update_mtab(f'Selected base segment has not yet been added to graph, please wait ...')
                return

            self.remove_downstream_base_segs(base_seg)
        
        else:

            # Adding a segment:
            agglo_seg = self.check_selected_segment('agglo', action_state)

            if agglo_seg == 'None': return

            self.cell_data['base2agglo'][self.agglo_id][base_seg] = agglo_seg

            if agglo_seg in self.large_agglo_segs:
                # Display single base segment
                with self.viewer.txn(overwrite=True) as s:
                    s.layers['base_segs'].segment_colors[int(base_seg)] = '#708090' 
                    s.layers['base_segs'].segments.add(int(base_seg))
            
            else:
                # Display agglo segment:
                with self.viewer.txn(overwrite=True) as s:
                    s.layers['agglo'].segment_colors[int(agglo_seg)] = '#ededed' 
                    s.layers['agglo'].segments.add(int(agglo_seg))

            # Add to queue:
            self.segs_to_add_queue.put([base_seg, agglo_seg])

        print(f'time taken to add or remove segment cell {self.cell_pos}, is {time.time()-start}')

    def get_downstream_base_segs(self, base_seg):

        edge_backup = list(self.pr_graph.edges([base_seg]))

        self.pr_graph.remove_node(base_seg)

        current_cc = list(nx.connected_components(self.pr_graph))
        ccs_to_remove = [cc for cc in current_cc if self.cell_data['anchor_seg'] not in cc]
        segs_to_remove = [str(x) for y in ccs_to_remove for x in y if str(x) != '0']
        segs_to_remove.append(base_seg)

        self.pr_graph.add_node(base_seg)
        self.pr_graph.add_edges_from(edge_backup)

        return segs_to_remove, len(current_cc)-1

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
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...')
            return

        if self.growing_graph == True: 
            self.update_mtab("Press 'A' to accept any incorporated base segments from this round of growing before exiting branch focus mode")
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

        if self.segs_to_add_queue.unfinished_tasks != 0:
            self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, please wait ...')
            return

        if self.growing_graph == True: return
        if self.current_red_seg != None: return

        base_seg = self.check_selected_segment('base_segs', action_state, banned_segs = [self.cell_data['anchor_seg']])

        if base_seg == 'None': return

        if base_seg not in self.pr_graph.nodes():
            self.update_mtab(f'Base segment {base_seg} was not in the base segment graph, updating displayed segments ...')
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
                time.sleep(0.1)
                continue

            self.get_new_gen_dict_entries(base_segs_to_get_edges, 0)

            for bs in base_segs_to_get_edges:
                self.pre_load_edges_queue.task_done()

    def add_seg_in_background(self):

        while True:

            base_seg, agglo_seg = self.segs_to_add_queue.get()

            all_current_segs = set([a for b in self.cell_data['base_segments'].values() for a in b])

            # In case this base seg was added when selecting another base seg in the same agglo segment:
            if base_seg in all_current_segs:

                assert base_seg in self.pr_graph.nodes()

                with self.viewer.txn(overwrite=True) as s:
                    if int(agglo_seg) in s.layers['agglo'].segments:
                        s.layers['agglo'].segments.remove(int(agglo_seg))

                self.segs_to_add_queue.task_done()
                self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments left to add from queue')
                continue

            # Get the base ids and the new segment graph, and combine with the current graph:
            # If a very large number of base segments is being added on (likely big merge error), just add the single base segment instead:
            base_ids = [base_seg]
            
            if agglo_seg not in self.large_agglo_segs:

                self.update_agglo2base_edges([agglo_seg])

                constituent_base_ids = self.agglo2base_segs(agglo_seg, base_seg=base_seg)

                if len(constituent_base_ids) > self.max_num_base_added:
                    self.large_agglo_segs.add(agglo_seg)
                else:
                    base_ids = constituent_base_ids
    
            self.update_base_locations(base_ids)
            self.pr_graph.add_nodes_from(base_ids)

            if len(base_ids) > 1:
                self.pr_graph.add_edges_from(self.cell_data['agglo2edges'][self.agglo_id][agglo_seg])

            if nx.number_connected_components(self.pr_graph) > 1:
                join_msg = self.add_closest_edge_to_graph(base_ids, base_seg) 
            else:
                join_msg = ', '

            # Update lists of base segments and displayed segs:
            self.cell_data['base_segments']['unknown'].update(set(base_ids))

            if self.current_red_seg != None:
                self.focus_seg_set.update(set(base_ids))

            with self.viewer.txn(overwrite=True) as s:

                for bs in base_ids:
                    s.layers['base_segs'].segment_colors[int(bs)] = '#708090'
                    s.layers['base_segs'].segments.add(int(bs))

                    if self.current_red_seg != None:
                        s.layers['focus_segs'].segment_colors[int(bs)] = '#708090'
                        s.layers['focus_segs'].segments.add(int(bs))

            # Add relevant synapses:
            if self.use_syn_for_seg == 1:
                self.update_syn_locs(base_ids)

            # Get next generation of links for new IDs:
            if self.pre_load_edges == 1:
                for bs in base_ids:
                    self.pre_load_edges_queue.put(bs)

            # Remove agglomerated seg from display:
            with self.viewer.txn(overwrite=True) as s:
                if int(agglo_seg) in s.layers['agglo'].segments:
                    s.layers['agglo'].segments.remove(int(agglo_seg))

            self.segs_to_add_queue.task_done()
            self.update_displayed_segs() 
            self.update_mtab(f'Added {len(base_ids)} base segments from agglomerated segment {agglo_seg}{join_msg}{self.segs_to_add_queue.unfinished_tasks} agglomerated segments left to process')

    def update_displayed_segs(self):

        displayed_segs = set([str(x) for x in self.viewer.state.layers['base_segs'].segments])
        listed_segs = set([x for y in self.cell_data['base_segments'].values() for x in y])
        graph_segs = set(self.pr_graph.nodes())

        assert listed_segs == graph_segs

        # Identify segments that failed to be removed from the viewer:
        if self.segs_to_add_queue.unfinished_tasks == 0:
            segs_to_remove = displayed_segs - listed_segs
        else:
            segs_to_remove = set()

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

        if self.segs_to_add_queue.unfinished_tasks == 0:
            with self.viewer.txn(overwrite=True) as s:
                s.layers['agglo'].segments = set()

        self.update_seg_counts_msg()

    def update_seg_counts_msg(self):

        b = self.cell_data['base_segments']
        second_part = ', '.join([f'{x}: {len(b[x])}' for x in b.keys()])

        self.update_msg(f'Current Base Segment Counts: {second_part}', layer='current_seg_count')
            
    def save_timing_and_user(self):

        time_taken = (time.time()-self.start_time)/60

        for dtype, datum in [['timing', time_taken], ['users', self.user]]:

            if len(self.todo['merge']) > 0 and len(self.todo['split']) > 0:
                self.cell_data['metadata'][dtype]['both'].append(datum)    
            else:
                for dtype2 in ['split', 'merge']:
                    if len(self.todo[dtype]) > 0:
                        self.cell_data['metadata'][dtype][dtype2].append(datum)
        
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

                    self.update_mtab(f'{len(overlapping_segs)} segments from {dtype} of cell {current_seg} are present in the {dtype}, of cell {index_seg}, removing this cell from to-do list')
                    
        with open(self.shared_bs_path, 'w') as fp:
            json.dump(self.dropped_cells, fp)

    def save_cell_seg_and_next(self):

        self.save_cell_seg(save_completion=True)

        # Ensure that any base segs incorporated into this cell are removed from the to-do list:
        if len(self.cells_todo) > 1:
            self.update_and_save_dropped_cells()
            
        self.next_cell('segmentation')

    def save_cell_seg(self, save_completion=False):

        self.tab_control.select(self.tabs['Messages'])

        self.update_mtab(f'{self.segs_to_add_queue.unfinished_tasks} segments in queue to add, waiting to save ...')
        self.segs_to_add_queue.join()

        if self.pre_load_edges == 1:
            self.pre_load_edges_queue.join()
        
        self.resolving_seg_overlap()
        if self.save_point_types() == 'redo': return

        self.update_displayed_segs() 
        self.save_timing_and_user()

        if save_completion == True:
            for dtype in ['split', 'merge']:
                for x in self.todo[dtype]:
                    if x not in self.cell_data['metadata']['completion'][dtype]:
                        self.cell_data['metadata']['completion'][dtype].append(x)

        self.save_cell_graph('segmentation')

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
                chosen_col = random.choice(list(available_colours))

            used_colours.add(chosen_col)
            self.chosen_seg_colours[x] = chosen_col
            
    def set_cell_structures(self):

        existing_struc = [x for x in self.cell_data['base_segments'].keys() if x!= 'unknown']

        self.cell_structures = list(set(self.selected_types) | set(existing_struc))

        for dtype in self.cell_structures:
            if dtype not in self.cell_data['base_segments'].keys():
                self.cell_data['base_segments'][dtype] = set()

    def reset_seg_pr_layers(self):

        with self.viewer.txn(overwrite=True) as s:

            s.layers['em'] = neuroglancer.ImageLayer(source = self.em)

            s.layers['agglo'] = neuroglancer.SegmentationLayer(source = self.agglo_seg, segment_colors={})
            s.layers['agglo'].pick = False
            s.layers['agglo'].visible = True
            s.layers['agglo'].ignoreNullVisibleSet = False
            s.layers['agglo'].selectedAlpha = 0.90
            s.layers['agglo'].objectAlpha = 1.00

            s.layers['focus_segs'] = neuroglancer.SegmentationLayer(source = self.base_seg, segment_colors={})
            s.layers['focus_segs'].visible = False
            s.layers['focus_segs'].pick = False
            s.layers['focus_segs'].ignoreNullVisibleSet = False
            s.layers['focus_segs'].selectedAlpha = 0.90
            s.layers['focus_segs'].objectAlpha = 1.00
            
            all_segs = [a for b in self.cell_data['base_segments'].values() for a in b]

            s.layers['base_segs'] = neuroglancer.SegmentationLayer(source = self.base_seg, segments=all_segs, segment_colors={})
            s.layers['base_segs'].ignoreNullVisibleSet = False
            s.layers['base_segs'].pick = False
            s.layers['base_segs'].selectedAlpha = 0.90 #For 2D

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
        loc = self.get_seg_locs([main_seg_id])[main_seg_id]
        self.change_view(loc, 0.22398, 389.338)
        self.reset_seg_pr_layers()

        all_base_ids = [a for b in self.cell_data['base_segments'].values() for a in b]

        if self.use_syn_for_seg == 1:
            self.create_syn_seg_layer()
            self.update_syn_locs(all_base_ids)

        self.update_seg_counts_msg()

# SYNAPSE PROOFREADING COMMON FUNCTIONS:

    def get_custom_options(self):

        custom_options = {}
        custom_options_used = []

        for i in range(10):

            this_options = self.user_selections['Cell Reconstruction'][f'custom_syn_cell_{i}_options'].get().strip()
            this_cat = self.user_selections['Cell Reconstruction'][f'custom_syn_cell_{i}_category'].get().strip()
            
            if this_options == '' or this_cat == '': continue

            this_entry_options = [x.strip() for x in this_options.split(',')]
            this_cat = this_cat.strip()

            if not 2 <= len(this_entry_options) <= 10:
                self.update_mtab(f'Please use between two and ten options for category {this_cat}')
                return [], []

            custom_options[this_cat] = this_entry_options
            
            custom_options_used.append(f'custom_syn_cell_{i}_options')
            custom_options_used.append(f'custom_syn_cell_{i}_category')

        return custom_options, custom_options_used

    def get_cell_decisions(self):

        self.cell_decisions = []

        for d_key in ['false_negatives_marked', 'ends_of_shafts_marked', 'merge_syn']:

            if self.user_selections['Cell Reconstruction'][d_key].get() == 1:

                if not (d_key == 'ends_of_shafts_marked' and self.point_types == []):
                    self.cell_decisions.append(d_key)

    def get_syn_decisions(self, custom_options):

        self.syn_decisions = []

        for k in custom_options.keys():
            self.syn_decisions.append([k, custom_options[k]])

        for dkey in ['root_points_marked', 'partner_splits']:
            if self.user_selections['Cell Reconstruction'][dkey].get() == 1:
                self.syn_decisions.append([dkey, []])

    def get_types_todo(self):

        self.types_todo = []

        for dkey in ['outgoing', 'incoming']:
            if self.user_selections['Cell Reconstruction'][dkey].get() == 1:
                self.types_todo.append(dkey)

    def set_ten_key_options(self):

        self.viewer.actions.add('option-1', lambda s: self.select_option(0))
        self.viewer.actions.add('option-2', lambda s: self.select_option(1))
        self.viewer.actions.add('option-3', lambda s: self.select_option(2))
        self.viewer.actions.add('option-4', lambda s: self.select_option(3))
        self.viewer.actions.add('option-5', lambda s: self.select_option(4))
        self.viewer.actions.add('option-6', lambda s: self.select_option(5))
        self.viewer.actions.add('option-7', lambda s: self.select_option(6))
        self.viewer.actions.add('option-8', lambda s: self.select_option(7))
        self.viewer.actions.add('option-9', lambda s: self.select_option(8))
        self.viewer.actions.add('option-10', lambda s: self.select_option(9))

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['digit1'] = 'option-1'
            s.input_event_bindings.viewer['digit2'] = 'option-2'
            s.input_event_bindings.viewer['digit3'] = 'option-3'
            s.input_event_bindings.viewer['digit4'] = 'option-4'
            s.input_event_bindings.viewer['digit5'] = 'option-5'
            s.input_event_bindings.viewer['digit6'] = 'option-6'
            s.input_event_bindings.viewer['digit7'] = 'option-7'
            s.input_event_bindings.viewer['digit8'] = 'option-8'
            s.input_event_bindings.viewer['digit9'] = 'option-9'
            s.input_event_bindings.viewer['digit10'] = 'option-10'

    def remove_skipped_cells(self, mode):
        
        if f'not_{mode}_proofread.json' not in os.listdir(self.save_dir):
            self.skipped = []
        else:
            with open(f'{self.save_dir}/not_{mode}_proofread.json', 'r') as fp:
                self.skipped = json.load(fp)
            
        self.cells_todo = [x for x in self.cells_todo if str(x) not in self.skipped]

    def synapse_seg_pr_batch_start(self, specific_file=None):

        self.update_mtab('Starting synapse proofreading of batch of cells')

        # Check required fields:
        required_info = [
            'cred','em','user','input_neurons','save_dir',
            'seg','base_seg','cell_structures','other_points',
            'outgoing','incoming', 'root_points_marked','false_negatives_marked',
            'partner_splits', 'ends_of_shafts_marked', 'merge_syn', 'syn_seg',     
            ]

        linked_fields = [
            [['root_points_marked', 'ends_of_shafts_marked'], ['skel_seg','skel_source_id']],
            [['partner_splits'], ['max_stalk']],
            [['merge_syn'], ['max_syn_merge']],
        ]
            
        for chosen_fields, required_fields in linked_fields:
            for cf in chosen_fields:
                if int(self.user_selections['Cell Reconstruction'][cf].get()) == 1:
                    required_info.extend(required_fields)

        custom_options, custom_options_used = self.get_custom_options()
        if custom_options == []: return

        required_info.extend(custom_options_used) 

        if not self.fields_complete(required_info, 'Cell Reconstruction', opf=['other_points']): return

        # Get user options common to synapse and segmentation proofreading:
        self.common_pr()

        # Create client
        self.use_syn_for_seg = 0
        self.pre_load_edges = 0
        self.get_vx_sizes('Cell Reconstruction')

        # Get fields specific to synapse proofreading:
        skel_seg_id = self.user_selections['Cell Reconstruction']['skel_seg'].get().strip()
        project_id = self.user_selections['Cell Reconstruction']['user'].get().strip()
        self.skel_seg = f'brainmaps://{project_id}:{skel_seg_id}'
        self.max_stalk = int(self.user_selections['Cell Reconstruction']['max_stalk'].get().strip())
        self.max_syn_merge = int(self.user_selections['Cell Reconstruction']['max_syn_merge'].get().strip())
        self.skel_source_id = self.user_selections['Cell Reconstruction']['skel_source_id'].get().strip()
        self.get_types_todo()
        self.get_syn_decisions(custom_options)
        self.get_cell_decisions()
        all_dec = deepcopy(self.cell_decisions+[x[0] for x in self.syn_decisions])
        self.todo = {x: all_dec for x in self.types_todo}

        if self.cell_decisions == [] and self.syn_decisions == []:
            self.update_mtab('Please select at least one cell or synapse feature to check')
            return

        if len(self.types_todo) == 0:
            self.update_mtab('Please select at least one type of synapse to check')
            return

        # Get cells todo:
        self.ensure_all_cells_have_graphs(specific_file, 'synapses')
        
        if self.cells_todo == []:
            self.update_mtab('All cells in this batch are complete, exiting')
            return

        # Get locations for final set of cells / segs:
        self.seg_locations = self.get_seg_locs(self.cells_todo)

        # Create keybindings:
        self.viewer.actions.add('next-q', lambda s: self.next_seg_syn_q())
        self.viewer.actions.add('prev-q', lambda s: self.prev_seg_syn_q())
        self.viewer.actions.add('next-q-cell', lambda s: self.next_cell_decision())
        self.viewer.actions.add('prev-q-cell', lambda s: self.prev_cell_decision())
        self.viewer.actions.add('prev-merge-pair', lambda s: self.prev_merge_pair())
        self.viewer.actions.add('separate-pair', lambda s: self.pair_decision('separate'))
        self.viewer.actions.add('join-pair', lambda s: self.pair_decision('join'))
        self.viewer.actions.add('shaft end points', lambda s: self.complete_end_points())
        self.viewer.actions.add('false negatives', lambda s: self.complete_fn())
        self.viewer.actions.add('change-fn-type', lambda s: self.change_fn_type())
        
        self.set_ten_key_options()

        # Load cell and start first cell decisions, or synapses:
        self.load_cell_to_edit()
        self.start_new_cell_syn_pr()
        self.create_and_open_pr_link('Cell Reconstruction', 5, 21)

    def add_agglo_seg_size_info(self, dtype):

        if dtype == 'outgoing':
            partner_type = 'post'

        if dtype == 'incoming':
            partner_type = 'pre'

        info_to_get = [   
            'id', 
            'bbox.size.x AS x',
            'bbox.size.y AS y',
            'bbox.size.z AS z'
            ]

        agglo_segs = [x[f'{partner_type}_agglo_id'] for x in self.cell_data['all_syn'][self.syn_id][dtype]]
        r = self.get_info_from_bigquery(info_to_get, 'id', agglo_segs, self.agglo_info_db)
        size_d = {str(x['id']): [x['x'], x['y'], x['y']] for x in r}  

        for syn in self.cell_data['all_syn'][self.syn_id][dtype]:
            agglo_id = syn[f'{partner_type}_agglo_id']
            sizes = [size_d[agglo_id][a]*self.vx_sizes['seg'][a] for a in range(3)]
            syn['partner_size'] = max(sizes)

    def get_pre_and_post_agglo_segs(self, dtype):

        for partner_type in ['pre', 'post']:

            base_segs = [x[f'{partner_type}_base_id'] for x in self.cell_data['all_syn'][self.syn_id][dtype]]

            self.update_base2agglo(base_segs)

            for syn in self.cell_data['all_syn'][self.syn_id][dtype]:
                syn[f'{partner_type}_agglo_id'] = self.cell_data['base2agglo'][self.agglo_id][str(syn[f'{partner_type}_base_id'])]


    def next_cell_decision(self):

        if self.cell_decision_pos == len(self.cell_decisions)-1:
            if len(self.syn_decisions) > 0:
                self.start_synapses()
            else:
                self.save_cell_syn_and_next()
                return
        else:
            self.cell_decision_pos +=1
            self.update_cell_decision()

    def prev_cell_decision(self):

        if self.cell_decision_pos == 0: 
            return 

        else:
            self.cell_decision_pos -= 1
            self.update_cell_decision()

    def update_cell_decision(self):

        cell_task = self.cell_decisions[self.cell_decision_pos]

        if cell_task == 'false_negatives_marked': 
            self.start_whole_cell_points('false negatives')
            self.start_false_negatives()
            return

        if cell_task == 'merge_syn':
            self.start_merge_check()
            return

        if cell_task == 'ends_of_shafts_marked':
            self.setup_point_ann(include_base_seg_merger=False)
            self.start_whole_cell_points('shaft end points')
            return

    def start_whole_cell_points(self, task_type):

        self.update_msg(f"Mark all {task_type}, then press 'A'")

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keya'] = task_type

        layers_to_show = [
            'em', 
            'outgoing_fn', 
            'incoming_fn',
            'outgoing_syn',
            'incoming_syn',
            'main_agglo_seg',
            'root_points',
            ]

        if task_type == 'shaft end points':
            layers_to_show.extend(self.point_types)

        with self.viewer.txn(overwrite=True) as s:

            for l in s.layers:
                if l.name in layers_to_show:
                    s.layers[l.name].visible = True
                else:
                    s.layers[l.name].visible = False
        
    def complete_end_points(self):

        if self.save_point_types() == 'redo': return
        self.next_cell_decision()

    def complete_fn(self):

        for t in ['incoming', 'outgoing']:
            ann = self.viewer.state.layers[f'{t}_fn'].annotations
            this_type_points = [[float(x) for x in list(x.point)] for x in ann]
            corrected = [[x[a]*self.vx_sizes['em'][a] for a in range(3)] for x in this_type_points]
            self.cell_data['fn_synapses'][t] = corrected

        self.next_cell_decision()

    def change_fn_type(self):

        if self.current_fn_mode == 'outgoing':
            self.current_fn_mode = 'incoming'
        else:
            self.current_fn_mode = 'outgoing'

        with self.viewer.txn(overwrite=True) as s:
            s.selectedLayer.layer = f'{self.current_fn_mode}_fn'
            s.selected_layer.visible = True

        self.update_msg(f'Current False Negative Type (P): {self.current_fn_mode}', layer='current point type')

    def start_false_negatives(self):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyp'] = 'change-fn-type'

        
        self.current_fn_mode = 'outgoing'
        self.change_fn_type()

    def start_cell_decisions(self, skip=0):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyd'] = 'prev-q-cell'

        loc = self.seg_locations[self.cells_todo[self.cell_pos]]
        self.change_view(loc, 0.22398, 2000)

        self.cell_decision_pos = skip
        self.update_cell_decision()

    def next_merge_pair(self):

        # Currently forced to make decisions on all cases
        if self.merge_pairs[self.merge_pair_pos]['decision'] == None:  return

        if self.merge_pair_pos == len(self.merge_pairs)-1:

            if self.cell_decision_pos == len(self.cell_decisions)-1:
                self.cell_data['synapse_merge_decisions'] = deepcopy(self.merge_pairs)
                self.next_cell_decision()
                return

            else:
                self.cell_data['synapse_merge_decisions'] = deepcopy(self.merge_pairs)
                self.start_cell_decisions(skip = self.cell_decisions.index('merge_syn')+1)
                return
        else:
            self.merge_pair_pos += 1
            self.update_merge_pair()

    def prev_merge_pair(self):

        if self.merge_pair_pos == 0:
            return
        else:
            self.merge_pair_pos -= 1
            self.update_merge_pair()

    def update_merge_pair(self):

        current_merge_pair = self.merge_pairs[self.merge_pair_pos]

        pair_loc = np.mean(current_merge_pair['synapse_locations'], axis = 0)
        pair_loc = [pair_loc[x]/self.vx_sizes['em'][x] for x in range(3)]

        self.change_view(np.array(pair_loc), 1, 1000)

        self.set_regular_q_state(current_merge_pair)

        with self.viewer.txn(overwrite=True) as s:
            s.layers['synapse_seg'].visible = True
            s.selectedLayer.layer = 'synapse_seg'
            s.selected_layer.visible = True

        syn_seg_ids = [x.split('_') for x in current_merge_pair['synapse_ids']]
        syn_seg_ids = [a for b in syn_seg_ids for a in b]

        self.update_segments(syn_seg_ids, 'synapse_seg')

        self.update_msg(f'Synapse pair {self.merge_pair_pos+1} of {len(self.merge_pairs)}: Join (J) or Keep separate (K)')

    def pair_decision(self, decision):

        self.merge_pairs[self.merge_pair_pos]['decision'] = decision
        self.next_merge_pair()

    def start_synapses(self):

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyd'] = 'prev-q'
            s.input_event_bindings.viewer['keyp'] = None

        self.update_msg('', layer='current point type')

        self.current_syn_results = {}
        self.type_pos = 0
        self.synapse_pos = 0
        self.syn_decision_pos = 0
        self.update_q()

    def get_merge_pairs(self):

        self.update_mtab('Getting synapse pairs to check for mergers')

        merge_pairs = [] 

        for dtype in self.cell_data['all_syn'][self.syn_id].keys():

            for syn_pos, syn1 in enumerate(self.cell_data['all_syn'][self.syn_id][dtype]):

                pre1, post1 = syn1['pre_agglo_id'], syn1['post_agglo_id']

                if pre1 == post1: continue

                for syn2 in self.cell_data['all_syn'][self.syn_id][dtype][syn_pos+1:]:

                    pre2, post2  = syn2['pre_agglo_id'], syn2['post_agglo_id']

                    if pre2 == post2: continue

                    if pre1 == pre2 and post1 == post2:
                        syn1_loc = self.get_corrected_bbox_centre(syn1['bounding_box'], 'syn_seg')
                        syn2_loc = self.get_corrected_bbox_centre(syn2['bounding_box'], 'syn_seg')

                        pair_dist = euclidean(syn1_loc, syn2_loc)

                        if pair_dist < self.max_syn_merge:

                            pre_sid1, post_sid1 = syn1['pre_syn_id'], syn1['post_syn_id']
                            pre_sid2, post_sid2 = syn2['pre_syn_id'], syn2['post_syn_id']

                            this_pair = {   
                                'synapse_ids': [f'{pre_sid1}_{post_sid1}', f'{pre_sid2}_{post_sid2}'], 
                                'decision': None, 
                                'distance_nm': pair_dist, 
                                'synapse_locations': [syn1_loc, syn2_loc], 
                                'pre_agglo_id': pre1, 
                                'post_agglo_id': post1,
                            }

                            merge_pairs.append(this_pair)

        return merge_pairs

    def start_merge_check(self):

        self.merge_pairs = self.get_merge_pairs()

        if self.merge_pairs == []:
            self.update_mtab('No pairs meet merger check distance cutoff')
            self.cell_data['synapse_merge_decisions'] = []
            self.next_cell_decision()
            return 

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keyd'] = 'prev-merge-pair'
            s.input_event_bindings.viewer['keyj'] = 'join-pair'
            s.input_event_bindings.viewer['keyk'] = 'separate-pair'
            s.input_event_bindings.viewer['keyp'] = None

        self.update_msg('', layer='current point type')

        self.merge_pair_pos = 0
        self.update_merge_pair()
    
    def get_current_synapses(self):

        seg_id = self.cell_data['metadata']['main_seg']['base']

        self.update_mtab(f'Getting synapse information for cell {seg_id}')

        self.cell_data['all_syn'][self.syn_id] = {}

        base_segs = [x for y in self.cell_data['base_segments'].values() for x in y]

        for dtype, syn_type in [['incoming','post_synaptic_partner'], ['outgoing', 'pre_synaptic_site']]:

            self.update_mtab(f'Retrieving {dtype} synapses')
            
            self.cell_data['all_syn'][self.syn_id][dtype] = self.get_synapses_for_set_of_neurons(base_segs, syn_type, 'base')

            if self.cell_data['all_syn'][self.syn_id][dtype] == []: continue

            self.get_pre_and_post_agglo_segs(dtype)
            self.add_agglo_seg_size_info(dtype)


    def check_root_points(self):

        r = self.viewer.state.layers['root_points']
        coords = [[float(x) for x in x.point] for x in r.annotations]

        if len(coords) != 1:
            self.update_msg('Please ensure one and only one root point annotation before saving')
        else:
            nm_coords = [coords[0][a]*self.vx_sizes['em'][a] for a in range(3)]
            self.current_syn_results['root_points_marked'] = nm_coords

            with self.viewer.txn(overwrite=True) as s:
                s.layers['main_agglo_seg'].source[0].subsources['/mesh'] = True
                s.layers['root_points'].annotations = []

    def check_partner_splits(self):

        if self.types_todo[self.type_pos] == 'incoming':
            rel_layer = 'current_pre_segs'

        if self.types_todo[self.type_pos] == 'outgoing':
            rel_layer = 'current_post_segs'

        selected_segs = [str(x) for x in self.viewer.state.layers[rel_layer].segments]
        
        if len(selected_segs) == 0:
            self.update_mtab('Error, no partner segs are selected')
        else:
            self.current_syn_results['partner_splits'] = selected_segs

    def next_seg_syn_q(self):

        current_question = self.syn_decisions[self.syn_decision_pos][0]
        current_type = self.types_todo[self.type_pos]

        if current_question == 'root_points_marked':
            self.check_root_points()

        if current_question == 'partner_splits':
            self.check_partner_splits()

        if current_question not in self.current_syn_results: return
        
        if self.syn_decision_pos == len(self.syn_decisions)-1:
            if self.synapse_pos == len(self.cell_data['all_syn'][self.syn_id][current_type])-1:
                self.save_current_synapse()
                if self.type_pos == len(self.types_todo)-1: 
                    self.save_cell_syn_and_next()
                    return
                else:
                    self.syn_decision_pos = 0
                    self.synapse_pos = 0
                    self.type_pos += 1
                    if len(self.cell_data['all_syn'][self.syn_id][self.types_todo[self.type_pos]]) == 0:
                        self.save_cell_syn_and_next()
                        return

            else:
                self.save_current_synapse()
                self.syn_decision_pos = 0
                self.synapse_pos +=1
        else:
            self.syn_decision_pos += 1

        self.update_q()

    def prev_seg_syn_q(self):

        current_type = self.types_todo[self.type_pos]

        if self.syn_decision_pos == 0:
            if self.synapse_pos == 0:
                if self.type_pos == 0:
                    return
                else:
                    self.synapse_pos = len(self.cell_data['all_syn'][self.syn_id][current_type])-1
                    self.syn_decision_pos = len(self.syn_decisions)-1
                    self.type_pos -= 1
            else:
                self.syn_decision_pos = len(self.syn_decisions)-1
                self.synapse_pos -=1
                
        else:
            self.syn_decision_pos -= 1
        
        self.update_q()

    def setup_partner_splits(self, current_synapse, current_type, message_start):

        if current_type == 'outgoing':
            opp, opp_struc = 'post', 'spines'

        if current_type == 'incoming':
            opp, opp_struc = 'pre', 'terminal bouton stalks'

        if current_synapse['partner_size'] >= self.max_stalk:
            stat = 'over'
            message_end = ", press 'A' to save"
        else:
            stat = 'under'
            message_end = f", please check and correct {opp}-synaptic partner for split errors, then press 'A' to save"
        
        psize = str(current_synapse['partner_size'])
        message_middle = f"{opp}-synaptic partner segment bbox is {psize}nm long, {stat} the {self.max_stalk}nm threshold for {opp_struc}"

        self.update_msg(message_start + message_middle + message_end)

        with self.viewer.txn(overwrite=True) as s:
            s.selectedLayer.layer = f'current_{opp}_segs'

        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keya'] = 'next-q'

    def setup_mark_root_points(self):

        with self.viewer.txn(overwrite=True) as s:
            s.layers['main_agglo_seg'].source[0].subsources['/mesh'] = False
            s.selectedLayer.layer = 'root_points'
            s.selected_layer.visible = True
        
        with self.viewer.config_state.txn() as s:
            s.input_event_bindings.viewer['keya'] = 'next-q'

        self.update_msg("Ctrl + L.Click to place a point annotation at the attachment point of the synapse to the shaft and then press 'A'")

    def update_q(self):

        current_type = self.types_todo[self.type_pos]
        current_synapse = self.cell_data['all_syn'][self.syn_id][current_type][self.synapse_pos]
        current_question, current_options = self.syn_decisions[self.syn_decision_pos]

        if self.syn_decision_pos in [0, len(self.syn_decisions)-1]:
            loc = self.get_corrected_bbox_centre(current_synapse['bounding_box'], 'syn_seg', rel_to_em=True)
            self.change_view(np.array(loc), 1, 1000)

        total_syn_n = len(self.cell_data['all_syn'][self.syn_id][current_type])

        message_start = f'{current_type} synapse {self.synapse_pos+1} of {total_syn_n}: '

        if current_question == 'partner_splits':
            self.setup_partner_splits(current_synapse, current_type, message_start)
            return

        if current_question == 'root_points_marked':
            self.setup_mark_root_points()
            return

        self.set_regular_q_state(current_synapse)
        self.set_regular_q_message(current_question, current_options, message_start)

    def set_regular_q_state(self, current_synapse):

        main_agglo_seg = self.cell_data['metadata']['main_seg']['agglo'][self.agglo_id]

        noshow = ['outgoing_syn', 'incoming_syn', 'outgoing_fn', 'incoming_fn','synapse_seg']

        with self.viewer.txn(overwrite=True) as s:

            for l in self.point_types + noshow:
                s.layers[l].visible = False

            for dtype in ['pre', 'post']:

                seg = current_synapse[f'{dtype}_agglo_id']

                if seg == main_agglo_seg:
                    s.layers[f'current_{dtype}_segs'].segments = set()
                    s.layers[f'current_{dtype}_segs'].visible = False

                else:
                    s.layers[f'current_{dtype}_segs'].segments = set([int(seg)])
                    s.layers[f'current_{dtype}_segs'].visible = True

    def set_regular_q_message(self, current_question, current_options, message_start):

        message_end = f'{current_question}: '

        for pos in range(10):

            if pos >= len(current_options): break

            option = current_options[pos]

            if pos == len(current_options)-1:
                message_end += f'{option} ({pos+1})'
            else:
                message_end += f'{option} ({pos+1}) or '

        self.update_msg(message_start + message_end)

    def select_option(self, pos_selected):

        current_question, current_options = self.syn_decisions[self.syn_decision_pos]

        if current_question in ['partner_splits', 'root_points_marked']: return

        if pos_selected >= len(current_options): return

        answer = deepcopy(current_options[pos_selected])

        self.current_syn_results[current_question] = answer

        self.next_seg_syn_q()

    def save_current_synapse(self):

        current_type = self.types_todo[self.type_pos]
        current_synapse = self.cell_data['all_syn'][self.syn_id][current_type][self.synapse_pos]
        syn_id = str(current_synapse['pre_syn_id']) + '_' + str(current_synapse['post_syn_id'])

        if syn_id not in self.cell_data['verified_synapses'][current_type]:
            self.cell_data['verified_synapses'][current_type][syn_id] = {
                'basic_info': current_synapse, 
                'results': {}
                }

        for k in self.current_syn_results.keys():
            self.cell_data['verified_synapses'][current_type][syn_id]['results'][k] = deepcopy(self.current_syn_results[k])
        
        self.current_syn_results = {}

    def get_fn_annotations(self, point_type):

        annotations = []
        
        for pos, point in enumerate(self.cell_data['fn_synapses'][point_type]):
            point_array = np.array([int(point[x]/self.vx_sizes['em'][x]) for x in range(3)])
            pa = neuroglancer.PointAnnotation(id=f'{point_type}_{pos}', point = point_array)
            annotations.append(pa)

        return annotations

    def get_syn_annotations(self, point_type):

        annotations = []

        for pos, syn in enumerate(self.cell_data['all_syn'][self.syn_id][point_type]):
            point = np.array(self.get_corrected_bbox_centre(syn['bounding_box'], 'syn_seg', rel_to_em=True))
            pa = neuroglancer.PointAnnotation(id=f'{point_type}_{pos}', point = point)
            annotations.append(pa)

        return annotations

    def create_syn_pr_layers(self):
        
        with self.viewer.txn(overwrite=True) as s:

            s.layers['em'] = neuroglancer.ImageLayer(source = self.em)

            for lname in ['current_pre_segs', 'current_post_segs']:
                s.layers[lname] = neuroglancer.SegmentationLayer(source = self.agglo_seg)
                s.layers[lname].selectedAlpha = 0.10 #For 2D 
                s.layers[lname].objectAlpha = 1.00 #For 3D  
                  
            main_agglo_seg = self.cell_data['metadata']['main_seg']['agglo'][self.agglo_id]
            s.layers['main_agglo_seg'] = neuroglancer.SegmentationLayer(source = self.skel_seg, segment_colors ={})
            s.layers['main_agglo_seg'].pick = False
            s.layers['main_agglo_seg'].selectedAlpha = 0.10 #For 2D 
            s.layers['main_agglo_seg'].objectAlpha = 1.00 #For 3D 
            s.layers['main_agglo_seg'].segments = set([main_agglo_seg])
            s.layers['main_agglo_seg'].segment_colors[int(main_agglo_seg)] = 'blue'
            s.layers['main_agglo_seg'].source[0].subsources[self.skel_source_id] = True
            s.layers['main_agglo_seg'].skeleton_rendering.mode2d = 'lines_and_points'
            s.layers['main_agglo_seg'].skeleton_rendering.line_width2d = 1
            s.layers['main_agglo_seg'].skeleton_rendering.mode3d = 'lines_and_points'
            s.layers['main_agglo_seg'].skeleton_rendering.line_width3d = 1
            
            for point_type in ['outgoing', 'incoming']:

                for point_type2, col in [['syn','yellow'], ['fn','orange']]:

                    l_name = f'{point_type}_{point_type2}'
                    s.layers[l_name] = neuroglancer.AnnotationLayer()
                    s.layers[l_name].tool = "annotatePoint"
                    s.layers[l_name].annotationColor = col

                    if point_type2 == 'syn':
                        s.layers[l_name].annotations = self.get_syn_annotations(point_type)
                    if point_type2 == 'fn':
                        s.layers[l_name].annotations = self.get_fn_annotations(point_type)

            s.layers['root_points'] = neuroglancer.AnnotationLayer()
            s.layers['root_points'].tool = "annotatePoint"
            s.layers['root_points'].annotationColor = 'green'
            s.layers['root_points'].visible = True

            s.layers['synapse_seg'] = neuroglancer.SegmentationLayer(source = self.syn_seg)
            s.layers['synapse_seg'].visible = False     
            s.layers['synapse_seg'].selectedAlpha = 1.0

    def skip_pr(self, mode):

        cell_id = str(self.cells_todo[self.cell_pos])

        if cell_id not in self.skipped:
            self.skipped.append(cell_id)

        with open(f'{self.save_dir}/not_{mode}_proofread.json', 'w') as fp:
            json.dump(self.skipped, fp)

        self.update_mtab(f'Skipped cell {self.cells_todo[self.cell_pos]}')

        self.next_cell(mode)

    def update_cell_data_with_syn(self):

        time_taken = (time.time()-self.start_time)/60

        for datum, dtype in [[time_taken, 'timing'], [self.user, 'users']]:
            self.cell_data['metadata'][dtype]['syn'].append(datum)

        for dtype in self.types_todo:

            for x in self.cell_decisions:
                self.cell_data['metadata']['completion'][dtype].append(x)

            for x in self.syn_decisions:
                self.cell_data['metadata']['completion'][dtype].append(x[0])
            
        self.cell_data['max_stalk_legnth'] = self.max_stalk
        self.cell_data['max_synapse_merge_distance_nm'] = self.max_syn_merge
        self.cell_data['all_synapse_options'] = self.syn_decisions
        self.cell_data['metadata']['data_sources']['skeleton_seg'] = self.skel_seg
        self.cell_data['metadata']['data_sources']['syn_id'] = self.syn_id

    def save_cell_syn_and_next(self):

        self.update_mtab('All synapses assessed, saving cell and moving on to next')
        self.update_cell_data_with_syn()
        self.save_cell_graph('synapses')
        self.next_cell('synapses')
        
        

        
if __name__ == '__main__':

    UserInterface()








    

    

 
