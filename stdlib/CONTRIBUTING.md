# Contributing to SpecQL stdlib

## Philosophy

stdlib entities must be:
1. **Generic**: Useful across multiple application domains
2. **Production-tested**: Proven in real applications
3. **Well-documented**: Clear descriptions for all fields
4. **Standard-based**: Follow ISO or industry standards where applicable
5. **Minimal dependencies**: Only reference other stdlib entities

## Contribution Process

1. **Propose entity**: Open issue with entity definition and use case
2. **Review**: Community reviews for genericness and design quality
3. **Submit PR**: Include entity YAML + documentation
4. **Validation**: Automated tests verify no external dependencies
5. **Merge**: Entity becomes part of next stdlib version

## Entity Requirements

- All fields must have descriptions
- Actions should be generic (create, update, delete, etc.)
- No application-specific business logic
- Follow SpecQL naming conventions
- Include example usage in comments
