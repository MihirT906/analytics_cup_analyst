import json
import dash
import copy
import hashlib
from dash import html, dcc, Input, Output, callback_context, no_update, State
from .DashPlotlyGameRenderer import DashPlotlyGameRenderer

class DashInteraction:
    def __init__(self, episode_file):
        self.episode_file = episode_file
        self.figures = None
        self.app = None
        self.annotation_store = {}

    def _display_annotation_store(self):
        annotation_text = ""
        for shape_hash, shape_dict in self.annotation_store.items():
            annotation_text += f"Shape Hash: {shape_hash}, Frame Start: {shape_dict.get('frame_start')}, Frame End: {shape_dict.get('frame_end')}, Shape: {shape_dict['shape']['type']}\n"
        return annotation_text

    def _get_shape_hash(self, shape):
        """Generate a unique hash for a shape based only on core geometric properties"""
        # Only use the properties that define the shape's position and type
        core_properties = {
            'type': shape.get('type'),
            'x0': shape.get('x0'),
            'y0': shape.get('y0'), 
            'x1': shape.get('x1'),
            'y1': shape.get('y1'),
            'xref': shape.get('xref', 'x'),
            'yref': shape.get('yref', 'y')
        }
        
        # Remove None values and round coordinates to avoid floating point precision issues
        core_properties = {k: round(v, 10) if isinstance(v, (int, float)) else v 
                        for k, v in core_properties.items() if v is not None}
        
        shape_str = json.dumps(core_properties, sort_keys=True)
        return hashlib.md5(shape_str.encode()).hexdigest()
    
    def _get_current_frame_number(self, n_intervals):
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
    
    
    def _create_annotation_area(self):
        clear_annotations_button = html.Button('Clear Annotations', id='clear-annotations', n_clicks=0, style={
                        'backgroundColor': '#ffc107',
                        'color': 'black',
                        'border': 'none',
                        'padding': '10px 20px',
                        'margin': '10px',
                        'borderRadius': '5px',
                        'cursor': 'pointer'
                    })
        
        annotations_display = html.Pre(id='annotations-display', style={
                    'backgroundColor': '#f8f9fa',
                    'padding': '15px',
                    'border': '1px solid #dee2e6',
                    'borderRadius': '5px',
                    'maxHeight': '300px',
                    'overflow': 'auto',
                    'whiteSpace': 'pre-wrap',
                    'fontSize': '12px',
                    'margin': '10px'
                }, children="No annotations yet. Start drawing on the graph!")
        
        return html.Div([clear_annotations_button, annotations_display], style={'textAlign': 'center'})
        
    
    def _create_layout(self):
        return html.Div([
                self._create_header(), 
                self._create_plot_controls(),
                self._create_plot_area(),
                self._create_annotation_area()
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
        """ Add callback to update figure based on animation interval """
        @self.app.callback(
            Output('current-frame-display', 'children'),
            [Input('animation-interval', 'n_intervals')]
        )
        def update_current_frame_display(n_intervals):
            current_frame = self._get_current_frame_number(n_intervals or 0)
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
            
            # Preserve any existing annotations (shapes) from the current figure
            if current_figure and 'layout' in current_figure and 'shapes' in current_figure['layout']:
                if 'layout' not in updated_figure:
                    updated_figure['layout'] = {}
                updated_figure['layout']['shapes'] = current_figure['layout']['shapes']
            
            return [updated_figure]

    def add_annotation_callback(self):
        @self.app.callback(
            [Output('annotations-display', 'children')],
            [Input('animated-figure', 'relayoutData'),
            Input('clear-annotations', 'n_clicks')],
            [State('animation-interval', 'n_intervals')],
            prevent_initial_call=True
        )
        def capture_annotations(relayout_data, clear_clicks, n_intervals):
            print("Annotation callback triggered")
            ctx = callback_context
            if not ctx.triggered:
                return ["No annotations yet. Start drawing on the graph!"]
            
            button_id = ctx.triggered_id
            current_frame = self._get_current_frame_number(n_intervals or 0)

            if button_id == 'clear-annotations':
                print("Clearing all annotations")
            
            if relayout_data and 'shapes' in relayout_data:
                current_shapes = relayout_data['shapes']
                current_shapes_hashes = [self._get_shape_hash(shape) for shape in current_shapes]
                stored_shapes_hashes = self.annotation_store.keys()
                # Store new shapes in annotation store
                for shape in current_shapes:
                    shape_hash = self._get_shape_hash(shape)
                    if shape_hash not in self.annotation_store:
                        self.annotation_store[shape_hash] = {'frame_start': current_frame, 'frame_end': None, 'shape': shape}
                # End shapes that are no longer present
                removed_shape_hashes = stored_shapes_hashes - current_shapes_hashes
                for shape_hash, shape_dict in list(self.annotation_store.items()):
                    if shape_hash in removed_shape_hashes:
                        shape_dict['frame_end'] = current_frame
                        self.annotation_store[shape_hash] = shape_dict

            print("Annotation Store: ", self._display_annotation_store())
            return ["Done"]

    
    def create_app(self):
        # Create App
        self.app = dash.Dash(__name__)
        self.app.title = "Interactive Episode Studio"
        self._get_episode()
        self.app.layout = self._create_layout()
        # Add callbacks
        self._add_control_animation_callback()
        self.add_animation_callback()
        self.add_annotation_callback()
        return self.app
