
# Contributing to Plagg Bot

Thank you for your interest in contributing to Plagg Bot! This document provides guidelines and information for contributors.

## 🎯 How to Contribute

### Reporting Bugs
1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include detailed reproduction steps
4. Provide system information and logs
5. Add screenshots if applicable

### Suggesting Features
1. Check if the feature already exists or is planned
2. Use the feature request template
3. Explain the use case and benefits
4. Provide mockups or examples if possible

### Code Contributions
1. Fork the repository
2. Create a feature branch from `main`
3. Write clean, documented code
4. Test your changes thoroughly
5. Submit a pull request

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- Discord Bot Token
- Google Gemini API Key (optional)
- Git

### Local Development
```bash
# Clone your fork
git clone https://github.com/yourusername/plagg-bot.git
cd plagg-bot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your tokens

# Run the bot
python main.py
```

### Testing
- Test new features with multiple users
- Verify database operations don't corrupt data
- Check memory usage for long-running operations
- Test edge cases and error conditions

## 📝 Code Style Guidelines

### Python Style
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write descriptive variable and function names
- Keep functions focused and under 50 lines
- Use docstrings for all public functions

### Example Code Style
```python
async def calculate_damage(
    base_damage: int, 
    attacker_stats: Dict[str, int], 
    target_defense: int
) -> int:
    """
    Calculate final damage after applying stats and defense.
    
    Args:
        base_damage: Base damage before modifications
        attacker_stats: Dictionary of attacker's stats
        target_defense: Target's defense value
        
    Returns:
        Final damage value after calculations
    """
    # Implementation here
    pass
```

### Discord.py Best Practices
- Use proper error handling for API calls
- Respect rate limits and implement backoff
- Use embeds for rich content
- Implement proper permission checks
- Clean up resources (views, files, etc.)

## 🏗️ Architecture Guidelines

### Adding New Features
1. Create new cog files for major features
2. Update game_data.py for new items/classes
3. Add helper functions to utils/
4. Update database schema if needed
5. Add comprehensive error handling

### Database Design
- Use descriptive keys for Replit DB
- Implement data validation
- Add migration support for schema changes
- Consider performance implications
- Document data structures

### Bot Commands
- Use clear, intuitive command names
- Implement proper permission checks
- Add helpful error messages
- Support both text and slash commands
- Include usage examples in help

## 🎮 Game Design Philosophy

### Balance Principles
- No single strategy should dominate
- Multiple viable paths to success
- Meaningful choices at each level
- Progression should feel rewarding
- Avoid power creep in updates

### User Experience
- Commands should be discoverable
- Feedback should be immediate and clear
- Complex systems need good documentation
- Error messages should be helpful
- UI should be consistent across features

### Content Guidelines
- Maintain Miraculous Ladybug theme
- Keep content family-friendly
- Respect intellectual property
- Add personality to bot responses
- Include cheese references for Plagg

## 📋 Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No breaking changes (or documented)
- [ ] Features work with existing systems

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Tested with multiple users
- [ ] Edge cases considered
- [ ] No data corruption

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🐛 Issue Templates

### Bug Report
```markdown
**Describe the bug**
Clear description of the problem

**To Reproduce**
Steps to reproduce the behavior

**Expected behavior**
What should happen

**Screenshots**
If applicable, add screenshots

**Environment:**
- Bot version:
- Python version:
- Operating System:

**Additional context**
Any other relevant information
```

### Feature Request
```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of desired feature

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Mockups, examples, or other context
```

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- In-bot credits command
- Special Discord roles (if applicable)
- Release notes for significant contributions

## 📞 Getting Help

- **Discord**: Join our development Discord
- **Issues**: Use GitHub issues for questions
- **Email**: Contact maintainers directly
- **Documentation**: Check the wiki for guides

## 📄 Code of Conduct

### Our Standards
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn
- Collaborate openly
- Respect different viewpoints

### Unacceptable Behavior
- Harassment or discrimination
- Trolling or inflammatory comments
- Personal attacks
- Publishing private information
- Commercial spam

Thank you for contributing to Plagg Bot! 🧀
```
