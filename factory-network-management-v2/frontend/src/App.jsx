import { lazy, Suspense, useEffect, useState } from 'react';
import AppShell from './components/layout/AppShell';
import Placeholder from './pages/Placeholder';
import Dashboard from './pages/Dashboard';
import SwitchInventory from './pages/SwitchInventory';
import Settings from './pages/Settings';
import SwitchCatalog from './pages/SwitchCatalog';
import Passport from './pages/Passport';
import { navigation } from './config/navigation';

const Showcase = import.meta.env.DEV ? lazy(() => import('./pages/showcase/Showcase')) : null;
function getRoute() { return window.location.hash.replace('#/', '') || 'dashboard'; }

export default function App() {
  const [route, setRoute] = useState(getRoute);
  useEffect(() => {
    const update = () => { setRoute(getRoute()); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  const passportMatch = window.location.pathname.match(/^\/passport\/([^/]+)\/?$/);
  if (passportMatch) return <Passport key={passportMatch[1]} uid={passportMatch[1]} />;
  const page = navigation.find((item) => item.id === route);
  return <AppShell route={route}>{Showcase && route === 'showcase' ? <Suspense fallback={<p>Loading showcase…</p>}><Showcase/></Suspense> : route === 'catalog' ? <SwitchCatalog /> : route === 'settings' ? <Settings /> : route === 'inventory' ? <SwitchInventory /> : route === 'dashboard' || route === 'lines' ? <Dashboard linesOnly={route === 'lines'} /> : page ? <Placeholder page={page}/> : <div className="empty-state"><h1>Page not found</h1><a href="#/dashboard" className="button button-secondary">Back to Dashboard</a></div>}</AppShell>;
}
