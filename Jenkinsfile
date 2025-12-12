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

                    echo "Checking out source code"

                    # Create virtual environment
                    ${PYTHON} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate

                    # Install requirements
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

                    # Add project root to PYTHONPATH so imports work
                    export PYTHONPATH="$PWD"

                    # Run tests and save XML output for Jenkins
                    pytest --junitxml=${TEST_REPORT_DIR}/results.xml || true
                '''

                junit allowEmptyResults: true, testResults: "${TEST_REPORT_DIR}/results.xml"
            }
        }

        stage('verify') {
            steps {
                echo "3. Running lint + smoke test"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate
                    export PYTHONPATH="$PWD"

                    # Run flake8
                    if command -v flake8 >/dev/null 2>&1; then
                        mkdir -p ${LINT_REPORT}
                        flake8 . --format=default > ${LINT_REPORT}/flake8.txt || true
                    else
                        echo "flake8 not installed; skipping lint"
                    fi

                    # Smoke test on sample fixture
                    if [ -f tests/fixtures/sample_article.txt ]; then
                        python tools/parse_article.py tests/fixtures/sample_article.txt \
                            > ${ARTIFACT_DIR}/smoke_output.json || true
                    else
                        echo "{}" > ${ARTIFACT_DIR}/smoke_output.json
                    fi
                '''

                archiveArtifacts artifacts: "${LINT_REPORT}/**", allowEmptyArchive: true
            }
        }

        stage('archive') {
            steps {
                echo "4. Archiving parser outputs and copying logs to ${REMOTE_LOG_DIR}"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate
                    export PYTHONPATH="$PWD"

                    mkdir -p ${ARTIFACT_DIR}/full_run

                    # Run parser on all example articles
                    if [ -d examples/input_articles ]; then
                        for f in examples/input_articles/*; do
                            fname=$(basename "$f")
                            python tools/parse_article.py "$f" > ${ARTIFACT_DIR}/full_run/${fname}.json || true
                        done
                    fi

                    # Create remote log directory
                    mkdir -p ${REMOTE_LOG_DIR}
                    chmod 0775 ${REMOTE_LOG_DIR} || true

                    # Copy reports + artifacts to /tmp/newsflow-logs
                    cp -r ${TEST_REPORT_DIR} ${REMOTE_LOG_DIR}/ || true
                    cp -r ${LINT_REPORT} ${REMOTE_LOG_DIR}/ || true
                    cp -r ${ARTIFACT_DIR} ${REMOTE_LOG_DIR}/ || true

                    echo "Newsflow logs for build ${BUILD_NUMBER} - $(date -u)" \
                        > ${REMOTE_LOG_DIR}/BUILD_INFO.txt || true
                '''

                archiveArtifacts artifacts: "${ARTIFACT_DIR}/**", fingerprint: true, allowEmptyArchive: true
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
