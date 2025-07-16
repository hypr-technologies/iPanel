# Development Setup Guide

## Setting up iPanel for Development

### Prerequisites
- Python 3.7+
- Flask framework

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate into the directory:
   ```bash
   cd iPanel
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Test Server
- Start the development server:
  ```bash
  python test_server.py
  ```
- Access the panel at: `http://localhost:8888`
- Default credentials: admin/admin

### Development Tips
- Ensure debug mode is on for auto-reloading
- Check logs under `logs/` for debugging

### Common Issues
- Import errors: Verify `sys.path` is correctly set
- CSS issues: Ensure braces are escaped in templates

### Contributions
- Fork the repository
- Create a feature branch
- Open a pull request
- Follow coding standards defined in the `CONTRIBUTING.md`
