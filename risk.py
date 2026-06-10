[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "aibrief"
version = "0.5.1"
description = "Multi-agent Aibrief إحاطة AI intelligence curation framework"
requires-python = ">=3.10"
authors = [{ name = "Aibrief إحاطة AI" }]
license = { text = "MIT" }
dependencies = ["sentry-sdk>=2.20.0"]
readme = "README.md"
keywords = ["ai", "intelligence", "agents", "briefing", "arabic"]
classifiers = [
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
  "License :: OSI Approved :: MIT License",
  "Topic :: Text Processing",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pre-commit>=4.0.0"]

[project.scripts]
aibrief = "aibrief.cli:main"

[tool.setuptools.packages.find]
include = ["aibrief*"]

[project.urls]
Homepage = "https://example.invalid/aibrief"
Repository = "https://example.invalid/aibrief"
