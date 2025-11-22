import dash
from dash import html, dcc, Input, Output, callback_context, no_update, State
from src.models.DashPlotlyGameRenderer import DashPlotlyGameRenderer
import json
import copy

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Interactive Episode Studio"

# Hardcoded match ID and frame range
MATCH_ID = "1886347"
START_FRAME = 0
END_FRAME = 100  # Reduced range for faster loading

def get_figures():
    """Load data using DashPlotlyGameRenderer and return the generated figures"""
    try:
        game_renderer = DashPlotlyGameRenderer(config_file='analytics_cup_analyst/src/config/simple_game_renderer_config.json')
        figures = game_renderer.plot_episode(MATCH_ID, START_FRAME, END_FRAME, delay=0)
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
                html.H3("Drawing Annotations", style={'textAlign': 'center', 'marginTop': '30px'}),
                html.P([
                    "Use the drawing tools in the graph's toolbar to annotate the visualization. ",
                    "Available tools: line, path, circle, rectangle. ",
                    "Annotations will be displayed below and printed to the console."
                ], style={'textAlign': 'center', 'margin': '10px', 'color': '#666'}),
                html.Button('Clear Annotations', id='clear-annotations', n_clicks=0, style={
                    'backgroundColor': '#ffc107',
                    'color': 'black',
                    'border': 'none',
                    'padding': '10px 20px',
                    'margin': '10px',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                }),
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

# Callback to update the figure
@app.callback(
    [Output('animated-figure', 'figure')],
    [Input('animation-interval', 'n_intervals')]
)
def update_figure(n_intervals):
    if len(figures) == 0:
        return [{}]
    
    # Show figures sequentially, stop at the last one
    if n_intervals >= len(figures):
        figure_index = len(figures) - 1  # Stay on last figure
    else:
        figure_index = n_intervals
    
    # Convert Figure to dict and then copy
    figure_dict = figures[figure_index].to_dict() if hasattr(figures[figure_index], 'to_dict') else dict(figures[figure_index])
    current_figure = copy.deepcopy(figure_dict)
    
    return [current_figure]

# Callback to capture and display annotations
@app.callback(
    Output('annotations-display', 'children'),
    [Input('animated-figure', 'relayoutData'),
     Input('clear-annotations', 'n_clicks')],
    prevent_initial_call=True
)
def display_annotations(relayout_data, clear_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return "No annotations yet. Start drawing on the graph!"
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle clear button
    if trigger_id == 'clear-annotations':
        print("\n=== ANNOTATIONS CLEARED ===")
        return "Annotations cleared. Start drawing on the graph!"
    
    # Handle relayout data from drawing
    if relayout_data and 'shapes' in relayout_data:
        shapes = relayout_data['shapes']
        if shapes:
            # Format and display the annotations
            annotations_text = f"Total Annotations: {len(shapes)}\n\n"
            
            for i, shape in enumerate(shapes):
                annotations_text += f"Annotation {i+1}:\n"
                annotations_text += f"  Type: {shape.get('type', 'unknown')}\n"
                
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
            
            # Print to console
            print("\n=== USER ANNOTATIONS ===")
            print(annotations_text)
            print(f"Raw annotation data:\n{json.dumps(shapes, indent=2)}")
            print("========================\n")
            
            return annotations_text
        else:
            return "No annotations yet. Start drawing on the graph!"
    
    return "No annotations yet. Start drawing on the graph!"

# Callback to clear annotations from the graph
@app.callback(
    Output('animated-figure', 'figure', allow_duplicate=True),
    [Input('clear-annotations', 'n_clicks')],
    [State('animated-figure', 'figure')],
    prevent_initial_call=True
)
def clear_graph_annotations(clear_clicks, current_figure):
    if clear_clicks and current_figure:
        # Remove all shapes from the figure
        updated_figure = copy.deepcopy(current_figure)
        if 'layout' in updated_figure and 'shapes' in updated_figure['layout']:
            updated_figure['layout']['shapes'] = []
        return updated_figure
    return no_update

if __name__ == '__main__':
    app.run(debug=True, port=8050)
