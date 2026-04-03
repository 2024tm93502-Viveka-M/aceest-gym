pipeline {
    agent any

    environment {
        APP_NAME    = "aceest-gym"
        DEPLOY_DIR  = "/opt/aceest-gym"
        VENV_DIR    = "${DEPLOY_DIR}/venv"
        APP_USER    = "aceest"
        // Set by Jenkins credentials store — never hardcode passwords
        BITS_VM_HOST = credentials('BITS_VM_HOST')
        BITS_VM_USER = credentials('BITS_VM_USER')
        BITS_VM_KEY  = credentials('BITS_VM_SSH_KEY')
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out source from Git..."
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo "Creating virtual environment and installing dependencies..."
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "Running unit tests..."
                sh '''
                    . venv/bin/activate
                    python -m pytest tests/ -v --tb=short
                '''
            }
            post {
                failure {
                    echo "Tests FAILED — triggering rollback to last stable version"
                    sh './rollback.sh'
                }
            }
        }

        stage('Package') {
            steps {
                echo "Packaging application..."
                sh '''
                    GIT_COMMIT_SHORT=$(git rev-parse --short HEAD)
                    tar -czf aceest-gym-${GIT_COMMIT_SHORT}.tar.gz \
                        app.py requirements.txt deploy.sh rollback.sh
                    echo "Package: aceest-gym-${GIT_COMMIT_SHORT}.tar.gz"
                '''
            }
        }

        stage('Deploy to BITS VM') {
            steps {
                echo "Deploying to BITS VM Lab..."
                sh '''
                    GIT_COMMIT_SHORT=$(git rev-parse --short HEAD)
                    PACKAGE="aceest-gym-${GIT_COMMIT_SHORT}.tar.gz"

                    # Copy package to VM
                    scp -i ${BITS_VM_KEY} -o StrictHostKeyChecking=no \
                        ${PACKAGE} deploy.sh rollback.sh \
                        ${BITS_VM_USER}@${BITS_VM_HOST}:/tmp/

                    # Execute deploy on VM
                    ssh -i ${BITS_VM_KEY} -o StrictHostKeyChecking=no \
                        ${BITS_VM_USER}@${BITS_VM_HOST} \
                        "chmod +x /tmp/deploy.sh /tmp/rollback.sh && \
                         PACKAGE=${PACKAGE} bash /tmp/deploy.sh"
                '''
            }
            post {
                failure {
                    echo "Deployment FAILED — triggering rollback on VM"
                    sh '''
                        ssh -i ${BITS_VM_KEY} -o StrictHostKeyChecking=no \
                            ${BITS_VM_USER}@${BITS_VM_HOST} \
                            "bash /tmp/rollback.sh"
                    '''
                }
            }
        }

        stage('Smoke Test') {
            steps {
                echo "Running smoke test on VM (headless import check)..."
                sh '''
                    ssh -i ${BITS_VM_KEY} -o StrictHostKeyChecking=no \
                        ${BITS_VM_USER}@${BITS_VM_HOST} \
                        "cd ${DEPLOY_DIR}/current && \
                         ${VENV_DIR}/bin/python -c \
                         'import ast, sys; ast.parse(open(\"app.py\").read()); print(\"Syntax OK\")'"
                '''
            }
            post {
                failure {
                    echo "Smoke test FAILED — rolling back"
                    sh '''
                        ssh -i ${BITS_VM_KEY} -o StrictHostKeyChecking=no \
                            ${BITS_VM_USER}@${BITS_VM_HOST} \
                            "bash /tmp/rollback.sh"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS — ACEest v${env.GIT_COMMIT} deployed"
        }
        failure {
            echo "Pipeline FAILED — check logs above"
        }
        always {
            cleanWs()
        }
    }
}
