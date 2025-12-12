pipeline {
    agent any

    environment {
        PYTHON = "python3"
        VENV_DIR = "venv"
        REQUIREMENTS = "requirements.txt"
        TEST_REPORT_DIR = "reports/tests"
        LINT_REPORT = "reports/lint"
        ARTIFACT_DIR = "artifacts"
        REMOTE_LOG_DIR = "/tmp/newsflow-logs"   // where logs will be copied on the agent
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    stages {

        stage('init') {
            steps {
                echo "1. Checking environment and setting up dependencies"

                sh '''
                    set -e

                    echo "Checking if python3 is installed..."
                    if ! command -v python3 >/dev/null 2>&1; then
                        echo "ERROR: python3 is not installed or not in PATH."
                        exit 1
                    else
                        echo "python3 found: $(python3 --version)"
                    fi

                    # Checkout repo (Jenkins does this automatically in many setups)
                    echo "Checking out source code"

                    # Create virtual environment
                    ${PYTHON} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate

                    # Install requirements if they exist
                    if [ -f "${REQUIREMENTS}" ]; then
                        pip install --upgrade pip
                        pip install -r ${REQUIREMENTS}
                    else
                        echo "No requirements.txt found. Continuing."
                    fi

                    mkdir -p ${TEST_REPORT_DIR} ${LINT_REPORT} ${ARTIFACT_DIR}
                '''
            }
        }

        stage('test') {
            steps {
                echo "2. Running unit tests"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate

                    # Run tests and save JUnit XML for Jenkins (don't fail pipeline before junit step)
                    pytest --junitxml=${TEST_REPORT_DIR}/results.xml || true
                '''

                // Publish test results to Jenkins
                junit allowEmptyResults: true, testResults: "${TEST_REPORT_DIR}/results.xml"
            }
        }

        stage('verify') {
            steps {
                echo "3. Running lint + smoke test"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate

                    # Run linter if available (save output)
                    if command -v flake8 >/dev/null 2>&1; then
                        mkdir -p ${LINT_REPORT}
                        flake8 . --format=default > ${LINT_REPORT}/flake8.txt || true
                    else
                        echo "flake8 not installed; skipping lint"
                    fi

                    # Smoke test: run parser on sample fixture and save output
                    if [ -f tests/fixtures/sample_article.txt ]; then
                        python tools/parse_article.py tests/fixtures/sample_article.txt \
                            > ${ARTIFACT_DIR}/smoke_output.json || true
                    else
                        echo "{}" > ${ARTIFACT_DIR}/smoke_output.json
                    fi
                '''

                // Archive lint report so it's downloadable
                archiveArtifacts artifacts: "${LINT_REPORT}/**", allowEmptyArchive: true
            }
        }

        stage('archive') {
            steps {
                echo "4. Archiving parser outputs and copying logs to ${REMOTE_LOG_DIR}"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate

                    # Ensure artifact output exists
                    mkdir -p ${ARTIFACT_DIR}/full_run

                    # Example: run parser on sample dataset if available and save outputs
                    if [ -d examples/input_articles ]; then
                        for f in examples/input_articles/*; do
                            fname=$(basename "$f")
                            python tools/parse_article.py "$f" > ${ARTIFACT_DIR}/full_run/${fname}.json || true
                        done
                    fi

                    # Ensure the remote log directory exists on the agent and is writable
                    mkdir -p ${REMOTE_LOG_DIR}
                    chmod 0775 ${REMOTE_LOG_DIR} || true

                    # Copy important logs and reports to /tmp/newsflow-logs
                    # We copy test reports, lint reports, and parser artifacts
                    cp -r ${TEST_REPORT_DIR} ${REMOTE_LOG_DIR}/ || true
                    cp -r ${LINT_REPORT} ${REMOTE_LOG_DIR}/ || true
                    cp -r ${ARTIFACT_DIR} ${REMOTE_LOG_DIR}/ || true

                    # Optionally create a small README inside the remote log dir
                    echo "Newsflow logs for build ${BUILD_NUMBER} - $(date -u)" > ${REMOTE_LOG_DIR}/BUILD_INFO.txt || true
                '''

                // Archive artifacts as before (keeps them attached to the Jenkins build)
                archiveArtifacts artifacts: "${ARTIFACT_DIR}/**", fingerprint: true, allowEmptyArchive: true

                // Stash artifacts for downstream jobs if needed
                stash includes: "${ARTIFACT_DIR}/**", name: "parser-artifacts", allowEmpty: true
            }
        }
    }

    post {
        always {
            echo "Cleaning workspace (but leaving ${REMOTE_LOG_DIR} intact for inspection)"
            sh '''
                set +e
                rm -rf ${VENV_DIR}
            '''
            cleanWs()
        }
        success {
            echo "Pipeline succeeded."
        }
        failure {
            echo "Pipeline failed. Check logs and reports."
        }
    }
}
