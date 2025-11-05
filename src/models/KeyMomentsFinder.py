
from .DataLoader import DataLoader

class KeyMomentsFinder:
    def __init__(self):
        self.data_loader = DataLoader()
    
    def import_data(self, match_id):
        events_data = self.data_loader.load_event_data(match_id)
        return events_data

    def create_sequence_column(self, match_id, sequence_func, events_data=None):
        # events_data = self.import_data(match_id)
        events_data['Sequence_ID'] = sequence_func(events_data)
        events_data = events_data.dropna(subset=['Sequence_ID'])
        return events_data

    def find_shots(self, match_id):
        def shot_sequence_logic(df):
            """Logic for shot sequences: all events before and including each shot get same number"""
            df = df[(df['lead_to_shot'] == True) & (df['event_type'] == 'player_possession')]
            return (df['end_type'] == 'shot').cumsum().shift(1, fill_value=0) + 1

        events_data = self.create_sequence_column(match_id, shot_sequence_logic)
        #print(events_data[['frame_start', 'frame_end', 'end_type', 'lead_to_goal', 'lead_to_shot', 'Sequence_ID']])
        return events_data

    def group_shots(self, events_data):
        grouped_data = events_data.groupby('Sequence_ID').agg({
            'frame_start': 'min',
            'frame_end': 'max',
            'lead_to_goal': 'first'
        }).reset_index()
        columns = ['frame_start', 'frame_end', 'lead_to_goal']
        #print(grouped_data[columns])
        return grouped_data[columns]
    
    def find_key_moments(self, config):
        match_id = config['match_id']
        sequence_func = config['sequence_func']
        column_aggregations = config.get('column_aggregations', {})
        events_data = self.import_data(match_id)
        events_with_sequence_data = self.create_sequence_column(match_id, sequence_func, events_data)
        events_with_sequence_data = events_with_sequence_data[list(column_aggregations.keys()) + ['Sequence_ID']]
        grouped_data = events_with_sequence_data.groupby('Sequence_ID').agg(column_aggregations).reset_index()
        return grouped_data
        


        
    # def find_shots(self, match_id):
    #     events_data = self.import_data(match_id)
    #     shots = events_data[(events_data['lead_to_shot'] == True) & (events_data['event_type'] == 'player_possession')]
    #     # Create a column group by index that assigns a number to all rows that lead to a shot. So until end_type == shot
    #     shots['group_by_index'] = (shots.index - shots.index[0]).to_series().cumsum()