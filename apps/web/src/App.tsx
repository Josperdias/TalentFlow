import { Navigate, Route, Routes } from 'react-router-dom';
import { SyncProvider, useAuth } from './state';
import Shell from './components/Shell';
import Login from './pages/Login';
import Overview from './pages/Overview';
import Jobs from './pages/Jobs';
import JobDetail from './pages/JobDetail';
import Candidates from './pages/Candidates';
import People from './pages/People';
import Development from './pages/Development';
import Leaves from './pages/Leaves';
import Account from './pages/Account';
import Portal from './pages/Portal';
import { Skeleton, ErrorState } from './components/ui';

export default function App() {
  const { status, user, error, retry } = useAuth();
  if (status === 'loading') return <main style={{ padding: 32 }}><Skeleton rows={4} /></main>;
  if (status === 'unreachable') return <main style={{ padding: 32, maxWidth: 560 }}><ErrorState error={new Error(error)} onRetry={retry} /></main>;
  if (status === 'anon' || !user) return <Login />;
  const home = user.role === 'candidate' ? '/minhas-candidaturas' : '/';
  return (
    <SyncProvider enabled={user.role !== 'candidate'}>
      <Routes>
        <Route element={<Shell />}>
          <Route index element={user.role === 'candidate' ? <Navigate to={home} replace /> : <Overview />} />
          <Route path="vagas" element={<Jobs />} />
          <Route path="vagas/:id" element={<JobDetail />} />
          <Route path="candidatos" element={<Candidates />} />
          <Route path="pessoas" element={<People />} />
          <Route path="desenvolvimento" element={<Development />} />
          <Route path="ausencias" element={<Leaves />} />
          <Route path="minhas-candidaturas" element={<Portal />} />
          <Route path="conta" element={<Account />} />
          <Route path="*" element={<Navigate to={home} replace />} />
        </Route>
      </Routes>
    </SyncProvider>
  );
}
