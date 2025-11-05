
from .DataLoader import DataLoader


class KeyMomentsFinder:
    def __init__(self):
        try:
            self.data_loader = DataLoader()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize KeyMomentsFinder: {str(e)}") from e
    
    def import_data(self, match_id):
        '''
            Imports event data for the given match_id using the DataLoader.
        '''
        if not match_id:
            raise ValueError("match_id cannot be empty or None")
            
        events_data = self.data_loader.load_event_data(match_id)
            
        if events_data is None or events_data.empty:
            raise ValueError(f"No events data found for match_id: {match_id}")

        return events_data

    def create_sequence_column(self, sequence_func, events_data=None):
        '''
            Creates a sequence column in the events_data DataFrame using the provided sequence_func that is used to find key moments
        '''
        if not callable(sequence_func):
            raise TypeError("sequence_func must be callable")
        
        if events_data.empty:
            raise ValueError("No data retrieved")

        try:    
            events_data_copy = events_data.copy()
            # Apply the sequence function to create 'Sequence_ID' column
            events_data_copy['Sequence_ID'] = sequence_func(events_data_copy)
            # Drop rows where 'Sequence_ID' is NaN
            events_data_copy = events_data_copy.dropna(subset=['Sequence_ID'])
            
            if events_data_copy.empty:
                raise ValueError("Error in sequence function: resulted in empty data after dropping NaN Sequence_IDs")

            return events_data_copy
            
        except Exception as e:
            raise RuntimeError(f"Failed to create sequence column: {str(e)}") from e

    def find_key_moments(self, config):
        '''
            Finds key moments in the event data based on the provided configuration.
        '''
        if not isinstance(config, dict):
            raise TypeError("config must be a dictionary")
        
        # Ensure required config keys are present
        required_keys = ['match_id', 'sequence_func', 'column_aggregations']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")
            
        try:
            match_id = config['match_id']
            sequence_func = config['sequence_func']
            start_buffer = config.get('start_buffer', 0)
            end_buffer = config.get('end_buffer', 0)
            column_aggregations = config.get('column_aggregations', {})
            
            if not isinstance(start_buffer, (int, float)) or start_buffer < 0:
                raise ValueError("start_buffer must be a non-negative number")
            if not isinstance(end_buffer, (int, float)) or end_buffer < 0:
                raise ValueError("end_buffer must be a non-negative number")
                
            if not column_aggregations:
                raise ValueError("column_aggregations cannot be empty")
            
            events_data = self.import_data(match_id)
            # Retrieve events data with sequence column
            events_with_sequence_data = self.create_sequence_column(sequence_func, events_data)
            
            required_columns = list(column_aggregations.keys()) + ['Sequence_ID']
            missing_columns = [col for col in required_columns if col not in events_with_sequence_data.columns]
            if missing_columns:
                raise KeyError(f"Events data does not contain the following columns mentioned in column_aggregations: {missing_columns}")

            # Filter to required columns only
            events_with_sequence_data = events_with_sequence_data[required_columns]
            # Perform grouping and aggregation
            grouped_data = events_with_sequence_data.groupby('Sequence_ID').agg(column_aggregations).reset_index()
            
            if grouped_data.empty:
                raise ValueError("No grouped data generated")
            
            # Apply buffers
            if 'frame_start' in grouped_data.columns:
                grouped_data['frame_start'] = (grouped_data['frame_start'] - start_buffer).clip(lower=0)
                
            if 'frame_end' in grouped_data.columns:
                grouped_data['frame_end'] = grouped_data['frame_end'] + end_buffer
            
            return grouped_data
            
        except (ValueError, TypeError, KeyError, AttributeError):
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to find key moments: {str(e)}") from e