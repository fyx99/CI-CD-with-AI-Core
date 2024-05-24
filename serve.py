from fastapi import FastAPI
import joblib
import numpy as np
import os
# Load the trained model


# Initialize FastAPI app
app = FastAPI()

# Define a POST endpoint for model inference
@app.post("/v2/predict/")
def predict(input_data: float):
    model = joblib.load("/app/model/linear_regression_model.pkl")
    # Convert input to numpy array for prediction
    input_array = np.array([[input_data]])
    
    # Perform inference using the loaded model
    prediction = model.predict(input_array)
    
    # Return the prediction as JSON response
    return {"prediction": prediction[0], "env_example": os.environ["ENV_EXAMPLE"]}

@app.post("/v2/hello/")
def hello():
    print("hello")
    return {"prediction": "hello", "env_example": os.environ["ENV_EXAMPLE"]}


# Run the FastAPI server with UVicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)