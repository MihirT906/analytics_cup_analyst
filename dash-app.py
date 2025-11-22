import dash
from dash import html, dcc, Input, Output, callback_context, no_update, State
from src.models.DashPlotlyGameRenderer import DashPlotlyGameRenderer
import json
import copy
import hashlib
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Interactive Episode Studio"

# Hardcoded match ID and frame range
MATCH_ID = "1886347"
START_FRAME = 10
END_FRAME = 100  # Reduced range for faster loading

# Global annotation tracking store
annotation_store = {}
annotation_counter = 0

def get_shape_hash(shape):
    """Generate a unique hash for a shape based on its properties"""
    shape_str = json.dumps(shape, sort_keys=True)
    return hashlib.md5(shape_str.encode()).hexdigest()

def get_current_frame_number(n_intervals):
    """Get the current frame number based on animation intervals"""
    if len(figures) == 0:
        return START_FRAME  # Return START_FRAME instead of 0 when no figures
    if n_intervals >= len(figures):
        # When at the end, we're at the last figure which represents END_FRAME
        return END_FRAME
    else:
        # n_intervals starts from 0, first figure is START_FRAME
        return n_intervals + START_FRAME

def get_figures():
    """Load data using DashPlotlyGameRenderer and return the generated figures"""
    try:
        game_renderer = DashPlotlyGameRenderer(config_file='analytics_cup_analyst/src/config/simple_game_renderer_config.json')
        figures = game_renderer.plot_episode(MATCH_ID, START_FRAME, END_FRAME, delay=0)
        print(f"Generated {len(figures)} figures for frames {START_FRAME} to {END_FRAME}")
        return figures
    except Exception as e:
        print(f"Error generating figures: {e}")
        return []

# Get the figures
figures = get_figures()

# Create layout components
def create_layout():
    if len(figures) > 0:
        return html.Div([
            html.H1("Interactive Episode Studio", style={'textAlign': 'center'}),
            html.H2(f"Match ID: {MATCH_ID}", style={'textAlign': 'center'}),
            html.H2(f"Frame Range: {START_FRAME} - {END_FRAME}", style={'textAlign': 'center'}),
            html.Div([
                html.Button('Play', id='play-button', n_clicks=0, style={
                    'backgroundColor': '#28a745',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                }),
                html.Button('Pause', id='pause-button', n_clicks=0, style={
                    'backgroundColor': '#dc3545',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                }),
                html.Button('Reset', id='reset-button', n_clicks=0, style={
                    'backgroundColor': '#6c757d',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px 5px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                })
            ], style={'textAlign': 'center'}),
            html.Div(id='current-frame-display', style={'textAlign': 'center', 'margin': '10px', 'fontSize': '18px', 'fontWeight': 'bold'}),
            html.Div(
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
            ),
            dcc.Interval(
                id='animation-interval',
                interval=100,  # 0.1 seconds = 100 milliseconds
                n_intervals=0,
                max_intervals=len(figures),  # Play once through all figures
                disabled=True  # Start paused
            ),
            html.Div([
                html.H3("Drawing Annotations with Frame Tracking", style={'textAlign': 'center', 'marginTop': '30px'}),
                html.P([
                    "Use the drawing tools in the graph's toolbar to annotate the visualization. ",
                    "Available tools: line, path, circle, rectangle. ",
                    "Annotations are tracked with frame start/end times and displayed below. ",
                    "Frame ranges show when annotations were created and removed/cleared."
                ], style={'textAlign': 'center', 'margin': '10px', 'color': '#666'}),
                html.Div([
                    html.Button('Clear Annotations', id='clear-annotations', n_clicks=0, style={
                        'backgroundColor': '#ffc107',
                        'color': 'black',
                        'border': 'none',
                        'padding': '10px 20px',
                        'margin': '10px',
                        'borderRadius': '5px',
                        'cursor': 'pointer'
                    }),
                    html.Button('Export Annotation Log', id='export-annotations', n_clicks=0, style={
                        'backgroundColor': '#17a2b8',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'margin': '10px',
                        'borderRadius': '5px',
                        'cursor': 'pointer'
                    })
                ], style={'textAlign': 'center'}),
                html.Pre(id='annotations-display', style={
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
            ], style={'textAlign': 'center'}),
            html.P("This app animates through all figures generated by DashPlotlyGameRenderer.")
        ], style={
            'maxWidth': '1200px',
            'margin': '0 auto',
            'fontFamily': 'Arial, sans-serif'
        })
    else:
        return html.Div([
            html.H1("DashPlotlyGameRenderer Animation", style={'textAlign': 'center'}),
            html.H2(f"Match ID: {MATCH_ID}", style={'textAlign': 'center'}),
            html.H2(f"Frame Range: {START_FRAME} - {END_FRAME}", style={'textAlign': 'center'}),
            html.H2("Error: No figures generated", style={'textAlign': 'center'}),
            html.P("Unable to generate figures using DashPlotlyGameRenderer.", style={'textAlign': 'center'})
        ], style={
            'maxWidth': '1200px',
            'margin': '0 auto',
            'padding': '20px',
            'fontFamily': 'Arial, sans-serif'
        })

# Set the layout
app.layout = create_layout()

# Callback to control play/pause/reset
@app.callback(
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
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'play-button':
        return False, no_update  # Enable interval, keep current n_intervals
    elif button_id == 'pause-button':
        return True, no_update   # Disable interval, keep current n_intervals
    elif button_id == 'reset-button':
        return True, 0                # Disable interval and reset to beginning
    
    return True, 0

# Callback to update current frame display
@app.callback(
    Output('current-frame-display', 'children'),
    [Input('animation-interval', 'n_intervals')]
)
def update_frame_display(n_intervals):
    current_frame = get_current_frame_number(n_intervals or 0)
    return f"Current Frame: {current_frame}"

# Callback to update the figure
@app.callback(
    [Output('animated-figure', 'figure')],
    [Input('animation-interval', 'n_intervals')],
    [State('animated-figure', 'figure')]
)
def update_figure(n_intervals, current_figure):
    if len(figures) == 0:
        return [{}]
    
    # Show figures sequentially, stop at the last one
    if n_intervals >= len(figures):
        figure_index = len(figures) - 1  # Stay on last figure
    else:
        figure_index = n_intervals
    
    # Convert Figure to dict and then copy
    figure_dict = figures[figure_index].to_dict() if hasattr(figures[figure_index], 'to_dict') else dict(figures[figure_index])
    updated_figure = copy.deepcopy(figure_dict)
    
    # Preserve any existing annotations (shapes) from the current figure
    if current_figure and 'layout' in current_figure and 'shapes' in current_figure['layout']:
        if 'layout' not in updated_figure:
            updated_figure['layout'] = {}
        updated_figure['layout']['shapes'] = current_figure['layout']['shapes']
    
    return [updated_figure]

# Callback to capture and display annotations
@app.callback(
    Output('annotations-display', 'children'),
    [Input('animated-figure', 'relayoutData'),
     Input('clear-annotations', 'n_clicks')],
    [State('animation-interval', 'n_intervals')],
    prevent_initial_call=True
)
def display_annotations(relayout_data, clear_clicks, n_intervals):
    global annotation_store, annotation_counter
    
    ctx = callback_context
    if not ctx.triggered:
        return format_annotation_display()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_frame = get_current_frame_number(n_intervals or 0)
    
    # Debug print
    print(f"Debug: n_intervals={n_intervals}, current_frame={current_frame}, START_FRAME={START_FRAME}")
    
    # Handle clear button
    if trigger_id == 'clear-annotations':
        # Mark all active annotations as ended
        for ann_id, annotation in annotation_store.items():
            if annotation['frame_end'] is None:
                annotation['frame_end'] = current_frame
                annotation['status'] = 'cleared'
        
        print(f"\n=== ANNOTATIONS CLEARED AT FRAME {current_frame} ===")
        return format_annotation_display()
    
    # Handle relayout data from drawing
    if relayout_data and 'shapes' in relayout_data:
        current_shapes = relayout_data['shapes']
        current_shape_hashes = {get_shape_hash(shape) for shape in current_shapes}
        
        # Find currently active annotations
        active_annotations = {ann_id for ann_id, annotation in annotation_store.items() 
                            if annotation['frame_end'] is None}
        active_shape_hashes = {annotation_store[ann_id]['shape_hash'] 
                             for ann_id in active_annotations}
        
        # Detect new annotations (shapes that are in current but not in active)
        new_shape_hashes = current_shape_hashes - active_shape_hashes
        for shape in current_shapes:
            shape_hash = get_shape_hash(shape)
            if shape_hash in new_shape_hashes:
                annotation_counter += 1
                annotation_store[annotation_counter] = {
                    'id': annotation_counter,
                    'shape': shape.copy(),
                    'shape_hash': shape_hash,
                    'frame_start': current_frame,
                    'frame_end': None,
                    'status': 'active',
                    'created_at': datetime.now().isoformat()
                }
                print(f"\n=== NEW ANNOTATION CREATED AT FRAME {current_frame} ===")
                print(f"Annotation ID: {annotation_counter}")
                print(f"Type: {shape.get('type', 'unknown')}")
        
        # Detect removed annotations (active shapes that are no longer in current)
        removed_shape_hashes = active_shape_hashes - current_shape_hashes
        for ann_id in list(active_annotations):
            if annotation_store[ann_id]['shape_hash'] in removed_shape_hashes:
                annotation_store[ann_id]['frame_end'] = current_frame
                annotation_store[ann_id]['status'] = 'removed'
                print(f"\n=== ANNOTATION REMOVED AT FRAME {current_frame} ===")
                print(f"Annotation ID: {ann_id}")
                print(f"Duration: {current_frame - annotation_store[ann_id]['frame_start']} frames")
    
    return format_annotation_display()

def format_annotation_display():
    """Format the annotation display text"""
    if not annotation_store:
        return "No annotations yet. Start drawing on the graph!"
    
    # Count active and total annotations
    active_count = sum(1 for ann in annotation_store.values() if ann['frame_end'] is None)
    total_count = len(annotation_store)
    
    annotations_text = f"Active Annotations: {active_count} | Total Created: {total_count}\n\n"
    
    # Sort annotations by creation order
    sorted_annotations = sorted(annotation_store.items(), key=lambda x: x[1]['frame_start'])
    
    for ann_id, annotation in sorted_annotations:
        annotations_text += f"Annotation {ann_id} ({annotation['status']}):\n"
        annotations_text += f"  Type: {annotation['shape'].get('type', 'unknown')}\n"
        annotations_text += f"  Frame Start: {annotation['frame_start']}\n"
        
        if annotation['frame_end'] is not None:
            duration = annotation['frame_end'] - annotation['frame_start']
            annotations_text += f"  Frame End: {annotation['frame_end']}\n"
            annotations_text += f"  Duration: {duration} frames\n"
        else:
            annotations_text += f"  Frame End: Still active\n"
        
        shape = annotation['shape']
        if shape.get('type') == 'rect':
            annotations_text += f"  Position: ({shape.get('x0', 0):.2f}, {shape.get('y0', 0):.2f}) to ({shape.get('x1', 0):.2f}, {shape.get('y1', 0):.2f})\n"
        elif shape.get('type') == 'circle':
            annotations_text += f"  Position: ({shape.get('x0', 0):.2f}, {shape.get('y0', 0):.2f}) to ({shape.get('x1', 0):.2f}, {shape.get('y1', 0):.2f})\n"
        elif shape.get('type') == 'line':
            annotations_text += f"  From: ({shape.get('x0', 0):.2f}, {shape.get('y0', 0):.2f}) to ({shape.get('x1', 0):.2f}, {shape.get('y1', 0):.2f})\n"
        elif shape.get('type') == 'path':
            annotations_text += f"  Path: {shape.get('path', 'N/A')}\n"
        
        annotations_text += f"  Line color: {shape.get('line', {}).get('color', 'N/A')}\n"
        annotations_text += f"  Line width: {shape.get('line', {}).get('width', 'N/A')}\n"
        annotations_text += "\n"
    
    return annotations_text

# Callback to clear annotations from the graph
@app.callback(
    Output('animated-figure', 'figure', allow_duplicate=True),
    [Input('clear-annotations', 'n_clicks')],
    [State('animated-figure', 'figure'),
     State('animation-interval', 'n_intervals')],
    prevent_initial_call=True
)
def clear_graph_annotations(clear_clicks, current_figure, n_intervals):
    global annotation_store
    
    if clear_clicks and current_figure:
        current_frame = get_current_frame_number(n_intervals or 0)
        
        # Mark all active annotations as cleared
        for ann_id, annotation in annotation_store.items():
            if annotation['frame_end'] is None:
                annotation['frame_end'] = current_frame
                annotation['status'] = 'cleared'
        
        # Remove all shapes from the figure
        updated_figure = copy.deepcopy(current_figure)
        if 'layout' in updated_figure:
            updated_figure['layout']['shapes'] = []
        else:
            updated_figure['layout'] = {'shapes': []}
        return updated_figure
    return no_update

# Callback to export annotation log
@app.callback(
    Output('annotations-display', 'children', allow_duplicate=True),
    [Input('export-annotations', 'n_clicks')],
    prevent_initial_call=True
)
def export_annotation_log(export_clicks):
    if export_clicks and annotation_store:
        # Create a detailed log
        log_data = []
        for ann_id, annotation in annotation_store.items():
            log_entry = {
                'annotation_id': ann_id,
                'type': annotation['shape'].get('type', 'unknown'),
                'frame_start': annotation['frame_start'],
                'frame_end': annotation['frame_end'],
                'duration_frames': (annotation['frame_end'] - annotation['frame_start']) if annotation['frame_end'] else None,
                'status': annotation['status'],
                'created_at': annotation['created_at'],
                'shape_properties': annotation['shape']
            }
            log_data.append(log_entry)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"annotation_log_{MATCH_ID}_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            print(f"\n=== ANNOTATION LOG EXPORTED ===")
            print(f"File saved: {filename}")
            print(f"Total annotations: {len(log_data)}")
            
            return format_annotation_display() + f"\n\n✅ Log exported to: {filename}"
        except Exception as e:
            print(f"Error exporting log: {e}")
            return format_annotation_display() + f"\n\n❌ Error exporting log: {e}"
    
    return format_annotation_display()

if __name__ == '__main__':
    app.run(debug=True, port=8050)
