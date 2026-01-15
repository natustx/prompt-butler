import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { PromptList } from './pages/PromptList';
import { PromptForm } from './pages/PromptForm';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<PromptList />} />
          <Route path="new" element={<PromptForm />} />
          <Route path="edit/:group/:name" element={<PromptForm />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;