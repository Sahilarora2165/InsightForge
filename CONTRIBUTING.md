# Contributing to InternalKnowledgeHub

Thank you for your interest in contributing to InternalKnowledgeHub! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to build something useful together.

## Getting Started

1. **Fork the repository** and clone it locally
2. **Set up your development environment** by running `./scripts/setup.sh`
3. **Create a branch** for your feature or fix

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/add-document-preview` - For new features
- `fix/login-error-handling` - For bug fixes
- `docs/update-api-docs` - For documentation
- `refactor/improve-rag-pipeline` - For refactoring

### Commit Messages

Follow conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(rag): add semantic caching for repeated queries

Implements Redis-based semantic cache that uses embedding similarity
to find cached answers for similar questions.

Closes #123
```

## Code Style

### Python (Backend)

- Use **Python 3.11+** features
- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Format with **Ruff** (configured in `pyproject.toml`)
- Maximum line length: 88 characters

```python
# Good
def process_document(
    document_id: str,
    options: ProcessingOptions | None = None
) -> ProcessingResult:
    """Process a document and extract chunks.
    
    Args:
        document_id: The unique identifier of the document
        options: Optional processing configuration
        
    Returns:
        Processing result with status and chunks
    """
    pass
```

### TypeScript (Frontend)

- Use **TypeScript** strict mode
- Follow **ESLint** rules (configured in `eslint.config.js`)
- Use **functional components** with hooks
- Format with **Prettier**

```typescript
// Good
interface DocumentCardProps {
  document: Document;
  onDelete?: (id: string) => void;
}

export function DocumentCard({ document, onDelete }: DocumentCardProps) {
  // Component implementation
}
```

## Testing

### Backend Tests

Run backend tests:
```bash
cd backend
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ -v --cov=app --cov-report=html
```

Write tests for:
- All new API endpoints
- Business logic in services
- Edge cases and error handling

### Frontend Tests

Run frontend tests:
```bash
cd frontend
npm run test
```

## Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features or bug fixes
3. **Run linting and tests** locally before submitting
4. **Fill out the PR template** completely
5. **Request review** from maintainers

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No console.log or debug statements
- [ ] No hardcoded secrets or credentials

## Architecture Guidelines

### Backend

```
backend/
├── app/
│   ├── api/          # API endpoints (routes/controllers)
│   ├── core/         # Core configuration and utilities
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas for validation
│   └── services/     # Business logic
├── worker/           # Celery async tasks
└── tests/            # Test files
```

- **API routes** should be thin - delegate to services
- **Services** contain business logic
- **Models** represent database entities
- **Schemas** handle validation and serialization

### Frontend

```
frontend/src/
├── api/              # API client functions
├── components/       # Reusable UI components
├── pages/            # Page components
├── store/            # Zustand state stores
└── types/            # TypeScript type definitions
```

- Use **React Query** for server state
- Use **Zustand** for client state
- Keep components small and focused

## Adding New Features

### New API Endpoint

1. Create schema in `backend/app/schemas/`
2. Add service method in `backend/app/services/`
3. Create route in `backend/app/api/`
4. Register blueprint if new file
5. Add tests in `backend/tests/`
6. Update API documentation

### New Frontend Page

1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Create API function if needed
4. Add link in navigation
5. Add tests

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Join discussions for broader topics

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
