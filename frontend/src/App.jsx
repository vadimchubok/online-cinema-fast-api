import { BrowserRouter, Routes, Route, Outlet, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import ProtectedRoute from './components/ui/ProtectedRoute'
import Spinner from './components/ui/Spinner'
import { useAuth } from './context/AuthContext'
import { lazy, Suspense } from 'react'

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

// ─── shell layout ────────────────────────────────────────────────────────────
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
  const { isAuthenticated } = useAuth()
  const [cartCount, setCartCount] = useState(0)
  const [hasUnread, setHasUnread] = useState(false)

  // Page-level callbacks passed down via context or props if needed
  // For now Navbar receives counts directly; pages call refreshCart / refreshNotifications
  // when they mutate cart/notification state.

  return (
    <BrowserRouter>
      <Routes>
        {/* Public + protected share the same shell */}
        <Route element={<AppShell cartCount={cartCount} hasUnread={hasUnread} />}>
          {/* Public */}
          <Route index element={<Home />} />
          <Route path="movies/:id" element={<MovieDetail />} />
          <Route path="login"    element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="activate" element={<Activate />} />

          {/* Protected */}
          <Route path="profile" element={
            <ProtectedRoute><Profile /></ProtectedRoute>
          } />
          <Route path="cart" element={
            <ProtectedRoute><Cart onCartChange={setCartCount} /></ProtectedRoute>
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
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
