pipeline {
    agent any

    environment {
        PYTHON = "python3"
        VENV_DIR = "venv"
        REQUIREMENTS = "requirements.txt"
        TEST_REPORT_DIR = "reports/tests"
        LINT_REPORT = "reports/lint"
        ARTIFACT_DIR = "artifacts"
        REMOTE_LOG_DIR = "/tmp/newsflow-logs"
        TIMESTAMP = "${new Date().format('yyyyMMdd-HHmmss')}"
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

                    echo "Creating virtual environment"
                    ${PYTHON} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate

                    if [ -f "${REQUIREMENTS}" ]; then
                        pip install --upgrade pip
                        pip install -r ${REQUIREMENTS}
                    fi

                    # Ensure required directories exist
                    mkdir -p ${TEST_REPORT_DIR}
                    mkdir -p ${LINT_REPORT}
                    mkdir -p ${ARTIFACT_DIR}
                '''
            }
        }

        stage('test') {
            steps {
                echo "2. Running unit tests"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate
                    export PYTHONPATH="$PWD"

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

                    mkdir -p ${LINT_REPORT}
                    mkdir -p ${ARTIFACT_DIR}

                    if command -v flake8 >/dev/null 2>&1; then
                        flake8 . > ${LINT_REPORT}/flake8.txt || true
                    fi

                    # Smoke test → ensure artifacts folder exists before writing
                    if [ -f tests/fixtures/sample_article.txt ]; then
                        python tools/parse_article.py tests/fixtures/sample_article.txt \
                            > ${ARTIFACT_DIR}/smoke_output-${TIMESTAMP}.json
                    else
                        echo "{}" > ${ARTIFACT_DIR}/smoke_output-${TIMESTAMP}.json
                    fi
                '''

                archiveArtifacts artifacts: "${LINT_REPORT}/**", allowEmptyArchive: true
            }
        }

        stage('archive') {
            steps {
                echo "4. Archiving full-run outputs + copying logs"

                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate
                    export PYTHONPATH="$PWD"

                    # Ensure directories exist (THIS FIXES YOUR ERROR)
                    mkdir -p ${ARTIFACT_DIR}
                    mkdir -p ${ARTIFACT_DIR}/full_run

                    # Full-run timestamped artifacts
                    if [ -d examples/input_articles ]; then
                        for f in examples/input_articles/*; do
                            fname=$(basename "$f")
                            python tools/parse_article.py "$f" \
                                > ${ARTIFACT_DIR}/full_run/${fname}-${TIMESTAMP}.json
                        done
                    fi

                    mkdir -p ${REMOTE_LOG_DIR}
                    chmod 0775 ${REMOTE_LOG_DIR} || true

                    cp -r ${TEST_REPORT_DIR} ${REMOTE_LOG_DIR}/ || true
                    cp -r ${LINT_REPORT} ${REMOTE_LOG_DIR}/ || true
                    cp -r ${ARTIFACT_DIR} ${REMOTE_LOG_DIR}/ || true

                    echo "Newsflow logs for build ${BUILD_NUMBER} - $(date -u)" \
                        > ${REMOTE_LOG_DIR}/BUILD_INFO.txt
                '''

                archiveArtifacts artifacts: "${ARTIFACT_DIR}/**", fingerprint: true
                stash includes: "${ARTIFACT_DIR}/**", name: "parser-artifacts"
            }
        }
    }

    post {
        always {
            echo "Cleaning workspace..."
            sh '''
                set +e
                rm -rf ${VENV_DIR}
            '''
            cleanWs()
        }
        success { echo "Pipeline succeeded." }
        failure { echo "Pipeline failed." }
    }
}
