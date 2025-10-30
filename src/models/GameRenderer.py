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

    def plot_frame(self, ax, enriched_data, events_data, frame_num):
        '''
            This function plots a single frame of the game on the provided axis.
        '''
        # Extract player in possession if any
        pp_data = events_data[events_data['event_type'] == 'player_possession']
        pps_in_frame = pp_data[(frame_num >= pp_data['frame_start']) & (frame_num <= pp_data['frame_end'])]
        pp_event_row = pps_in_frame.iloc[0] if not pps_in_frame.empty else None
        
        
        #if pp_event_row is not None:
        # Extract passing options
        po_data = events_data[events_data['event_type'] == 'passing_option']
        po_event_rows = po_data[po_data['associated_player_possession_event_id'] == pp_event_row['event_id']] if pp_event_row is not None else pd.DataFrame()
        
        # Extract on ball engagements
        obe_data = events_data[events_data['event_type'] == 'on_ball_engagement']
        obe_event_rows = obe_data[obe_data['associated_player_possession_event_id'] == pp_event_row['event_id']] if pp_event_row is not None else pd.DataFrame()

        # Extract off ball runs
        obr_data = events_data[events_data['event_type'] == 'off_ball_run']
        obr_event_rows = obr_data[obr_data['associated_player_possession_event_id'] == pp_event_row['event_id']] if pp_event_row is not None else pd.DataFrame()

        # Clear everything from the axes
        ax.clear()
        
        # Recreate the pitch for this frame
        pitch = Pitch(
            pitch_type="skillcorner",
            line_alpha=0.75,
            pitch_length=105,
            pitch_width=68,
            pitch_color="#001400",
            line_color="white",
            linewidth=1.5,
        )
        pitch.draw(ax=ax)
        
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
        
        # Get player IDs for passing options and on-ball engagements
        passing_option_player_ids = set(po_event_rows['player_id'].tolist()) if not po_event_rows.empty else set()
        on_ball_engagement_player_ids = set(obe_event_rows['player_id'].tolist()) if not obe_event_rows.empty else set()
            
        for i, team in enumerate(teams):
            team_data = frame_data[frame_data['team_name'] == team]
            
            # Regular players (excluding player in possession, goalkeepers, passing options, and on-ball engagements)
            regular_players = team_data[
                (team_data['is_gk'] == False) & 
                (team_data['player_id'] != player_in_possession_id) &
                (~team_data['player_id'].isin(passing_option_player_ids)) &
                (~team_data['player_id'].isin(on_ball_engagement_player_ids))
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
            
            # Players with passing options (yellow border)
            passing_option_players = team_data[
                (team_data['is_gk'] == False) & 
                (team_data['player_id'].isin(passing_option_player_ids)) &
                (team_data['player_id'] != player_in_possession_id)
            ]
            if not passing_option_players.empty:
                ax.scatter(
                    passing_option_players['x'],
                    passing_option_players['y'],
                    c=colors[i % len(colors)],
                    alpha=0.95,
                    s=size,
                    edgecolors='yellow',
                    linewidths=2.5,
                    zorder=11
                )
            
            # Players with on-ball engagements (black border and larger size)
            on_ball_engagement_players = team_data[
                (team_data['is_gk'] == False) & 
                (team_data['player_id'].isin(on_ball_engagement_player_ids)) &
                (team_data['player_id'] != player_in_possession_id)
            ]
            if not on_ball_engagement_players.empty:
                ax.scatter(
                    on_ball_engagement_players['x'],
                    on_ball_engagement_players['y'],
                    c=colors[i % len(colors)],
                    alpha=0.95,
                    s=size * 1.3,
                    edgecolors='black',
                    linewidths=2.5,
                    zorder=11
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
        
        # Plot off-ball runs
        if not obr_event_rows.empty:
            for _, run_event in obr_event_rows.iterrows():
                # Get the current position of the runner from tracking data
                runner_current = frame_data[frame_data['player_id'] == run_event['player_id']]
                if not runner_current.empty:
                    # Plot the run trajectory line from start to current position
                    ax.plot(
                        [run_event['x_start'], run_event['y_start']],
                        [runner_current['x'].iloc[0], runner_current['y'].iloc[0]],
                        color='#E5BA21',
                        linewidth=2,
                        linestyle='--',
                        zorder=8
                    )
                    
                    # Plot the start position of the run
                    ax.scatter(
                        run_event['x_start'],
                        run_event['y_start'],
                        c='#E5BA21',
                        alpha=0.55,
                        s=size / 2,
                        edgecolors='#E5BA21',
                        linewidths=2.5,
                        zorder=9
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
            plt.scatter([], [], c='gray', s=130, edgecolors='white', linewidths=3, label='Player in Possession'),
            plt.scatter([], [], c='gray', s=100, edgecolors='yellow', linewidths=2.5, label='Passing Option'),
            plt.scatter([], [], c='gray', s=130, edgecolors='black', linewidths=2.5, label='On-Ball Engagement'),
            plt.scatter([], [], c='#E5BA21', s=50, edgecolors='#E5BA21', linewidths=2.5, label='Off-Ball Run Start'),
            plt.Line2D([0], [0], color='#E5BA21', linewidth=2, linestyle='--', label='Off-Ball Run Path'),
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
        events_data = self.data_loader.load_event_data(match_id)
        
        # Collect the frames within episode
        available_frames = sorted(enriched_data['frame'].unique())
        frames_to_plot = [f for f in available_frames if start_frame <= f <= end_frame]
            

        # Create pitch once
        fig, ax = self.create_pitch()
        
        # Animation loop - plot each frame
        for frame_num in frames_to_plot:
            self.plot_frame(ax, enriched_data, events_data, frame_num)
            clear_output(wait=True)
            display(fig)
            
            if delay > 0:
                time.sleep(delay)