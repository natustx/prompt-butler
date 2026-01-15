# Prompt Butler Web UI Test Cases

Test cases for validating the web UI after terminal aesthetic restyling and API updates.

## Visual Styling

### TC-001: Terminal Font
- [ ] All text uses JetBrains Mono or Fira Code
- [ ] Font renders correctly on Chrome, Firefox, Safari

### TC-002: Color Scheme
- [ ] Background is near-black (#0a0a0a or similar)
- [ ] Primary accent is green (#00ff00 or terminal green)
- [ ] Secondary accent is amber (#ffb000 or similar)
- [ ] Text has sufficient contrast for readability

### TC-003: Terminal Effects
- [ ] Scanline overlay visible (subtle horizontal lines)
- [ ] CRT glow effect on text/borders
- [ ] No rounded corners on any component

### TC-004: Component Styling
- [ ] Buttons have visible borders, no fill
- [ ] Input fields have green/amber outlines on focus
- [ ] Tables use box-drawing characters or solid borders

## Prompt CRUD Operations

### TC-010: List Prompts
- [ ] Shows all prompts in table format
- [ ] Displays name, description, group, tags for each
- [ ] Handles empty state gracefully

### TC-011: View Prompt Detail
- [ ] Shows full system prompt content
- [ ] Shows user prompt section (if present)
- [ ] Displays tags and group
- [ ] Copy-to-clipboard button works

### TC-012: Create Prompt
- [ ] Form accepts: name, description, system prompt, user prompt, tags, group
- [ ] Tag input supports multiple tags
- [ ] Group dropdown/input shows existing groups
- [ ] Submit creates prompt, redirects to list
- [ ] Validation: name required, shows error if missing

### TC-013: Edit Prompt
- [ ] Pre-fills all fields with existing data
- [ ] Save updates prompt correctly
- [ ] Cancel returns to previous view without saving

### TC-014: Delete Prompt
- [ ] Confirmation dialog appears before delete
- [ ] Confirm deletes prompt, updates list
- [ ] Cancel closes dialog, no deletion

## Search & Filter

### TC-020: Fuzzy Search
- [ ] Search input filters prompts as you type
- [ ] Matches on name and description
- [ ] Shows "no results" for unmatched queries
- [ ] Clear search restores full list

### TC-021: Filter by Tag
- [ ] Tag filter dropdown shows all existing tags
- [ ] Selecting tag filters to matching prompts only
- [ ] Can clear tag filter

### TC-022: Filter by Group
- [ ] Group filter dropdown shows all existing groups
- [ ] Selecting group filters to matching prompts only
- [ ] Shows ungrouped prompts option
- [ ] Can clear group filter

## Tag Management

### TC-030: List Tags
- [ ] GET /api/tags returns all tags with usage counts
- [ ] UI displays tags correctly

### TC-031: Rename Tag
- [ ] Can rename tag across all prompts
- [ ] POST /api/tags/rename updates all affected prompts
- [ ] UI reflects renamed tag immediately

## Group Management

### TC-040: List Groups
- [ ] GET /api/groups returns all group names
- [ ] UI displays groups in filter/dropdown

### TC-041: Rename Group
- [ ] Can rename group (moves all prompts to new group)
- [ ] POST /api/groups/rename updates folder structure
- [ ] UI reflects renamed group immediately

## Edge Cases

### TC-050: Special Characters
- [ ] Prompt names with spaces work correctly
- [ ] Tags with special chars display properly
- [ ] Markdown content in prompts renders/escapes correctly

### TC-051: Long Content
- [ ] Long prompt names truncate with ellipsis in list
- [ ] Long descriptions don't break layout
- [ ] Large prompt content scrolls in detail view

### TC-052: Empty States
- [ ] No prompts: shows helpful message
- [ ] No tags: tag filter disabled or shows empty
- [ ] No groups: group filter shows only "ungrouped"
