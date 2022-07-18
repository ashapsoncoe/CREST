import pandas as pd
import sqlite3
import os
#import win32api

agglo_address = 'brainmaps://964355253395:h01:goog14r0seg1_agg20200916c3_flat'
em_address = 'precomputed://gs://h01-release/data/20210601/4nm_raw' #'brainmaps://964355253395:h01:goog14r0_8nm'
base_address = 'brainmaps://964355253395:h01:goog14r0seg1'
base_agglo_map_dir = '/home/alexshapsoncoe/drive/agg20200916c3_resolved'
agglo_to_edges_map_dir = '/home/alexshapsoncoe/drive/agg20200916c3_agglotoedges'
base_info_db_dir = '/home/alexshapsoncoe/drive/goog14r0seg1.objinfo_xyz_only'
# all_edges = 'goog14r0seg1.agg20200916c3_alledges'
cloud_storage_address = 'h01-crest-proofread-files'
output_db_path = '/home/alexshapsoncoe/drive/agg20200916c3_crest_proofreading_database.db'
temp_store_dir = '/home/alexshapsoncoe/drive/sqlite3_tmp_files'

em_voxel_size = ['em', 8, 8, 33, 513479, 352744, 5220]
agglo_voxel_size = ['seg', 8, 8, 33, 513479, 352744, 5220]





def make_sql_db_from_shards(conn, table_name, shard_dir):

    c = conn.cursor()

    first_file = os.listdir(shard_dir)[0]

    first_df = pd.read_csv(f'{shard_dir}/{first_file}')

    columns = list(first_df.columns)

    col_str = ', '.join([f'{c} INT' for c in columns])

    c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({col_str})')
    conn.commit()

    for f in os.listdir(shard_dir):

        print(f'Adding data from {f} to {table_name}')

        df = pd.read_csv(f'{shard_dir}/{f}')

        df.to_sql(table_name, conn, index=False, if_exists='append')

        conn.commit()



if __name__ == '__main__':

    #win32api.SetEnvironmentVariable('TMP', tmp_storage_dir)

    # Create database:
    conn = sqlite3.connect(output_db_path) 
    c = conn.cursor()

    c.execute('PRAGMA max_page_count = 2147483646')
    c.execute(f"PRAGMA temp_store_directory = '{temp_store_dir}'")

    # Make voxel_sizes_table
    c.execute('CREATE TABLE IF NOT EXISTS voxel_sizes_table (dtype text, x INT, y INT, z INT, x_size INT, y_size INT, z_size INT)')
    conn.commit()

    df = pd.DataFrame([em_voxel_size, agglo_voxel_size], columns=['dtype', 'x', 'y', 'z', 'x_size', 'y_size', 'z_size'])
    df.to_sql('voxel_sizes_table', conn, method='multi',index=False, if_exists='replace')
    conn.commit()


    # Make addresses table:

    c.execute('CREATE TABLE IF NOT EXISTS addresses_table (agglo_address text, em_address text, base_address text, cloud_storage_address text)')
    conn.commit()

    df = pd.DataFrame([[agglo_address, em_address, base_address, cloud_storage_address]], columns=['agglo_address', 'em_address', 'base_address', 'cloud_storage_address'])

    df.to_sql('addresses_table', conn, method='multi',index=False, if_exists='replace')


    # Make agglo_base_resolved table:

    print('Making agglo_base_resolved table')

    make_sql_db_from_shards(conn, 'agglo_base_resolved', base_agglo_map_dir)

    print('Making index')

    c.execute('''CREATE INDEX covering_idx_agglo_to_base ON agglo_base_resolved (agglo_id, base_id)''')
    conn.commit()

    print('Making index')

    c.execute('''CREATE INDEX covering_idx_base_to_agglo ON agglo_base_resolved (base_id, agglo_id)''')
    conn.commit()


    # Make agglo_to_edges table:
    print('Making agglo_to_edges table')

    make_sql_db_from_shards(conn, 'agglo_to_edges', agglo_to_edges_map_dir)

    print('Making index')

    c.execute('''CREATE INDEX covering_idx_agglo_to_edges ON agglo_to_edges (agglo_id, label_a, label_b)''')
    conn.commit()

    # Make base_location table:
    print('Making base_location table')
    
    make_sql_db_from_shards(conn, 'base_location', base_info_db_dir)

    print('Making index')

    c.execute('''CREATE INDEX covering_idx_base_to_xyz ON base_location (seg_id, x, y, z)''')
    conn.commit()

    print('Completed')





