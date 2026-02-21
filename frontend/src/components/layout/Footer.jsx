import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-[#2a2a38] bg-[#0a0a0f]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <span className="text-sm font-semibold tracking-tight text-white">
          Cinema<span className="text-red-600">Hub</span>
        </span>
        <p className="text-xs text-[#55556a]">
          &copy; {new Date().getFullYear()} CinemaHub. All rights reserved.
        </p>
        <nav className="flex gap-4 text-xs text-[#9999aa]">
          <Link to="/" className="hover:text-white transition-colors">Movies</Link>
          <Link to="/orders" className="hover:text-white transition-colors">Orders</Link>
        </nav>
      </div>
    </footer>
  )
}
