from src.models.DashInteraction import DashInteraction
da = DashInteraction(episode_file='src/episodes/custom_episodes/episode_10_100.json')
app = da.create_app()
app.run(debug=True, port=8051)