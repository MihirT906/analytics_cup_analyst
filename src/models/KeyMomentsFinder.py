
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

    def find_key_moments(self, config):
        match_id = config['match_id']
        sequence_func = config['sequence_func']
        start_buffer = config.get('start_buffer', 0)
        end_buffer = config.get('end_buffer', 0)
        column_aggregations = config.get('column_aggregations', {})
        events_data = self.import_data(match_id)
        events_with_sequence_data = self.create_sequence_column(match_id, sequence_func, events_data)
        events_with_sequence_data = events_with_sequence_data[list(column_aggregations.keys()) + ['Sequence_ID']]
        grouped_data = events_with_sequence_data.groupby('Sequence_ID').agg(column_aggregations).reset_index()
        grouped_data['frame_start'] = grouped_data['frame_start'] - start_buffer
        grouped_data['frame_end'] = grouped_data['frame_end'] + end_buffer
        return grouped_data