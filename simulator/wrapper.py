import time
import re
import numpy as np
import pandas as pd

import simulator.simcode.ToPlayWith.MainCode4Simulation as simcode



class Simulation:
    # Input data
    nodes = pd.DataFrame()
    durations = None
    vehicles = pd.DataFrame()
    disruptions = pd.DataFrame()
    movements = pd.DataFrame()
    # Output data
    mission_log = pd.DataFrame()

    def __init__(self):
        self.params = {
                'init_tog': 3,
                'alpha': 10,
                'beta': 1,
                'delta': 1,
                'gamma': 0,
                'threshold': 1,
                'EAD_slack': 24 * 3,
                'tog_reset': 5,
                'save_folder_path': "sim_output",
                'mog_slowdown_times': [0],
                'prioritize_unit_integrity': 0
            }

    # Get trip durations for each type of vectorize
    #   sheets: 'Durations_plane', 'Durations_boot', 'Durations_train', 'Durations_truck'
    def get_durations_xlsx(self, xls: pd.ExcelFile):
        vehicle_kinds = ["plane", "boat", "train", "truck"]
        self.durations = {}
        for kind in vehicle_kinds:
            raw = pd.read_excel(xls, "Durations_%s" % kind, index_col=0).to_dict()
            cleaned = {}
            # Add routes with value for duration (skip NaNs)
            for a in raw.keys():
                row = {}
                for b in raw[a].keys():
                    if not np.isnan(raw[a][b]):
                        row[b] = raw[a][b]
                if len(row) > 0:
                    cleaned[a] = row
            self.durations[kind] = cleaned

    # Gets vehicles and add duration data to them
    #   sheets: 'Vehicles'
    #   requires: self.durations
    def get_vehicles_xlsx(self, xls: pd.ExcelFile):
        if not self.durations:
            raise ValueError("Durations must be added before get_vehicles_xlsx() is called")
        self.vehicles = pd.read_excel(xls, "Vehicles")
        self.vehicles.rename(columns = {
                "pax_capacity": "PAX_capacity",
                "speed": "speed",
                "offload_time": "ofld_time",
                "Enrt_time": "ENRT_time",
                "Model": "model"
            }, inplace = True)
        self.vehicles.set_index("model", inplace=True)
        self.vehicles.insert(len(self.vehicles.columns), "edge_dict", {})

        for idx, row in self.vehicles.iterrows():
            # Convert home bases string to dict
            d = dict()
            for home in row["home"].split(","):
                ele = home.split(":")
                d[ele[0]] = ele[1]
            self.vehicles.at[idx,"home"] = d

            # Add travel durations dictionary for each vehicle
            kind = self.vehicles.at[idx, "type"]
            if kind not in ["train", "truck"]:
                self.vehicles.at[idx, "edge_dict"] = self.durations[self.vehicles.at[idx, "type"]]
            # Add only paths connected to the home node for trains and trucks
            else:
                visited = set()
                edge_dict = {}
                to_visit = [list(self.vehicles.at[idx, "home"].keys())[0]]
                while len(to_visit) > 0:
                    node = to_visit.pop()
                    edge_dict[node] = self.durations[kind][node]
                    for dest, distance in edge_dict[node].items():
                        if dest in visited:
                            continue
                        to_visit.append(dest)
                        visited.add(dest)
                self.vehicles.at[idx, "edge_dict"] = edge_dict

    # Get location nodes (bases, ports, etc)
    #   sheets: 'Army_nodes'
    def get_nodes_xlsx(self, xls: pd.ExcelFile):
        self.nodes = pd.read_excel(xls, "Army_nodes")
        self.nodes[["Dist_start","Dist_len"]] = 0
        self.nodes.set_index("ICAO", inplace=True)
        self.nodes["pmog"] = [
                {
                    "plane": row.pmog_p,
                    "boat": row.pmog_b,
                    "truck": row.wmog_t,
                    "train": row.wmog_tr
                }
                for idx, row in self.nodes.iterrows()
            ]
        self.nodes["wmog"] = [
                {
                    "plane": row.wmog_p,
                    "boat": row.wmog_b,
                    "truck": np.ceil(row.wmog_t/24),
                    "train": np.ceil(row.wmog_tr/24)
                }
                for idx, row in self.nodes.iterrows()
            ]
        unwanted = self.nodes.columns[self.nodes.columns.str.startswith(("pmog_", "wmog_"))]
        self.nodes.drop(unwanted, axis=1, inplace=True)

    # Get cargo movements required for mission
    #   sheets: 'cargo_agg'
    #   note: does NOT read TPFDD sheet
    def get_movements_xlsx(self, xls: pd.ExcelFile):
        movement_data_grouped = pd.read_excel(xls,'cargo_agg')
        if movement_data_grouped.empty:
            raise ValueError("Missing movement data (empty Excel sheet)")
        a = 1
        movement_data_grouped['ID'] = movement_data_grouped['ID'] + '_' +  movement_data_grouped['Unit_Name']
        movement_data_grouped.ID = movement_data_grouped.ID.str.replace(r'[^0-9a-zA-Z]+', r'_')
        # clean up names
        def column_clean(x):
            x = re.sub(" ", "_", x)
            x = re.sub("#", "n", x)
            x = re.sub("[^0-9a-zA-Z_]+", "", x)
            return x
        movement_data_grouped = movement_data_grouped.rename(columns=column_clean)

        # multiply values by number of units
        total_column_names = ['PERSONNEL', 'SP_SQ_FT','TOWED_SQ_FT','NR_SQ_FT','T_SQ_FT','BULK_STONS','OVER_STON','OUT_STON' ]
        for col in total_column_names:
            movement_data_grouped['TOT_'+col] = movement_data_grouped[col]*movement_data_grouped['n_OF_UNITS']

        # break each row up into different types of cargo
        self.movements = pd.DataFrame()
        cargo_types = ['cargo', 'out', 'PAX']
        cs = len(cargo_types)
        cols_to_copy = ['POE','POD','ALD','EAD','LAD','RDD','Unit_prio','PRIORITY','TRUCKTRAIN','COMBAT_POWER']
        for idx, row in movement_data_grouped.iterrows():
            for i,c_type in enumerate(cargo_types):
                index = idx*len(cargo_types) + i
                self.movements.loc[index,'UNIT_NAME'] = movement_data_grouped.loc[idx,'Unit_Name']
                self.movements.loc[index,cols_to_copy] = movement_data_grouped.loc[idx,cols_to_copy]
                self.movements.loc[index,'ID'] = movement_data_grouped.loc[idx,'ID']+'-'+c_type
                self.movements.loc[index,'c_type'] = c_type
                self.movements.loc[index,'PAX2load'] = 0
                self.movements.loc[index,'cargo2load'] = 0
                self.movements.loc[index,'out2loadsqft'] = 0
                self.movements.loc[index,'out2loadStons'] = 0

                if c_type == 'cargo':
                    self.movements.loc[index,'cargo_STONS'] = movement_data_grouped.loc[idx,'TOT_BULK_STONS'].astype(float)
                    self.movements.loc[index,'SQFT'] =  0
                    self.movements.loc[index,'PERSONNEL'] = 0
                    self.movements.loc[index,'cargo2load'] = self.movements.loc[index,'cargo_STONS']
                elif c_type == 'PAX':
                     self.movements.loc[index,'STONS'] = 0
                     self.movements.loc[index,'cargo_STONS'] = 0
                     self.movements.loc[index,'SQFT'] =  0
                     self.movements.loc[index,'PERSONNEL'] = movement_data_grouped.loc[idx,'TOT_PERSONNEL']
                else: # outover
                    self.movements.loc[index,'cargo_STONS'] = 0
                    self.movements.loc[index,'STONS'] = movement_data_grouped.loc[idx,'TOT_OVER_STON'] + movement_data_grouped.loc[idx,'TOT_OUT_STON']
                    self.movements.loc[index,'SQFT'] = movement_data_grouped.loc[idx,'TOT_SP_SQ_FT'] + movement_data_grouped.loc[idx,'TOT_NR_SQ_FT'] + movement_data_grouped.loc[idx,'TOT_T_SQ_FT'] +movement_data_grouped.loc[idx,'TOT_TOWED_SQ_FT']
                    self.movements.loc[index,'PERSONNEL'] = 0
                    self.movements.loc[index,'out2loadsqft'] = self.movements.loc[index,'SQFT']
                    self.movements.loc[index,'out2loadStons'] = self.movements.loc[index,'STONS']

        # consolodate PAX loads and cargo loads by priority level and unit
        prio_df = self.movements.groupby(['PRIORITY','Unit_prio']).agg({
                'UNIT_NAME':'unique',
                'POE':'unique',
                'POD':'unique',
                'ALD':'unique',
                'EAD':'unique',
                'LAD':'unique',
                'RDD':'unique',
                'COMBAT_POWER':'unique',
                'ID':'unique',
                'PERSONNEL':'sum',
                'cargo_STONS':'sum'
            }).reset_index()
        cols_2_simplify = ['POE','POD','ALD','EAD','LAD','RDD','UNIT_NAME']
        for cols in cols_2_simplify:
            prio_df[cols] = prio_df[cols].map(lambda x: x[0])

        prio_df.columns = prio_df.columns.get_level_values(0)

        prio_df['MTONS'] = prio_df['ID']
        prio_df['ID'] = prio_df['UNIT_NAME']+'_cargo_prio_'+prio_df['PRIORITY'].astype(str)
        prio_df['c_type'] = 'cargo'
        prio_df['cargo2load'] = prio_df['cargo_STONS']
        prio_df['out2loadsqft'] = 0
        prio_df['out2loadStons'] = 0
        prio_df['SQFT'] = 0
        prio_df['STONS'] = 0
        prio_df['PAX2load'] = 0
        prio_df['TRUCKTRAIN'] = 'C17' # don't like this card coded inhere

        prio_df2 = prio_df.copy(deep=True)
        prio_df2['ID'] = prio_df2['UNIT_NAME']+'_PAX_prio_'+prio_df2['PRIORITY'].astype(str)
        prio_df2['cargo_STONS'] = 0
        prio_df2['cargo2load'] = 0
        prio_df['PERSONNEL'] = 0
        prio_df2['c_type'] = 'PAX'
        prio_df2['PAX2load'] = prio_df2['PERSONNEL']
        prio_df2['TRUCKTRAIN'] = 'B777'

        # need to clean up values here - sets rather than int.. ect....
        self.movements = self.movements[self.movements['c_type'] == 'out']
        self.movements = pd.concat([self.movements, prio_df, prio_df2], ignore_index=True)
        self.movements['PRIORITYx'] = self.movements['PRIORITY'] + 10*(self.movements['Unit_prio'] - 1)
        self.movements['Load_time'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['arrive_time'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['vehicle'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['amount_moved'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['Location'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['current_Leg'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['undeliverable'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['late'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['est_boat_arrival'] = None
        self.movements['sub_idx'] = np.empty((len(self.movements), 0)).tolist()
        self.movements['est_dur2_next_port'] = 0
        self.movements['transloaded'] = 0
        self.movements['need2transload'] = 0
        self.movements['delivered'] = 0

        self.movements.reset_index(inplace=True)
        self.movements = self.movements[self.movements['POD'].notna()]
        self.movements['LAD'] = self.movements['LAD']*24
        self.movements['ALD'] = self.movements['ALD']*24
        self.movements['RLD'] = self.movements['ALD']-24*3
        self.movements['EAD'] = self.movements['LAD']-24*5
        self.movements['RDD'] = self.movements['RDD']*24
        self.movements = self.movements.reindex(columns=[*self.movements.columns.tolist(), 'transload_vehicle', 'est_TOA_next_port', 'latest_arrival_next_node','earliest_arrival_next_node','status'], fill_value=None)
        # sort self.movements by priority
        self.movements.sort_values(by = 'PRIORITYx', inplace= True)
        # Remove 'index' column
        if 'index' in self.movements:
            self.movements.drop(['index'], axis = 1, inplace=True)


    # Create simulation with data from single XLSX file
    @staticmethod
    def from_xlsx(path: str):
        self = Simulation()
        xls = pd.ExcelFile(path)
        self.get_nodes_xlsx(xls)
        self.get_durations_xlsx(xls)
        self.get_vehicles_xlsx(xls)
        self.get_movements_xlsx(xls)
        self.distruption = pd.read_excel(xls, 'disturbances')
        return self

    def set_vehicle_counts(self, counts: dict):
        for v, c in counts.items():
            self.vehicles.at[v, "number_avail"] = c
            homes = self.vehicles.at[v, "home"]
            frac = int(c / len(homes))
            for h in homes:
                homes[h] = frac
                c -= frac
            homes[h] += c
            self.vehicles.at[v, "home"] = homes

    def run(self):
        if self.nodes.empty or self.vehicles.empty or self.movements.empty:
            raise ValueError("Missing simulation data")
        simcode.run_simulation(self.params, self.vehicles, self.movements, self.nodes, self.disruptions)
        # Create log
        vehicle_POEs = list(self.movements['POE'])
        self.mission_log = simcode.calc_late_loads(vehicle_POEs)

    def save_to_csv(self, path: str):
        if self.mission_log.empty:
            raise ValueError("No mission data to save to CSV")
        self.mission_log.to_csv(path)
