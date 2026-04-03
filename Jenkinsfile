pipeline {
    agent any

    environment {
        IMAGE_NAME = "aceest-gym"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Pulling latest code from GitHub..."
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Save Previous Version') {
            steps {
                echo "Saving current latest as previous for rollback..."
                sh '''
                    if docker image inspect ${IMAGE_NAME}:latest > /dev/null 2>&1; then
                        docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:previous
                        echo "Saved ${IMAGE_NAME}:latest as ${IMAGE_NAME}:previous"
                    else
                        echo "No previous image found — first build, skipping"
                    fi
                '''
            }
        }

        stage('Lint') {
            steps {
                echo "Checking Python syntax..."
                sh 'python3 -m py_compile app.py && echo "Syntax OK"'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }

        stage('Run Tests in Container') {
            steps {
                echo "Running pytest inside Docker container..."
                sh '''
                    docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} \
                        pytest tests/ -v --tb=short
                '''
            }
        }

        stage('Tag as Latest') {
            steps {
                sh 'docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest'
                echo "Promoted ${IMAGE_NAME}:${IMAGE_TAG} to latest"
            }
        }
    }

    post {
        success {
            echo "BUILD SUCCESS — ${IMAGE_NAME}:${IMAGE_TAG} is now latest"
        }
        failure {
            echo "BUILD FAILED — rolling back to previous version"
            sh '''
                if docker image inspect ${IMAGE_NAME}:previous > /dev/null 2>&1; then
                    docker tag ${IMAGE_NAME}:previous ${IMAGE_NAME}:latest
                    echo "ROLLBACK COMPLETE — restored ${IMAGE_NAME}:previous as latest"
                else
                    echo "No previous image to roll back to"
                fi
                docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true
            '''
        }
        always {
            cleanWs()
        }
    }
}
