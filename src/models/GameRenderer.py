from mplsoccer.pitch import Pitch 
from .DataLoader import DataLoader
from IPython.display import clear_output, display
import time
import matplotlib.pyplot as plt
import pandas as pd

class GameRenderer:
    def __init__(self):
        self.data_loader = DataLoader()

    def create_pitch(self):
        '''
            This function creates a background soccer pitch using mplsoccer.
        '''
        pitch = Pitch(
            pitch_type="skillcorner",
            line_alpha=0.75,
            pitch_length=105,
            pitch_width=68,
            pitch_color="#001400",
            line_color="white",
            linewidth=1.5,
        )
        fig, ax = pitch.draw(figsize=(14, 10))
        
        return fig, ax

    def plot_frame(self, ax, enriched_data, pp_event_row, frame_num):
        '''
            This function plots a single frame of the game on the provided axis.
        '''
        # Remove only scatter plots (players and ball), keep pitch lines
        # Get all collections (scatter plots) and remove them
        for collection in ax.collections[:]:
            if hasattr(collection, '_sizes'):  # This identifies scatter plots
                collection.remove()
        
        frame_data = enriched_data[enriched_data['frame'] == frame_num]
        if frame_data.empty:
            print(f"No data found for frame {frame_num}")
            return

        # Plot configuration
        size = 300
    
        # Get unique teams in this frame
        teams = frame_data['team_name'].unique()
        colors = ['#084D42', '#E51717'] # Green for team 1, Red for team 2
        
        player_in_possession_id = None
        if pp_event_row is not None:
            player_in_possession_id = pp_event_row['player_id']
            
        for i, team in enumerate(teams):
            team_data = frame_data[frame_data['team_name'] == team]
            
            # Regular players (excluding player in possession and goalkeepers)
            regular_players = team_data[
                (team_data['is_gk'] == False) & 
                (team_data['player_id'] != player_in_possession_id)
            ]
            if not regular_players.empty:
                ax.scatter(
                    regular_players['x'],
                    regular_players['y'],
                    c=colors[i % len(colors)],
                    alpha=0.95,
                    s=size,
                    edgecolors='white',
                    linewidths=1.5,
                    zorder=10
                )
            
            # Goalkeepers (different marker)
            goalkeepers = team_data[team_data['is_gk'] == True]
            if not goalkeepers.empty:
                ax.scatter(
                    goalkeepers['x'],
                    goalkeepers['y'],
                    c=colors[i % len(colors)],
                    alpha=0.95,
                    s=size * 1.2,
                    edgecolors='yellow',
                    linewidths=3,
                    marker='s',  # Square marker for GK
                    zorder=10
                )
        
        # Plot player in possession with same team color but thicker edge
        if player_in_possession_id is not None:
            possession_player = frame_data[frame_data['player_id'] == player_in_possession_id]
            if not possession_player.empty:
                # Get the team color for the player in possession
                team_name = possession_player['team_name'].iloc[0]
                team_index = list(teams).index(team_name)
                team_color = colors[team_index % len(colors)]
                
                ax.scatter(
                    possession_player['x'],
                    possession_player['y'],
                    c=team_color,  # Same color as team
                    alpha=1.0,
                    s=size * 1.3,
                    edgecolors='white',
                    linewidths=3,  # Thicker edge
                    zorder=12  # Higher z-order to be on top
                )
        
        # Plot ball if available
        if 'ball_x' in frame_data.columns and not frame_data['ball_x'].isna().all():
            ball_data = frame_data[['ball_x', 'ball_y']].dropna()
            if not ball_data.empty:
                ax.scatter(
                    ball_data['ball_x'].iloc[0],
                    ball_data['ball_y'].iloc[0],
                    c='white',
                    s=100,
                    edgecolors='black',
                    linewidths=2,
                    zorder=15
                )
        
        # Add frame info
        timestamp = frame_data['timestamp'].iloc[0] if 'timestamp' in frame_data.columns else 'N/A'
        period = frame_data['period'].iloc[0] if 'period' in frame_data.columns else 'N/A'
        
        ax.set_title(f'Frame: {frame_num} | Time: {timestamp} | Period: {period}', 
                    fontsize=12, fontweight='bold', color='white', pad=20)
        
        # Add legend
        legend_elements = [
            plt.scatter([], [], c='#084D42', s=100, label='Team 1'),
            plt.scatter([], [], c='#E51717', s=100, label='Team 2'),
            plt.scatter([], [], c='gray', s=130, edgecolors='white', linewidths=3, label='Player in Possession (thicker edge)'),
            plt.scatter([], [], c='white', s=50, edgecolors='black', label='Ball'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
        
        return ax
        
 
    
    def plot_episode(self, match_id, start_frame, end_frame, delay=0.3, plot_events=False):
        '''
            This function plots an episode (sequence of frames) from start_frame to end_frame.
        '''
        # Load data
        enriched_data = self.data_loader.create_enriched_tracking_data(match_id)
        
        # Collect the frames within episode
        available_frames = sorted(enriched_data['frame'].unique())
        frames_to_plot = [f for f in available_frames if start_frame <= f <= end_frame]

        if plot_events == True:
            events_data = self.data_loader.load_event_data(match_id)
            pp_data = events_data[events_data['event_type'] == 'player_possession']
            

        # Create pitch once
        fig, ax = self.create_pitch()
        
        # Animation loop - plot each frame
        for frame_num in frames_to_plot:
            if plot_events == True:
                pps_in_frame = pp_data[(frame_num >= pp_data['frame_start']) & (frame_num <= pp_data['frame_end'])]
                pp_event_row = pps_in_frame.iloc[0] if not pps_in_frame.empty else None
            self.plot_frame(ax, enriched_data, pp_event_row, frame_num)
            clear_output(wait=True)
            display(fig)
            
            if delay > 0:
                time.sleep(delay)
        
        return ax