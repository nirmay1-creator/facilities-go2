// ==========================================================================
// Jenkinsfile – Facilities Request Triage (Group g02)
// ==========================================================================
// Stages:
//   1. Checkout
//   2. Install dependencies
//   3. Run pytest (mock mode, no LM Studio required)
//   4. Publish JUnit XML (even on test failure)
//   5. Validate Terraform
//   6. Build Docker image (only after tests pass)
//   7. Smoke test container in mock mode
//   8. Archive artefacts / tag
// ==========================================================================

pipeline {
    agent any

    environment {
        GROUP_ID   = 'g02'
        IMAGE_NAME = "facilities-triage-${GROUP_ID}"
        // Use mock provider – Jenkins must NOT call LM Studio
        PROVIDER_MODE   = 'mock'
        DATABASE_PATH   = '/tmp/jenkins_facilities.db'
        // Immutable build tag: groupid-buildnumber-commithash
        IMAGE_TAG = "${GROUP_ID}-${BUILD_NUMBER}-${GIT_COMMIT?.take(7) ?: 'unknown'}"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        // ------------------------------------------------------------------
        // 1. Checkout
        // ------------------------------------------------------------------
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --oneline'
            }
        }

        // ------------------------------------------------------------------
        // 2. Install dependencies
        // ------------------------------------------------------------------
        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip -q
                    pip install -r requirements.txt -q
                '''
            }
        }

        // ------------------------------------------------------------------
        // 3. Run pytest (mock mode – no LM Studio, no GPU, no API tokens)
        // ------------------------------------------------------------------
        stage('Run tests') {
            environment {
                PROVIDER_MODE = 'mock'
                DATABASE_PATH = '/tmp/jenkins_facilities_test.db'
            }
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest tests/ \
                        --junitxml=reports/junit.xml \
                        -v
                '''
            }
            // 4. Publish JUnit XML even if tests fail
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        // ------------------------------------------------------------------
        // 5. Validate Terraform
        // ------------------------------------------------------------------
        stage('Terraform validate') {
            steps {
                dir('terraform') {
                    sh '''
                        terraform init -backend=false -input=false
                        terraform validate
                    '''
                }
            }
        }

        // ------------------------------------------------------------------
        // 6. Build Docker image (only reached if tests pass)
        // ------------------------------------------------------------------
        stage('Build Docker image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
                sh "echo Built: ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        // ------------------------------------------------------------------
        // 7. Smoke test – run container in mock mode, call /health
        // ------------------------------------------------------------------
        stage('Container smoke test') {
            steps {
                sh '''
                    docker run -d \
                        --name facilities_smoke_${BUILD_NUMBER} \
                        -p 18002:8000 \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/smoke.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    # Wait for the API to start
                    for i in $(seq 1 15); do
                        sleep 2
                        curl -sf http://localhost:18002/health && break
                    done

                    # Assert health endpoint
                    curl -sf http://localhost:18002/health | grep '"status":"ok"'
                    echo "Smoke test passed"
                '''
            }
            post {
                always {
                    sh 'docker rm -f facilities_smoke_${BUILD_NUMBER} || true'
                }
            }
        }

        // ------------------------------------------------------------------
        // 8. Archive artefacts / image tag
        // ------------------------------------------------------------------
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'reports/junit.xml', fingerprint: true
                sh "echo IMAGE_TAG=${IMAGE_TAG} > reports/image_tag.txt"
                archiveArtifacts artifacts: 'reports/image_tag.txt', fingerprint: true
                sh "echo Build complete: ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }
    }

    post {
        failure {
            echo """
            ============================================================
            BUILD FAILED – Docker image was NOT created.
            A deliberate failing test prevents image publication.
            Fix the test, commit, and re-run.
            ============================================================
            """
        }
        success {
            echo "Pipeline complete – image: ${IMAGE_NAME}:${IMAGE_TAG}"
        }
    }
}
