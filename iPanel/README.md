# iPanel v8.0.0

A modern web-based control panel for server management by Hypr Technologies.

## 🚀 Features

- **Modern Web Interface**: Built with Flask and responsive design
- **Cross-Platform Support**: Works on Windows, Linux, and macOS
- **Development Environment**: Includes test server for easy development
- **Modular Architecture**: Clean separation of concerns with plugin system
- **Security**: Built-in authentication and session management

## 📦 Installation

### Prerequisites
- Python 3.7+
- Flask framework

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd iPanel

# Install dependencies
pip install flask

# Start development server
python test_server.py
```

Access the panel at: `http://localhost:8888`  
Default credentials: **admin/admin**

## 🔧 Development

For development setup and contribution guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Test Server
The included test server provides:
- ✅ Basic web interface
- ✅ User authentication
- ✅ Session management
- ✅ API endpoints
- ✅ Development debugging

## 📁 Project Structure

```
iPanel/
├── BTPanel/           # Main panel module
├── class/            # Core classes and utilities
├── data/             # Configuration and data files
├── test_server.py    # Development test server
├── runserver.py      # Production server launcher
├── CHANGELOG.md      # Version history
├── DEVELOPMENT.md    # Development guide
└── VERSION          # Current version
```

## 🔄 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and release notes.

## 🐛 Troubleshooting

Common issues and solutions:

1. **Import Errors**: Ensure all dependencies are installed
2. **Windows Compatibility**: Use the test server for development
3. **CSS Issues**: Check template formatting for proper escaping

## 📜 License

This project is developed by Hypr Technologies.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For detailed contribution guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

---

**iPanel v8.0.0** - Modern server management made simple.
