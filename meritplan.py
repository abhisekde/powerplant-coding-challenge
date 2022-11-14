import pandas
import logging

class MeritPlan:

    def __get_fuel_price(self, fuel_type: str):
        prices = self.__data['fuels']
        if fuel_type == 'gasfired':
            return prices['gas(euro/MWh)']
        if fuel_type == 'turbojet':
            return prices['kerosine(euro/MWh)']
        if fuel_type == 'windturbine':
            return 0.0


    def __get_co2_em_allowances_per_mwh(self, fuel_type: str):
        co2_ton_per_mwh = 0.3
        prices = self.__data['fuels']
        if fuel_type == 'gasfired':
            return prices['co2(euro/ton)'] * co2_ton_per_mwh
        else:
            return 0.0


    def __get_wind_percent(self, fuel_type: str):
        prices = self.__data['fuels']
        if fuel_type == 'windturbine':
            return prices['wind(%)'] * 0.01
        else:
            return 1.0


    def __verify_data(self):
        
        # Expecting a numeric and positive demand for load
        assert int(self.__data['load']) > 0, 'load validation failed'
        
        # Expecting floating positive rates for fuels 
        fuels = dict(self.__data['fuels'])
        assert (
            float(fuels['gas(euro/MWh)']) >= 0.0 and 
            float(fuels['kerosine(euro/MWh)']) >= 0.0 and 
            float(fuels['co2(euro/ton)']) >= 0.0 and 
            float(fuels['wind(%)']) >= 0.0
        ), 'fuels validation failed'

        # Expecting values for powerplant features
        powerplants = self.__data['powerplants']
        for item in powerplants:
            plant = dict(item)
            assert (
                float(plant['efficiency']) >= 0.0 and
                float(plant['efficiency']) <= 1.0 and 
                int(plant['pmin']) >= 0 and 
                int(plant['pmax']) >= 0 and 
                len(plant['name']) >= 1 and 
                len(plant['type']) >= 1
            ), 'powerplants validation failed' 
        # If control reach here - All OK

    def __stage(self):
        # Calculation basis - Efficiency used the fuel cost
        # For sources equal to windpower, the efficiency is alway 1
        self.power_plants['net_efficiency'] = self.power_plants['efficiency'] * self.power_plants['wind_percent']
        self.power_plants['eur_net_fuel_per_mwh'] = self.power_plants['eur_fuel_per_mwh'] / self.power_plants['net_efficiency']
        self.power_plants = self.power_plants.fillna(0)

        # Calculation basis - Efficiency used the power output
        # self.power_plants['eur_net_per_mwh'] = self.power_plants['eur_net_fuel_per_mwh'] + self.power_plants['eur_co2_em_per_mwh']
        # self.power_plants['net_max_mwh'] = self.power_plants['pmax'] * self.power_plants['net_efficiency']
        # self.power_plants['net_min_mwh'] = self.power_plants['pmin'] * self.power_plants['net_efficiency']

        # For fuel sources other than windpower, the wind_percent is alway 1
        self.power_plants['net_max_mwh'] = self.power_plants['pmax'] * self.power_plants['wind_percent']
        self.power_plants['net_min_mwh'] = self.power_plants['pmin'] * self.power_plants['wind_percent']
        self.power_plants['eur_net_per_mwh'] = (self.power_plants['eur_net_fuel_per_mwh'] / self.power_plants['efficiency']) + self.power_plants['eur_co2_em_per_mwh']

        output_unit_mw = 0.1
        self.power_plants['max_units'] = self.power_plants['net_max_mwh'] / output_unit_mw
        self.power_plants['min_units'] = self.power_plants['net_min_mwh'] / output_unit_mw
        self.power_plants['target_units'] = self.power_plants['target_mwh'] / output_unit_mw
        logging.info(f'Staging data complete\n{self.power_plants}')


    def __commit_units(self):
        target_units = self.power_plants['target_units'][0]

        for row in self.power_plants.iterrows():
            data = row[1]

            # Only commit if target_units > 0 

            # Commit powerplant's max_units if target_units > max_units
            # Else commit whatever target_units left

            # Power plant also have to consider the min power output
            # So, while co,,iting target_units find the max b/w 
            # target_units and plant's min_units production

            commit = (
                data.max_units if target_units > data.max_units 
                else max(target_units, data.min_units)
            ) if target_units > 0 else 0
            target_units = target_units - commit

            self.results.append({
                'name': row[1]['name'],
                'p': int(commit)
            })

        result_df = pandas.DataFrame(data=self.results)
        logging.info(f'Operational order\n{result_df}')


    def __sort_by_economy(self):
        params = self.power_plants[[
            "eur_net_per_mwh", 
            "eur_net_fuel_per_mwh", 
            "eur_co2_em_per_mwh", 
            "eur_fuel_per_mwh", 
            "net_efficiency", 
            "efficiency", 
            "wind_percent"
        ]]
        logging.info(f'Parameters\n{params}')
        
        # Sort such that we start the most economic option first
        # For multiple options, start with the max capacity
        # This will ensure that we operate less no. of plants
        self.power_plants.sort_values(
            by=['eur_net_per_mwh', 'max_units', 'min_units'], 
            inplace=True, 
            ascending=[True, False, False],
        )
        logging.info(f'After sorting power plants by economy\n{self.power_plants}')
        

    def calculate(self):
        self.__stage()
        self.__sort_by_economy()
        self.__commit_units()
        return self.results
 
        
        
    def __init__(self, request_data: dict):
        self.__data = request_data
        self.errors = None
        self.results = []

        self.__verify_data()
        logging.info('Request body validation successful')

        plants = pandas.DataFrame(data=self.__data['powerplants'])
        plants['target_mwh'] = self.__data['load'] 
        plants['eur_fuel_per_mwh'] = plants['type'].map(self.__get_fuel_price)
        plants['eur_co2_em_per_mwh'] = plants['type'].map(self.__get_co2_em_allowances_per_mwh)
        plants['wind_percent'] = plants['type'].map(self.__get_wind_percent)
        self.power_plants = plants

