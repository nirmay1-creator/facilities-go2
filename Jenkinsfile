pipeline {
    agent any

    environment {
        GROUP_ID = 'g02'
        IMAGE_NAME = "facilities-triage-${GROUP_ID}"
        PROVIDER_MODE = 'mock'
        DATABASE_PATH = '/tmp/jenkins_facilities.db'
        SMOKE_PORT = '18002'
        SMOKE_NAME = "facilities_smoke_${BUILD_NUMBER}"
        REPORTS_DIR = 'reports'
        VENV = '.venv/bin/activate'
        IMAGE_TAG = "g02-${BUILD_NUMBER}-nogit"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    echo "Facilities Request Triage - CI Pipeline"
                    echo "Branch : $(git rev-parse --abbrev-ref HEAD)"
                    echo "Commit : $(git log -1 --oneline)"
                    echo "Author : $(git log -1 --format='%an <%ae>')"
                    echo "Date   : $(git log -1 --format='%cd' --date=short)"

                    mkdir -p ${REPORTS_DIR}

                    SHORT_COMMIT=$(git rev-parse --short=7 HEAD)
                    echo "Short Commit : ${SHORT_COMMIT}"
                    echo "IMAGE_TAG=${GROUP_ID}-${BUILD_NUMBER}-${SHORT_COMMIT}" > .build_env
                '''

                script {
                    def shortCommit = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG = "${env.GROUP_ID}-${env.BUILD_NUMBER}-${shortCommit}"
                    env.GIT_SHORT = shortCommit
                }
            }
        }

        stage('Code Quality') {
            steps {
                sh '''
                    echo "[venv] Creating virtual environment..."

                    if [ ! -d ".venv" ]; then
                        python3 -m venv .venv
                    fi

                    . ${VENV}

                    python --version
                    pip --version

                    pip install --upgrade pip -q
                    pip install flake8 bandit -q
                '''

                parallel(
                    'Lint - flake8': {
                        sh '''
                            . ${VENV}

                            echo "[flake8] Linting..."
                            flake8 facilities/ tests/ \
                                --max-line-length=120 \
                                --exclude=__pycache__,.venv \
                                --format="%(path)s:%(row)d:%(col)d: %(code)s %(text)s" \
                                --tee \
                                --output-file=${REPORTS_DIR}/flake8.txt \
                            || true

                            echo "[flake8] Done."
                        '''
                    },
                    'Security - bandit': {
                        sh '''
                            . ${VENV}

                            echo "[bandit] Running security scan..."
                            bandit -r facilities/ \
                                -ll \
                                -f txt \
                                -o ${REPORTS_DIR}/bandit.txt \
                            || true

                            echo "[bandit] Done."
                        '''
                    }
                )
            }
        }

        stage('Install & Test') {
            environment {
                PROVIDER_MODE = 'mock'
                DATABASE_PATH = '/tmp/jenkins_facilities_test.db'
            }

            steps {
                sh '''
                    . ${VENV}

                    echo "[dependencies] Installing requirements..."
                    pip install -r requirements.txt -q

                    echo "[pytest] Running test suite..."
                    pytest tests/ \
                        --junitxml=${REPORTS_DIR}/junit.xml \
                        --tb=short \
                        -v \
                        --color=yes

                    echo "[pytest] Tests completed."
                '''
            }

            post {
                always {
                    junit "${REPORTS_DIR}/junit.xml"
                }

                failure {
                    echo "QUALITY GATE FAILED - Tests did not pass."
                }
            }
        }

        stage('Coverage Report') {
            environment {
                PROVIDER_MODE = 'mock'
                DATABASE_PATH = '/tmp/jenkins_cov.db'
            }

            steps {
                sh '''
                    . ${VENV}

                    pip install pytest-cov -q

                    echo "[coverage] Generating coverage report..."

                    pytest tests/ \
                        --cov=facilities \
                        --cov-report=term-missing \
                        --cov-report=html:${REPORTS_DIR}/htmlcov \
                        --cov-report=xml:${REPORTS_DIR}/coverage.xml \
                        -q

                    echo "[coverage] Done."
                '''
            }

            post {
                always {
                    publishHTML(target: [
                        reportName: 'Coverage Report',
                        reportDir: "${REPORTS_DIR}/htmlcov",
                        reportFiles: 'index.html',
                        keepAll: true,
                        alwaysLinkToLastBuild: true
                    ])
                }
            }
        }

        stage('Terraform Validate') {
            steps {
                dir('terraform') {
                    sh '''
                        echo "[terraform] Initialising..."
                        terraform init -backend=false -input=false -no-color

                        echo "[terraform] Validating..."
                        terraform validate -no-color

                        echo "[terraform] Configuration is valid."
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "[docker] Building image..."
                    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

                    docker build \
                        --label "build.number=${BUILD_NUMBER}" \
                        --label "git.commit=${GIT_COMMIT}" \
                        --label "git.short=${GIT_SHORT}" \
                        --label "git.branch=${GIT_BRANCH}" \
                        --label "group.id=${GROUP_ID}" \
                        -t ${IMAGE_NAME}:${IMAGE_TAG} \
                        -t ${IMAGE_NAME}:latest \
                        .

                    echo "[docker] Image built successfully."

                    docker images ${IMAGE_NAME} \
                        --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
                '''
            }
        }

        stage('Container Smoke Test') {
            steps {
                sh '''
                    echo "[smoke] Starting container..."

                    docker run -d \
                        --name ${SMOKE_NAME} \
                        -p ${SMOKE_PORT}:8000 \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/smoke.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    echo "[smoke] Waiting for API..."

                    READY=0

                    for i in $(seq 1 20); do
                        sleep 2

                        if curl -sf http://localhost:${SMOKE_PORT}/health > /dev/null 2>&1; then
                            READY=1
                            echo "[smoke] API ready after $((i * 2)) seconds."
                            break
                        fi

                        echo "[smoke] Attempt ${i}/20..."
                    done

                    if [ "$READY" -ne 1 ]; then
                        echo "[smoke] ERROR: API did not start."
                        docker logs ${SMOKE_NAME}
                        exit 1
                    fi

                    HEALTH=$(curl -sf http://localhost:${SMOKE_PORT}/health)

                    echo "[smoke] Health response:"
                    echo "${HEALTH}"

                    echo "${HEALTH}" | grep '"status":"ok"'

                    echo "[smoke] Health check passed."
                '''
            }

            post {
                always {
                    sh 'docker rm -f ${SMOKE_NAME} 2>/dev/null || true'
                    echo "[smoke] Container cleaned up."
                }
            }
        }

        stage('Integration Check') {
            steps {
                sh '''
                    INT_NAME="facilities_int_${BUILD_NUMBER}"

                    echo "[integration] Starting container..."

                    docker run -d \
                        --name ${INT_NAME} \
                        -p 18003:8000 \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/int.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    echo "[integration] Waiting for API..."

                    READY=0

                    for i in $(seq 1 20); do
                        sleep 2

                        if curl -sf http://localhost:18003/health > /dev/null 2>&1; then
                            READY=1
                            break
                        fi
                    done

                    if [ "$READY" -ne 1 ]; then
                        echo "[integration] API failed to start."
                        docker logs ${INT_NAME}
                        exit 1
                    fi

                    echo "[integration] Sending test request..."

                    RESPONSE=$(curl -sf \
                        -X POST \
                        http://localhost:18003/api/analyze \
                        -H "Content-Type: application/json" \
                        -d '{"subject":"Lights out in lab","request_text":"The overhead lights in Lab 3B have failed completely."}')

                    echo "[integration] Response:"
                    echo "${RESPONSE}"

                    echo "${RESPONSE}" | grep -q '"category"' \
                        || (echo "FAIL: missing category" && exit 1)

                    echo "${RESPONSE}" | grep -q '"priority"' \
                        || (echo "FAIL: missing priority" && exit 1)

                    echo "${RESPONSE}" | grep -q '"summary"' \
                        || (echo "FAIL: missing summary" && exit 1)

                    echo "${RESPONSE}" | grep -q '"next_action"' \
                        || (echo "FAIL: missing next_action" && exit 1)

                    echo "${RESPONSE}" | grep -q '"requires_review":true' \
                        || (echo "FAIL: requires_review is not true" && exit 1)

                    echo "[integration] All response fields validated."
                '''
            }

            post {
                always {
                    sh 'docker rm -f facilities_int_${BUILD_NUMBER} 2>/dev/null || true'
                    echo "[integration] Container cleaned up."
                }
            }
        }

        stage('Archive') {
            steps {
                sh '''
                    echo "[archive] Creating build manifest..."

                    cat > ${REPORTS_DIR}/build_manifest.txt << EOF
Facilities Request Triage - Build Manifest
==========================================
Group      : ${GROUP_ID}
Build      : ${BUILD_NUMBER}
Image Name : ${IMAGE_NAME}
Image Tag  : ${IMAGE_TAG}
Git Branch : ${GIT_BRANCH}
Git Commit : ${GIT_COMMIT}
Build URL  : ${BUILD_URL}
Timestamp  : $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Provider   : mock (CI) / lmstudio (production)
EOF

                    cat ${REPORTS_DIR}/build_manifest.txt
                '''

                archiveArtifacts \
                    artifacts: "${REPORTS_DIR}/**", \
                    fingerprint: true, \
                    allowEmptyArchive: true
            }
        }
    }

    post {
        success {
            echo """
PIPELINE SUCCESS
Image: ${IMAGE_NAME}:${IMAGE_TAG}
All stages completed successfully.
"""
        }

        failure {
            echo """
PIPELINE FAILED
Check the failed stage above.
"""
        }

        unstable {
            echo "Build is UNSTABLE. Review the test and JUnit reports."
        }

        always {
            cleanWs(
                patterns: [
                    [pattern: '.venv/**', type: 'INCLUDE']
                ]
            )
        }
    }
}
