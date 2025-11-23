import json
import dash
import copy
from dash import html, dcc, Input, Output, callback_context, no_update, State
from .DashPlotlyGameRenderer import DashPlotlyGameRenderer

class DashInteraction:
    def __init__(self, episode_file):
        self.episode_file = episode_file
        self.figures = None
        self.app = None

    def get_current_frame_number(self, n_intervals):
        """Get the current frame number based on animation intervals"""
        if len(self.figures) == 0:
            return self.episode_data['frame_start']  # Return START_FRAME instead of 0 when no figures
        if n_intervals >= len(self.figures):
            # When at the end, we're at the last figure which represents END_FRAME
            return self.episode_data['frame_end']
        else:
            # n_intervals starts from 0, first figure is START_FRAME
            return n_intervals + self.episode_data['frame_start']

    def _get_episode_data(self):
        """ Load episode data from the provided JSON file """
        if not self.episode_file:
            raise ValueError("Episode file path is not provided.")
        
        with open(self.episode_file, 'r') as f:
            data = json.load(f)

        self.episode_data = data['episode_data']
    
    def _get_episode(self):
        """ Generate figures for the episode using DashPlotlyGameRenderer """
        try:
            self._get_episode_data()
            game_renderer = DashPlotlyGameRenderer(config_file='src/config/simple_game_renderer_config.json')
            figures = game_renderer.plot_episode(self.episode_data['match_id'], self.episode_data['frame_start'], self.episode_data['frame_end'], delay=0)
            print(f"Generated {len(figures)} figures for frames {self.episode_data['frame_start']} to {self.episode_data['frame_end']}")
            self.figures = figures
            
        except Exception as e:
            print(f"Error generating figures: {e}")
            self.figures = []
    
    def _create_header(self):
        """ Create header section of the Dash app """
        return html.Div([
            html.H1("Interactive Episode Studio", style={'textAlign': 'center'}),
            html.H2(f"Match ID: {self.episode_data['match_id']}", style={'textAlign': 'center'}),
            html.H2(f"Frame Range: {self.episode_data['frame_start']} - {self.episode_data['frame_end']}", style={'textAlign': 'center'}),
        ])
    
    def _create_plot_controls(self):
        """ Create plot control buttons """
        play_button = html.Button('Play', id='play-button', n_clicks=0, style={
                    'backgroundColor': '#28a745',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        pause_button = html.Button('Pause', id='pause-button', n_clicks=0, style={
                    'backgroundColor': '#dc3545',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        reset_button = html.Button('Reset', id='reset-button', n_clicks=0, style={
                    'backgroundColor': '#6c757d',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        return html.Div([play_button, pause_button, reset_button], style={'textAlign': 'center'})
    
    def _create_plot_area(self):
        """ Create plot area with graph and interval component """
        current_frame_display = html.Div(id='current-frame-display', style={'textAlign': 'center', 'margin': '10px', 'fontSize': '18px', 'fontWeight': 'bold'})
        graph_display = html.Div(
                children=[
                    html.Div(
                        dcc.Graph(
                            id='animated-figure',
                            style={"width": "100%", "height": "100%"},
                            config={
                                'modeBarButtonsToAdd': [
                                    'drawline',
                                    'drawopenpath',
                                    'drawclosedpath',
                                    'drawcircle',
                                    'drawrect',
                                    'eraseshape'
                                ],
                                'displayModeBar': True
                            }
                        ),
                        style={
                            "flex": "0 0 auto",   # do not stretch
                        }
                    )
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",  # horizontal center
                    "alignItems": "center",      # vertical center
                }
            )
        interval = dcc.Interval(
            id='animation-interval',
            interval=100,  # 0.1 seconds = 100 milliseconds
            n_intervals=0,
            max_intervals=len(self.figures),  # Play once through all figures
            disabled=True  # Start paused
        )
        return html.Div([current_frame_display, graph_display, interval])
    
    def _create_layout(self):
        return html.Div([
                self._create_header(), 
                self._create_plot_controls(),
                self._create_plot_area()
            ])
    
    def _add_control_animation_callback(self):
        """ Add callback to control animation playback """
        @self.app.callback(    
            [Output('animation-interval', 'disabled'),
             Output('animation-interval', 'n_intervals')],
            [Input('play-button', 'n_clicks'),
             Input('pause-button', 'n_clicks'),
             Input('reset-button', 'n_clicks')],
            prevent_initial_call=True
        )
        def control_animation(play_clicks, pause_clicks, reset_clicks):
            ctx = callback_context
            if not ctx.triggered:
                return True, 0
            
           #button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            button_id = ctx.triggered_id
            
            if button_id == 'play-button':
                return False, no_update  # Enable interval, keep current n_intervals
            elif button_id == 'pause-button':
                return True, no_update   # Disable interval, keep current n_intervals
            elif button_id == 'reset-button':
                return True, 0                # Disable interval and reset to beginning
            
            return True, 0
    
    def add_animation_callback(self):
        
        @self.app.callback(
            Output('current-frame-display', 'children'),
            [Input('animation-interval', 'n_intervals')]
        )
        def update_current_frame_display(n_intervals):
            current_frame = self.get_current_frame_number(n_intervals or 0)
            return f"Current Frame: {current_frame}"
        
        @self.app.callback(
            [Output('animated-figure', 'figure')],
            [Input('animation-interval', 'n_intervals')],
            [State('animated-figure', 'figure')]
        )
        def update_figure(n_intervals, current_figure):
            len_figures = len(self.figures)
            if len_figures == 0:
                return [{}]
            # Show figures sequentially, stop at the last one
            if n_intervals >= len_figures:
                figure_index = len_figures - 1  # Stay on last figure
            else:
                figure_index = n_intervals
 
            figure_dict = self.figures[figure_index].to_dict() if hasattr(self.figures[figure_index], 'to_dict') else dict(self.figures[figure_index])
            updated_figure = copy.deepcopy(figure_dict)
            
            return [updated_figure]

    def create_app(self):
        # Create App
        self.app = dash.Dash(__name__)
        self.app.title = "Interactive Episode Studio"
        self._get_episode()
        self.app.layout = self._create_layout()
        # Add callbacks
        self._add_control_animation_callback()
        self.add_animation_callback()
        return self.app
