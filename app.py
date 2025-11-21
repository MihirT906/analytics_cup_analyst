import streamlit as st
from src.models.PlotlyGameRenderer import PlotlyGameRenderer

# Initialize session state variables
if 'is_paused' not in st.session_state:
    st.session_state['is_paused'] = False
if 'figs' not in st.session_state:
    st.session_state['figs'] = None
if 'current_frame' not in st.session_state:
    st.session_state['current_frame'] = 0

# Configure page to use wide layout and remove padding
st.set_page_config(
    page_title="Interactive Episode Studio",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display text
st.title("Interactive Episode Studio")

# Add a side bar
st.sidebar.title("Configuration")
match_id = st.sidebar.text_input("Match ID:", 1886347)
(frame_start, frame_end) = st.sidebar.slider("Frame Range:", 0, 1000, (0, 100))


# Add a button to generate plots
if st.sidebar.button("Generate Episode Plots", type="primary"):
    with st.spinner("Loading game data and generating plots..."):
        game_renderer = PlotlyGameRenderer(config_file='analytics_cup_analyst/src/config/simple_game_renderer_config.json', is_streamlit=True)
        st.session_state['figs'] = game_renderer.plot_episode(match_id, start_frame=frame_start, end_frame=frame_end, delay=0)
        st.session_state['current_frame'] = 0
        st.session_state['is_paused'] = False

# Only show controls and animation if we have generated figures
if st.session_state['figs'] is not None:
    # Create animation by updating the same placeholder
    # Use columns to better organize the layout
    col1, col2 = st.columns([4, 1])
    
    with col1:
        plot_placeholder = st.empty()
    with col2:
        controls_placeholder = st.empty()
        st.markdown("### Controls")
        
        # Control buttons
        col_pause, col_resume = st.columns(2)
        with col_pause:
            if st.button("Pause"):
                st.session_state['is_paused'] = True
        with col_resume:
            if st.button("Resume"):
                st.session_state['is_paused'] = False
        
        if st.button("Reset"):
            st.session_state['current_frame'] = 0
            st.session_state['is_paused'] = False
    
    # Get current figures from session state
    figs = st.session_state['figs']
    
    # Fast animation using direct loop instead of st.rerun
    if not st.session_state['is_paused']:
        import time
        
        # Continue from current frame instead of restarting
        start_frame = st.session_state['current_frame']
        
        # Display frames starting from current position
        for i in range(start_frame, len(figs)):
            if st.session_state['is_paused']:  # Check for pause during animation
                break
                
            fig = figs[i]
            # Update figure size
            fig.update_layout(
                height=700,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            # Update plot and frame counter
            plot_placeholder.plotly_chart(fig, use_container_width=True, height=700)
            
            # Update current frame in session state
            st.session_state['current_frame'] = i
            
            # Fast animation speed
            time.sleep(0.1)

        # Animation finished, pause at the end
        st.session_state['is_paused'] = True
    
    # Display current frame when paused or manually controlled
    else:
        if figs and len(figs) > 0:
            current_frame_idx = st.session_state['current_frame'] % len(figs)
            fig = figs[current_frame_idx]
            
            # Update figure size to fill available space
            fig.update_layout(
                height=700,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            # Display the plot
            plot_placeholder.plotly_chart(fig, use_container_width=True, height=700)
