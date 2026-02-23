import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import { useState, useEffect, lazy, Suspense } from 'react'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import ProtectedRoute from './components/ui/ProtectedRoute'
import Spinner from './components/ui/Spinner'

// ─── lazy pages ───────────────────────────────────────────────────────────────
const Home           = lazy(() => import('./pages/Home'))
const MovieDetail    = lazy(() => import('./pages/MovieDetail'))
const Login          = lazy(() => import('./pages/Login'))
const Register       = lazy(() => import('./pages/Register'))
const Activate       = lazy(() => import('./pages/Activate'))
const Profile        = lazy(() => import('./pages/Profile'))
const Cart           = lazy(() => import('./pages/Cart'))
const Orders         = lazy(() => import('./pages/Orders'))
const PaymentSuccess = lazy(() => import('./pages/PaymentSuccess'))
const PaymentCancel  = lazy(() => import('./pages/PaymentCancel'))
const Notifications  = lazy(() => import('./pages/Notifications'))
const Admin          = lazy(() => import('./pages/Admin'))

// ─── shell ────────────────────────────────────────────────────────────────────
function AppShell({ cartCount, hasUnread }) {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar cartCount={cartCount} hasUnread={hasUnread} />
      <main className="flex-1">
        <Suspense fallback={<Spinner className="min-h-[60vh]" />}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}

// ─── root ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [cartCount, setCartCount] = useState(0)
  const [hasUnread, setHasUnread] = useState(false)

  // Listen for cart mutations dispatched from any page/component
  useEffect(() => {
    const handler = (e) => setCartCount((c) => Math.max(0, c + (e.detail?.delta ?? 0)))
    window.addEventListener('cinemahub:cart', handler)
    return () => window.removeEventListener('cinemahub:cart', handler)
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell cartCount={cartCount} hasUnread={hasUnread} />}>
          {/* Public */}
          <Route index                element={<Home />} />
          <Route path="movies/:id"    element={<MovieDetail />} />
          <Route path="login"         element={<Login />} />
          <Route path="register"      element={<Register />} />
          <Route path="activate"      element={<Activate />} />

          {/* Protected */}
          <Route path="profile" element={
            <ProtectedRoute><Profile /></ProtectedRoute>
          } />
          <Route path="cart" element={
            <ProtectedRoute><Cart setCartCount={setCartCount} /></ProtectedRoute>
          } />
          <Route path="orders" element={
            <ProtectedRoute><Orders /></ProtectedRoute>
          } />
          <Route path="payment/success" element={
            <ProtectedRoute><PaymentSuccess /></ProtectedRoute>
          } />
          <Route path="payment/cancel" element={
            <ProtectedRoute><PaymentCancel /></ProtectedRoute>
          } />
          <Route path="notifications" element={
            <ProtectedRoute><Notifications setHasUnread={setHasUnread} /></ProtectedRoute>
          } />
          <Route path="admin" element={
            <ProtectedRoute><Admin /></ProtectedRoute>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
