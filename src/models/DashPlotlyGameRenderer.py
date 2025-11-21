from .Pitch import PlotlyPitch
from .DataLoader import DataLoader
from IPython.display import clear_output, display
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict
import plotly.graph_objects as go

class DashPlotlyGameRenderer:
    def __init__(self, config_file=None):
        self.data_loader = DataLoader()

        # Load default configuration from JSON file
        default_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default_game_renderer_config.json')
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        
        # Convert JSON arrays back to tuples where needed
        default_config['display']['figsize'] = tuple(default_config['display']['figsize'])
        default_config['legend']['bbox_anchor'] = tuple(default_config['legend']['bbox_anchor'])
        if config_file:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
            self.config = self._merge_configs(default_config, user_config)
        else:
            self.config = default_config
            
        # Cache for performance optimization
        self._data_cache = {}  # Stores enriched_data, events_data, and frame_events per match_id

    def _merge_configs(self, default_config, user_config):
        """
        Recursively merge user configuration with default configuration.
        User config values take precedence, but missing keys are filled from defaults.
        """
        import copy
        merged = copy.deepcopy(default_config)
        
        for key, value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Override with user value
                merged[key] = value
        
        return merged

    def _get_cached_data(self, match_id):
        '''
        Get cached data or load and cache it for future use.
        '''
        if match_id not in self._data_cache:
            try:
                enriched_data = self.data_loader.create_enriched_tracking_data(match_id)
                events_data = self.data_loader.load_event_data(match_id)
                frame_events = self._precompute_event_associations(events_data)

                self._data_cache[match_id] = {
                'enriched_data': enriched_data,
                'events_data': events_data,
                'frame_events': frame_events
            }
            except Exception as e:
                print(f"Error loading data for match_id {match_id}: {e}")
                raise e
        
        return self._data_cache[match_id]

    def _precompute_event_associations(self, events_data):
        '''
        Pre-compute event associations for all frames by creating a dictionary mapping frame numbers to complete event information like:
        {1: {'player_possession': [...], 'passing_options': [...], ...}}
        '''
        frame_events = defaultdict(lambda: {
            'player_possession': [],
            'passing_options': [],
            'on_ball_engagements': [],
            'off_ball_runs': []
        })
        
        # Group events by type for efficient processing
        event_groups = events_data.groupby('event_type')
        
        # Map event types to their corresponding keys in frame_events
        event_type_mapping = {
            'player_possession': 'player_possession',
            'passing_option': 'passing_options',
            'on_ball_engagement': 'on_ball_engagements',
            'off_ball_run': 'off_ball_runs'
        }
        
        # Process all event types in a single loop
        for event_type, events_group in event_groups:
            if event_type in event_type_mapping:
                target_key = event_type_mapping[event_type]
                for _, event in events_group.iterrows():
                    event_dict = event.to_dict()
                    for frame in range(int(event['frame_start']), int(event['frame_end']) + 1):
                        frame_events[frame][target_key].append(event_dict)
        
        return dict(frame_events)

    def create_pitch(self):
        '''
            This function creates a background soccer pitch using mplsoccer.
        '''
        # Get pitch configuration
        # pitch_config = self.config['pitch']
        pitch = PlotlyPitch(self.config)
        fig = pitch.draw_image()
        
        return fig

    def _get_team_color_mapping(self, enriched_data):
        """
        Create a consistent team name to color mapping based on first occurrence.
        This ensures teams keep the same colors even when they switch sides.
        """
        if not hasattr(self, '_team_color_map'):
            all_teams = sorted(enriched_data['team_name'].unique())  # Sort for consistency
            colors = self.config['teams']['colors']
            self._team_color_map = {team: colors[i % len(colors)] for i, team in enumerate(all_teams)}
        return self._team_color_map

    def _prepare_frame_data(self, enriched_data, frame_events, frame_num):
        '''
        Extract and prepare data for a specific frame.
        Returns frame_data and events, or None if no data found.
        '''
        # Extract tracking in frame - single filter operation
        frame_data = enriched_data[enriched_data['frame'] == frame_num]
        
        if frame_data.empty:
            print(f"No data found for frame {frame_num}")
            return None, None
        
        # Get pre-computed events for this frame
        events = frame_events.get(frame_num, {
            'player_possession': [],
            'passing_options': [],
            'on_ball_engagements': [],
            'off_ball_runs': []
        })
        
        return frame_data, events

    def _compute_player_masks(self, frame_data, events):
        '''
        Compute boolean masks for different player event types.
        Returns dictionary of masks and player IDs.
        '''
        # Extract player IDs from event lists for efficient mask creation
        possession_player_id = events['player_possession'][0]['player_id'] if events['player_possession'] else None
        passing_player_ids = set(event['player_id'] for event in events['passing_options'])
        engagement_player_ids = set(event['player_id'] for event in events['on_ball_engagements'])
        run_player_ids = set(event['player_id'] for event in events['off_ball_runs'])
        
        # Use vectorized operations to create masks
        masks = {
            'player_possession': frame_data['player_id'] == possession_player_id,
            'passing_options': frame_data['player_id'].isin(passing_player_ids),
            'on_ball_engagements': frame_data['player_id'].isin(engagement_player_ids),
            'off_ball_runs': frame_data['player_id'].isin(run_player_ids)
        }
        
        player_ids = {
            'possession_player_id': possession_player_id,
            'passing_player_ids': passing_player_ids,
            'engagement_player_ids': engagement_player_ids,
            'run_player_ids': run_player_ids
        }
        
        return masks, player_ids

    def _clear_dynamic_elements(self, fig):
        '''
        Clear only dynamic elements (players and trajectories), preserve pitch elements.
        The pitch image is stored in layout.images, so clearing fig.data is safe.
        '''
        # Clear all traces (scatter plots, lines, etc.) but preserve layout images (pitch)
        fig.data = []

    def plot_frame(self, fig, enriched_data, frame_events, frame_num):
        '''
        Main function to plot a single frame of the game.
        Assumes pitch is already drawn on the axes.
        '''
        # Step 1: Prepare frame data
        frame_data, events = self._prepare_frame_data(enriched_data, frame_events, frame_num)
        if frame_data is None:
            return fig
        
        # Step 2: Clear dynamic elements from previous frame
        self._clear_dynamic_elements(fig)
        
        # Step 3: Compute player masks
        masks, player_ids = self._compute_player_masks(frame_data, events)

        # Step 4: Plot players using vectorized operations
        self._plot_players(fig, frame_data, masks, enriched_data)
        
        # Step 5: Plot off-ball runs and trajectories
        self._plot_off_ball_runs(fig, frame_data, events, masks)
        
        # Step 6: Plot ball
        self._plot_ball(fig, frame_data)
        
        # Step 7: Add title and legend
        self._add_frame_title(fig, frame_data, frame_num)
        #self._add_legend(fig, frame_data, enriched_data)
        
        return fig

    def _plot_players(self, fig, frame_data, masks, enriched_data):
        '''
        Plot all players using vectorized operations for better performance.
        '''
        # Plot configuration
        size = self.config['players']['styling']['size']
        team_color_map = self._get_team_color_mapping(enriched_data)
        teams = frame_data['team_name'].unique()
            
        # Extract masks for easier access
        possession_mask = masks['player_possession']
        passing_mask = masks['passing_options']
        engagement_mask = masks['on_ball_engagements']
        run_mask = masks['off_ball_runs']

        # Vectorized plotting for better performance
        for team in teams:
            team_mask = frame_data['team_name'] == team
            team_color = team_color_map[team]
            team_data = frame_data[team_mask]
            
            if team_data.empty:
                continue
                
            # Separate goalkeepers and field players for different markers
            gk_mask = team_data['is_gk'] == True
            field_mask = team_data['is_gk'] == False
            
            # Regular field players (no special events)
            regular_field_mask = field_mask & ~possession_mask[team_mask] & ~passing_mask[team_mask] & ~engagement_mask[team_mask]
            regular_field_players = team_data[regular_field_mask]
            
            if not regular_field_players.empty:
                fig.add_trace(go.Scatter(
                    x=regular_field_players['x'],
                    y=regular_field_players['y'],
                    mode='markers',
                    marker=dict(
                        color=[team_color] * len(regular_field_players),
                        size=self.config['players']['styling']['size'],
                        opacity=self.config['players']['styling']['alpha'],
                        line=dict(
                            color=self.config['players']['styling']['edgecolors'],
                            width=self.config['players']['styling']['edge_width']
                        ),
                        symbol='circle'
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # Regular goalkeepers (no special events)
            regular_gk_mask = gk_mask & ~possession_mask[team_mask] & ~passing_mask[team_mask] & ~engagement_mask[team_mask]
            regular_gk_players = team_data[regular_gk_mask]
            
            if not regular_gk_players.empty:
                fig.add_trace(go.Scatter(
                    x=regular_gk_players['x'],
                    y=regular_gk_players['y'],
                    mode='markers',
                    marker=dict(
                        color=[team_color] * len(regular_gk_players),
                        size=self.config['players']['styling']['size'],
                        opacity=self.config['players']['styling']['alpha'],
                        line=dict(
                            color=self.config['players']['styling']['edgecolors'],
                            width=self.config['players']['styling']['edge_width']
                        ),
                        symbol='square'
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Passing option players - field players
            if self.config['players']['events']['passing_options']['enabled']:
                passing_field_mask = field_mask & passing_mask[team_mask]
                passing_field_players = team_data[passing_field_mask]
                
                if not passing_field_players.empty:
                    fig.add_trace(go.Scatter(
                        x=passing_field_players['x'],
                        y=passing_field_players['y'],
                        mode='markers',
                        marker=dict(
                            color=[team_color] * len(passing_field_players),
                            size=self.config['players']['styling']['size'],
                            opacity=self.config['players']['styling']['alpha'],
                            line=dict(
                                color=self.config['players']['events']['passing_options']['edge_color'],
                                width=self.config['players']['events']['passing_options']['edge_width']
                            )
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))

                # Passing option goalkeepers
                passing_gk_mask = gk_mask & passing_mask[team_mask]
                passing_gk_players = team_data[passing_gk_mask]
                
                if not passing_gk_players.empty:
                    fig.add_trace(go.Scatter(
                        x=passing_gk_players['x'],
                        y=passing_gk_players['y'],
                        mode='markers',
                        marker=dict(
                            color=[team_color] * len(passing_gk_players),
                            size=self.config['players']['styling']['size'],
                            opacity=self.config['players']['styling']['alpha'],
                            line=dict(
                                color=self.config['players']['events']['passing_options']['edge_color'],
                                width=self.config['players']['events']['passing_options']['edge_width']
                            ),
                            symbol='square'
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))

            # On-ball engagement players - field players
            if self.config['players']['events']['on_ball_engagement']['enabled']:
                engagement_field_mask = field_mask & engagement_mask[team_mask]
                engagement_field_players = team_data[engagement_field_mask]
                
                if not engagement_field_players.empty:
                    fig.add_trace(go.Scatter(
                        x=engagement_field_players['x'],
                        y=engagement_field_players['y'],
                        mode='markers',
                        marker=dict(
                            color=[team_color] * len(engagement_field_players),
                            size=self.config['players']['styling']['size'],
                            opacity=self.config['players']['styling']['alpha'],
                            line=dict(
                                color=self.config['players']['events']['on_ball_engagement']['edge_color'],
                                width=self.config['players']['events']['on_ball_engagement']['edge_width']
                            )
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                
                # On-ball engagement goalkeepers
                engagement_gk_mask = gk_mask & engagement_mask[team_mask]
                engagement_gk_players = team_data[engagement_gk_mask]
                
                if not engagement_gk_players.empty:
                    fig.add_trace(go.Scatter(
                        x=engagement_gk_players['x'],
                        y=engagement_gk_players['y'],
                        mode='markers',
                        marker=dict(
                            color=[team_color] * len(engagement_gk_players),
                            size=self.config['players']['styling']['size'],
                            opacity=self.config['players']['styling']['alpha'],
                            line=dict(
                                color=self.config['players']['events']['on_ball_engagement']['edge_color'],
                                width=self.config['players']['events']['on_ball_engagement']['edge_width']
                            ),
                            symbol='square'
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
            
            # Player in possession - field players
            if self.config['players']['events']['possession']['enabled']:
                possession_field_mask = field_mask & possession_mask[team_mask]
                possession_field_players = team_data[possession_field_mask]
                
                if not possession_field_players.empty:
                    fig.add_trace(go.Scatter(
                        x=possession_field_players['x'],
                        y=possession_field_players['y'],
                        mode='markers',
                        marker=dict(
                            color=[team_color] * len(possession_field_players),
                            size=self.config['players']['styling']['size'] * self.config['players']['events']['possession']['size_multiplier'],
                            opacity=1.0,
                            line=dict(
                                color=self.config['players']['events']['possession']['edge_color'],
                                width=self.config['players']['events']['possession']['edge_width']
                            )
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))

                # Player in possession - goalkeepers
                possession_gk_mask = gk_mask & possession_mask[team_mask]
                possession_gk_players = team_data[possession_gk_mask]
                
                if not possession_gk_players.empty:
                    marker_size = self.config['players']['styling']['size'] * self.config['players']['events']['possession']['size_multiplier']
                    fig.add_trace(go.Scatter(
                        x=possession_gk_players['x'],
                        y=possession_gk_players['y'],
                        mode='markers',
                        marker=dict(
                            color=[team_color] * len(possession_gk_players),
                            size=marker_size,
                            opacity=1.0,
                            line=dict(
                                color=self.config['players']['events']['possession']['edge_color'],
                                width=self.config['players']['events']['possession']['edge_width']
                            ),
                            symbol='square'
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))

    def _plot_off_ball_runs(self, fig, frame_data, events, masks):
        '''
        Plot off-ball run trajectories.
        '''
        run_mask = masks['off_ball_runs']

        # Plot off ball runs for all teams
        if events['off_ball_runs']:
            run_players = frame_data[run_mask]
            # Create a lookup dictionary for run events by player_id for efficient access
            run_events_by_player = {event['player_id']: event for event in events['off_ball_runs']}
            
            for _, runner in run_players.iterrows():
                player_id = runner['player_id']
                if player_id in run_events_by_player:
                    run_event = run_events_by_player[player_id]
                    
                    # Determine player's direction based on period
                    period = runner['period']
                    if period == 1.0:
                        direction = runner['direction_player_1st_half']
                    elif period == 2.0:
                        direction = runner['direction_player_2nd_half']
                    else:
                        direction = 'left_to_right'  # Default fallback
                    
                    # Apply coordinate transformation based on direction
                    if direction == 'right_to_left':
                        # Negate coordinates when playing right to left
                        x_start = -run_event['x_start']
                        y_start = -run_event['y_start']
                    else:
                        # Keep original coordinates when playing left to right
                        x_start = run_event['x_start']
                        y_start = run_event['y_start']
                    
                    # Plot trajectory line using transformed coordinates
                    fig.add_trace(go.Scatter(
                        x=[x_start, runner['x']],
                        y=[y_start, runner['y']],
                        mode='lines',
                        line=dict(
                            color=self.config['players']['events']['off_ball_runs']['path_color'],
                            width=2,
                            dash='10px 2px'
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    # Plot start position
                    fig.add_trace(go.Scatter(
                        x=[x_start],
                        y=[y_start],
                        mode='markers',
                        marker=dict(
                            color=self.config['players']['events']['off_ball_runs']['path_color'],
                            size=self.config['players']['styling']['size'] / 2,
                            opacity=self.config['players']['events']['off_ball_runs']['alpha'],
                            line=dict(
                                color=self.config['players']['styling']['edgecolors'],
                                width=self.config['players']['styling']['edge_width']
                            )
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
    def _plot_ball(self, fig, frame_data):
        '''
        Plot the ball if available.
        '''
        # Plot ball if available
        if 'ball_x' in frame_data.columns and not frame_data['ball_x'].isna().all():
            ball_data = frame_data[['ball_x', 'ball_y']].dropna()
            if not ball_data.empty:
                fig.add_trace(go.Scatter(
                    x=ball_data['ball_x'],
                    y=ball_data['ball_y'],
                    mode='markers',
                    marker=dict(
                        color=self.config['ball']['color'],
                        size=self.config['ball']['size'],
                        line=dict(
                            color=self.config['ball']['edge_color'],
                            width=self.config['ball']['edge_width']
                        )
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))

    def _add_frame_title(self, fig, frame_data, frame_num):
        '''
        Add frame information as title.
        '''
        # Add frame num | Time elapsed | Period
        timestamp = frame_data['timestamp'].iloc[0] if 'timestamp' in frame_data.columns else 'N/A'
        period = frame_data['period'].iloc[0] if 'period' in frame_data.columns else 'N/A'
        
        if timestamp != 'N/A':
            try:
                timestamp_dt = pd.to_datetime(timestamp)
                time_display = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_display = str(timestamp)
        else:
            time_display = str(timestamp)
        
        # Create a more prominent title display
        title_text = f'Frame: {frame_num} | Timestamp : {time_display} | Period: {int(period)}'
        fig.update_layout(title=title_text)

    def _add_legend(self, fig, frame_data, enriched_data):
        '''
        Add legend to the plot (only if not already cached).
        '''
        pass
        
 
    
    def plot_episode(self, match_id, start_frame, end_frame, delay=0.0):
        '''
        Highly optimized function to plot an episode (sequence of frames) from start_frame to end_frame.
        Uses caching, pre-computed event associations, vectorized plotting, and static pitch reuse.
        '''
        # Get cached data or load and cache it
        cached_data = self._get_cached_data(match_id)
        enriched_data = cached_data['enriched_data']
        frame_events = cached_data['frame_events']
        
        # Collect frames within episode
        available_frames = sorted(enriched_data['frame'].unique())
        frames_to_plot = [f for f in available_frames if start_frame <= f <= end_frame]
        
        if not frames_to_plot:
            print(f"No frames found in range {start_frame}-{end_frame}")
            return
        
        # Create figure and axes with pitch drawn once
        fig = self.create_pitch()
        
        # Reset legend cache for new episode
        if hasattr(self, '_legend_created'):
            delattr(self, '_legend_created')
        
        # Alternative: If display handle doesn't work, use optimized clear_output
        # Optimized animation loop - pitch is already drawn by create_pitch()
        figs = []
        for frame_num in frames_to_plot:
                
            fig = self.plot_frame(fig, enriched_data, frame_events, frame_num)
            
            # Use clear_output with wait=True to minimize blank time
            import copy
            figs.append(copy.deepcopy(fig))
                    
        return figs
    
    def plot_saved_episode(self, episode_path, delay=0.0):
        '''
            Plot a saved episode from it's JSON file in the specified directory.
        '''
        # Check if file exists
        if not os.path.exists(episode_path):
            raise FileNotFoundError(f"Episode file not found: {episode_path}")
        try:
            with open(episode_path, 'r') as f:
                episode_data = json.load(f)
            
            match_id = episode_data['episode_data']['match_id']
            start_frame = episode_data['episode_data']['frame_start']
            end_frame = episode_data['episode_data']['frame_end']
            
            self.plot_episode(match_id, start_frame, end_frame, delay)
            
        except Exception as e:
            print(f"Error loading episode from {episode_path}: {e}")
       
        
    
    def clear_cache(self):
        '''
        Clear all cached data to free memory.
        '''
        self._data_cache.clear()
        if hasattr(self, '_team_color_map'):
            delattr(self, '_team_color_map')
        if hasattr(self, '_legend_created'):
            delattr(self, '_legend_created')