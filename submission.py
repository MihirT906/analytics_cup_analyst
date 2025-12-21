# More information in submission.ipynb. Use this if the notebook is not working.
from src.models.DashInteraction import DashInteraction

def create_dash_app():
    print("Creating dash app")
    da = DashInteraction(episode_file='src/episodes/custom_episodes/episode_10_100.json')
    app = da.create_app()
    return app

if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, port=8051, dev_tools_hot_reload=True)
