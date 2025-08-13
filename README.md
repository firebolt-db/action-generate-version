# action-generate-version

Automatic version generation for Ecosystem components based on semantic versioning and conventional commit messages.

## Overview

This GitHub Action generates semantic version tags based on conventional commit messages following the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification and [Semantic Versioning](https://semver.org/) rules.

## Features

- **Automatic version calculation** based on commit message types
- **Conventional commits support** with proper semantic versioning
- **Breaking change detection** with explicit major release requirement
- **Prerelease support** for alpha, beta, and release candidate versions
- **Version finalization** from prerelease to stable versions

## Inputs

### `changes`
**Required:** Newline-separated list of commit messages since the last release. Typically obtained from `git log $OLD_TAG..HEAD --pretty=format:%s`.

### `old-tag`
**Required:** Previous semantic version tag (e.g., `1.0.1`, `2.3.0-alpha`).

### `prerelease-tag`
**Optional:** Tag for pre-release versions (e.g., `alpha`, `beta`, `rc`). Leave empty for stable releases.

### `major-release`
**Optional:** Trigger a major release. Any non-empty value indicates it's a major release. Required when breaking changes are detected.

## Outputs

### `new-tag`
The generated semantic version tag (e.g., `1.0.2`, `1.1.0`, `2.0.0-alpha`).

## Version Calculation Rules

### Commit Types and Version Bumps

- **`feat:`** commits → **Minor version bump** (1.0.0 → 1.1.0)
- **Other commits** (fix, docs, style, etc.) → **Patch version bump** (1.0.0 → 1.0.1)
- **Breaking changes** (commits with `!`) → **Major version bump** (1.0.0 → 2.0.0)
  - Requires explicit `major-release` input to prevent accidental major releases
- **Prerelease versions** → **Finalized** when no prerelease-tag is provided (1.0.0-alpha → 1.0.0)

### Breaking Changes

Commits with breaking changes are identified by the `!` suffix in the commit type:
```
feat!: remove deprecated API endpoint
fix!: change function signature
```

When breaking changes are detected, the action will fail unless `major-release` is explicitly set.

## Usage Examples

### Basic Usage

```yaml
- name: Generate version
  id: version
  uses: firebolt-db/action-generate-version@main
  with:
    changes: |
      feat: add new feature
      fix: resolve bug in parser
      docs: update README
    old-tag: '1.0.0'

- name: Use generated version
  run: echo "New version: ${{ steps.version.outputs.new-tag }}"
```

### With Prerelease

```yaml
- name: Generate alpha version
  id: version
  uses: firebolt-db/action-generate-version@main
  with:
    changes: |
      feat: experimental feature
    old-tag: '1.0.0'
    prerelease-tag: 'alpha'
```

### With Major Release

```yaml
- name: Generate major version
  id: version
  uses: firebolt-db/action-generate-version@main
  with:
    changes: |
      feat!: breaking API change
    old-tag: '1.0.0'
    major-release: 'true'
```

### Integration with Git Log

```yaml
- name: Get changes since last release
  id: changes
  run: |
    OLD_TAG=$(git describe --tags --abbrev=0)
    CHANGES=$(git log $OLD_TAG..HEAD --pretty=format:%s)
    echo "changes<<EOF" >> $GITHUB_OUTPUT
    echo "$CHANGES" >> $GITHUB_OUTPUT
    echo "EOF" >> $GITHUB_OUTPUT
    echo "old_tag=$OLD_TAG" >> $GITHUB_OUTPUT

- name: Generate version
  id: version
  uses: firebolt-db/action-generate-version@main
  with:
    changes: ${{ steps.changes.outputs.changes }}
    old-tag: ${{ steps.changes.outputs.old_tag }}
```

## Error Handling

The action will fail in the following scenarios:

1. **No changes detected**: When the changes input is empty
2. **Breaking changes without major-release**: When commits contain `!` but major-release is not set
3. **Invalid version format**: When old-tag is not a valid semantic version

## Conventional Commits Reference

This action supports the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New features (minor version bump)
- `fix:` - Bug fixes (patch version bump)
- `docs:` - Documentation changes (patch version bump)
- `style:` - Code style changes (patch version bump)
- `refactor:` - Code refactoring (patch version bump)
- `test:` - Test additions/modifications (patch version bump)
- `chore:` - Maintenance tasks (patch version bump)

Adding `!` to any type indicates a breaking change requiring a major version bump.

## License

This project is licensed under the same terms as the Firebolt ecosystem components.
