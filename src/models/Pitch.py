import plotly.graph_objects as go
from mplsoccer import Pitch 
import os
import json
from PIL import Image
import io
import base64
import matplotlib.pyplot as plt

class PlotlyPitch:
    def __init__(self, config=None):
        self.config = config
        
    def draw_image(self):
        # Create matplotlib figure first
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
        fig_mpl, ax = pitch.draw(figsize=self.config['display']['figsize'])
        
        # Get the actual axis limits from the matplotlib figure
        xlims = ax.get_xlim()
        ylims = ax.get_ylim()
        
        # Save to memory buffer instead of file to avoid I/O issues
        img_buffer = io.BytesIO()
        fig_mpl.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Create base64 encoded image for Plotly
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        img_src = f"data:image/png;base64,{img_base64}"
        
        # Close matplotlib figure to free memory
        fig_mpl.clf()

        plt.close(fig_mpl)
        
        # Create Plotly figure with the image as background
        fig_plotly = go.Figure()
        
        # Add the image as a background using the actual matplotlib axis limits
        fig_plotly.add_layout_image(
            dict(
                source=img_src,
                xref="x",
                yref="y",
                x=xlims[0],
                y=ylims[1],
                sizex=xlims[1] - xlims[0],
                sizey=ylims[1] - ylims[0],
                sizing="stretch",
                opacity=1,
                layer="below"
            )
        )
        
        # Configure layout using the actual matplotlib axis limits
        figsize = self.config['display']['figsize']
        fig_plotly.update_layout(
            width=figsize[0]*50,
            height=figsize[1]*50,
            plot_bgcolor=self.config['pitch']['styling']['background_color'],
            paper_bgcolor=self.config['pitch']['styling']['background_color'],
            xaxis=dict(
                range=[xlims[0], xlims[1]], 
                visible=False,
                showgrid=False
            ),
            yaxis=dict(
                range=[ylims[0], ylims[1]], 
                visible=False, 
                scaleanchor="x", 
                scaleratio=1,
                showgrid=False
            ),
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False
        )
        
        return fig_plotly