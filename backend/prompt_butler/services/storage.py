import logging
import os
import re
from pathlib import Path
from typing import Optional

import frontmatter
import yaml
from rapidfuzz import fuzz, process

from prompt_butler.models import Prompt

# User prompt separator in markdown files
USER_PROMPT_SEPARATOR = '---user---'
logger = logging.getLogger(__name__)


class PromptStorage:
    """Storage service for prompts using markdown with YAML frontmatter.

    File format:
    ```markdown
    ---
    name: code-review
    description: Reviews code for best practices
    tags: [coding, review]
    ---

    System prompt content here...

    ---user---

    User prompt content here (optional section)
    ```

    Group is derived from parent folder name. Filename is slugified from name.
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or Path(os.getenv('PROMPTS_DIR', os.path.expanduser('~/.prompts')))
        self.ensure_prompts_dir()

    def ensure_prompts_dir(self) -> None:
        """Create prompts directory if it doesn't exist."""
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def slugify(name: str) -> str:
        """Convert a name to a filesystem-safe slug."""
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def _get_prompt_path(self, name: str, group: str = '') -> Path:
        """Get the file path for a prompt given its name and group."""
        filename = f'{self.slugify(name)}.md'
        normalized_group = self._normalize_group(group)
        if normalized_group:
            return self.prompts_dir / normalized_group / filename
        return self.prompts_dir / filename

    def _parse_content(self, content: str) -> tuple[str, str]:
        """Parse content into system_prompt and user_prompt.

        Splits on ---user--- separator. Everything before is system_prompt,
        everything after is user_prompt.
        """
        if USER_PROMPT_SEPARATOR in content:
            parts = content.split(USER_PROMPT_SEPARATOR, 1)
            system_prompt = parts[0].strip()
            user_prompt = parts[1].strip() if len(parts) > 1 else ''
            return system_prompt, user_prompt
        return content.strip(), ''

    def _format_content(self, system_prompt: str, user_prompt: str = '') -> str:
        """Format system_prompt and user_prompt into file content."""
        if user_prompt:
            return f'{system_prompt}\n\n{USER_PROMPT_SEPARATOR}\n\n{user_prompt}'
        return system_prompt

    def _derive_group(self, file_path: Path) -> str:
        """Derive group from parent folder relative to prompts_dir."""
        try:
            relative = file_path.parent.relative_to(self.prompts_dir)
        except ValueError:
            return ''

        if relative == Path('.'):
            return ''
        if len(relative.parts) > 1:
            raise ValueError('Nested group paths are not supported')
        try:
            return self._normalize_group(relative.parts[0])
        except StorageError as exc:
            raise ValueError(str(exc)) from exc

    @staticmethod
    def _normalize_group(group: str) -> str:
        """Normalize and validate single-level group names."""
        normalized = group.strip()
        if not normalized:
            return ''
        if '/' in normalized or '\\' in normalized:
            raise StorageError('Group must be a single-level name without path separators.')
        return normalized

    def create(self, prompt: Prompt) -> Prompt:
        """Create a new prompt file.

        Raises:
            PromptExistsError: If a prompt with this name already exists
            StorageError: If file cannot be written
        """
        file_path = self._get_prompt_path(prompt.name, prompt.group)

        # Create group directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._write_prompt(file_path, prompt, mode='x')
            return prompt
        except FileExistsError as e:
            raise PromptExistsError(f'Prompt "{prompt.name}" already exists') from e
        except OSError as e:
            raise StorageError(f'Failed to create prompt: {e}') from e

    def read(self, name: str, group: str = '') -> Optional[Prompt]:
        """Read a prompt by name and optional group.

        Returns None if the prompt doesn't exist.
        """
        file_path = self._get_prompt_path(name, group)

        if not file_path.exists():
            # Try to find by name across all groups
            for match in self.prompts_dir.rglob(f'{self.slugify(name)}.md'):
                file_path = match
                break
            else:
                return None

        try:
            return self._read_prompt(file_path)
        except (OSError, ValueError) as e:
            raise StorageError(f'Failed to read prompt: {e}') from e

    def update(self, name: str, prompt: Prompt, group: str = '') -> Prompt:
        """Update an existing prompt.

        Raises:
            PromptNotFoundError: If the prompt doesn't exist
            StorageError: If file cannot be written
        """
        old_path = self._get_prompt_path(name, group)

        if not old_path.exists():
            # Try to find by name
            for match in self.prompts_dir.rglob(f'{self.slugify(name)}.md'):
                old_path = match
                break
            else:
                raise PromptNotFoundError(f'Prompt "{name}" not found')

        new_path = self._get_prompt_path(prompt.name, prompt.group)

        try:
            # If path changed (name or group changed), delete old file
            if old_path != new_path:
                old_path.unlink()
                new_path.parent.mkdir(parents=True, exist_ok=True)

            self._write_prompt(new_path, prompt, mode='w')
            return prompt
        except OSError as e:
            raise StorageError(f'Failed to update prompt: {e}') from e

    def delete(self, name: str, group: str = '') -> bool:
        """Delete a prompt by name.

        Returns True if deleted, False if not found.
        """
        file_path = self._get_prompt_path(name, group)

        if not file_path.exists():
            # Try to find by name
            for match in self.prompts_dir.rglob(f'{self.slugify(name)}.md'):
                file_path = match
                break
            else:
                return False

        try:
            file_path.unlink()
            return True
        except OSError as e:
            raise StorageError(f'Failed to delete prompt: {e}') from e

    def list_all(self, tag: Optional[str] = None, group: Optional[str] = None) -> list[Prompt]:
        """List all prompts with optional tag and group filters.

        Args:
            tag: Filter by tag (exact match)
            group: Filter by group (exact match, empty string for root)
        """
        prompts = []

        for file_path in self.prompts_dir.rglob('*.md'):
            try:
                prompt = self._read_prompt(file_path)
                if prompt:
                    # Apply filters
                    if tag is not None and tag not in prompt.tags:
                        continue
                    if group is not None and prompt.group != group:
                        continue
                    prompts.append(prompt)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                logger.warning('Failed to parse prompt file %s: %s', file_path, exc)
                continue

        return sorted(prompts, key=lambda p: (p.group, p.name))

    def search(self, query: str, limit: int = 10) -> list[Prompt]:
        """Fuzzy search prompts by name and description.

        Uses rapidfuzz for fuzzy matching.
        """
        if not query:
            return self.list_all()[:limit]

        all_prompts = self.list_all()

        if not all_prompts:
            return []

        # Create search strings combining name and description
        search_texts = [f'{p.name} {p.description}' for p in all_prompts]

        # Use rapidfuzz process.extract for fuzzy matching
        results = process.extract(
            query,
            search_texts,
            scorer=fuzz.WRatio,
            limit=limit,
        )

        # Map back to prompts
        matched_prompts = []
        for _match_text, score, index in results:
            if score >= 50:  # Minimum score threshold
                matched_prompts.append(all_prompts[index])

        return matched_prompts

    def get_all_tags(self) -> dict[str, int]:
        """Get all unique tags with usage counts."""
        tag_counts: dict[str, int] = {}

        for prompt in self.list_all():
            for tag in prompt.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    def get_all_groups(self) -> dict[str, int]:
        """Get all groups with prompt counts."""
        group_counts: dict[str, int] = {}

        for prompt in self.list_all():
            group = prompt.group or ''
            group_counts[group] = group_counts.get(group, 0) + 1

        return group_counts

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Rename a tag across all prompts.

        Args:
            old_tag: The tag to rename
            new_tag: The new tag name

        Returns:
            Number of prompts updated

        Raises:
            TagNotFoundError: If no prompts have the old_tag
            StorageError: If file operations fail
        """
        prompts_with_tag = [p for p in self.list_all() if old_tag in p.tags]

        if not prompts_with_tag:
            raise TagNotFoundError(f'Tag "{old_tag}" not found')

        updated_count = 0
        for prompt in prompts_with_tag:
            new_tags = [new_tag if t == old_tag else t for t in prompt.tags]
            updated_prompt = prompt.model_copy(update={'tags': new_tags})
            self.update(prompt.name, updated_prompt, prompt.group)
            updated_count += 1

        return updated_count

    def _read_prompt(self, file_path: Path) -> Prompt:
        """Read and parse a prompt file."""
        with open(file_path, encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Parse content into system_prompt and user_prompt
        system_prompt, user_prompt = self._parse_content(post.content)

        # Derive group from folder structure
        group = self._derive_group(file_path)

        return Prompt(
            name=post.metadata.get('name', file_path.stem),
            description=post.metadata.get('description', ''),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tags=post.metadata.get('tags', []),
            group=group,
        )

    def _serialize_prompt(self, prompt: Prompt) -> str:
        """Serialize a prompt into frontmatter-formatted content."""
        metadata = {
            'name': prompt.name,
            'description': prompt.description,
            'tags': prompt.tags,
        }
        content = self._format_content(prompt.system_prompt, prompt.user_prompt)
        post = frontmatter.Post(content, **metadata)
        return frontmatter.dumps(post)

    def _write_prompt(self, file_path: Path, prompt: Prompt, mode: str = 'w') -> None:
        """Write a prompt to a file."""
        payload = self._serialize_prompt(prompt)
        if mode == 'x':
            # Use O_EXCL for atomic create-if-not-exists.
            fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    fd = None
                    f.write(payload)
            finally:
                if fd is not None:
                    os.close(fd)
            return

        with open(file_path, mode, encoding='utf-8') as f:
            f.write(payload)


class PromptExistsError(Exception):
    """Raised when trying to create a prompt that already exists."""

    pass


class StorageError(Exception):
    """Raised when a storage operation fails."""

    pass


class PromptNotFoundError(Exception):
    """Raised when a prompt is not found."""

    pass


class TagNotFoundError(Exception):
    """Raised when a tag is not found."""

    pass
