import plotly.graph_objects as go

class Pitch:
    def __init__(self, dim=None, pitch_color=None, line_color=None, line_alpha=1, line_width=2, linestyle=None, line_zorder=0.9, pad_left=None, pad_right=None, pad_bottom=None, pad_top=None, shade_middle=False, shade_color='#f2f2f2', shade_alpha=1, shade_zorder=0.7, pitch_length=None, pitch_width=None):
        
        self.dim = dim if dim is not None else (6, 4)
        self.pitch_color = pitch_color if pitch_color is not None else "#558b18"
        self.line_color = line_color if line_color is not None else "white"
        self.line_alpha = line_alpha
        self.line_width = line_width
        self.linestyle = linestyle
        self.line_zorder = line_zorder
        self.pad_left = pad_left
        self.pad_right = pad_right
        self.pad_bottom = pad_bottom
        self.pad_top = pad_top
        self.shade_middle = shade_middle
        self.shade_color = shade_color
        self.shade_alpha = shade_alpha
        self.shade_zorder = shade_zorder
        
        # Set pitch dimensions - use provided values or defaults
        if pitch_length is not None and pitch_width is not None:
            self.pitch_length = pitch_length
            self.pitch_width = pitch_width
        elif dim is not None and len(dim) == 2:
            # If dim is provided, assume it's (length, width) for the pitch
            self.pitch_length = 105  # Standard FIFA pitch length
            self.pitch_width = 68    # Standard FIFA pitch width
        else:
            self.pitch_length = 105
            self.pitch_width = 68
            
        # Background color (used in layout)
        self.bg_color = self.pitch_color
        
    def draw(self):
        fig = go.Figure()
        
        # Add field outline
        fig.add_shape(
            type="rect",
            x0=-self.pitch_length/2, y0=-self.pitch_width/2, x1=self.pitch_length/2, y1=self.pitch_width/2,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor=self.pitch_color,
            layer="below"
        )
        
        # Center line
        fig.add_shape(
            type="line",
            x0=0, y0=-self.pitch_width/2, x1=0, y1=self.pitch_width/2,
            line=dict(color=self.line_color, width=self.line_width),
            layer="below"
        )
        
        # Center circle
        fig.add_shape(
            type="circle",
            x0=-self.pitch_length/10, y0=-self.pitch_length/10, x1=self.pitch_length/10, y1=self.pitch_length/10,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Left penalty area
        fig.add_shape(
            type="rect",
            x0=-self.pitch_length/2, y0=-self.pitch_width/3, x1=(-self.pitch_length/2)+(self.pitch_length/5), y1=self.pitch_width/3,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Right penalty area
        fig.add_shape(
            type="rect",
            x0=(self.pitch_length/2)-(self.pitch_length/5), y0=-self.pitch_width/3, x1=self.pitch_length/2, y1=self.pitch_width/3,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Left goal area
        fig.add_shape(
            type="rect",
            x0=-self.pitch_length/2, y0=-self.pitch_width/10, x1=(-self.pitch_length/2)+(self.pitch_length/15), y1=self.pitch_width/10,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Right goal area
        fig.add_shape(
            type="rect",
            x0=(self.pitch_length/2)-(self.pitch_length/15), y0=-self.pitch_width/10, x1=self.pitch_length/2, y1=self.pitch_width/10,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Left goal
        fig.add_shape(
            type="rect",
            x0=-self.pitch_length/2-(self.pitch_length/30), y0=-self.pitch_width/20, x1=-self.pitch_length/2, y1=self.pitch_width/20,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Right goal
        fig.add_shape(
            type="rect",
            x0=self.pitch_length/2, y0=-self.pitch_width/20, x1=self.pitch_length/2+(self.pitch_length/15), y1=self.pitch_width/20,
            line=dict(color=self.line_color, width=self.line_width),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        
        # Configure layout
        figsize = (self.dim[0], self.dim[1])
        fig.update_layout(
            width=figsize[0]*100,
            height=figsize[1]*100,
            plot_bgcolor=self.pitch_color,
            paper_bgcolor=self.pitch_color,
            xaxis=dict(range=[-self.pitch_length/2, self.pitch_length/2], visible=False),
            yaxis=dict(range=[-self.pitch_width/2, self.pitch_width/2], visible=False, scaleanchor="x", scaleratio=1),
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False
        )
        #print(self.pitch_length, self.pitch_width)
        
        return fig