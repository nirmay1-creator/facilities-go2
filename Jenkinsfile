// ==========================================================================
// Jenkinsfile – Facilities Request Triage (Group g02)
// ==========================================================================
// Declarative Pipeline with 9 stages:
//
//   Stage 1 · Checkout          – clone + print commit info
//   Stage 2 · Code Quality      – flake8 lint + bandit security scan
//   Stage 3 · Install & Test    – venv, pytest (mock mode), JUnit report
//   Stage 4 · Coverage Report   – pytest-cov, publish HTML coverage
//   Stage 5 · Terraform Validate– init + validate IaC
//   Stage 6 · Docker Build      – dual-tag image (build-tag + latest)
//   Stage 7 · Smoke Test        – spin up container, call /health + /api/analyze
//   Stage 8 · Integration Check – validate mock /api/analyze response shape
//   Stage 9 · Archive           – publish all reports + image manifest
//
// Design decisions:
//   • PROVIDER_MODE=mock throughout – no LM Studio / GPU required in CI
//   • Tests must pass before Docker build (quality gate)
//   • Smoke container is always cleaned up even on failure (post always)
//   • Parallel lint + security scan in Stage 2 to save time
//   • Build number + short commit hash baked into image tag (immutable)
// ==========================================================================

pipeline {
    agent any

    // ── Global environment ─────────────────────────────────────────────────
    environment {
        GROUP_ID      = 'g02'
        IMAGE_NAME    = "facilities-triage-${GROUP_ID}"
        PROVIDER_MODE = 'mock'
        DATABASE_PATH = '/tmp/jenkins_facilities.db'
        SMOKE_PORT    = '18002'
        SMOKE_NAME    = "facilities_smoke_${BUILD_NUMBER}"
        // Immutable tag: g02-<buildNumber>-<shortHash>
        IMAGE_TAG     = "${GROUP_ID}-${BUILD_NUMBER}-${GIT_COMMIT?.take(7) ?: 'nogit'}"
        REPORTS_DIR   = 'reports'
        VENV          = '.venv/bin/activate'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        ansiColor('xterm')
    }

    stages {

        // ── 1. CHECKOUT ────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    echo "┌─────────────────────────────────────────────────────┐"
                    echo "│  Facilities Request Triage — CI Pipeline (g02)      │"
                    echo "└─────────────────────────────────────────────────────┘"
                    echo ""
                    echo "Branch : $(git rev-parse --abbrev-ref HEAD)"
                    echo "Commit : $(git log -1 --oneline)"
                    echo "Author : $(git log -1 --format='%an <%ae>')"
                    echo "Date   : $(git log -1 --format='%cd' --date=short)"
                    echo ""
                    mkdir -p ${REPORTS_DIR}
                '''
            }
        }

        // ── 2. CODE QUALITY (parallel lint + security) ─────────────────────
        stage('Code Quality') {
            parallel {
                stage('Lint – flake8') {
                    steps {
                        sh '''
                            . ${VENV}
                            pip install flake8 -q
                            echo "[flake8] Linting facilities/ and tests/..."
                            flake8 facilities/ tests/ \
                                --max-line-length=120 \
                                --exclude=__pycache__,.venv \
                                --format="%(path)s:%(row)d:%(col)d: %(code)s %(text)s" \
                                --tee \
                                --output-file=${REPORTS_DIR}/flake8.txt \
                            || true
                            echo "[flake8] Done. See ${REPORTS_DIR}/flake8.txt"
                        '''
                    }
                }
                stage('Security – bandit') {
                    steps {
                        sh '''
                            . ${VENV}
                            pip install bandit -q
                            echo "[bandit] Running security scan on facilities/..."
                            bandit -r facilities/ \
                                -ll \
                                -f txt \
                                -o ${REPORTS_DIR}/bandit.txt \
                            || true
                            echo "[bandit] Done. See ${REPORTS_DIR}/bandit.txt"
                        '''
                    }
                }
            }
        }

        // ── 3. INSTALL & TEST ──────────────────────────────────────────────
        stage('Install & Test') {
            environment {
                PROVIDER_MODE = 'mock'
                DATABASE_PATH = '/tmp/jenkins_facilities_test.db'
            }
            steps {
                sh '''
                    echo "[venv] Creating virtual environment..."
                    python3 -m venv .venv
                    . ${VENV}
                    pip install --upgrade pip -q
                    pip install -r requirements.txt -q

                    echo "[pytest] Running test suite in MOCK mode..."
                    pytest tests/ \
                        --junitxml=${REPORTS_DIR}/junit.xml \
                        --tb=short \
                        -v \
                        --color=yes
                    echo "[pytest] Done."
                '''
            }
            post {
                always {
                    junit "${REPORTS_DIR}/junit.xml"
                }
                failure {
                    echo """
╔══════════════════════════════════════════════════════════╗
║  QUALITY GATE FAILED — Tests did not pass.               ║
║  Docker image will NOT be built.                         ║
║  Fix failing tests, commit, and re-run.                  ║
╚══════════════════════════════════════════════════════════╝
"""
                }
            }
        }

        // ── 4. COVERAGE REPORT ─────────────────────────────────────────────
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
                        reportName : 'Coverage Report',
                        reportDir  : "${REPORTS_DIR}/htmlcov",
                        reportFiles: 'index.html',
                        keepAll    : true,
                        alwaysLinkToLastBuild: true
                    ])
                }
            }
        }

        // ── 5. TERRAFORM VALIDATE ──────────────────────────────────────────
        stage('Terraform Validate') {
            steps {
                dir('terraform') {
                    sh '''
                        echo "[terraform] Initialising..."
                        terraform init -backend=false -input=false -no-color
                        echo "[terraform] Validating..."
                        terraform validate -no-color
                        echo "[terraform] ✓ Configuration is valid."
                    '''
                }
            }
        }

        // ── 6. BUILD DOCKER IMAGE ──────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "[docker] Building image: ${IMAGE_NAME}:${IMAGE_TAG}"
                    docker build \
                        --label "build.number=${BUILD_NUMBER}" \
                        --label "git.commit=${GIT_COMMIT}" \
                        --label "git.branch=${GIT_BRANCH}" \
                        --label "group.id=${GROUP_ID}" \
                        -t ${IMAGE_NAME}:${IMAGE_TAG} \
                        -t ${IMAGE_NAME}:latest \
                        .
                    echo "[docker] ✓ Image built successfully."
                    docker images ${IMAGE_NAME} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
                '''
            }
        }

        // ── 7. SMOKE TEST – /health ────────────────────────────────────────
        stage('Container Smoke Test') {
            steps {
                sh '''
                    echo "[smoke] Starting container: ${SMOKE_NAME}"
                    docker run -d \
                        --name ${SMOKE_NAME} \
                        -p ${SMOKE_PORT}:8000 \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/smoke.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    echo "[smoke] Waiting for API to be ready..."
                    READY=0
                    for i in $(seq 1 20); do
                        sleep 2
                        if curl -sf http://localhost:${SMOKE_PORT}/health > /dev/null 2>&1; then
                            READY=1
                            echo "[smoke] API ready after $((i * 2))s."
                            break
                        fi
                        echo "[smoke] Attempt ${i}/20 — not ready yet..."
                    done

                    if [ "$READY" -ne 1 ]; then
                        echo "[smoke] ERROR: API did not start in time."
                        docker logs ${SMOKE_NAME}
                        exit 1
                    fi

                    HEALTH=$(curl -sf http://localhost:${SMOKE_PORT}/health)
                    echo "[smoke] Health response: ${HEALTH}"
                    echo "${HEALTH}" | grep '"status":"ok"'
                    echo "[smoke] ✓ Health check passed."
                '''
            }
            post {
                always {
                    sh 'docker rm -f ${SMOKE_NAME} 2>/dev/null || true'
                    echo "[smoke] Container cleaned up."
                }
            }
        }

        // ── 8. INTEGRATION CHECK – /api/analyze (mock) ────────────────────
        stage('Integration Check') {
            steps {
                sh '''
                    echo "[integration] Starting container for integration check..."
                    docker run -d \
                        --name facilities_int_${BUILD_NUMBER} \
                        -p 18003:8000 \
                        -e PROVIDER_MODE=mock \
                        -e DATABASE_PATH=/data/int.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    echo "[integration] Waiting for API..."
                    for i in $(seq 1 20); do
                        sleep 2
                        curl -sf http://localhost:18003/health > /dev/null 2>&1 && break
                    done

                    echo "[integration] Posting test request..."
                    RESPONSE=$(curl -sf -X POST http://localhost:18003/api/analyze \
                        -H "Content-Type: application/json" \
                        -d "{\\"subject\\": \\"Lights out in lab\\", \\"request_text\\": \\"The overhead lights in Lab 3B have failed completely.\\"}" \
                    )
                    echo "[integration] Response: ${RESPONSE}"

                    # Assert required fields exist in response
                    echo "${RESPONSE}" | grep -q '"category"'    || (echo "FAIL: missing category"    && exit 1)
                    echo "${RESPONSE}" | grep -q '"priority"'    || (echo "FAIL: missing priority"    && exit 1)
                    echo "${RESPONSE}" | grep -q '"summary"'     || (echo "FAIL: missing summary"     && exit 1)
                    echo "${RESPONSE}" | grep -q '"next_action"' || (echo "FAIL: missing next_action" && exit 1)
                    echo "${RESPONSE}" | grep -q '"requires_review":true' || (echo "FAIL: requires_review not true" && exit 1)

                    echo "[integration] ✓ All response fields validated."
                '''
            }
            post {
                always {
                    sh 'docker rm -f facilities_int_${BUILD_NUMBER} 2>/dev/null || true'
                    echo "[integration] Container cleaned up."
                }
            }
        }

        // ── 9. ARCHIVE ARTEFACTS ───────────────────────────────────────────
        stage('Archive') {
            steps {
                sh '''
                    echo "[archive] Writing build manifest..."
                    cat > ${REPORTS_DIR}/build_manifest.txt << EOF
Facilities Request Triage – Build Manifest
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
                archiveArtifacts artifacts: "${REPORTS_DIR}/**", fingerprint: true, allowEmptyArchive: true
            }
        }
    }

    // ── GLOBAL POST ────────────────────────────────────────────────────────
    post {
        success {
            echo """
╔══════════════════════════════════════════════════════════╗
║  ✓ PIPELINE SUCCESS                                      ║
║  Image : ${IMAGE_NAME}:${IMAGE_TAG}
║  All 9 stages completed — image ready for deployment.    ║
╚══════════════════════════════════════════════════════════╝
"""
        }
        failure {
            echo """
╔══════════════════════════════════════════════════════════╗
║  ✗ PIPELINE FAILED                                       ║
║  Check the stage above that turned red.                  ║
║  Docker image was NOT published.                         ║
╚══════════════════════════════════════════════════════════╝
"""
        }
        unstable {
            echo "[post] Build is UNSTABLE — test results may have failures. Review JUnit report."
        }
        always {
            cleanWs(patterns: [[pattern: '.venv/**', type: 'INCLUDE']])
        }
    }
}
