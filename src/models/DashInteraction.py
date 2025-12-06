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
        self.is_playing = False
        self.is_recording = False
        self.last_recorded_interval = None
        self.annotation_store = {}

    def _display_annotation_store(self):
        if not self.annotation_store:
            return html.Div("No annotations yet", style={
                'backgroundColor': '#ffa500', 
                'border': '2px solid rgba(255, 165, 0, 0.8)',
                'padding': '10px',
                'margin': '5px',
                'borderRadius': '5px'
            })
        
        annotation_boxes = []
        for shape_hash, shape_dict in self.annotation_store.items():
            box = html.Div([
                html.P(f"Frame Start: {shape_dict.get('frame_start')}", style={'margin': '2px 0'}),
                html.P(f"Frame End: {shape_dict.get('frame_end')}", style={'margin': '2px 0'}),
                html.P(f"Shape: {shape_dict['shape']['type']}", style={'margin': '2px 0'})
            ], style={
                'backgroundColor': '#ffa500',
                'border': '2px solid rgba(255, 165, 0, 0.8)', 
                'padding': '10px',
                'margin': '5px',
                'borderRadius': '5px'
            })
            annotation_boxes.append(box)
        
        return html.Div(annotation_boxes)

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

        self.episode_data = data.get('episode_data', {})
        self.annotation_store = data.get('annotation_data', {})
    
    def _save_episode_data(self):
        """ Save episode data and annotations back to the JSON file """
        if not self.episode_file:
            raise ValueError("Episode file path is not provided.")
        
        data_to_save = {
            'episode_data': self.episode_data,
            'annotation_data': self.annotation_store
        }
        
        with open(self.episode_file, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        
        print(f"Episode data and annotations saved to {self.episode_file}")
    
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
        return html.Div(id='header', children=[
            html.H1("Episode Craft Studio", style={'textAlign': 'left', 'padding-left': '20px'}),
            html.Div(id='match-info', children=[
                html.P([html.B("Match ID: "), f"{self.episode_data['match_id']}"], style={'textAlign': 'left', 'padding-left': '20px', 'margin': '5px 0'}),
                html.P([html.B("Frame Range: "), f"{self.episode_data['frame_start']} - {self.episode_data['frame_end']}"], style={'textAlign': 'left', 'padding-left': '20px', 'margin': '5px 0'}),
            ], style={'backgroundColor': "#f0f0f0", 'margin-bottom': '20px', 'border': '1px solid black'})
        ])
    
    def _create_plot_controls(self):
        """ Create plot control buttons """
        record_button = html.Button('REC', id='record-button', n_clicks=0, style={
                    'backgroundColor': "white",
                    'color': 'black',
                    'border': '1px solid black',
                    'borderBottom': '5px solid #ff0000',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        play_button = html.Button('Play', id='play-button', n_clicks=0, style={
                    'backgroundColor': 'white',
                    'color': 'black',
                    'border': '1px solid black',
                    'borderBottom': '5px solid #28a745',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        pause_button = html.Button('Pause', id='pause-button', n_clicks=0, style={
                    'backgroundColor': "white",
                    'color': 'black',
                    'border': '1px solid black',
                    'borderBottom': '5px solid #e9cb09',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        reset_button = html.Button('Reset', id='reset-button', n_clicks=0, style={
                    'backgroundColor': 'white',
                    'color': 'black',
                    'border': '1px solid black',
                    'borderBottom': '5px solid #6c757d',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        save_button = html.Button('Save', id='save-episode-button', n_clicks=0, style={
                    'backgroundColor': 'white',
                    'color': 'black',
                    'border': '1px solid black',
                    'borderBottom': '5px solid #007bff',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
        
        return html.Div(id='plot-controls', children=[record_button, play_button, pause_button, reset_button, save_button], style={'textAlign': 'center'})

    def _create_episode_slider(self):
        """ Create episode frame slider """
        red_percentage = 10
        frame_slider = html.Div([
            dcc.Slider(
                id='frame-slider',
                min=self.episode_data['frame_start'],
                max=self.episode_data['frame_end'],
                value=self.episode_data['frame_start'],
                marks={str(i): {'label': str(i), 'style': {'color': 'black'}} for i in range(self.episode_data['frame_start'], self.episode_data['frame_end'] + 1, 10)},
                step=1,
                disabled=True,
                tooltip={
                    "placement": "bottom",
                    "always_visible": True,
                    "style": {"color": "white", "fontSize": "14px"},
                    "template": "Frame: {value}"
                }
            )
        ], style={
        'width': '70%',
        'margin': '10px auto',
        'padding': '0 20px',
        'textAlign': 'center'
    })
        return frame_slider
    
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
                                    'drawcircle',
                                    'drawrect',
                                    'eraseshape'
                                ],
                                'modeBarButtonsToRemove': [
                                'lasso2d',
                                'select2d', 
                                'zoom2d',
                                'pan2d',
                                'zoomIn2d',
                                'zoomOut2d',
                                'autoScale2d',
                                'resetScale2d'
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
        return html.Div(id='plot-area', children=[current_frame_display, graph_display, interval])


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

        return html.Div(id='annotation-area', children=[clear_annotations_button, annotations_display], style={'textAlign': 'center'})


    def _create_layout(self):
        return html.Div(id='main-layout', children=[
                self._create_header(), 
                html.Div(children=[
                    html.Div(children=[
                        self._create_plot_controls(),
                        self._create_plot_area(),
                        self._create_episode_slider(),
                    ], style={'width': '70%'}),
                    html.Div(children=[
                        self._create_annotation_area()
                    ], style={'width': '30%'})
                ], style={'display': 'flex', 'gap': '10px'})
            ])
    
    def _add_control_animation_callback(self):
        """ Add callback to control animation playback """
        @self.app.callback(
            [Output('record-button', 'disabled'),
             Output('reset-button', 'disabled'),
             Output('frame-slider', 'value')],
            [Input('play-button', 'n_clicks'),
             Input('pause-button', 'n_clicks'),
             Input('reset-button', 'n_clicks'),
             Input('animation-interval', 'n_intervals'),
             Input('animation-interval', 'max_intervals')],
            prevent_initial_call=True
        )
        def toggle_pause_play(play_clicks, pause_clicks, reset_clicks, n_intervals, max_intervals):

            if n_intervals >= max_intervals:
                self.is_playing = False # If end of playback, is_playing state should be false
                
            ctx = callback_context
            if not ctx.triggered:
                return True, True, no_update
            
            button_id = ctx.triggered_id
            
            if button_id == 'play-button':
                self.is_playing = True
                
            elif button_id == 'pause-button':
                self.is_playing = False
            
            elif button_id == 'reset-button':
                self.is_playing = False
                return False, False, self.episode_data['frame_start']  # Reset frame slider to start frame
                
            if self.is_playing:
                return True, True, self._get_current_frame_number(n_intervals) # Disable record and reset while playing
            else:
                return False, False, no_update # Enable record and reset when paused or stopped

        @self.app.callback(
            [Output('plot-area', 'style'),
            Output('record-button', 'children'),
            Output('frame-slider', 'marks')],
            [Input('record-button', 'n_clicks'),
            Input('animation-interval', 'n_intervals')],
            prevent_initial_call=True
        )
        def toggle_recording(n_clicks, n_intervals):
            if n_clicks % 2 == 1:
                self.is_recording = True
                self.last_recorded_interval = n_intervals
                return {'border': '5px solid red'}, 'STOP', no_update
            else:
                self.is_recording = False
                if self.last_recorded_interval is not None:
                    frame_slider_marks = {str(i): {'label': str(i), 'style': {'color': 'black'}} for i in range(self._get_current_frame_number(self.last_recorded_interval), self.episode_data['frame_end'] + 1, 1) if i%10 == 0}
                    new_frame_slider_marks = {**frame_slider_marks, str(self._get_current_frame_number(self.last_recorded_interval)): {'label': str(self._get_current_frame_number(self.last_recorded_interval)), 'style': {'color': 'red'}}}
                    red_marks = {str(i): {'label': '*', 'style': {'backgroundColor': 'red', 'color': 'red'}} for i in range(self.episode_data['frame_start'], self._get_current_frame_number(self.last_recorded_interval)-1, 1)}
                    new_frame_slider_marks = {**red_marks, **new_frame_slider_marks}
                    return {'border': 'none'}, 'REC', new_frame_slider_marks
                else:
                    return {'border': 'none'}, 'REC', no_update

        @self.app.callback(    
            [Output('animation-interval', 'disabled'),
             Output('animation-interval', 'n_intervals'),
             Output('animation-interval', 'max_intervals')],
            [Input('play-button', 'n_clicks'),
             Input('pause-button', 'n_clicks'),
             Input('reset-button', 'n_clicks'),
             Input('record-button', 'n_clicks')],
            prevent_initial_call=True
        )
        def control_animation(play_clicks, pause_clicks, reset_clicks, record_clicks):
            len_figures = len(self.figures)
            ctx = callback_context
            if not ctx.triggered:
                return True, 0, len_figures

           #button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            button_id = ctx.triggered_id
            
            if button_id == 'play-button':
                if self.is_recording or self.last_recorded_interval is None:
                    return False, no_update, len_figures  # Enable interval, keep current n_intervals
                else:
                    return False, 0, self.last_recorded_interval
            elif button_id == 'pause-button':
                if self.is_recording or self.last_recorded_interval is None:
                    return True, no_update, len_figures  # Disable interval, keep current n_intervals
                else:
                    return True, no_update, self.last_recorded_interval
            elif button_id == 'reset-button':
                self.last_recorded_interval = None
            
            elif button_id == 'record-button':
                if self.last_recorded_interval is None:
                    return no_update, 0, no_update
            
            return True, 0, 0

    def _add_animation_callback(self):
        """ Add callback to update figure based on animation interval """
        @self.app.callback(
            Output('current-frame-display', 'children'),
            [Input('animation-interval', 'n_intervals')]
        )
        def update_current_frame_display(n_intervals):
            current_frame = self._get_current_frame_number(n_intervals or 0)
            return f"Current Frame: {current_frame} | {n_intervals} | {self.last_recorded_interval} | self.is_recording={self.is_recording} | self.is_playing={self.is_playing}"

        @self.app.callback(
            [Output('animated-figure', 'figure')],
            [Input('animation-interval', 'n_intervals'), 
             Input('clear-annotations', 'n_clicks')],
            [State('animated-figure', 'figure'),
             State('record-button', 'n_clicks')],
        )
        def update_figure(n_intervals, clear_clicks, current_figure, record_clicks):
            len_figures = len(self.figures)
            if len_figures == 0:
                return [{}]
            # Show figures sequentially, stop at the last one
            if self.is_recording:
                #print(f"Recording mode: ", n_intervals)
                if n_intervals >= len_figures:
                    figure_index = len_figures - 1  # Stay on last figure
                else:
                    figure_index = n_intervals
            else:
                if self.last_recorded_interval is None:
                    if n_intervals >= len_figures:
                        figure_index = len_figures - 1  # Stay on last figure
                    else:
                        figure_index = n_intervals
                else:
                    if n_intervals >= self.last_recorded_interval:
                        figure_index = self.last_recorded_interval - 1  # Stay on last recorded frame
                    else:
                        figure_index = n_intervals

            figure_dict = self.figures[figure_index].to_dict() if hasattr(self.figures[figure_index], 'to_dict') else dict(self.figures[figure_index])
            updated_figure = copy.deepcopy(figure_dict)
            
            # Preserve any existing annotations (shapes) from the current figure or from the annotation store
            if self.annotation_store:
                active_shapes = []
                for shape_hash, shape_dict in self.annotation_store.items():
                    frame_start = shape_dict.get('frame_start')
                    frame_end = shape_dict.get('frame_end')
                    current_frame = self._get_current_frame_number(n_intervals or 0)
                    if frame_start < current_frame and (frame_end is None or frame_end > current_frame):  # Ongoing shape
                        active_shapes.append(shape_dict['shape'])
                if active_shapes:
                    if 'layout' not in updated_figure:
                        updated_figure['layout'] = {}
                    updated_figure['layout']['shapes'] = active_shapes
            # else:
            #     if current_figure and 'layout' in current_figure and 'shapes' in current_figure['layout']:
            #         if 'layout' not in updated_figure:
            #             updated_figure['layout'] = {}
            #         updated_figure['layout']['shapes'] = current_figure['layout']['shapes']
            
            ctx = callback_context
            button_id = ctx.triggered_id
            if button_id == 'clear-annotations':
                print("Clearing annotations from figure via animation callback")
                self.annotation_store = {}
                if current_figure and 'layout' in current_figure and 'shapes' in current_figure['layout']:
                    updated_figure['layout']['shapes'] = []
                    
            return [updated_figure]

    def _add_annotation_callback(self):
        @self.app.callback(
            [Output('annotations-display', 'children')],
            [Input('animated-figure', 'relayoutData'),
            Input('clear-annotations', 'n_clicks')],
            [State('animation-interval', 'n_intervals')],
            prevent_initial_call=True
        )
        def capture_annotations(relayout_data, clear_clicks, n_intervals):
            if self.is_recording:
                ctx = callback_context
                if not ctx.triggered:
                    return ["No annotations yet. Start drawing on the graph!"]
                
                button_id = ctx.triggered_id
                current_frame = self._get_current_frame_number(n_intervals or 0)
                
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
                        if (shape_hash in removed_shape_hashes) and (shape_dict['frame_end'] is None):
                            shape_dict['frame_end'] = current_frame
                            self.annotation_store[shape_hash] = shape_dict
                        if shape_dict['frame_end'] is not None and shape_dict['frame_end'] <= shape_dict['frame_start']:
                            del self.annotation_store[shape_hash]

            #     return [self._display_annotation_store()]
            # else:
            #     return ["Recording is OFF. Click REC to start recording annotations."]
            if self.annotation_store:
                return [self._display_annotation_store()]
            else:
                return ["No annotations yet. Start recording and drawing on the graph!"]

        @self.app.callback(
            Output('save-episode-button', 'n_clicks'),
            Input('save-episode-button', 'n_clicks')
        )
        def save_episode(n_clicks):
            if n_clicks > 0:
                # Save the episode data
                self._save_episode_data()
                
            return no_update

    def create_app(self):
        # Create App
        self.app = dash.Dash(__name__)
        self.app.title = "Episode Craft Studio"
        self._get_episode()
        self.app.layout = self._create_layout()
        # Add callbacks
        self._add_control_animation_callback()
        self._add_animation_callback()
        self._add_annotation_callback()
        return self.app
