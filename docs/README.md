# Pantheon Agents Documentation

This directory contains the documentation for Pantheon Agents, built with Sphinx and using the modern Furo theme.

## Features

- 🌓 **Dark/Light Mode**: Automatic theme switching based on system preferences
- 📱 **Responsive Design**: Works great on all devices
- 🔍 **Full-Text Search**: Quick navigation through documentation
- 📚 **Comprehensive Coverage**: From getting started to advanced topics
- 🎨 **Modern UI**: Clean, professional appearance with Furo theme

## Building Documentation Locally

### Prerequisites

```bash
pip install -r requirements.txt
```

### Build HTML Documentation

```bash
# Using Make
make html

# Or directly with sphinx-build
sphinx-build -b html source build/html
```

### Live Development Server

For development with auto-reload:

```bash
sphinx-autobuild source build/html
```

Then open http://localhost:8000 in your browser.

## Documentation Structure

```
docs/
├── source/
│   ├── _static/          # Static assets (CSS, images)
│   ├── _templates/       # Custom templates
│   ├── api/             # API reference documentation
│   ├── examples/        # Example code and tutorials
│   ├── guides/          # User guides
│   ├── conf.py          # Sphinx configuration
│   └── index.rst        # Main documentation index
├── build/               # Built documentation (git-ignored)
├── requirements.txt     # Documentation dependencies
└── Makefile            # Build automation
```

## Read the Docs Integration

This documentation is configured for automatic building on Read the Docs:

1. Import the project on readthedocs.org
2. The `.readthedocs.yaml` file configures the build
3. Documentation will auto-build on each commit

## Adding New Documentation

1. Create `.rst` or `.md` files in appropriate directories
2. Add to relevant `toctree` directives
3. Use proper heading hierarchy
4. Include code examples where appropriate

## Theme Customization

The Furo theme supports extensive customization through `conf.py`:

- Color schemes for light/dark modes
- Typography settings
- Navigation behavior
- Custom CSS via `_static/custom.css`

## Contributing

See the [Contributing Guide](source/contributing.rst) for guidelines on improving documentation.