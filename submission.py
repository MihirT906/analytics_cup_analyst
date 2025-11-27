from src.models.DashInteraction import DashInteraction

def create_dash_app():
    da = DashInteraction(episode_file='src/episodes/custom_episodes/episode_10_100.json')
    app = da.create_app()
    return app

if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, port=8051)
