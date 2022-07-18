import pandas as pd
import sqlite3
from google.cloud import bigquery 
from google.cloud import bigquery_storage            
from google.oauth2 import service_account
import os

agglo_address = 'brainmaps://964355253395:h01:goog14r0seg1_agg20200916c3_flat'
synapse_seg_address = 'brainmaps://964355253395:h01:goog14r0s5c3'
em_address = 'precomputed://gs://h01-release/data/20210601/4nm_raw'

em_voxel_size = ['em', 8, 8, 33, 513479, 352744, 5220]
agglo_voxel_size = ['seg', 8, 8, 33, 513479, 352744, 5220]
synapse_voxel_size = ['syn_seg', 8, 8, 33, 513479, 352744, 5220]

synapse_biquery_db = 'goog14r0s5c3.synaptic_connections_ei_conserv_reorient_fix_ei_spinecorrected_merge_correction2'
region_and_type_bigquery_db = 'goog14r0seg1.agg20200916c3_regions_types_circ_bounds_no_duplicates'
agglo_seg_info_bigquery_db = 'goog14r0seg1.agg20200916c3_objinfo'
output_db_path = '/home/alexshapsoncoe/drive/CREST_browsing_database_goog14r0s5c3_spinecorrected_july2022.db' #'D:/sqlite_databases/CREST_browsing_database_goog14r0s5c3_spinecorrected_july2022.db' #
cred_path = '/home/alexshapsoncoe/drive/alexshapsoncoe.json' #'c:/work/alexshapsoncoe.json' #
temp_store_dir = '/home/alexshapsoncoe/drive/sqlite3_tmp_files' #'D:/sqlite_databases/sqlite3_tmp_files' #


if __name__ == '__main__':

    credentials = service_account.Credentials.from_service_account_file(cred_path)
    client = bigquery.Client(project=credentials.project_id, credentials=credentials)
    bqstorageclient = bigquery_storage.BigQueryReadClient(credentials=credentials)

    if not os.path.exists(temp_store_dir):
        os.mkdir(temp_store_dir)

    # Create database:
    conn = sqlite3.connect(output_db_path) 
    c = conn.cursor()

    c.execute('PRAGMA max_page_count = 2147483646')
    c.execute(f"PRAGMA temp_store_directory = '{temp_store_dir}'")

    # Make segment_lookup_table
    print('Making segment lookup table')

    query = f"""
            with edge_list AS (
                            SELECT 
                                CAST(pre_synaptic_site.neuron_id AS INT) AS pre_seg_id, 
                                CAST(post_synaptic_partner.neuron_id AS INT) AS post_seg_id, 
                                CAST(COUNT(*) AS INT) AS pair_count
                                FROM {synapse_biquery_db}
                                WHERE pre_synaptic_site.neuron_id IS NOT NULL
                                AND post_synaptic_partner.neuron_id IS NOT NULL
                                GROUP BY pre_synaptic_site.neuron_id, post_synaptic_partner.neuron_id
                            ),

                            post_data AS (
                                SELECT 
                                    pre_seg_id, 
                                    SUM(pair_count) AS total_out_syn
                                FROM edge_list
                                GROUP BY pre_seg_id
                                ),
                                
                            pre_data AS (
                                SELECT 
                                    post_seg_id, 
                                    SUM(pair_count) AS total_in_syn
                                FROM edge_list
                                GROUP BY post_seg_id
                                ),

                            combo_counts_pre AS (
                            SELECT
                            pre_seg_id AS seg_id, 
                            IFNULL(total_out_syn, 0) AS total_out_syn,
                            IFNULL(B.total_in_syn, 0) AS total_in_syn
                            FROM post_data A
                            FULL OUTER JOIN pre_data B
                            on B.post_seg_id = A.pre_seg_id
                            ),

                            combo_counts_post AS (
                            SELECT
                            post_seg_id AS seg_id, 
                            IFNULL(B.total_out_syn, 0) AS total_out_syn,
                            IFNULL(total_in_syn, 0) AS total_in_syn
                            FROM pre_data A
                            FULL OUTER JOIN post_data B
                            on B.pre_seg_id = A.post_seg_id
                            ),

                            combo_counts_total AS (
                                SELECT * FROM combo_counts_pre WHERE seg_id IS NOT NULL
                                UNION DISTINCT
                                SELECT * FROM combo_counts_post WHERE seg_id IS NOT NULL
                            ),




            edge_list_by_struc_ei AS(

            SELECT 
                                CAST(pre_synaptic_site.neuron_id AS INT) AS pre_seg_id, 
                                CAST(post_synaptic_partner.neuron_id AS INT) AS post_seg_id, 
                                CAST(COUNT(*) AS INT) AS pair_count,
                                LOWER(pre_synaptic_site.class_label) AS pre_struc_type,
                                LOWER(post_synaptic_partner.class_label) AS post_struc_type,
                                IFNULL(type, 3) AS ei_type
                                FROM {synapse_biquery_db}
                                WHERE pre_synaptic_site.neuron_id IS NOT NULL
                                AND post_synaptic_partner.neuron_id IS NOT NULL
                                GROUP BY pre_synaptic_site.neuron_id, post_synaptic_partner.neuron_id, pre_synaptic_site.class_label, post_synaptic_partner.class_label, IFNULL(type, 3)

            ),

            post_data_by_struc_ei AS (
                                SELECT 
                                    pre_seg_id, 
                                    pre_struc_type,
                                    post_struc_type,
                                    ei_type,
                                    SUM(pair_count) AS total_out_syn, 
                                    MAX(pair_count) AS greatest_post_partner,
                                FROM edge_list_by_struc_ei
                                GROUP BY pre_seg_id, pre_struc_type, post_struc_type, ei_type
                                ),


                                
                            pre_data_by_struc_ei AS (
                                SELECT 
                                    post_seg_id, 
                                    pre_struc_type,
                                    post_struc_type,
                                    ei_type, 
                                    SUM(pair_count) AS total_in_syn, 
                                    MAX(pair_count) AS greatest_pre_partner
                                FROM edge_list_by_struc_ei
                                GROUP BY post_seg_id, pre_struc_type, post_struc_type, ei_type
                                ),

                            combo_counts_pre_by_struc_ei AS (
                            SELECT
                            pre_seg_id AS seg_id, 
                            A.pre_struc_type,
                            A.post_struc_type,
                            A.ei_type, 
                            IFNULL(total_out_syn, 0) AS total_out_syn, 
                            IFNULL(greatest_post_partner, 0) AS greatest_post_partner,
                            IFNULL(B.total_in_syn, 0) AS total_in_syn, 
                            IFNULL(B.greatest_pre_partner, 0) AS greatest_pre_partner
                            FROM post_data_by_struc_ei A
                            FULL OUTER JOIN pre_data_by_struc_ei B
                            ON B.post_seg_id = A.pre_seg_id 
                            AND B.pre_struc_type = A.pre_struc_type
                            AND B.post_struc_type = A.post_struc_type
                            AND B.ei_type = A.ei_type
                            ),

                            combo_counts_post_by_struc_ei AS (
                            SELECT
                            post_seg_id AS seg_id, 
                            A.pre_struc_type,
                            A.post_struc_type,
                            A.ei_type, 
                            IFNULL(B.total_out_syn, 0) AS total_out_syn, 
                            IFNULL(B.greatest_post_partner, 0) AS greatest_post_partner,
                            IFNULL(total_in_syn, 0) AS total_in_syn, 
                            IFNULL(greatest_pre_partner, 0) AS greatest_pre_partner
                            FROM pre_data_by_struc_ei A
                            FULL OUTER JOIN post_data_by_struc_ei B
                            ON B.pre_seg_id = A.post_seg_id
                            AND B.pre_struc_type = A.pre_struc_type
                            AND B.post_struc_type = A.post_struc_type
                            AND B.ei_type = A.ei_type
                            ),

                            combo_counts_total_by_struc_ei AS (
                                SELECT * FROM combo_counts_pre_by_struc_ei WHERE seg_id IS NOT NULL
                                UNION DISTINCT
                                SELECT * FROM combo_counts_post_by_struc_ei WHERE seg_id IS NOT NULL
                            ),

            all_combo_counts AS (
                SELECT
                            A.seg_id, 
                            A.pre_struc_type,
                            A.post_struc_type,
                            A.ei_type, 
                            A.total_out_syn, 
                            A.greatest_post_partner,
                            A.total_in_syn, 
                            A.greatest_pre_partner,
                            B.total_out_syn AS overall_total_out_syn, 
                            B.total_in_syn AS overall_total_in_syn
                            FROM combo_counts_total_by_struc_ei A
                            FULL OUTER JOIN combo_counts_total B
                            ON B.seg_id = A.seg_id
            ),


            post_site_rts AS (
                    select distinct 
                    A.post_synaptic_partner.neuron_id AS seg_id,
                    B.region AS region,
                    B.type AS type,
                    FROM {synapse_biquery_db} A
                    INNER JOIN 
                    {region_and_type_bigquery_db} B
                    ON A.post_synaptic_partner.neuron_id = CAST(B.agglo_id AS INT)
                    ),

                    pre_site_rts AS (
                    select distinct
                    A.pre_synaptic_site.neuron_id AS seg_id,
                    B.region AS region,
                    B.type AS type,
                    FROM {synapse_biquery_db} A
                    INNER JOIN 
                    {region_and_type_bigquery_db} B
                    ON A.pre_synaptic_site.neuron_id = CAST(B.agglo_id AS INT)
                    ),

                    seg_ids_with_region_type AS (
                        select * from pre_site_rts
                        union distinct
                        select * from post_site_rts
                    ),

            region_and_type_and_loc AS (

                    SELECT DISTINCT
                    A.seg_id, 
                    A.type,
                    A.region,
                    CAST((B.bbox.start.x + (B.bbox.size.x / 2)) AS INT) AS x,
                    CAST((B.bbox.start.y + (B.bbox.size.y / 2)) AS INT) AS y,
                    CAST((B.bbox.start.z + (B.bbox.size.z / 2)) AS INT) AS z
                    FROM
                    seg_ids_with_region_type A
                    INNER JOIN {agglo_seg_info_bigquery_db} B
                    on B.id = A.seg_id

            )

            SELECT 
            A.seg_id,
            A.type,
            A.region,
            A.x,
            A.y,
            A.z,
            B.pre_struc_type,
            B.post_struc_type,
            B.ei_type, 
            B.total_out_syn, 
            B.greatest_post_partner,
            B.total_in_syn, 
            B.greatest_pre_partner
            FROM
                    region_and_type_and_loc A
                    INNER JOIN all_combo_counts B
                    on B.seg_id = A.seg_id
            """
    print('pt0')
    df = client.query(query).result().to_dataframe(bqstorage_client=bqstorageclient)
    print('pt1')
    c.execute('''CREATE TABLE IF NOT EXISTS segment_lookup_table 
                (seg_id INT, type text, region text, x INT, y INT, z INT, pre_struc_type text,
                post_struc_type text, ei_type INT, total_out_syn INT, greatest_post_partner INT,
                total_in_syn INT, greatest_pre_partner INT)'''
    )
    conn.commit()
    print('pt2')
            
    df.to_sql('segment_lookup_table', conn,index=False, if_exists='replace')
    conn.commit()
    print('pt3')
    c.execute('''CREATE INDEX idx_segment_xyz ON segment_lookup_table (seg_id, x, y, z)''')
    conn.commit()
    print('pt4')
    c.execute('''CREATE INDEX idx_segment_type_region_only ON segment_lookup_table (seg_id, type, region)''')
    conn.commit()
    print('pt5')
    c.execute('''CREATE INDEX covering_idx_segment_lookup ON segment_lookup_table (ei_type, pre_struc_type, 
                    post_struc_type, type, region, greatest_post_partner, greatest_pre_partner,
                    total_out_syn, total_in_syn, seg_id)''')
    conn.commit()
    print('pt6')

    # Create edge_list_table

    print('Making edge list table')

    query = f"""
        WITH 

        post_site_rts AS (
        select 
        A.post_synaptic_partner.id,
        B.region,
        B.type,
        FROM {synapse_biquery_db} A
        INNER JOIN 
        {region_and_type_bigquery_db} B
        ON A.post_synaptic_partner.neuron_id = CAST(B.agglo_id AS INT)
        ),

        pre_site_rts AS (
        select 
        A.pre_synaptic_site.id,
        B.region,
        B.type,
        FROM {synapse_biquery_db} A
        INNER JOIN 
        {region_and_type_bigquery_db} B
        ON A.pre_synaptic_site.neuron_id = CAST(B.agglo_id AS INT)
        ),

        syn_simple AS (
        SELECT DISTINCT
        A.pre_synaptic_site.id AS pre_id,
        A.pre_synaptic_site.neuron_id AS pre_seg_id,
        A.post_synaptic_partner.id AS post_id,
        A.post_synaptic_partner.neuron_id AS post_seg_id,
        CAST(IFNULL(A.type, 3) AS INT) AS ei_type, 
        LOWER(A.pre_synaptic_site.class_label) AS pre_struc_type, 
        LOWER(A.post_synaptic_partner.class_label) AS post_struc_type, 
        B.region AS pre_region,
        B.type AS pre_type,
        C.region AS post_region,
        C.type AS post_type
        FROM {synapse_biquery_db} A
        INNER JOIN pre_site_rts B
        ON A.pre_synaptic_site.id = B.id
        INNER JOIN post_site_rts C
        ON A.post_synaptic_partner.id = C.id
        WHERE A.pre_synaptic_site.neuron_id IS NOT NULL
        AND A.post_synaptic_partner.neuron_id IS NOT NULL
        )


        SELECT DISTINCT 
        CAST(pre_seg_id AS INT) AS pre_seg_id, 
        CAST(post_seg_id AS INT) AS post_seg_id, 
        CAST(ei_type AS INT) AS ei_type,
        CAST(pre_struc_type AS STRING) AS pre_struc_type,
        CAST(post_struc_type AS STRING) AS post_struc_type,
        CAST(COUNT(*) AS INT) AS pair_count,
        ARRAY_AGG(pre_region)[ORDINAL(1)] AS pre_region,
        ARRAY_AGG(pre_type)[ORDINAL(1)] AS pre_type,
        ARRAY_AGG(post_region)[ORDINAL(1)] AS post_region,
        ARRAY_AGG(post_type)[ORDINAL(1)] AS post_type
        FROM syn_simple
        GROUP BY pre_seg_id, post_seg_id, ei_type, pre_struc_type, post_struc_type

    """
            
    df = client.query(query).result().to_dataframe(bqstorage_client=bqstorageclient) #, progress_bar_type='tqdm_gui')
    print('downloaded edge list')
    c.execute('''CREATE TABLE IF NOT EXISTS edge_list_table 
                (   pre_seg_id INT,
                    post_seg_id INT,
                    ei_type INT,
                    pre_struc_type TEXT,
                    post_struc_type TEXT,
                    pair_count INT,
                    pre_region text,
                    pre_type text,
                    post_region text
                    post_type text)'''
                    )
    conn.commit()


    df.to_sql('edge_list_table', conn,index=False, if_exists='replace')
    conn.commit()
    print('made edge list table')
    c.execute('''CREATE INDEX covering_idx_edge_list ON edge_list_table (ei_type, pre_struc_type, post_struc_type, pre_region, pre_type, post_region, post_type, pair_count,  pre_seg_id, post_seg_id)''')
    conn.commit()
    print('indexed edge list table')

    c.execute('''CREATE INDEX covering_idx_edge_list2 ON edge_list_table (pre_region, pre_type, post_region, post_type, ei_type, pre_struc_type, post_struc_type, pair_count, pre_seg_id, post_seg_id)''')
    conn.commit()
    print('indexed edge list table again')

    
    # Make individual_synapses_table

    query = f"""SELECT 
        CAST(pre_synaptic_site.neuron_id AS INT) AS pre_seg_id, 
        CAST(post_synaptic_partner.neuron_id AS INT) AS post_seg_id, 
        CAST(location.x AS INT) AS x,
        CAST(location.y AS INT) AS y,
        CAST(location.z AS INT) AS z,
        CAST(IFNULL(type, 3) AS INT) AS ei_type,
        LOWER(pre_synaptic_site.class_label) AS pre_struc_type, 
        LOWER(post_synaptic_partner.class_label) AS post_struc_type, 
        FROM {synapse_biquery_db}
        WHERE pre_synaptic_site.neuron_id IS NOT NULL
        AND post_synaptic_partner.neuron_id IS NOT NULL
    """
            
    df = client.query(query).result().to_dataframe(bqstorage_client=bqstorageclient, progress_bar_type='tqdm_gui')

    c.execute('''CREATE TABLE IF NOT EXISTS individual_synapses_table 
                (pre_seg_id INT, post_seg_id INT, x INT, y INT, z INT, ei_type INT, pre_struc_type TEXT, post_struc_type TEXT)'''
    )
    conn.commit()

    print('Making individual synapses table')
    df.to_sql('individual_synapses_table', conn,index=False, if_exists='replace')
    conn.commit()


    c.execute('''CREATE INDEX covering_idx_synapses_pre_seg_first ON individual_synapses_table (pre_seg_id, post_seg_id, ei_type, pre_struc_type, post_struc_type, x, y, z)''')
    conn.commit()

    c.execute('''CREATE INDEX covering_idx_synapses_post_seg_first ON individual_synapses_table (post_seg_id, pre_seg_id, ei_type, pre_struc_type, post_struc_type, x, y, z)''')
    conn.commit()


    # Make voxel_sizes_table
    print('Making voxel sizes and addresses tables')

    c.execute('CREATE TABLE IF NOT EXISTS voxel_sizes_table (dtype text, x INT, y INT, z INT, x_size INT, y_size INT, z_size INT)')
    conn.commit()

    df = pd.DataFrame([em_voxel_size, agglo_voxel_size, synapse_voxel_size], columns=['dtype', 'x', 'y', 'z', 'x_size', 'y_size', 'z_size'])
    df.to_sql('voxel_sizes_table', conn, method='multi',index=False, if_exists='replace')
    conn.commit()


    # Make addresses table:

    c.execute('CREATE TABLE IF NOT EXISTS addresses_table (agglo_address text, synapse_seg_address text, em_address text)')
    conn.commit()

    df = pd.DataFrame([[agglo_address, synapse_seg_address, em_address]], columns=['agglo_address', 'synapse_seg_address', 'em_address'])

    df.to_sql('addresses_table', conn, method='multi',index=False, if_exists='replace')


    # Make unique_pre_structures_table:
    c.execute('''CREATE TABLE IF NOT EXISTS unique_pre_structures_table (pre_structure text)''')
    conn.commit()

    c.execute('SELECT DISTINCT pre_struc_type FROM individual_synapses_table')
    df = pd.DataFrame([x[0] for x in c.fetchall()], columns=['pre_struc_type'])
    df.to_sql('unique_pre_structures_table', conn,index=False, if_exists='replace')
    conn.commit()


    # Make unique_post_structures_table:
    c.execute('''CREATE TABLE IF NOT EXISTS unique_post_structures_table (post_structure text)''')
    conn.commit()

    c.execute('SELECT DISTINCT post_struc_type FROM individual_synapses_table')
    df = pd.DataFrame([x[0] for x in c.fetchall()], columns=['post_struc_type'])
    df.to_sql('unique_post_structures_table', conn,index=False, if_exists='replace')
    conn.commit()

    

    # Make unique types table:

    print('Making unique types and regions table')

    c.execute('''CREATE TABLE IF NOT EXISTS unique_seg_types_table (type text)''')
    conn.commit()

    c.execute('SELECT DISTINCT type FROM segment_lookup_table')
    df = pd.DataFrame([x[0] for x in c.fetchall()], columns=['type'])
    df.to_sql('unique_seg_types_table', conn,index=False, if_exists='replace')
    conn.commit()

    # Make unique regions table:
    c.execute('''CREATE TABLE IF NOT EXISTS unique_seg_regions_table (region text)''')
    conn.commit()

    c.execute('SELECT DISTINCT region FROM segment_lookup_table')
    df = pd.DataFrame([x[0] for x in c.fetchall()], columns=['region'])
    df.to_sql('unique_seg_regions_table', conn,index=False, if_exists='replace')
    conn.commit()

    print('Completed')





# More minimal segment_lookup_table:

# query = f"""
#         WITH 

#         post_site_rts AS (
#         select distinct 
#         A.post_synaptic_partner.neuron_id AS seg_id,
#         B.region AS region,
#         B.type AS type,
#         FROM {synapse_biquery_db} A
#         INNER JOIN 
#         {region_and_type_bigquery_db} B
#         ON A.post_synaptic_partner.neuron_id = CAST(B.agglo_id AS INT)
#         ),

#         pre_site_rts AS (
#         select distinct
#         A.pre_synaptic_site.neuron_id AS seg_id,
#         B.region AS region,
#         B.type AS type,
#         FROM {synapse_biquery_db} A
#         INNER JOIN 
#         {region_and_type_bigquery_db} B
#         ON A.pre_synaptic_site.neuron_id = CAST(B.agglo_id AS INT)
#         ),

#         seg_ids_with_region_type AS (
#             select * from pre_site_rts
#             union distinct
#             select * from post_site_rts
#         )

#         SELECT DISTINCT
#         A.seg_id, 
#         A.type,
#         A.region,
#         CAST((B.bbox.start.x + (B.bbox.size.x / 2)) AS INT) AS x,
#         CAST((B.bbox.start.y + (B.bbox.size.y / 2)) AS INT) AS y,
#         CAST((B.bbox.start.z + (B.bbox.size.z / 2)) AS INT) AS z
#         FROM
#         seg_ids_with_region_type A
#         INNER JOIN {agglo_seg_info_bigquery_db} B
#         on B.id = A.seg_id

#         """


# # Query to get selected seg ids from edge list table, but was too slow:

# query = """

# WITH acceptable_edges AS (

# SELECT pre_seg_id, post_seg_id, pair_count, pre_region, post_region, post_type, pre_type
# FROM edge_list_table
# WHERE
# ei_type IN (1,2, 3)
# AND
# pre_struc_type IN ('axon', 'ais')
# AND
# post_struc_type IN ('dendrite', 'soma')
# ),

# edge_info_condensed AS (
# SELECT
# pre_seg_id, 
# post_seg_id,
# sum(pair_count) AS pair_count,
# SUBSTR(GROUP_CONCAT(pre_region), 0, instr(GROUP_CONCAT(pre_region), ',')-1) AS pre_region,
# SUBSTR(GROUP_CONCAT(pre_type), 0, instr(GROUP_CONCAT(pre_type), ',')-1) AS pre_type,
# SUBSTR(GROUP_CONCAT(post_region), 0, instr(GROUP_CONCAT(post_region), ',')-1) AS post_region,
# SUBSTR(GROUP_CONCAT(post_type), 0, instr(GROUP_CONCAT(post_type), ',')-1) AS post_type
# FROM acceptable_edges
# GROUP BY pre_seg_id, post_seg_id
# ),


# ids_meeting_post_criteria_precursor AS (

#     SELECT 
#     pre_seg_id AS seg_id,
#     SUM(pair_count) AS total_out_syn, 
#     MAX(pair_count) AS greatest_post_partner
#     FROM edge_info_condensed
#     WHERE pre_region IN ('Layer 1', 'Layer 2', 'Layer 3', 'Layer 4', 'Layer 5') 
#     AND pre_type IN ('majority dendrite fragment', 'pure axon fragment', 'majority axon fragment', 'interneuron')
#     GROUP BY pre_seg_id
# ),

# ids_meeting_pre_criteria_precursor AS (

#     SELECT 
#     post_seg_id AS seg_id,
#     SUM(pair_count) AS total_in_syn, 
#     MAX(pair_count) AS greatest_pre_partner
#     FROM edge_info_condensed
#     WHERE post_region IN ('Layer 1', 'Layer 2', 'Layer 3', 'Layer 4', 'Layer 5') 
#     AND post_type IN ('majority dendrite fragment', 'pure axon fragment', 'majority axon fragment', 'interneuron')
#     GROUP BY post_seg_id
# ),

# combined_data AS (

# SELECT 
#     A.seg_id, 
#     IFNULL(A.total_out_syn, 0) AS total_out_syn, 
#     IFNULL(A.greatest_post_partner, 0) AS greatest_post_partner,
#     IFNULL(B.total_in_syn, 0) AS total_in_syn, 
#     IFNULL(B.greatest_pre_partner, 0) AS greatest_pre_partner
# FROM ids_meeting_post_criteria_precursor A
# LEFT JOIN ids_meeting_pre_criteria_precursor B USING(seg_id)
# UNION ALL
# SELECT 
#     A.seg_id, 
#     IFNULL(A.total_out_syn, 0) AS total_out_syn, 
#     IFNULL(A.greatest_post_partner, 0) AS greatest_post_partner,
#     IFNULL(B.total_in_syn, 0) AS total_in_syn, 
#     IFNULL(B.greatest_pre_partner, 0) AS greatest_pre_partner
# FROM ids_meeting_pre_criteria_precursor B
# LEFT JOIN ids_meeting_post_criteria_precursor A USING(seg_id)
# WHERE A.seg_id IS NULL
# )

# SELECT DISTINCT seg_id FROM combined_data 
# WHERE greatest_post_partner > 3
# AND total_out_syn > 0
# AND greatest_pre_partner >= 0 
# AND total_in_syn >= 0

# """

# import time

# start = time.time()
# c.execute(query)
# print(time.time()-start)
# l = c.fetchall()
# print(time.time()-start)
# assert 1==1

