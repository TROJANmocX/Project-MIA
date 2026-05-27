# Contributing to MIA

Thank you for your interest in contributing to MIA (My Intelligent Assistant). This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Improving Documentation](#improving-documentation)
  - [Submitting Code Changes](#submitting-code-changes)
- [Development Setup](#development-setup)
- [Project Architecture Overview](#project-architecture-overview)
- [Code Style Guidelines](#code-style-guidelines)
- [Commit Message Convention](#commit-message-convention)
- [Branch Naming Convention](#branch-naming-convention)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Common Contribution Areas](#common-contribution-areas)
- [Getting Help](#getting-help)

---

## Code of Conduct

By participating in this project, you agree to treat all contributors and maintainers with respect. We are committed to providing a welcoming and inclusive environment for everyone, regardless of background or experience level.

- Be respectful and constructive in all interactions.
- Accept constructive criticism gracefully.
- Focus on what is best for the project and its community.
- Show empathy toward other contributors.

---

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please open a GitHub Issue with the following information:

1. **Title**: A clear, concise description of the bug.
2. **Environment**: Your operating system, Python version, and relevant hardware (microphone, webcam).
3. **Steps to Reproduce**: A numbered list of steps that reliably reproduce the issue.
4. **Expected Behavior**: What you expected to happen.
5. **Actual Behavior**: What actually happened, including error messages and tracebacks.
6. **Screenshots / Logs**: If applicable, include screenshots of the UI or console output.

Use this template when opening a bug report:

```
**Bug Description**
A clear description of the bug.

**Environment**
- OS: Windows 11 / macOS 14 / Ubuntu 24.04
- Python: 3.12.x
- MIA Version: 1.0.0
- Hardware: [microphone model, webcam model if relevant]

**Steps to Reproduce**
1. Launch MIA with `python mia_main.py`
2. Navigate to Commands page
3. Click "Start Listening"
4. Say "open youtube"

**Expected Behavior**
YouTube should open in the default browser.

**Actual Behavior**
Nothing happens. Console shows: [paste error here]

**Additional Context**
Any other relevant information.
```

### Suggesting Features

Feature requests are welcome. Please open a GitHub Issue with:

1. **Title**: A clear description of the feature.
2. **Problem Statement**: What problem does this feature solve?
3. **Proposed Solution**: How you envision the feature working.
4. **Alternatives Considered**: Any alternative approaches you thought about.
5. **Additional Context**: Mockups, diagrams, or references to similar features in other projects.

### Improving Documentation

Documentation improvements are always appreciated. This includes:

- Fixing typos or unclear wording in the README, code comments, or docstrings.
- Adding usage examples.
- Writing tutorials or guides.
- Improving inline code documentation.

For documentation-only changes, you can submit a pull request directly without opening an issue first.

### Submitting Code Changes

For code contributions, please follow the full workflow described in the sections below.

---

## Development Setup

1. **Fork the repository** on GitHub.

2. **Clone your fork**:

   ```sh
   git clone https://github.com/<your-username>/Project-MIA.git
   cd Project-MIA
   ```

3. **Add the upstream remote**:

   ```sh
   git remote add upstream https://github.com/TROJANmocX/Project-MIA.git
   ```

4. **Create a virtual environment**:

   ```sh
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

5. **Install dependencies**:

   ```sh
   pip install -r requirements.txt
   ```

   For development, also install testing tools:

   ```sh
   pip install pytest flake8
   ```

6. **Verify the setup**:

   ```sh
   python mia_main.py
   ```

   The neon control center should launch. If any component shows "Missing" on the About page, install the corresponding package.

---

## Project Architecture Overview

Understanding where to make changes:

```
PROJECT - MIA/
|
|-- mia_main.py              # GUI entry point -- edit for UI changes
|
|-- mia_assistant/            # Stable core modules
|   |-- command_parser.py     # Add new voice commands here
|   |-- actions.py            # Add new system actions here
|   |-- tts_response.py       # Add new TTS personalities here
|   |-- ollama_client.py      # Modify LLM integration here
|   |-- agent.py              # Add new agent tools here
|   |-- voice_activation.py   # Modify wake word behavior here
|   |-- hud_overlay.py        # Modify visual feedback here
|   |-- mood_detection.py     # Modify emotion detection here
|   |-- combo_controller.py   # Modify combo mode timing here
|
|-- mia/                      # Experimental next-gen modules
|   |-- llm/canary_engine.py  # Transformer-based intent parsing
|   |-- llm/intent_guard.py   # Safety validation
|
|-- gesture_control/          # Gesture recognition
|   |-- main.py               # Add new gestures here
|
|-- server/                   # REST API
|   |-- api.py                # Add new API endpoints here
|
|-- tests/                    # Test suite
|   |-- test_command_parser.py
```

---

## Code Style Guidelines

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) for code formatting.
- Use 4 spaces for indentation (no tabs).
- Maximum line length: 120 characters.
- Use type hints for function signatures where practical.
- Write docstrings for all public functions and classes.
- Use descriptive variable names. Avoid single-letter variables except for loop counters.

### Naming Conventions

| Element      | Convention      | Example               |
|-------------|-----------------|------------------------|
| Functions    | snake_case      | `launch_app()`         |
| Variables    | snake_case      | `wake_word`            |
| Classes      | PascalCase      | `VoiceWorker`          |
| Constants    | UPPER_SNAKE     | `API_URL`              |
| Files        | snake_case      | `command_parser.py`    |
| Private      | _leading_under  | `_listen_loop()`       |

### Imports

Order imports as follows, separated by blank lines:

1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
import os
import sys
import threading

import cv2
import mediapipe as mp
from fastapi import FastAPI

from mia_assistant.actions import execute_action
from mia_assistant.tts_response import speak
```

### Comments

- Use comments to explain **why**, not **what**.
- Keep comments up to date when changing code.
- Use `# TODO:` for planned improvements.
- Use `# FIXME:` for known issues that need fixing.

---

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type       | Description                                       |
|------------|---------------------------------------------------|
| `feat`     | A new feature                                     |
| `fix`      | A bug fix                                         |
| `docs`     | Documentation changes only                        |
| `style`    | Code style changes (formatting, no logic change)  |
| `refactor` | Code restructuring without changing behavior      |
| `test`     | Adding or updating tests                          |
| `chore`    | Build process, dependency updates, tooling        |
| `perf`     | Performance improvements                          |

### Scope

The scope is optional and indicates the module affected:

- `voice` -- Voice activation, STT, wake word
- `gesture` -- Gesture recognition
- `tts` -- Text-to-speech
- `hud` -- HUD overlay
- `ui` -- Desktop GUI (mia_main.py)
- `api` -- FastAPI server
- `llm` -- Ollama, Canary, agent
- `actions` -- System actions
- `parser` -- Command parsing
- `mood` -- Mood detection

### Examples

```
feat(gesture): add pinch-to-zoom gesture detection
fix(voice): handle microphone permission denied on Windows 11
docs: update README with architecture diagrams
refactor(tts): extract personality config to separate file
test(parser): add unit tests for weather command parsing
chore: update mediapipe to 0.10.x
```

---

## Branch Naming Convention

Create branches from `main` using this format:

```
<type>/<short-description>
```

Examples:

```
feat/gesture-pinch-zoom
fix/mic-permission-error
docs/architecture-diagrams
refactor/tts-config-extract
```

---

## Pull Request Process

1. **Sync with upstream** before starting work:

   ```sh
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:

   ```sh
   git checkout -b feat/your-feature-name
   ```

3. **Make your changes** following the code style guidelines.

4. **Test your changes** (see [Testing](#testing) below).

5. **Commit your changes** following the commit message convention.

6. **Push to your fork**:

   ```sh
   git push origin feat/your-feature-name
   ```

7. **Open a Pull Request** on GitHub with:

   - A clear title following the commit message convention.
   - A description of what changed and why.
   - Screenshots or recordings for UI changes.
   - Reference to any related issues (e.g., "Fixes #42").

8. **Respond to review feedback**. Maintainers may request changes. Push additional commits to the same branch to update the PR.

### PR Checklist

Before submitting, verify:

- [ ] Code follows the project style guidelines.
- [ ] New functions have docstrings.
- [ ] Existing tests still pass.
- [ ] New features have corresponding tests (where practical).
- [ ] No new warnings or errors in the console.
- [ ] The UI renders correctly (if applicable).
- [ ] The commit history is clean and follows conventions.

---

## Testing

### Running Existing Tests

```sh
pytest tests/ -v
```

### Writing New Tests

Place test files in the `tests/` directory with the naming convention `test_<module>.py`.

Example test structure:

```python
# tests/test_actions.py

from mia_assistant.actions import launch_app, search_web

def test_search_web_returns_message():
    result = search_web("python tutorials")
    assert "Searching for" in result

def test_search_web_empty_query():
    result = search_web("")
    assert "What should I search for?" in result
```

### Manual Testing Checklist

For UI or integration changes, manually verify:

1. Launch MIA with `python mia_main.py`.
2. Navigate through all four pages (Home, Commands, Settings, About).
3. Click "Start MIA" and verify component status indicators turn green.
4. Test voice commands (if modifying voice/parser modules).
5. Test gesture recognition (if modifying gesture modules).
6. Verify the system tray icon works (show, hide, quit).
7. Check that "Stop MIA" cleanly terminates all processes.

---

## Common Contribution Areas

Here are some areas where contributions are especially welcome:

### Beginner-Friendly

- Fix typos in documentation or code comments.
- Add docstrings to functions that are missing them.
- Add unit tests for existing modules.
- Improve error messages for better user experience.

### Intermediate

- Add new voice command intents to `command_parser.py`.
- Add new gesture types to `gesture_control/main.py`.
- Add new system actions to `mia_assistant/actions.py`.
- Improve the HUD overlay with richer visual feedback.
- Add new personality styles to `tts_response.py`.

### Advanced

- Integrate offline STT (Whisper, Vosk) as an alternative to Google STT.
- Implement the plugin system for third-party extensions.
- Add cross-platform support for macOS and Linux actions.
- Improve the Canary Engine with better prompt engineering.
- Add gesture-based cursor control with MediaPipe.
- Implement multi-monitor HUD overlay support.

---

## Getting Help

If you have questions about contributing:

1. **Check existing issues** on GitHub -- your question may already be answered.
2. **Open a new issue** with the "question" label if you need clarification.
3. **Review the README** for architecture details and module descriptions.

We are happy to help new contributors get started. Do not hesitate to ask if something is unclear.

---

Thank you for helping make MIA better.
