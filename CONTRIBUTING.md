# 🤝 Contributing to Template

Thank you for your interest in contributing to the Template Flask application! This document outlines the process for contributing and helps ensure a smooth collaboration experience.

## 📋 **Table of Contents**

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)
- [Community](#community)

---

## 🌟 **Code of Conduct**

### **Our Pledge**
We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### **Our Standards**
**Positive behaviors include:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints and experiences
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what is best for the community
- ✅ Showing empathy towards other community members

**Unacceptable behaviors include:**
- ❌ Trolling, insulting/derogatory comments, and personal attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information without permission
- ❌ Other conduct which could reasonably be considered inappropriate

---

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.12 or higher
- Git knowledge
- Familiarity with Flask framework
- Basic understanding of HTML/CSS/JavaScript

### **Development Environment Setup**

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/template.git
   cd template
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate    # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Initialize Database**
   ```bash
   python run.py
   ```

5. **Verify Setup**
   ```bash
   # Run tests
   python -m pytest tests/
   
   # Start development server
   python run.py
   ```

---

## 🔄 **Development Workflow**

### **Branch Strategy**
- `main` - Production-ready code
- `develop` - Integration branch for new features
- `feature/feature-name` - Individual feature development
- `bugfix/issue-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes

### **Feature Development Process**

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Develop and Test**
   ```bash
   # Make your changes
   # Write/update tests
   # Test your changes
   python -m pytest tests/
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new theme customization options
   
   - Add custom color picker for themes
   - Implement gradient background options
   - Update theme API with new endpoints
   
   Closes #123"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request on GitHub
   ```

### **Commit Message Convention**

We use conventional commits for clear commit history:

```
<type>(<scope>): <description>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**
```bash
feat(theme): add custom color picker support
fix(api): resolve entry deletion cascade issue
docs(readme): update installation instructions
style(css): improve responsive layout on mobile
refactor(db): optimize query performance
test(api): add comprehensive endpoint testing
chore(deps): update Flask to latest version
```

---

## 📝 **Coding Standards**

### **Python Code Style**
- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Maximum line length: **88 characters** (Black formatter)
- Use **descriptive variable names**

### **Code Quality Tools**
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy app/
```

### **Flask-Specific Guidelines**

#### **Route Organization**
```python
# Good: Organized in blueprints
from flask import Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/entries')
def list_entries():
    """List all entries with pagination."""
    pass
```

#### **Error Handling**
```python
# Good: Consistent error handling
try:
    result = database_operation()
    return jsonify({"data": result}), 200
except ValidationError as e:
    return jsonify({"error": str(e)}), 400
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500
```

#### **Database Operations**
```python
# Good: Proper transaction handling
def create_entry(data):
    """Create new entry with proper error handling."""
    try:
        cursor.execute(query, params)
        conn.commit()
        return {"id": cursor.lastrowid}
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"Data integrity error: {e}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
```

### **Frontend Guidelines**

#### **HTML Structure**
```html
<!-- Good: Semantic HTML with proper accessibility -->
<section class="entries-section" aria-labelledby="entries-heading">
    <h2 id="entries-heading">Recent Entries</h2>
    <div class="entries-grid" role="grid">
        <!-- Entry cards -->
    </div>
</section>
```

#### **CSS Organization**
```css
/* Good: Organized CSS with clear naming */
/* Base styles */
.card {
    background: var(--bs-secondary-bg);
    border: 1px solid var(--bs-border-color);
    border-radius: 12px;
}

/* Component styles */
.entry-card {
    /* Specific entry card styles */
}

/* State styles */
.entry-card:hover {
    transform: translateY(-2px);
}
```

---

## 🧪 **Testing Guidelines**

### **Testing Strategy**
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test API endpoints and database operations
- **Feature Tests**: Test complete user workflows

### **Test Structure**
```python
# tests/test_api_entries.py
import pytest
from app import create_app

class TestEntriesAPI:
    """Test suite for entries API endpoints."""
    
    def test_list_entries_success(self, client):
        """Test successful entry listing."""
        response = client.get('/api/entries')
        assert response.status_code == 200
        assert 'entries' in response.json
    
    def test_create_entry_validation(self, client):
        """Test entry creation with invalid data."""
        response = client.post('/api/entries', json={})
        assert response.status_code == 400
        assert 'error' in response.json
```

### **Running Tests**
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_api_entries.py

# Run with coverage
python -m pytest --cov=app tests/

# Run tests in parallel
python -m pytest -n auto
```

### **Test Data**
```python
# tests/fixtures.py
@pytest.fixture
def sample_entry():
    """Create sample entry for testing."""
    return {
        "name": "Test Entry",
        "description": "Test description",
        "entry_type_id": 1
    }
```

---

## 📥 **Submitting Changes**

### **Pull Request Guidelines**

#### **PR Title Format**
```
<type>(<scope>): <description>

Examples:
feat(theme): add custom color picker
fix(api): resolve entry deletion bug
docs(readme): update installation guide
```

#### **PR Description Template**
```markdown
## 📋 Summary
Brief description of the changes made.

## 🔄 Changes
- Change 1
- Change 2
- Change 3

## 🧪 Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## 📸 Screenshots (if applicable)
Include screenshots for UI changes.

## 🔗 Related Issues
Closes #123
References #456

## ✅ Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### **Review Process**

1. **Automated Checks**: CI pipeline runs tests and linting
2. **Code Review**: Maintainers review code quality and design
3. **Testing**: Manual testing of new features
4. **Documentation**: Verify documentation is complete
5. **Merge**: Approved changes are merged to main branch

### **Review Criteria**
- ✅ Code quality and style compliance
- ✅ Test coverage for new features
- ✅ Documentation completeness
- ✅ Backward compatibility
- ✅ Performance considerations
- ✅ Security implications

---

## 📚 **Documentation**

### **Documentation Types**

#### **Code Documentation**
```python
def create_entry(name: str, entry_type_id: int, description: str = None) -> dict:
    """Create a new entry in the database.
    
    Args:
        name: The entry name (required)
        entry_type_id: ID of the entry type (required)
        description: Optional entry description
        
    Returns:
        dict: Created entry data with ID
        
    Raises:
        ValidationError: If required fields are missing
        DatabaseError: If database operation fails
        
    Example:
        >>> entry = create_entry("My Book", 1, "Great book")
        >>> print(entry['id'])
        123
    """
```

#### **API Documentation**
- Update `API_DOCUMENTATION.md` for new endpoints
- Include request/response examples
- Document error codes and messages

#### **User Documentation**
- Update `README.md` for new features
- Create/update guides in docs folder
- Include screenshots for UI changes

### **Documentation Standards**
- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Keep documentation up-to-date with code changes

---

## 🌐 **Community**

### **Getting Help**
- 📖 **Documentation**: Check existing docs first
- 🐛 **Issues**: Search existing issues before creating new ones
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Email**: For security issues only

### **Communication Channels**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Request Reviews**: Code-specific discussions

### **Recognition**
Contributors will be:
- ✅ Listed in README.md contributors section
- ✅ Mentioned in release notes
- ✅ Credited in documentation

---

## 🎯 **Areas for Contribution**

### **High Priority**
- 🧪 **Testing**: Expand test coverage
- 📖 **Documentation**: Improve user guides
- ♿ **Accessibility**: Enhance WCAG compliance
- 🔒 **Security**: Security audits and improvements

### **Feature Opportunities**
- 🔐 **Authentication**: User management system
- 📊 **Analytics**: Usage metrics and reporting
- 🌐 **Internationalization**: Multi-language support
- 📱 **Mobile App**: Native mobile applications
- ⚡ **Performance**: Optimization and caching

### **Beginner-Friendly**
Look for issues labeled with:
- `good first issue`
- `help wanted`
- `documentation`
- `testing`

---

## 📄 **License**

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing! 🙏**

Your contributions help make this project better for everyone. Whether you're fixing bugs, adding features, improving documentation, or helping other users, every contribution is valuable and appreciated.

**Happy Coding! 🚀**
