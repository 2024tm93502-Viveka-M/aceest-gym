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
                echo "Image tagged as ${IMAGE_NAME}:latest"
            }
        }
    }

    post {
        success {
            echo "BUILD SUCCESS — ${IMAGE_NAME}:${IMAGE_TAG} is ready"
        }
        failure {
            echo "BUILD FAILED — check stage logs above"
            sh 'docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true'
        }
        always {
            cleanWs()
        }
    }
}
