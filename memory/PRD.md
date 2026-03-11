# Joyn Portal PRD

## Original Problem Statement
User requested to remove the "How it works" section from marketplace/index.html and put it on the right side of the "AI Staff Marketplace" hero section, similar to how visuals are displayed for the right side of Creator Studio page.

## Architecture
- Static HTML website with multiple pages (index.html, marketplace/index.html, creator-studio.html, etc.)
- CSS-in-HTML styling with CSS variables for theming
- JavaScript for interactive components

## User Personas
- **Businesses**: Looking to hire AI staff from the marketplace
- **Creators/Builders**: Domain experts wanting to build AI staff

## Core Requirements (Static)
- Maintain consistent visual language across pages
- Hero sections with 2-column grid layout (content left, visual panel right)
- Timeline-style visual panels for process steps

## What's Been Implemented
### 2026-03-11
- **Layout Change**: Moved "How It Works" section from separate section to right side of hero
- Added CSS classes for hero grid layout (.hero-grid)
- Added visual timeline panel styles (.hiw-visual-panel, .hiw-visual-step, etc.)
- Removed old hiw-compact section HTML
- Updated responsive breakpoints for new layout
- Visual consistency achieved with Creator Studio page pattern

## Files Modified
- `/app/marketplace/index.html` - Hero section restructured, CSS added, old section removed

## Prioritized Backlog
### P0 (Critical)
- None

### P1 (High)
- None

### P2 (Nice to Have)
- Consider adding hover effects on timeline steps
- Could add animation on page load for timeline

## Next Tasks
- User to review and provide feedback
- Deploy to production via GitHub save
