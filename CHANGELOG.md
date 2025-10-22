# Changelog

All notable changes to the Wretched & Alone Game Generator will be documented in this file.

## [Unreleased] - 2025-10-22

### Added

#### CLI Improvements
- **New `new` command** - Quickly scaffold new game projects from template
- **Colored terminal output** - Beautiful, informative output with color-coded messages
- **Progress indicators** - Clear visual feedback during build process
- **Global options** - `--no-color` and `--debug` flags for all commands
- **Better error messages** - Detailed, helpful error reporting
- **HTML minification** - Optional `--minify` flag for build command

#### Code Quality
- **Type hints** - Full type annotations throughout builder.py
- **Custom exceptions** - ValidationError and BuildError for better error handling
- **Comprehensive docstrings** - Detailed documentation for all classes and methods
- **Better error handling** - Try/catch blocks with informative error messages
- **Improved path handling** - Safer file operations with Path objects
- **load_all() method** - Convenience method to load all config files at once

#### Accessibility & UX
- **Responsive design** - Mobile-friendly layout with CSS media queries
- **ARIA labels** - Full accessibility support for screen readers
- **ARIA live regions** - Dynamic content updates announced to assistive technologies
- **Keyboard navigation** - Better focus styles and keyboard support
- **Print styles** - Journal-optimized print layout
- **Loading states** - Visual feedback during interactions
- **Better history display** - Improved card history styling
- **Stability color coding** - Visual indicators for stability levels (safe/danger/critical)
- **Screen reader only content** - Hidden descriptive text for better accessibility

#### Template Enhancements
- **Meta tags** - SEO and mobile-optimized meta information
- **Improved modals** - Better modal accessibility with proper ARIA roles
- **Enhanced buttons** - Better button states and visual feedback
- **Game end screen** - Improved styling for win/loss screens

### Changed

#### Build Process
- **Better validation** - Enhanced validation with card field checking
- **Improved CSS generation** - Better font loading and variable generation
- **Enhanced output path handling** - Safer filename generation
- **Better template loading** - Improved template directory handling

#### CLI Commands
- **build** - Now shows detailed progress, file sizes, and helpful completion messages
- **validate** - Enhanced with step-by-step validation progress
- **info** - Improved formatting with better visual presentation

### Documentation
- Updated README.md with new features and commands
- Added comprehensive docstrings to all functions
- Created CHANGELOG.md to track changes
- Improved code comments throughout

### Technical Details

#### Dependencies
- All existing dependencies maintained
- Optional: htmlmin for minification feature

#### Browser Compatibility
- Improved mobile browser support
- Better responsive layout on all screen sizes
- Enhanced print layout for journal export

#### Accessibility
- WCAG 2.1 compliant ARIA labels
- Keyboard navigation support
- Screen reader optimization
- Focus management for modals
- Live region updates for dynamic content

---

## [1.0.0] - Previous

### Initial Features
- YAML configuration parsing
- CSS and JavaScript generation
- HTML template rendering
- Card deck mechanics
- Dice rolling system
- Stability/tower mechanics
- Token management
- Auto-save functionality
- Journal with download
- Win/loss conditions
- Basic CLI (build, validate, info commands)
