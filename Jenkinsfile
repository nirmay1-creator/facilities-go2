pipeline {
    agent any

    environment {
        GROUP_ID = 'g02'
        IMAGE_NAME = 'facilities-triage-g02'
        PROVIDER_MODE = 'mock'
        DATABASE_PATH = '/tmp/jenkins_facilities.db'
        REPORTS_DIR = 'reports'
        VENV_DIR = '.venv'

        SMOKE_PORT = '18002'
        SMOKE_NAME = "facilities_smoke_${BUILD_NUMBER}"

        INTEGRATION_PORT = '18003'
        INTEGRATION_NAME = "facilities_int_${BUILD_NUMBER}"

        IMAGE_TAG = "g02-${BUILD_NUMBER}-pending"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                script {
                    env.GIT_COMMIT_FULL = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG = "${env.GROUP_ID}-${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                }

                sh '''
                    echo "=============================================="
                    echo "Facilities Request Triage - CI Pipeline"
                    echo "=============================================="
                    echo "Branch : $(git rev-parse --abbrev-ref HEAD)"
                    echo "Commit : $(git log -1 --oneline)"
                    echo "Author : $(git log -1 --format='%an <%ae>')"
                    echo "Date   : $(git log -1 --format='%cd' --date=short)"
                    echo "Image  : ${IMAGE_NAME}:${IMAGE_TAG}"
                    echo "=============================================="

                    mkdir -p "${REPORTS_DIR}"
                '''
            }
        }

        stage('Code Quality') {
            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Setting up Python environment"
                    echo "=============================================="

                    if [ ! -d "${VENV_DIR}" ]; then
                        python3 -m venv "${VENV_DIR}"
                    fi

                    "${VENV_DIR}/bin/python" --version

                    "${VENV_DIR}/bin/python" -m pip install --upgrade pip -q

                    if [ -f requirements.txt ]; then
                        echo "Installing project dependencies..."
                        "${VENV_DIR}/bin/pip" install -r requirements.txt -q
                    fi

                    echo "Installing CI tools..."
                    "${VENV_DIR}/bin/pip" install flake8 bandit pytest pytest-cov -q

                    echo "=============================================="
                    echo "Running flake8"
                    echo "=============================================="

                    "${VENV_DIR}/bin/flake8" \
                        facilities/ \
                        tests/ \
                        --max-line-length=120 \
                        --exclude=__pycache__,.venv \
                        --format="%(path)s:%(row)d:%(col)d: %(code)s %(text)s" \
                        --tee \
                        --output-file="${REPORTS_DIR}/flake8.txt"

                    echo "flake8 passed."

                    echo "=============================================="
                    echo "Running Bandit security scan"
                    echo "=============================================="

                    "${VENV_DIR}/bin/bandit" \
                        -r facilities/ \
                        -ll \
                        -f txt \
                        -o "${REPORTS_DIR}/bandit.txt"

                    echo "Bandit scan passed."
                '''
            }
        }

        stage('Install & Test') {
            environment {
                PROVIDER_MODE = 'mock'
                DATABASE_PATH = '/tmp/jenkins_facilities_test.db'
            }

            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Running Tests"
                    echo "=============================================="

                    "${VENV_DIR}/bin/pytest" \
                        tests/ \
                        --junitxml="${REPORTS_DIR}/junit.xml" \
                        --tb=short \
                        -v \
                        --color=yes

                    echo "Tests passed."
                '''
            }

            post {
                always {
                    junit(
                        testResults: "${REPORTS_DIR}/junit.xml",
                        allowEmptyResults: true
                    )
                }

                failure {
                    echo "QUALITY GATE FAILED - Tests did not pass."
                }
            }
        }

        stage('Coverage Report') {
            environment {
                PROVIDER_MODE = 'mock'
                DATABASE_PATH = '/tmp/jenkins_facilities_cov.db'
            }

            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Generating Coverage Report"
                    echo "=============================================="

                    "${VENV_DIR}/bin/pytest" \
                        tests/ \
                        --cov=facilities \
                        --cov-report=term-missing \
                        --cov-report=html:${REPORTS_DIR}/htmlcov \
                        --cov-report=xml:${REPORTS_DIR}/coverage.xml \
                        -q

                    echo "Coverage report generated."
                '''
            }

            post {
                always {
                    publishHTML(
                        target: [
                            reportName: 'Coverage Report',
                            reportDir: "${REPORTS_DIR}/htmlcov",
                            reportFiles: 'index.html',
                            keepAll: true,
                            alwaysLinkToLastBuild: true,
                            allowMissing: true
                        ]
                    )
                }
            }
        }

        stage('Terraform Validate') {
            steps {
                dir('terraform') {
                    sh '''
                        set -e

                        echo "=============================================="
                        echo "Terraform Validation"
                        echo "=============================================="

                        terraform init \
                            -backend=false \
                            -input=false \
                            -no-color

                        terraform validate -no-color

                        echo "Terraform validation passed."
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Building Docker Image"
                    echo "=============================================="

                    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

                    docker build \
                        --label "build.number=${BUILD_NUMBER}" \
                        --label "git.commit=${GIT_COMMIT_FULL}" \
                        --label "git.short=${GIT_COMMIT_SHORT}" \
                        --label "git.branch=${GIT_BRANCH}" \
                        --label "group.id=${GROUP_ID}" \
                        --label "provider.mode=${PROVIDER_MODE}" \
                        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
                        -t "${IMAGE_NAME}:latest" \
                        .

                    echo "Docker image built successfully."

                    docker images "${IMAGE_NAME}" \
                        --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
                '''
            }
        }

        stage('Container Smoke Test') {
            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Container Smoke Test"
                    echo "=============================================="

                    docker rm -f "${SMOKE_NAME}" 2>/dev/null || true

                    docker run -d \
                        --name "${SMOKE_NAME}" \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/smoke.db \
                        "${IMAGE_NAME}:${IMAGE_TAG}"

                    READY=0

                    echo "Waiting for API inside container..."

                    for i in $(seq 1 20); do
                        sleep 2

                        if docker exec "${SMOKE_NAME}" \
                            curl -sf \
                            http://localhost:8000/health \
                            > /dev/null 2>&1; then

                            READY=1
                            echo "API ready after $((i * 2)) seconds."
                            break
                        fi

                        echo "Attempt ${i}/20..."
                    done

                    if [ "$READY" -ne 1 ]; then
                        echo "ERROR: API did not start."

                        echo "=============================================="
                        echo "Container Logs"
                        echo "=============================================="

                        docker logs "${SMOKE_NAME}" || true

                        echo "=============================================="
                        echo "Container Status"
                        echo "=============================================="

                        docker inspect "${SMOKE_NAME}" \
                            --format '{{.State.Status}} - ExitCode={{.State.ExitCode}}' \
                            || true

                        exit 1
                    fi

                    HEALTH=$(docker exec "${SMOKE_NAME}" \
                        curl -sf \
                        http://localhost:8000/health)

                    echo "Health response:"
                    echo "${HEALTH}"

                    echo "${HEALTH}" | grep -q '"status":"ok"'

                    echo "Health check passed."
                    echo "Container smoke test passed."
                '''
            }

            post {
                always {
                    sh '''
                        docker logs "${SMOKE_NAME}" 2>/dev/null || true
                        docker rm -f "${SMOKE_NAME}" 2>/dev/null || true
                    '''

                    echo "Smoke container cleaned up."
                }
            }
        }

        stage('Integration Check') {
            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Integration Check"
                    echo "=============================================="

                    docker rm -f "${INTEGRATION_NAME}" 2>/dev/null || true

                    docker run -d \
                        --name "${INTEGRATION_NAME}" \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/int.db \
                        "${IMAGE_NAME}:${IMAGE_TAG}"

                    READY=0

                    echo "Waiting for integration API inside container..."

                    for i in $(seq 1 20); do
                        sleep 2

                        if docker exec "${INTEGRATION_NAME}" \
                            curl -sf \
                            http://localhost:8000/health \
                            > /dev/null 2>&1; then

                            READY=1
                            echo "Integration API ready after $((i * 2)) seconds."
                            break
                        fi

                        echo "Attempt ${i}/20..."
                    done

                    if [ "$READY" -ne 1 ]; then
                        echo "ERROR: Integration container did not start."

                        echo "=============================================="
                        echo "Integration Container Logs"
                        echo "=============================================="

                        docker logs "${INTEGRATION_NAME}" || true

                        exit 1
                    fi

                    echo "API ready."

                    echo "=============================================="
                    echo "Sending Integration Request"
                    echo "=============================================="

                    RESPONSE=$(docker exec "${INTEGRATION_NAME}" \
                        curl -sf \
                        -X POST \
                        -H "Content-Type: application/json" \
                        -d '{
                            "subject": "Lights out in lab",
                            "request_text": "The overhead lights in Lab 3B have failed completely."
                        }' \
                        http://localhost:8000/api/analyze)

                    echo "Response:"
                    echo "${RESPONSE}"

                    echo "=============================================="
                    echo "Checking Response Fields"
                    echo "=============================================="

                    echo "${RESPONSE}" | grep -q '"category"' || {
                        echo "FAIL: missing category"
                        exit 1
                    }

                    echo "${RESPONSE}" | grep -q '"priority"' || {
                        echo "FAIL: missing priority"
                        exit 1
                    }

                    echo "${RESPONSE}" | grep -q '"summary"' || {
                        echo "FAIL: missing summary"
                        exit 1
                    }

                    echo "${RESPONSE}" | grep -q '"next_action"' || {
                        echo "FAIL: missing next_action"
                        exit 1
                    }

                    echo "${RESPONSE}" | grep -q '"requires_review":true' || {
                        echo "FAIL: requires_review is not true"
                        exit 1
                    }

                    echo "Integration check passed."
                '''
            }

            post {
                always {
                    sh '''
                        docker logs "${INTEGRATION_NAME}" 2>/dev/null || true
                        docker rm -f "${INTEGRATION_NAME}" 2>/dev/null || true
                    '''

                    echo "Integration container cleaned up."
                }
            }
        }

        stage('Archive') {
            steps {
                sh '''
                    set -e

                    echo "=============================================="
                    echo "Creating Build Manifest"
                    echo "=============================================="

                    mkdir -p "${REPORTS_DIR}"

                    cat > "${REPORTS_DIR}/build_manifest.txt" << EOF
Facilities Request Triage - Build Manifest
==========================================
Group           : ${GROUP_ID}
Build           : ${BUILD_NUMBER}
Image Name      : ${IMAGE_NAME}
Image Tag       : ${IMAGE_TAG}
Git Branch      : ${GIT_BRANCH}
Git Commit      : ${GIT_COMMIT_FULL}
Git Short Hash  : ${GIT_COMMIT_SHORT}
Build URL       : ${BUILD_URL}
Timestamp       : $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Provider        : mock (CI)
Production      : lmstudio
EOF

                    cat "${REPORTS_DIR}/build_manifest.txt"
                '''

                archiveArtifacts(
                    artifacts: "${REPORTS_DIR}/**",
                    fingerprint: true,
                    allowEmptyArchive: true
                )
            }
        }
    }

    post {
        success {
            echo """
==============================================
PIPELINE SUCCESS
==============================================
Image: ${IMAGE_NAME}:${IMAGE_TAG}
All stages completed successfully.
==============================================
"""
        }

        failure {
            echo """
==============================================
PIPELINE FAILED
==============================================
Check the failed stage in Console Output.
==============================================
"""
        }

        unstable {
            echo "Build is UNSTABLE. Review the test reports."
        }

        always {
            sh '''
                docker rm -f "${SMOKE_NAME}" 2>/dev/null || true
                docker rm -f "${INTEGRATION_NAME}" 2>/dev/null || true
                rm -rf "${VENV_DIR}" 2>/dev/null || true
            '''

            cleanWs(
                deleteDirs: true,
                notFailBuild: true
            )
        }
    }
}
