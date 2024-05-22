# CI-CD-with-AI-Core




docker build -t bfwork/cicdexample -f Dockerfile . ;


docker push bfwork/cicdexample 

docker run -it --user nobody bfwork/cicdexample /bin/sh -c "python /app/src/train.py"

docker run --user nobody -it bfwork/cicdexample /bin/sh

python /app/src/main.py

echo "This is a sample file." > ~samplefile.txt
