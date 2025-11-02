from mplsoccer.pitch import Pitch 
from .DataLoader import DataLoader
from IPython.display import clear_output, display
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict

class GameRenderer:
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
        pitch = Pitch(
            pitch_type=self.config['pitch']['type'],
            pitch_length=self.config['pitch']['dimensions']['length'],
            pitch_width=self.config['pitch']['dimensions']['width'],
            pitch_color=self.config['pitch']['styling']['background_color'],
            line_color=self.config['pitch']['styling']['line_color'],
            linewidth=self.config['pitch']['styling']['line_width'],
            line_alpha=self.config['pitch']['styling']['line_alpha'],
            stripe_color=self.config['pitch']['styling']['stripe_color'],
            stripe=self.config['pitch']['styling']['show_stripes']
        )
        fig, ax = pitch.draw(figsize=self.config['display']['figsize'])
        
        return fig, ax

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

    def plot_frame(self, ax, enriched_data, frame_events, frame_num):
        '''
        Plots a single frame of the game.
        '''     

        # Extract tracking in frame - single filter operation
        frame_data = enriched_data[enriched_data['frame'] == frame_num]
        
        if frame_data.empty:
            print(f"No data found for frame {frame_num}")
            return ax
        
        # Get pre-computed events for this frame
        events = frame_events.get(frame_num, {
            'player_possession': [],
            'passing_options': [],
            'on_ball_engagements': [],
            'off_ball_runs': []
        })
        
        # Extract player IDs from event lists for efficient mask creation
        possession_player_id = events['player_possession'][0]['player_id'] if events['player_possession'] else None
        passing_player_ids = set(event['player_id'] for event in events['passing_options'])
        engagement_player_ids = set(event['player_id'] for event in events['on_ball_engagements'])
        run_player_ids = set(event['player_id'] for event in events['off_ball_runs'])
        
        # Clear everything from the axes and recreate the pitch
        ax.clear()
        
        # Recreate the pitch for this frame
        pitch = Pitch(
            pitch_type=self.config['pitch']['type'],
            pitch_length=self.config['pitch']['dimensions']['length'],
            pitch_width=self.config['pitch']['dimensions']['width'],
            pitch_color=self.config['pitch']['styling']['background_color'],
            line_color=self.config['pitch']['styling']['line_color'],
            linewidth=self.config['pitch']['styling']['line_width'],
            line_alpha=self.config['pitch']['styling']['line_alpha'],
            stripe_color=self.config['pitch']['styling']['stripe_color'],
            stripe=self.config['pitch']['styling']['show_stripes']
        )
        pitch.draw(ax=ax)

        # Plot configuration
        size = self.config['players']['styling']['size']
        team_color_map = self._get_team_color_mapping(enriched_data)
        teams = frame_data['team_name'].unique()
            
        # Use vectorized operations to create masks
        possession_mask = frame_data['player_id'] == possession_player_id
        passing_mask = frame_data['player_id'].isin(passing_player_ids)
        engagement_mask = frame_data['player_id'].isin(engagement_player_ids)
        run_mask = frame_data['player_id'].isin(run_player_ids)

        for team in teams:
            team_mask = frame_data['team_name'] == team
            team_color = team_color_map[team]
            
            # Regular players (no special events)
            regular_mask = team_mask & ~possession_mask & ~passing_mask & ~engagement_mask
            regular_players = frame_data[regular_mask]
            if not regular_players.empty:
                for _, player in regular_players.iterrows():
                    marker = 's' if player['is_gk'] else 'o'
                    ax.scatter(player['x'], player['y'], c=team_color,
                              alpha=self.config['players']['styling']['alpha'], s=self.config['players']['styling']['size'], edgecolors=self.config['players']['styling']['edgecolors'], linewidths=self.config['players']['styling']['edge_width'],
                              marker=marker, zorder=self.config['players']['styling']['z_order'])

            # Passing option players (yellow border)
            passing_option_players = frame_data[team_mask & passing_mask]
            if self.config['players']['events']['passing_options']['enabled'] == True and not passing_option_players.empty:
                for _, player in passing_option_players.iterrows():
                    marker = 's' if player['is_gk'] else 'o'
                    ax.scatter(player['x'], player['y'], c=team_color,
                              alpha=self.config['players']['styling']['alpha'], s=self.config['players']['styling']['size'], edgecolors=self.config['players']['events']['passing_options']['edge_color'], linewidths=self.config['players']['events']['passing_options']['edge_width'],
                              marker=marker, zorder=self.config['players']['events']['passing_options']['z_order'])

            # On-ball engagement players (black border and larger size)
            engagement_players = frame_data[team_mask & engagement_mask]
            if self.config['players']['events']['on_ball_engagement']['enabled'] == True and not engagement_players.empty:
                for _, player in engagement_players.iterrows():
                    marker = 's' if player['is_gk'] else 'o'
                    ax.scatter(player['x'], player['y'], c=team_color,
                              alpha=self.config['players']['styling']['alpha'], s=self.config['players']['styling']['size'], edgecolors=self.config['players']['events']['on_ball_engagement']['edge_color'], linewidths=self.config['players']['events']['on_ball_engagement']['edge_width'],
                              marker=marker, zorder=self.config['players']['events']['on_ball_engagement']['z_order'])
            
            # Player in possession (largest size and white border)
            possession_player = frame_data[team_mask & possession_mask]
            if self.config['players']['events']['possession']['enabled'] == True and not possession_player.empty:
                for _, player in possession_player.iterrows():
                    marker = 's' if player['is_gk'] else 'o'
                    marker_size = self.config['players']['styling']['size'] * self.config['players']['events']['possession']['size_multiplier']
                    ax.scatter(player['x'], player['y'], c=team_color,
                              alpha=1.0, s=marker_size, edgecolors=self.config['players']['events']['possession']['edge_color'], linewidths=self.config['players']['events']['possession']['edge_width'],
                              marker=marker, zorder=self.config['players']['events']['possession']['z_order'])

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
                    ax.plot([x_start, runner['x']],
                           [y_start, runner['y']],
                           color=self.config['players']['events']['off_ball_runs']['path_color'], linewidth=2, linestyle='--', zorder=8)
                    # Plot start position
                    ax.scatter(x_start, y_start, c=self.config['players']['events']['off_ball_runs']['path_color'],
                              alpha=self.config['players']['events']['off_ball_runs']['alpha'], s=size / 2, edgecolors=self.config['players']['styling']['edgecolors'], linewidths=self.config['players']['styling']['edge_width'], zorder=self.config['players']['events']['off_ball_runs']['z_order'])
        # Plot ball if available
        if 'ball_x' in frame_data.columns and not frame_data['ball_x'].isna().all():
            ball_data = frame_data[['ball_x', 'ball_y']].dropna()
            if not ball_data.empty:
                ax.scatter(
                    ball_data['ball_x'].iloc[0],
                    ball_data['ball_y'].iloc[0],
                    c=self.config['ball']['color'],
                    s=self.config['ball']['size'],
                    edgecolors=self.config['ball']['edge_color'],
                    linewidths=self.config['ball']['edge_width'],
                    zorder=self.config['ball']['z_order']
                )
        
        
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
        ax.set_title(title_text, fontsize=self.config['display']['title']['fontsize'], color=self.config['display']['title']['color'], pad=self.config['display']['title']['pad'])
        
        # Add legend
        if self.config['legend']['enabled'] == True:
            # Create team legend elements using the consistent color mapping
            team_legend_elements = [
                plt.scatter([], [], c=team_color_map[team], s=self.config['legend']['text_size'], 
                           edgecolors=self.config['players']['styling']['edgecolors'], 
                           linewidths=self.config['players']['styling']['edge_width'], label=team)
                for team in sorted(teams)  # Sort for consistent legend order
            ]
            
            legend_elements = team_legend_elements + [
                plt.scatter([], [], c='gray', s=self.config['legend']['text_size'], edgecolors=self.config['players']['events']['possession']['edge_color'], linewidths=self.config['players']['events']['possession']['edge_width'], label='Player in Possession'),
                plt.scatter([], [], c='gray', s=self.config['legend']['text_size'], edgecolors=self.config['players']['events']['passing_options']['edge_color'], linewidths=self.config['players']['events']['passing_options']['edge_width'], label='Passing Option'),
                plt.scatter([], [], c='gray', s=self.config['legend']['text_size'], edgecolors=self.config['players']['events']['on_ball_engagement']['edge_color'], linewidths=self.config['players']['events']['on_ball_engagement']['edge_width'], label='On-Ball Engagement'),
                plt.Line2D([0], [0], color=self.config['players']['events']['off_ball_runs']['path_color'], linestyle=self.config['players']['events']['off_ball_runs']['path_style'], label='Off-Ball Run Path'),
                plt.scatter([], [], c='white', s=50, edgecolors='black', label='Ball'),
            ]
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
        return ax
        
 
    
    def plot_episode(self, match_id, start_frame, end_frame, delay=0.0):
        '''
        Optimized function to plot an episode (sequence of frames) from start_frame to end_frame.
        Uses pre-computed event associations and avoids repeated data loading.
        '''
        # Load data once
        enriched_data = self.data_loader.create_enriched_tracking_data(match_id)
        events_data = self.data_loader.load_event_data(match_id)
        
        # Pre-compute event associations once
        frame_events = self._precompute_event_associations(events_data)
        
        # Collect frames within episode
        available_frames = sorted(enriched_data['frame'].unique())
        frames_to_plot = [f for f in available_frames if start_frame <= f <= end_frame]
        
        # Create pitch once and reuse
        fig, ax = self.create_pitch()
        
        # Optimized animation loop
        for frame_num in frames_to_plot:
            self.plot_frame(ax, enriched_data, frame_events, frame_num)
            clear_output(wait=True)
            display(fig)
            
            if delay > 0:
                time.sleep(delay)
                    
        # return fig, ax