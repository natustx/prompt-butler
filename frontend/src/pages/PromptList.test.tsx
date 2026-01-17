import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { PromptList } from './PromptList';
import { usePrompts } from '../hooks/usePrompts';
import { groupApi } from '../services/api';

vi.mock('../hooks/usePrompts', () => ({
  usePrompts: vi.fn(),
}));

vi.mock('../services/api', () => ({
  groupApi: {
    listGroups: vi.fn(),
  },
}));

const mockedUsePrompts = vi.mocked(usePrompts);
const mockedListGroups = vi.mocked(groupApi.listGroups);

describe('PromptList', () => {
  it('filters prompts by selected group', async () => {
    const user = userEvent.setup();
    mockedUsePrompts.mockReturnValue({
      prompts: [
        {
          name: 'work-prompt',
          description: 'Work prompt',
          system_prompt: 'System content',
          user_prompt: '',
          tags: ['work'],
          group: 'work',
        },
        {
          name: 'root-prompt',
          description: 'Root prompt',
          system_prompt: 'System content',
          user_prompt: '',
          tags: [],
          group: '',
        },
      ],
      loading: false,
      error: null,
      refetch: vi.fn(),
      deletePrompt: vi.fn().mockResolvedValue(undefined),
    });

    mockedListGroups.mockResolvedValue([
      { group: 'work', count: 1 },
      { group: '', count: 1 },
    ]);

    render(
      <MemoryRouter initialEntries={['/']}>
        <PromptList />
      </MemoryRouter>
    );

    await waitFor(() => expect(mockedListGroups).toHaveBeenCalled());

    expect(screen.getByText('work-prompt')).toBeInTheDocument();
    expect(screen.getByText('root-prompt')).toBeInTheDocument();

    const select = screen.getByLabelText(/filter:group/i);
    await user.selectOptions(select, 'work');

    expect(screen.getByText('work-prompt')).toBeInTheDocument();
    expect(screen.queryByText('root-prompt')).not.toBeInTheDocument();
  });
});
