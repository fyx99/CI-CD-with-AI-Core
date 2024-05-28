# Import necessary libraries
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib

import os
import sys

# Get all environment variables
env_vars = os.environ



if __name__ == "__main__":
    
    # Print each environment variable
    # for key, value in env_vars.items():
    #     print(f"{key}: {value}", file=sys.stderr)

    
    
    print("envexample:", os.environ.get("envexample"), file=sys.stderr)

    # Specify the directory
    directory = "/app/data"

    # List all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Print the list of files
    print(files)
    
    # Generate some sample data for training
    np.random.seed(0)
    X = np.random.rand(100, 1)  # Random input features
    y = 2.0 * X.squeeze() + np.random.normal(0, 0.1, size=100)  # True relationship with noise

    # Initialize and train the linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Save the trained model to a file
    joblib.dump(model, "/app/model/linear_regression_model.pkl")
    
    print("Training done", file=sys.stderr)
    
    directory = "/app/model"

    # List all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Print the list of files
    print(files)
    