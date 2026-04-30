from app import app
from ml.clustering import train_clustering

with app.app_context():
    train_clustering()