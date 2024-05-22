# Build the Docker image
docker build -t bfwork/cicdexample -f Dockerfile .

# Push the Docker image to the repository
docker push bfwork/cicdexample

# Execute the Python script
python cicd/pipeline.py
