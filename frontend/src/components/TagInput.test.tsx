import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TagInput } from './TagInput';
import { tagApi } from '../services/api';

vi.mock('../services/api', () => ({
  tagApi: {
    listTags: vi.fn(),
  },
}));

const mockedListTags = vi.mocked(tagApi.listTags);

describe('TagInput autocomplete', () => {
  beforeEach(() => {
    mockedListTags.mockResolvedValue([
      { tag: 'alpha', count: 2 },
      { tag: 'beta', count: 1 },
    ]);
  });

  it('shows suggestions and allows selecting existing tags', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<TagInput tags={[]} onChange={handleChange} />);

    await waitFor(() => expect(mockedListTags).toHaveBeenCalled());

    const input = screen.getByRole('textbox');
    await user.type(input, 'alp');

    const suggestion = await screen.findByText('alpha');
    await user.click(suggestion);

    expect(handleChange).toHaveBeenCalledWith(['alpha']);
  });

  it('shows create option when no suggestions match', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<TagInput tags={[]} onChange={handleChange} />);

    await waitFor(() => expect(mockedListTags).toHaveBeenCalled());

    const input = screen.getByRole('textbox');
    await user.type(input, 'gamma');

    const createLabel = await screen.findByText('Create new tag:');
    expect(createLabel).toBeInTheDocument();

    const createButton = createLabel.closest('button');
    expect(createButton).not.toBeNull();
    if (createButton) {
      await user.click(createButton);
    }

    expect(handleChange).toHaveBeenCalledWith(['gamma']);
  });

  it('allows keyboard navigation to the create option', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<TagInput tags={[]} onChange={handleChange} />);

    await waitFor(() => expect(mockedListTags).toHaveBeenCalled());

    const input = screen.getByRole('textbox');
    await user.type(input, 'delta');
    await user.keyboard('{ArrowDown}{Enter}');

    expect(handleChange).toHaveBeenCalledWith(['delta']);
  });
});
