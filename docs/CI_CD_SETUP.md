# CI/CD Setup for iPanel

This document describes the GitHub Actions CI/CD pipeline configuration for the iPanel project.

## Overview

The CI/CD pipeline consists of several workflows that handle different aspects of the development and deployment process:

1. **CI/CD Pipeline** (`ci-cd.yml`) - Main workflow for testing, building, and deployment
2. **Security Scan** (`security-scan.yml`) - Security analysis and vulnerability scanning
3. **Docker Release** (`docker-release.yml`) - Docker image building and publishing on tags
4. **Release** (`release.yml`) - Automated release management

## Workflows

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

This is the main workflow that runs on every push and pull request.

#### Jobs:

##### Lint and Type Check
- **Triggers**: Push to main/develop, Pull requests
- **Python versions**: 3.8, 3.9, 3.10, 3.11
- **Tools**:
  - **Ruff**: Modern Python linter (replaces flake8, black, isort)
  - **mypy**: Static type checker
- **Configuration**: `pyproject.toml`

##### Test
- **Triggers**: Push to main/develop, Pull requests
- **Python versions**: 3.8, 3.9, 3.10, 3.11
- **Tools**:
  - **pytest**: Test framework
  - **coverage**: Code coverage measurement
- **Requirements**: 
  - Minimum 85% test coverage
  - All tests must pass
- **Reports**: 
  - HTML coverage report
  - XML coverage report for Codecov
  - Terminal coverage summary

##### Build
- **Triggers**: Push events and releases
- **Dependencies**: Requires test job to pass
- **Actions**:
  - Build frontend assets (Node.js/npm)
  - Build Python package
  - Upload build artifacts

##### Docker Build
- **Triggers**: Push events and releases
- **Dependencies**: Requires lint-and-type-check and test jobs to pass
- **Actions**:
  - Build Docker image
  - Push to GitHub Container Registry (GHCR)
  - Multi-platform support (linux/amd64, linux/arm64)
  - Image caching with GitHub Actions cache

##### Deployment
- **Staging**: Deploys to staging environment on develop branch
- **Production**: Deploys to production environment on releases

### 2. Security Scan (`.github/workflows/security-scan.yml`)

Comprehensive security analysis workflow.

#### Jobs:

##### CodeQL Analysis
- **Triggers**: Push, Pull requests, Weekly schedule
- **Languages**: Python
- **Actions**:
  - Static application security testing (SAST)
  - Vulnerability detection
  - Security advisory integration

##### Security Scan
- **Tools**:
  - **TruffleHog**: Secret detection
  - **Semgrep**: Static analysis for security vulnerabilities
  - **Bandit**: Python security linter
  - **Safety**: Python dependency vulnerability scanner
- **Configuration**: `.bandit` file for Bandit settings
- **Reports**: Security scan results uploaded as artifacts

### 3. Docker Release (`.github/workflows/docker-release.yml`)

Dedicated workflow for Docker image releases on tags.

#### Features:
- **Triggers**: Git tags (v*), Published releases
- **Registry**: GitHub Container Registry (GHCR)
- **Multi-platform**: linux/amd64, linux/arm64
- **Versioning**: Semantic versioning support
- **Security**: Build provenance attestation
- **Caching**: GitHub Actions cache for faster builds

### 4. Release (`.github/workflows/release.yml`)

Automated release management workflow.

#### Features:
- **Semantic Release**: Automated versioning
- **Changelog**: Automated changelog generation
- **Commit Validation**: Conventional commits
- **Artifact Building**: Python packages and Docker images
- **Multi-environment**: Different release channels

## Configuration Files

### `pyproject.toml`
Central configuration file for Python tooling:
- **Ruff**: Linting and formatting configuration
- **mypy**: Type checking configuration
- **pytest**: Test configuration
- **coverage**: Code coverage configuration

### `.bandit`
Bandit security scanner configuration:
- Exclusions for development files
- Skip specific security checks where appropriate
- File-specific security rules

### `Dockerfile`
Multi-stage Docker build:
- **Frontend build**: Node.js for static assets
- **Python environment**: Python 3.9 slim
- **Security**: Non-root user, minimal dependencies
- **Health checks**: Container health monitoring

## Tool Configurations

### Ruff Configuration
Modern Python linter that replaces multiple tools:
- **Line length**: 127 characters
- **Target version**: Python 3.8+
- **Rules**: Comprehensive set including security (Bandit rules)
- **Formatting**: Consistent code style

### mypy Configuration
Static type checking:
- **Python version**: 3.8 compatible
- **Strict mode**: Balanced strictness
- **Import handling**: Ignore missing imports for external packages

### pytest Configuration
Test framework setup:
- **Test discovery**: Automatic test file discovery
- **Coverage**: 85% minimum coverage requirement
- **Reporting**: Multiple output formats
- **Markers**: Test categorization support

### Coverage Configuration
Code coverage measurement:
- **Source**: iPanel package
- **Exclusions**: Tests, migrations, virtual environments
- **Reporting**: HTML, XML, terminal output
- **Thresholds**: 85% minimum coverage

## Security Measures

### Code Security
- **Static Analysis**: CodeQL, Semgrep, Bandit
- **Secret Detection**: TruffleHog
- **Dependency Scanning**: Safety for Python packages
- **Container Security**: Non-root user, minimal attack surface

### Supply Chain Security
- **Dependency Pinning**: Exact version specifications
- **Provenance**: Build attestation for Docker images
- **Registry Security**: GitHub Container Registry with authentication

### Access Control
- **Permissions**: Minimal required permissions for each job
- **Secrets**: Secure handling of sensitive data
- **Environment Protection**: Staging and production environments

## Development Workflow

### Pre-commit
Before committing code:
```bash
# Install development dependencies
pip install ruff mypy pytest pytest-cov

# Run linting
ruff check iPanel/
ruff format iPanel/

# Run type checking
mypy iPanel/

# Run tests
pytest iPanel/ --cov=iPanel --cov-fail-under=85
```

### Pull Request Process
1. Create feature branch
2. Make changes
3. Run local tests and linting
4. Push to GitHub
5. Create pull request
6. Automated CI/CD pipeline runs
7. Review and merge

### Release Process
1. Merge to main branch
2. Tag release (e.g., `v1.0.0`)
3. GitHub Actions automatically:
   - Builds and tests
   - Creates Docker images
   - Publishes to registries
   - Generates release notes

## Monitoring and Maintenance

### Build Monitoring
- **GitHub Actions**: View workflow runs in GitHub
- **Codecov**: Code coverage trends
- **Security Alerts**: GitHub security advisories

### Maintenance Tasks
- **Dependencies**: Regular updates of action versions
- **Security**: Review and update security configurations
- **Performance**: Monitor build times and optimize
- **Documentation**: Keep this document updated

## Troubleshooting

### Common Issues

#### Test Failures
- Check test output in GitHub Actions logs
- Verify 85% coverage requirement is met
- Ensure all dependencies are properly installed

#### Linting Errors
- Run `ruff check` locally to see specific issues
- Use `ruff format` to auto-fix formatting
- Check `pyproject.toml` for rule configurations

#### Docker Build Issues
- Verify Dockerfile syntax
- Check that all required files are present
- Ensure multi-platform build compatibility

#### Security Scan Failures
- Review security scan artifacts
- Address high-severity issues
- Update `.bandit` configuration if needed

### Getting Help
- Check GitHub Actions documentation
- Review tool-specific documentation (Ruff, mypy, pytest)
- Consult security scanning tool docs
- Check project issues and discussions

## Best Practices

### Code Quality
- Maintain high test coverage (≥85%)
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write meaningful commit messages

### Security
- Regular dependency updates
- Address security findings promptly
- Use secure coding practices
- Keep secrets out of code

### CI/CD
- Keep workflows maintainable
- Use appropriate caching
- Monitor build performance
- Document changes

This CI/CD setup provides a robust foundation for maintaining code quality, security, and reliable deployments for the iPanel project.
